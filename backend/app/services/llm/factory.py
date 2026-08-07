from sqlalchemy.orm import Session

from app.core.crypto import decrypt_secret
from app.models.provider_credential import ProviderCredential
from app.models.user import User
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.base import LLMProvider, LLMProviderError
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openai_provider import OpenAIProvider

_CLOUD_PROVIDERS = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
}


def get_api_key(db: Session, user: User, provider: str) -> str:
    credential = (
        db.query(ProviderCredential)
        .filter(ProviderCredential.owner_id == user.id, ProviderCredential.provider == provider)
        .one_or_none()
    )
    if credential is None:
        raise LLMProviderError(
            f"No API key on file for {provider}. Add one via PUT /provider-credentials/{provider}."
        )
    return decrypt_secret(credential.encrypted_api_key)


def get_provider(db: Session, user: User, provider: str, model: str) -> LLMProvider:
    if provider == "ollama":
        return OllamaProvider(model)

    provider_cls = _CLOUD_PROVIDERS.get(provider)
    if provider_cls is None:
        raise LLMProviderError(f"Unknown provider: {provider}")

    api_key = get_api_key(db, user, provider)
    return provider_cls(model, api_key)
