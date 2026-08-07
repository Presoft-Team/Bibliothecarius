import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_tone
from app.db.session import get_db
from app.models.tone import Tone
from app.models.user import User
from app.schemas.tone import ToneCreate, ToneOut, ToneUpdate

router = APIRouter(prefix="/tones", tags=["tones"])


def _clear_other_defaults(db: Session, user: User, except_tone_id: uuid.UUID | None) -> None:
    query = db.query(Tone).filter(Tone.owner_id == user.id, Tone.is_default.is_(True))
    if except_tone_id is not None:
        query = query.filter(Tone.id != except_tone_id)
    query.update({"is_default": False})


@router.get("", response_model=list[ToneOut])
def list_tones(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Tone).filter(Tone.owner_id == user.id).order_by(Tone.name).all()


@router.post("", response_model=ToneOut, status_code=status.HTTP_201_CREATED)
def create_tone(
    payload: ToneCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    tone = Tone(
        owner_id=user.id,
        name=payload.name,
        description=payload.description,
        system_prompt_template=payload.system_prompt_template,
        params=payload.params,
        is_default=payload.is_default,
    )
    db.add(tone)
    db.flush()
    if payload.is_default:
        _clear_other_defaults(db, user, except_tone_id=tone.id)
    db.commit()
    db.refresh(tone)
    return tone


@router.patch("/{tone_id}", response_model=ToneOut)
def update_tone(
    tone_id: uuid.UUID,
    payload: ToneUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tone = get_owned_tone(db, user, tone_id)

    for field in ("name", "description", "system_prompt_template", "params"):
        value = getattr(payload, field)
        if value is not None:
            setattr(tone, field, value)

    if payload.is_default is not None:
        tone.is_default = payload.is_default
        if payload.is_default:
            _clear_other_defaults(db, user, except_tone_id=tone.id)

    db.commit()
    db.refresh(tone)
    return tone


@router.delete("/{tone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tone(
    tone_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    tone = get_owned_tone(db, user, tone_id)
    db.delete(tone)
    db.commit()
