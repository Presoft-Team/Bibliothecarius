import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    tone_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tones.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String, default="ollama")
    model: Mapped[str] = mapped_column(String, default="llama3")
    # None until the user renames it or the first message auto-titles it; frontend falls back to
    # displaying provider/model when this is unset rather than a raw "New Chat" placeholder here.
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String)  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    # retrieval_scope: {"type": "all"} | {"type": "folders", "folder_ids": [...]}
    retrieval_scope: Mapped[dict] = mapped_column(JSON, default=lambda: {"type": "all"})
    scope_fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    source_chunk_ids: Mapped[list] = mapped_column(JSON, default=list)
    # Snapshot of citation details (filename, page, chunk text, distance) at send time — kept
    # here rather than re-resolved from document_chunks on read, so history stays meaningful
    # even if the source document is later edited, moved, or deleted.
    citations: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
