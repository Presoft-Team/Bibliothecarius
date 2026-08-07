import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class Tone(Base):
    __tablename__ = "tones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    system_prompt_template: Mapped[str] = mapped_column(Text)
    params: Mapped[dict] = mapped_column(JSON, default=dict)  # formality, verbosity, persona traits, etc.
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
