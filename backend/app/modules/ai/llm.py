import logging
import os
import threading
import time
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import Settings

logger = logging.getLogger(__name__)

DEFAULT_CIRCUIT_BREAKER_TTL_SECONDS: float = 300.0  # 5 minutes

OPTIONAL_PROVIDER_EXTRAS: dict[str, str] = {
    "anthropic": "uv sync --extra anthropic",
    "google_genai": "uv add langchain-google-genai",
    "mistralai": "uv add langchain-mistralai",
}


class LLMConfigurationError(RuntimeError):
    """Raised when LLM credentials are not configured for AI workflows."""


class LLMProviderPackageError(RuntimeError):
    """Raised when the selected LLM provider's optional LangChain adapter is not installed."""


class QuarantinedProviderError(RuntimeError):
    """Raised when an LLM provider is temporarily quarantined due to 429/401 errors."""


def is_circuit_breaker_error(exc: BaseException) -> bool:
    """Return True if exception indicates a 429 (quota / rate limit) or 401 (auth failure)."""
    # Check status_code or code attribute
    code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if isinstance(code, int) and code in (401, 403, 404, 429):
        return True

    # Check response attribute (requests, httpx, etc.)
    response = getattr(exc, "response", None)
    if response is not None:
        resp_code = getattr(response, "status_code", None)
        if isinstance(resp_code, int) and resp_code in (401, 403, 404, 429):
            return True

    # Check exception type name
    type_name = type(exc).__name__.lower()
    if any(
        k in type_name
        for k in (
            "ratelimit",
            "authentication",
            "permissiondenied",
            "resourceexhausted",
            "unauthorized",
        )
    ):
        return True

    # Check message keywords
    msg = str(exc).lower()
    return any(
        k in msg
        for k in (
            "429",
            "401",
            "404",
            "quota",
            "rate limit",
            "rate_limit",
            "insufficient_quota",
            "credits remaining",
            "unauthorized",
            "invalid api key",
            "not found",
        )
    )


class LLMCircuitBreaker:
    """Thread-safe in-memory circuit breaker putting failing LLM providers in quarantine."""

    def __init__(self, default_ttl_seconds: float = DEFAULT_CIRCUIT_BREAKER_TTL_SECONDS) -> None:
        self._default_ttl = default_ttl_seconds
        # Maps provider name to (expiry_monotonic, failure_reason)
        self._quarantine: dict[str, tuple[float, str]] = {}
        self._lock = threading.Lock()

    def record_failure(
        self,
        provider: str,
        reason: str,
        ttl_seconds: float | None = None,
    ) -> None:
        """Quarantine a provider for ttl_seconds (default 5 minutes)."""
        p = provider.strip().lower()
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expiry = time.monotonic() + ttl
        with self._lock:
            self._quarantine[p] = (expiry, reason)
        logger.warning(
            "Circuit Breaker: quarantined LLM provider '%s' for %ds. Reason: %s",
            p,
            int(ttl),
            reason,
        )

    def is_quarantined(self, provider: str) -> bool:
        """Check if provider is currently quarantined. Cleans up expired entry if elapsed."""
        p = provider.strip().lower()
        with self._lock:
            entry = self._quarantine.get(p)
            if not entry:
                return False
            expiry, _reason = entry
            if time.monotonic() < expiry:
                return True
            # Quarantine expired
            del self._quarantine[p]
            logger.info("Circuit Breaker: quarantine expired for provider '%s'; re-armed.", p)
            return False

    def get_quarantined_providers(self) -> list[str]:
        """Return list of currently quarantined provider names."""
        with self._lock:
            now = time.monotonic()
            active: list[str] = []
            expired: list[str] = []
            for p, (expiry, _) in self._quarantine.items():
                if now < expiry:
                    active.append(p)
                else:
                    expired.append(p)
            for p in expired:
                del self._quarantine[p]
            return sorted(active)

    def clear(self, provider: str | None = None) -> None:
        """Clear quarantine for one or all providers."""
        with self._lock:
            if provider:
                self._quarantine.pop(provider.strip().lower(), None)
            else:
                self._quarantine.clear()


global_llm_circuit_breaker = LLMCircuitBreaker()


def get_llm_circuit_breaker() -> LLMCircuitBreaker:
    """Return the global LLM Circuit Breaker instance."""
    return global_llm_circuit_breaker


class CircuitBreakerCallbackHandler(AsyncCallbackHandler):
    """LangChain callback handler recording provider 429/401 failures to Circuit Breaker."""

    def __init__(
        self,
        provider: str,
        circuit_breaker: LLMCircuitBreaker | None = None,
    ) -> None:
        super().__init__()
        self.provider = provider.strip().lower()
        self.circuit_breaker = circuit_breaker or global_llm_circuit_breaker

    async def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        if is_circuit_breaker_error(error):
            self.circuit_breaker.record_failure(self.provider, str(error))


def configure_langsmith_tracing(settings: Settings) -> bool:
    """Apply optional LangSmith environment flags without logging secret keys."""
    if not settings.langsmith_tracing:
        os.environ["LANGSMITH_TRACING"] = "false"
        return False

    if settings.langsmith_api_key is None:
        logger.warning(
            "LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY is missing; tracing disabled."
        )
        os.environ["LANGSMITH_TRACING"] = "false"
        return False

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key.get_secret_value()
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    return True


def _call_init_chat_model(model: str, model_provider: str, **kwargs: Any) -> BaseChatModel:
    try:
        return init_chat_model(model=model, model_provider=model_provider, **kwargs)
    except ImportError as exc:
        install_hint = OPTIONAL_PROVIDER_EXTRAS.get(
            model_provider,
            f"install the LangChain integration package for '{model_provider}'",
        )
        raise LLMProviderPackageError(
            f"LangChain adapter for LLM_PROVIDER='{model_provider}' is not installed. "
            f"Install it via: {install_hint}."
        ) from exc


