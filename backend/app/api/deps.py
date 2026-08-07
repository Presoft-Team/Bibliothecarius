import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_token, extract_realm_roles
from app.db.session import get_db
from app.models.assistant_config import AssistantConfig
from app.models.chat import Conversation
from app.models.folder import Folder
from app.models.tone import Tone
from app.models.user import User

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        claims = decode_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    keycloak_sub = claims["sub"]
    roles = extract_realm_roles(claims)
    role = "admin" if "admin" in roles else "user"

    email = claims.get("email", f"{keycloak_sub}@unknown.local")
    user = db.query(User).filter(User.keycloak_sub == keycloak_sub).one_or_none()
    dirty = False

    if user is None:
        # A different keycloak_sub can already own this email if the Keycloak realm was
        # recreated (dev) or the account was recreated upstream (prod) — reattach rather
        # than insert, or the unique email constraint throws a 500 instead of proceeding.
        user = db.query(User).filter(User.email == email).one_or_none()
        if user is not None:
            user.keycloak_sub = keycloak_sub
            dirty = True

    if user is None:
        user = User(
            keycloak_sub=keycloak_sub,
            display_name=claims.get("preferred_username", keycloak_sub),
            email=email,
            role=role,
        )
        db.add(user)
        dirty = True
    elif user.role != role:
        # Keycloak is the source of truth for roles; keep the local mirror in sync.
        user.role = role
        dirty = True

    if dirty:
        db.commit()
        db.refresh(user)

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


def get_owned_folder(db: Session, user: User, folder_id: uuid.UUID) -> Folder:
    folder = (
        db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == user.id).one_or_none()
    )
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    return folder


def get_owned_tone(db: Session, user: User, tone_id: uuid.UUID) -> Tone:
    tone = db.query(Tone).filter(Tone.id == tone_id, Tone.owner_id == user.id).one_or_none()
    if tone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tone not found")
    return tone


def get_owned_conversation(db: Session, user: User, conversation_id: uuid.UUID) -> Conversation:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.owner_id == user.id)
        .one_or_none()
    )
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


def get_or_create_assistant_config(db: Session, user: User) -> AssistantConfig:
    config = db.query(AssistantConfig).filter(AssistantConfig.owner_id == user.id).one_or_none()
    if config is None:
        config = AssistantConfig(owner_id=user.id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config
