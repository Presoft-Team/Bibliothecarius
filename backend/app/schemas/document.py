import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    folder_id: uuid.UUID | None
    filename: str
    content_type: str
    status: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DocumentPageOut(BaseModel):
    page_number: int
    extracted_text: str
    extraction_method: str
    confidence: float

    model_config = {"from_attributes": True}


class DocumentPreviewOut(BaseModel):
    document: DocumentOut
    pages: list[DocumentPageOut]


class DocumentMove(BaseModel):
    folder_id: uuid.UUID | None = None


class DocumentConfirmResult(BaseModel):
    document: DocumentOut
    chunk_count: int