def _instantiate_provider_model(
    provider_name: str,
    settings: Settings,
    circuit_breaker: LLMCircuitBreaker | None = None,
) -> BaseChatModel | None:
    cb = circuit_breaker or global_llm_circuit_breaker
    p = provider_name.strip().lower()
    cb_handler = CircuitBreakerCallbackHandler(p, circuit_breaker=cb)

    if p == "openai":
        key = settings.openai_api_key or (
            settings.llm_api_key if settings.llm_provider == "openai" else None
        )
        if not key or not key.get_secret_value().strip():
            return None
        model_name = settings.openai_model if settings.openai_api_key else settings.llm_model
        kwargs: dict[str, Any] = {
            "temperature": settings.llm_temperature,
            "timeout": settings.llm_timeout_seconds,
            "api_key": key.get_secret_value(),
            "callbacks": [cb_handler],
        }
        if settings.llm_base_url:
            kwargs["base_url"] = settings.llm_base_url
        return _call_init_chat_model(
            model=model_name,
            model_provider="openai",
            **kwargs,
        )

    if p in ("google", "google_genai", "gemini"):
        key = settings.google_api_key or (
            settings.llm_api_key if settings.llm_provider == "google_genai" else None
        )
        if not key or not key.get_secret_value().strip():
            return None
        model_name = settings.google_model or "gemini-2.0-flash"
        return _call_init_chat_model(
            model=model_name,
            model_provider="google_genai",
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
            api_key=key.get_secret_value(),
            callbacks=[cb_handler],
        )

    if p in ("mistral", "mistralai"):
        key = settings.mistral_api_key or (
            settings.llm_api_key if settings.llm_provider in ("mistral", "mistralai") else None
        )
        if not key or not key.get_secret_value().strip():
            return None
        model_name = settings.mistral_model or "mistral-small-latest"
        return _call_init_chat_model(
            model=model_name,
            model_provider="mistralai",
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
            api_key=key.get_secret_value(),
            callbacks=[cb_handler],
        )

    if p == "openrouter":
        key = settings.openrouter_api_key or (
            settings.llm_api_key
            if settings.llm_base_url and "openrouter" in settings.llm_base_url
            else None
        )
        if not key or not key.get_secret_value().strip():
            return None
        model_name = settings.openrouter_model or "deepseek/deepseek-chat"
        base_url = settings.openrouter_base_url or "https://openrouter.ai/api/v1"
        return _call_init_chat_model(
            model=model_name,
            model_provider="openai",
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
            api_key=key.get_secret_value(),
            base_url=base_url,
            callbacks=[cb_handler],
        )

    # Generic provider fallback from settings.llm_provider
    if settings.llm_api_key and settings.llm_api_key.get_secret_value().strip():
        kwargs = {
            "temperature": settings.llm_temperature,
            "timeout": settings.llm_timeout_seconds,
            "api_key": settings.llm_api_key.get_secret_value(),
            "callbacks": [cb_handler],
        }
        if settings.llm_base_url:
            kwargs["base_url"] = settings.llm_base_url
        return _call_init_chat_model(
            model=settings.llm_model,
            model_provider=settings.llm_provider,
            **kwargs,
        )

    return None


def build_chat_model(
    settings: Settings,
    circuit_breaker: LLMCircuitBreaker | None = None,
) -> BaseChatModel:
    """Create a resilient, provider-agnostic LangChain chat model with automated failover.

    If multiple providers are configured in LLM_FALLBACK_CHAIN (e.g. OpenAI, Google,
    Mistral, OpenRouter), wraps the primary model with LangChain's .with_fallbacks()
    to guarantee zero downtime on token expiration or quota limits.

    Integrates with the in-memory LLMCircuitBreaker: providers in quarantine (due to recent
    429/401 errors) are automatically placed at the end of the fallback chain so that
    healthy models are invoked immediately without waiting for timeouts.
    """
    cb = circuit_breaker or global_llm_circuit_breaker
    chain_order = [p.strip().lower() for p in settings.llm_fallback_chain.split(",") if p.strip()]

    # Prioritize healthy models over quarantined ones
    healthy_providers = [p for p in chain_order if not cb.is_quarantined(p)]
    quarantined_providers = [p for p in chain_order if cb.is_quarantined(p)]
    effective_chain = healthy_providers + quarantined_providers

    models: list[BaseChatModel] = []
    seen: set[str] = set()
    for provider in effective_chain:
        if provider in seen:
            continue
        try:
            m = _instantiate_provider_model(provider, settings, circuit_breaker=cb)
            if m is not None:
                models.append(m)
                seen.add(provider)
        except LLMProviderPackageError:
            raise
        except Exception as exc:
            logger.warning("Failed to initialize LLM provider '%s': %s", provider, exc)

    # If chain_order did not produce models, try generic fallback
    if not models:
        m = _instantiate_provider_model(settings.llm_provider, settings, circuit_breaker=cb)
        if m is not None:
            models.append(m)

    if not models:
        raise LLMConfigurationError(
            f"LLM_API_KEY is not configured for provider '{settings.llm_provider}' "
            f"(model '{settings.llm_model}'). Set LLM_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, "
            "or MISTRAL_API_KEY in root .env to enable natural-language SQL workflows."
        )

    quarantined_active = [p for p in seen if cb.is_quarantined(p)]
    primary = models[0]
    if len(models) > 1:
        logger.info(
            "Multi-Provider Resilient Failover armed with %d providers: %s (quarantined: %s)",
            len(models),
            list(seen),
            quarantined_active,
        )
        return primary.with_fallbacks(models[1:])

    return primary
