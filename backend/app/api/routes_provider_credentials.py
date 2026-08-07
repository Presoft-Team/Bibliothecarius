from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.crypto import encrypt_secret
from app.db.session import get_db
from app.models.provider_credential import ProviderCredential
from app.models.user import User
from app.schemas.provider_credential import (
    CLOUD_PROVIDERS,
    ProviderCredentialOut,
    ProviderCredentialSet,
)

router = APIRouter(prefix="/provider-credentials", tags=["provider-credentials"])


def _validate_provider(provider: str) -> None:
    if provider not in CLOUD_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"provider must be one of {sorted(CLOUD_PROVIDERS)}",
        )


@router.get("", response_model=list[ProviderCredentialOut])
def list_provider_credentials(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return db.query(ProviderCredential).filter(ProviderCredential.owner_id == user.id).all()


@router.put("/{provider}", response_model=ProviderCredentialOut)
def set_provider_credential(
    provider: str,
    payload: ProviderCredentialSet,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_provider(provider)

    credential = (
        db.query(ProviderCredential)
        .filter(ProviderCredential.owner_id == user.id, ProviderCredential.provider == provider)
        .one_or_none()
    )
    encrypted = encrypt_secret(payload.api_key)
    key_hint = payload.api_key[-4:]
    if credential is None:
        credential = ProviderCredential(
            owner_id=user.id, provider=provider, encrypted_api_key=encrypted, key_hint=key_hint
        )
        db.add(credential)
    else:
        credential.encrypted_api_key = encrypted
        credential.key_hint = key_hint

    db.commit()
    db.refresh(credential)
    return credential


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider_credential(
    provider: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    credential = (
        db.query(ProviderCredential)
        .filter(ProviderCredential.owner_id == user.id, ProviderCredential.provider == provider)
        .one_or_none()
    )
    if credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No credential on file")
    db.delete(credential)
    db.commit()
