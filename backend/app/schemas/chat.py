import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator


class RetrievalScope(BaseModel):
    type: Literal["all", "folders"] = "all"
    folder_ids: list[uuid.UUID] | None = None

    @model_validator(mode="after")
    def _validate_folders(self):
        if self.type == "folders" and not self.folder_ids:
            raise ValueError("folder_ids is required when type is 'folders'")
        return self


class ConversationCreate(BaseModel):
    tone_id: uuid.UUID | None = None
    provider: str | None = None
    model: str | None = None


class ConversationUpdate(BaseModel):
    title: str


class ConversationOut(BaseModel):
    id: uuid.UUID
    tone_id: uuid.UUID | None
    provider: str
    model: str
    title: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str
    retrieval_scope: RetrievalScope = RetrievalScope()


class CitationOut(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page_ref: int | None
    chunk_text: str
    distance: float


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    retrieval_scope: dict
    scope_fallback_used: bool
    source_chunk_ids: list[str]
    citations: list[CitationOut]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatTurnOut(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut
