from datetime import datetime

from pydantic import BaseModel

CLOUD_PROVIDERS = {"anthropic", "openai", "gemini"}


class ProviderCredentialSet(BaseModel):
    api_key: str


class ProviderCredentialOut(BaseModel):
    provider: str
    key_hint: str
    created_at: datetime

    model_config = {"from_attributes": True}
