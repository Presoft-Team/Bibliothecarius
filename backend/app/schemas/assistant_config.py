import uuid

from pydantic import BaseModel

VALID_PROVIDERS = {"ollama", "anthropic", "openai", "gemini"}


class AssistantConfigUpdate(BaseModel):
    name: str | None = None
    persona_description: str | None = None
    default_tone_id: uuid.UUID | None = None
    default_provider: str | None = None
    default_model: str | None = None
    temperature: float | None = None
    max_context_chunks: int | None = None
    params: dict | None = None


class AssistantConfigOut(BaseModel):
    id: uuid.UUID
    name: str
    persona_description: str
    default_tone_id: uuid.UUID | None
    default_provider: str
    default_model: str
    temperature: float
    max_context_chunks: int
    params: dict

    model_config = {"from_attributes": True}
