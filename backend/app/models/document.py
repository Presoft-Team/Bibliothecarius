import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.db.session import Base

EMBEDDING_DIM = 768  # matches Ollama's nomic-embed-text; change alongside app.core.config.embedding_model


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    folder_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    filename: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String)  # pdf | docx | xlsx | txt
    status: Mapped[str] = mapped_column(String, default="uploaded")  # uploaded | previewing | ingested
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    extraction_method: Mapped[str] = mapped_column(String)  # native | ocr_fallback
    confidence: Mapped[float] = mapped_column(Float, default=1.0)  # low confidence flags a page for user review


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), index=True)
    folder_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    chunk_text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    page_ref: Mapped[int | None] = mapped_column(Integer, nullable=True)
