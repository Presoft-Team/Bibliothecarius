import uuid
from datetime import datetime

from pydantic import BaseModel


class ToneCreate(BaseModel):
    name: str
    description: str = ""
    system_prompt_template: str
    params: dict = {}
    is_default: bool = False


class ToneUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt_template: str | None = None
    params: dict | None = None
    is_default: bool | None = None


class ToneOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    system_prompt_template: str
    params: dict
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}
