from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_or_create_assistant_config, get_owned_tone
from app.db.session import get_db
from app.models.user import User
from app.schemas.assistant_config import VALID_PROVIDERS, AssistantConfigOut, AssistantConfigUpdate

router = APIRouter(prefix="/assistant-config", tags=["assistant-config"])


@router.get("", response_model=AssistantConfigOut)
def read_assistant_config(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_or_create_assistant_config(db, user)


@router.patch("", response_model=AssistantConfigOut)
def update_assistant_config(
    payload: AssistantConfigUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    config = get_or_create_assistant_config(db, user)
    updates = payload.model_dump(exclude_unset=True)

    if "default_provider" in updates and updates["default_provider"] not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"default_provider must be one of {sorted(VALID_PROVIDERS)}",
        )

    if updates.get("default_tone_id") is not None:
        get_owned_tone(db, user, updates["default_tone_id"])

    for field, value in updates.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return config
