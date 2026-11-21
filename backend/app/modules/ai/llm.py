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
    """Return True if exception indicates a 429, 401, 402 (payment/quota), 403, 404, 405, or 400."""
    # Check status_code or code attribute
    code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if isinstance(code, int) and code in (400, 401, 402, 403, 404, 405, 429):
        return True

    # Check response attribute (requests, httpx, etc.)
    response = getattr(exc, "response", None)
    if response is not None:
        resp_code = getattr(response, "status_code", None)
        if isinstance(resp_code, int) and resp_code in (400, 401, 402, 403, 404, 405, 429):
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
            "payment",
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
            "402",
            "404",
            "quota",
            "rate limit",
            "rate_limit",
            "insufficient_quota",
            "credits remaining",
            "unauthorized",
            "invalid api key",
            "not found",
            "payment method",
            "payment required",
            "billing",
        )
    )


class LLMCircuitBreaker:
    """Thread-safe in-memory circuit breaker and quota-aware load balancer."""

    def __init__(self, default_ttl_seconds: float = DEFAULT_CIRCUIT_BREAKER_TTL_SECONDS) -> None:
        self._default_ttl = default_ttl_seconds
        # Maps provider name to (expiry_monotonic, failure_reason)
        self._quarantine: dict[str, tuple[float, str]] = {}
        # Maps key_id to cumulative tokens consumed for quota-aware load balancing
        self._token_usage: dict[str, int] = {}
        self._lock = threading.Lock()

    def record_tokens(self, key_id: str, tokens: int) -> None:
        """Record token consumption for deterministic quota load balancing."""
        k = key_id.strip().lower()
        with self._lock:
            self._token_usage[k] = self._token_usage.get(k, 0) + max(0, tokens)

    def get_token_usage(self, key_id: str) -> int:
        """Get cumulative tokens consumed by key_id."""
        k = key_id.strip().lower()
        with self._lock:
            return self._token_usage.get(k, 0)

    def get_all_token_usage(self) -> dict[str, int]:
        """Return a snapshot of all token consumption per key."""
        with self._lock:
            return dict(self._token_usage)

    def record_failure(
        self,
        provider: str,
        reason: str,
        ttl_seconds: float | None = None,
    ) -> None:
        """Quarantine a provider or key_id for ttl_seconds (default 5 minutes)."""
        p = provider.strip().lower()
        if p in ("google_genai", "gemini"):
            p = "google"
        elif p == "mistralai":
            p = "mistral"
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expiry = time.monotonic() + ttl
        with self._lock:
            self._quarantine[p] = (expiry, reason)
        logger.warning(
            "Circuit Breaker: quarantined LLM provider/key '%s' for %ds. Reason: %s",
            p,
            int(ttl),
            reason,
        )

    def is_quarantined(self, provider: str) -> bool:
        """Check if provider or key_id is currently quarantined. Cleans expired entries."""
        p = provider.strip().lower()
        if p in ("google_genai", "gemini"):
            p = "google"
        elif p == "mistralai":
            p = "mistral"

        with self._lock:
            entry = self._quarantine.get(p)
            if not entry and ":" in p:
                prefix = p.split(":", 1)[0]
                if prefix in ("google_genai", "gemini"):
                    prefix = "google"
                elif prefix == "mistralai":
                    prefix = "mistral"
                entry = self._quarantine.get(prefix)

            if not entry:
                return False
            expiry, _reason = entry
            if time.monotonic() < expiry:
                return True
            # Quarantine expired
            self._quarantine.pop(p, None)
            logger.info("Circuit Breaker: quarantine expired for '%s'; re-armed.", p)
            return False

    def get_quarantined_providers(self) -> list[str]:
        """Return list of currently quarantined provider names."""
        with self._lock:
            now = time.monotonic()
            active: list[str] = []
            expired: list[str] = []
            for p, (expiry, _) in list(self._quarantine.items()):
                if now < expiry:
                    active.append(p)
                else:
                    expired.append(p)
            for p in expired:
                del self._quarantine[p]
            return sorted(active)

    def get_quarantine_details(self) -> list[dict[str, Any]]:
        """Return detailed list of quarantined keys with remaining TTL and failure reason."""
        with self._lock:
            now = time.monotonic()
            details: list[dict[str, Any]] = []
            expired: list[str] = []
            for p, (expiry, reason) in list(self._quarantine.items()):
                remaining = expiry - now
                if remaining > 0:
                    details.append(
                        {
                            "key_id": p,
                            "ttl_remaining_seconds": round(remaining, 1),
                            "reason": reason,
                        }
                    )
                else:
                    expired.append(p)
            for p in expired:
                del self._quarantine[p]
            return sorted(details, key=lambda d: d["ttl_remaining_seconds"])

    def clear(self, provider: str | None = None) -> None:
        """Clear quarantine for one or all providers."""
        with self._lock:
            if provider:
                p = provider.strip().lower()
                if p in ("google_genai", "gemini"):
                    p = "google"
                elif p == "mistralai":
                    p = "mistral"
                self._quarantine.pop(p, None)
                to_remove = [k for k in self._quarantine if k.startswith(f"{p}:")]
                for k in to_remove:
                    self._quarantine.pop(k, None)
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
        if model_provider == "openai" and "max_retries" not in kwargs:
            kwargs["max_retries"] = 0
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


