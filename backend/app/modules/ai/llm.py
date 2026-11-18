import logging
import os
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import Settings

logger = logging.getLogger(__name__)

OPTIONAL_PROVIDER_EXTRAS: dict[str, str] = {
    "anthropic": "uv sync --extra anthropic",
    "google_genai": "uv sync --extra google",
}


class LLMConfigurationError(RuntimeError):
    """Raised when LLM credentials are not configured for AI workflows."""


class LLMProviderPackageError(RuntimeError):
    """Raised when the selected LLM provider's optional LangChain adapter is not installed."""


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


def build_chat_model(settings: Settings) -> BaseChatModel:
    """Create a provider-agnostic LangChain chat model purely from Settings.

    Never hardcodes provider-specific branches or assumes local inference.
    """
    if not settings.is_llm_configured or settings.llm_api_key is None:
        raise LLMConfigurationError(
            f"LLM_API_KEY is not configured for provider '{settings.llm_provider}' "
            f"(model '{settings.llm_model}'). Set LLM_API_KEY in root .env to enable "
            "natural-language SQL workflows."
        )

    kwargs: dict[str, Any] = {
        "temperature": settings.llm_temperature,
        "timeout": settings.llm_timeout_seconds,
        "api_key": settings.llm_api_key.get_secret_value(),
    }
    if settings.llm_base_url:
        kwargs["base_url"] = settings.llm_base_url

    try:
        model = init_chat_model(
            model=settings.llm_model,
            model_provider=settings.llm_provider,
            **kwargs,
        )
    except ImportError as exc:
        install_hint = OPTIONAL_PROVIDER_EXTRAS.get(
            settings.llm_provider,
            f"install the LangChain integration package for '{settings.llm_provider}'",
        )
        raise LLMProviderPackageError(
            f"LangChain adapter for LLM_PROVIDER='{settings.llm_provider}' is not installed. "
            f"Install it via: {install_hint}."
        ) from exc

    return model
