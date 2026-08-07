import uuid

from sqlalchemy import String, ForeignKey, JSON, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class AssistantConfig(Base):
    __tablename__ = "assistant_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String, default="Assistant")
    persona_description: Mapped[str] = mapped_column(String, default="")
    default_tone_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tones.id"), nullable=True)
    default_provider: Mapped[str] = mapped_column(String, default="ollama")  # ollama | anthropic | openai | gemini
    default_model: Mapped[str] = mapped_column(String, default="llama3")
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_context_chunks: Mapped[int] = mapped_column(Integer, default=5)
    params: Mapped[dict] = mapped_column(JSON, default=dict)  # language, cite_sources, response_length, etc.
