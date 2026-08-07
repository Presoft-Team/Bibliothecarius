import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class ProviderCredential(Base):
    __tablename__ = "provider_credentials"
    __table_args__ = (UniqueConstraint("owner_id", "provider", name="uq_provider_credentials_owner_provider"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String)  # anthropic | openai | gemini
    encrypted_api_key: Mapped[str] = mapped_column(Text)
    # Last 4 chars in plaintext, purely so the UI can show "•••• ab12" — knowing 4 trailing
    # characters of an API key isn't exploitable, and it isn't enough to reconstruct the key.
    key_hint: Mapped[str] = mapped_column(String(4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