def _decorate_model(m: BaseChatModel | None, provider: str, raw_key: str) -> BaseChatModel | None:
    if m is not None:
        tail = raw_key[-4:] if len(raw_key) >= 4 else "key"
        try:
            object.__setattr__(m, "_provider_name", provider.strip().lower())
            object.__setattr__(m, "_key_fingerprint", tail)
        except Exception:
            pass
    return m


def _instantiate_single_model(
    provider_name: str,
    key: Any,
    key_id: str,
    settings: Settings,
    circuit_breaker: LLMCircuitBreaker,
) -> BaseChatModel | None:
    p = provider_name.strip().lower()
    raw_key = key.get_secret_value().strip()
    if not raw_key:
        return None

    cb_handler = CircuitBreakerCallbackHandler(key_id, circuit_breaker=circuit_breaker)
    temperature = settings.llm_temperature
    timeout = settings.llm_timeout_seconds

    def _create(model: str, model_provider: str, **kwargs: Any) -> BaseChatModel:
        return _decorate_model(  # type: ignore[return-value]
            _call_init_chat_model(model=model, model_provider=model_provider, **kwargs),
            provider=p,
            raw_key=raw_key,
        )

    # 1. Groq Cloud (Ultra-fast LPU inference, OpenAI-compatible)
    if p == "groq":
        return _create(
            model=settings.groq_model,
            model_provider="openai",
            temperature=temperature,
            timeout=timeout,
            api_key=raw_key,
            base_url=settings.groq_base_url,
            callbacks=[cb_handler],
        )

    # 2. SambaNova Cloud (High-speed SN40L chips, OpenAI-compatible)
    if p in ("sambanova", "sambanova.ai"):
        return _create(
            model=settings.sambanova_model,
            model_provider="openai",
            temperature=temperature,
            timeout=timeout,
            api_key=raw_key,
            base_url=settings.sambanova_base_url,
            callbacks=[cb_handler],
        )

    # 3. OpenRouter (Multi-model aggregator with free & paid tiers)
    if p == "openrouter":
        return _create(
            model=settings.openrouter_model,
            model_provider="openai",
            temperature=temperature,
            timeout=timeout,
            api_key=raw_key,
            base_url=settings.openrouter_base_url,
            callbacks=[cb_handler],
        )

    # 4. Cloudflare Workers AI (10,000 neurons/day free, OpenAI-compatible)
    if p in ("cloudflare", "cloudflare_ai"):
        base_url = settings.cloudflare_base_url or "https://api.cloudflare.com/client/v4"
        return _create(
            model=settings.cloudflare_model,
            model_provider="openai",
            temperature=temperature,
            timeout=timeout,
            api_key=raw_key,
            base_url=base_url,
            callbacks=[cb_handler],
        )

    # 5. Cohere (Command R+ via OpenAI-compatible endpoint)
    if p == "cohere":
        return _create(
            model=settings.cohere_model,
            model_provider="openai",
            temperature=temperature,
            timeout=timeout,
            api_key=raw_key,
            base_url=settings.cohere_base_url,
            callbacks=[cb_handler],
        )

    # 6. z.ai / Custom Provider (OpenAI-compatible)
    if p in ("zai", "z.ai"):
        base_url = settings.zai_base_url or "https://api.z.ai/v1"
        return _create(
            model=settings.zai_model,
            model_provider="openai",
            temperature=temperature,
            timeout=timeout,
            api_key=raw_key,
            base_url=base_url,
            callbacks=[cb_handler],
        )

    # 6b. Kimi / Moonshot AI (OpenAI-compatible)
    if p in ("kimi", "moonshot"):
        base_url = settings.kimi_base_url or "https://api.moonshot.cn/v1"
        return _create(
            model=settings.kimi_model,
            model_provider="openai",
            temperature=temperature,
            timeout=timeout,
            api_key=raw_key,
            base_url=base_url,
            callbacks=[cb_handler],
        )

    # 6c. Novita AI (OpenAI-compatible)
    if p == "novita":
        base_url = settings.novita_base_url or "https://api.novita.ai/v3/openai"
        return _create(
            model=settings.novita_model,
            model_provider="openai",
            temperature=temperature,
            timeout=timeout,
            api_key=raw_key,
            base_url=base_url,
            callbacks=[cb_handler],
        )

    # 6d. Meta (OpenAI-compatible Llama endpoint)
    if p == "meta":
        base_url = settings.meta_base_url or "https://api.groq.com/openai/v1"
        return _create(
            model=settings.meta_model,
            model_provider="openai",
            temperature=temperature,
            timeout=timeout,
            api_key=raw_key,
            base_url=base_url,
            callbacks=[cb_handler],
        )

    # 7. Google Gemini (Google AI Studio native)
    if p in ("google", "google_genai", "gemini"):
        model_name = settings.google_model or "gemini-2.0-flash"
        return _create(
            model=model_name,
            model_provider="google_genai",
            temperature=temperature,
            timeout=timeout,
            api_key=raw_key,
            callbacks=[cb_handler],
        )

    # 8. Mistral AI (Codestral / Mistral native)
    if p in ("mistral", "mistralai"):
        model_name = settings.mistral_model or "mistral-small-latest"
        return _create(
            model=model_name,
            model_provider="mistralai",
            temperature=temperature,
            timeout=timeout,
            api_key=raw_key,
            callbacks=[cb_handler],
        )

    # 9. OpenAI Standard
    if p == "openai":
        kwargs: dict[str, Any] = {
            "temperature": temperature,
            "timeout": timeout,
            "api_key": raw_key,
            "callbacks": [cb_handler],
        }
        if settings.llm_base_url:
            kwargs["base_url"] = settings.llm_base_url
        return _create(
            model=settings.openai_model,
            model_provider="openai",
            **kwargs,
        )

    # 10. Generic fallback from settings.llm_provider
    kwargs = {
        "temperature": temperature,
        "timeout": timeout,
        "api_key": raw_key,
        "callbacks": [cb_handler],
    }
    if settings.llm_base_url:
        kwargs["base_url"] = settings.llm_base_url
    return _create(
        model=settings.llm_model,
        model_provider=settings.llm_provider,
        **kwargs,
    )


