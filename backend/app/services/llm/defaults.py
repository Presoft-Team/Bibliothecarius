from sqlalchemy.orm import Session

from app.models.assistant_config import AssistantConfig
from app.models.user import User
from app.services.llm.base import LLMProviderError

# Last-resort static guess, only used if live listing also fails (e.g. provider unreachable).
# Model catalogs change faster than this file does — live listing is the real fix, this is
# just so conversation creation doesn't hard-fail when a provider's API is briefly down.
STATIC_FALLBACK_MODELS = {
    "ollama": "qwen2.5:0.5b",
    "anthropic": "claude-sonnet-5",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-3.1-flash-lite",
}


def default_model_for(
    db: Session, user: User, provider: str, assistant_config: AssistantConfig
) -> str:
    """The assistant's configured default_model only makes sense when the provider matches —
    otherwise it's e.g. an Ollama model name being handed to Gemini. Ask the provider what it
    actually supports instead of guessing a hardcoded name (which goes stale)."""
    if provider == assistant_config.default_provider:
        return assistant_config.default_model

    from app.services.llm.model_listing import list_models  # local import avoids a cycle

    try:
        models = list_models(db, user, provider)
        if models:
            return models[0]
    except LLMProviderError:
        pass

    return STATIC_FALLBACK_MODELS.get(provider, assistant_config.default_model)
