import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class User(Base):
    """Mirrors the identity Keycloak manages; keyed by Keycloak's subject id."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keycloak_sub: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    role: Mapped[str] = mapped_column(String, default="user")  # "user" | "admin"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