def build_chat_model(
    settings: Settings,
    circuit_breaker: LLMCircuitBreaker | None = None,
) -> BaseChatModel:
    """Create a resilient, multi-token multi-provider chat model with automated failover.

    Supports multiple keys per provider (e.g. GROQ_API_KEYS="k1,k2", OPENROUTER_API_KEYS="...").
    If any single token encounters quota limits (HTTP 429) or auth errors (HTTP 401),
    that specific token is quarantined by key-id in the LLMCircuitBreaker for 5 minutes.
    Subsequent requests immediately rotate to the next healthy token or provider.
    """
    cb = circuit_breaker or global_llm_circuit_breaker
    chain_order = [p.strip().lower() for p in settings.llm_fallback_chain.split(",") if p.strip()]

    all_models: list[tuple[str, BaseChatModel]] = []
    seen_keys: set[str] = set()

    for provider in chain_order:
        keys = settings.get_provider_keys(provider)
        for key in keys:
            raw = key.get_secret_value().strip()
            if not raw:
                continue
            tail = raw[-4:] if len(raw) >= 4 else "key"
            key_id = f"{provider}:{tail}"
            if key_id in seen_keys:
                continue
            try:
                m = _instantiate_single_model(
                    provider_name=provider,
                    key=key,
                    key_id=key_id,
                    settings=settings,
                    circuit_breaker=cb,
                )
                if m is not None:
                    all_models.append((key_id, m))
                    seen_keys.add(key_id)
            except LLMProviderPackageError:
                raise
            except Exception as exc:
                logger.warning("Failed to initialize model for %s: %s", key_id, exc)

    # If chain_order did not produce models, try generic fallback
    if not all_models:
        keys = settings.get_provider_keys(settings.llm_provider)
        if keys:
            for key in keys:
                raw = key.get_secret_value().strip()
                tail = raw[-4:] if len(raw) >= 4 else "key"
                key_id = f"{settings.llm_provider}:{tail}"
                try:
                    m = _instantiate_single_model(
                        provider_name=settings.llm_provider,
                        key=key,
                        key_id=key_id,
                        settings=settings,
                        circuit_breaker=cb,
                    )
                    if m is not None:
                        all_models.append((key_id, m))
                except LLMProviderPackageError:
                    raise
                except Exception as exc:
                    logger.warning("Failed fallback initialization for %s: %s", key_id, exc)

    if not all_models:
        raise LLMConfigurationError(
            f"LLM_API_KEY is not configured or no valid keys found for: {chain_order}. "
            "Set LLM_API_KEY, GROQ_API_KEYS, SAMBANOVA_API_KEYS, OPENROUTER_API_KEYS, "
            "GOOGLE_API_KEY, or OPENAI_API_KEY in root .env to enable SQL workflows."
        )

    # Quota-Aware Load Balancing without if-else: sort healthy models by least tokens consumed
    healthy_models = [(k_id, m) for k_id, m in all_models if not cb.is_quarantined(k_id)]
    sorted_healthy = sorted(healthy_models, key=lambda pair: cb.get_token_usage(pair[0]))
    quarantined_models = [(k_id, m) for k_id, m in all_models if cb.is_quarantined(k_id)]
    ordered = sorted_healthy + quarantined_models

    models = [m for _, m in ordered]
    primary = models[0]
    if len(models) > 1:
        logger.info(
            "Multi-Token Multi-Provider Pool armed with %d model(s) across %d provider(s): %s",
            len(models),
            len(settings.configured_llm_providers),
            [k_id for k_id, _ in ordered],
        )
        resilient_model = primary.with_fallbacks(models[1:])
        try:
            object.__setattr__(
                resilient_model, "_provider_name", getattr(primary, "_provider_name", "llm")
            )
            object.__setattr__(
                resilient_model, "_key_fingerprint", getattr(primary, "_key_fingerprint", "key")
            )
        except Exception:
            pass
        return resilient_model

    return primary
