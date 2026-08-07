import httpx
import openai
import google.generativeai as genai
import anthropic
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.services.llm.base import LLMProviderError

# Used only when a provider's API can't tell us what it supports (Anthropic has no public
# list-models call in the pinned SDK version) — kept short and current, not exhaustive.
ANTHROPIC_FALLBACK_MODELS = ["claude-sonnet-5", "claude-opus-4-8", "claude-haiku-4-5-20251001"]


def _sort_stable_first(names: list[str], required_substring: str | None = None) -> list[str]:
    """A provider's full catalog includes preview/experimental models (and, apparently, entirely
    different unreleased product lines under the same API) that are unreliable choices for an
    auto-picked default. Push those to the end instead of excluding them — still selectable, just
    not what gets picked first."""

    def rank(name: str) -> tuple[bool, bool, str]:
        lname = name.lower()
        offbrand = required_substring is not None and required_substring not in lname
        unstable = any(marker in lname for marker in ("preview", "exp"))
        return (offbrand, unstable, name)

    return sorted(names, key=rank)


def list_ollama_models() -> list[str]:
    try:
        response = httpx.get(f"{settings.ollama_url}/api/tags", timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LLMProviderError(f"Could not reach Ollama: {exc}") from exc

    # Ollama's /api/tags lists every pulled model with no reliable chat-vs-embedding capability
    # flag; exclude the embedding model we ourselves configure (app.core.config.embedding_model)
    # by name so it doesn't show up as a selectable chat model and fail if picked.
    models = [
        m["name"]
        for m in response.json().get("models", [])
        if not m["name"].startswith(settings.embedding_model)
    ]
    if not models:
        raise LLMProviderError(
            "No models are pulled into Ollama yet. Run e.g. "
            "`docker compose exec ollama ollama pull llama3` and try again."
        )
    return models


def list_gemini_models(api_key: str) -> list[str]:
    genai.configure(api_key=api_key)
    try:
        models = list(genai.list_models())
    except Exception as exc:
        raise LLMProviderError(f"Could not list Gemini models: {exc}") from exc

    names = [
        m.name.removeprefix("models/")
        for m in models
        if "generateContent" in getattr(m, "supported_generation_methods", [])
    ]
    return _sort_stable_first(names, required_substring="gemini")


def list_openai_models(api_key: str) -> list[str]:
    try:
        models = openai.OpenAI(api_key=api_key).models.list()
    except Exception as exc:
        raise LLMProviderError(f"Could not list OpenAI models: {exc}") from exc

    return _sort_stable_first([m.id for m in models if "gpt" in m.id])


def list_anthropic_models(api_key: str) -> list[str]:
    client = anthropic.Anthropic(api_key=api_key)
    try:
        return sorted(m.id for m in client.models.list())
    except (AttributeError, anthropic.APIError):
        # Older SDK/API without a list-models endpoint — the fallback list still lets the
        # user pick something valid instead of typing a guessed model id blind.
        return ANTHROPIC_FALLBACK_MODELS


def list_models(db: Session, user: User, provider: str) -> list[str]:
    from app.services.llm.factory import get_api_key  # local import avoids a circular import

    if provider == "ollama":
        return list_ollama_models()
    if provider == "gemini":
        return list_gemini_models(get_api_key(db, user, provider))
    if provider == "openai":
        return list_openai_models(get_api_key(db, user, provider))
    if provider == "anthropic":
        return list_anthropic_models(get_api_key(db, user, provider))
    raise LLMProviderError(f"Unknown provider: {provider}")
