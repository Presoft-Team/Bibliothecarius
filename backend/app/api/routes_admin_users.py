from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin_user import VALID_ROLES, AdminUserInvite, AdminUserInviteOut, AdminUserOut
from app.services.keycloak_admin import (
    KeycloakAdminConflict,
    KeycloakAdminError,
    assign_realm_role,
    create_user,
    get_realm_roles_for_user,
    list_users,
    remove_realm_role,
)

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def _to_admin_user_out(kc_user: dict, db: Session) -> AdminUserOut:
    keycloak_id = kc_user["id"]
    roles = get_realm_roles_for_user(keycloak_id)
    provisioned = db.query(User).filter(User.keycloak_sub == keycloak_id).one_or_none() is not None
    return AdminUserOut(
        keycloak_id=keycloak_id,
        username=kc_user["username"],
        email=kc_user.get("email"),
        enabled=kc_user.get("enabled", True),
        roles=[r for r in roles if r in VALID_ROLES],
        provisioned=provisioned,
    )


@router.get("", response_model=list[AdminUserOut])
def list_all_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        kc_users = list_users()
        return [_to_admin_user_out(u, db) for u in kc_users]
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("", response_model=AdminUserInviteOut, status_code=status.HTTP_201_CREATED)
def invite_user(payload: AdminUserInvite, admin: User = Depends(require_admin)):
    """Creates a Keycloak account with a temporary password and the baseline 'user' role.
    Local scaffold only sends no email — hand the returned temporary_password to the invitee
    out of band; production deployments should wire this to Keycloak's email/reset flow instead."""
    try:
        keycloak_id = create_user(payload.username, payload.email, payload.temporary_password)
        assign_realm_role(keycloak_id, "user")
    except KeycloakAdminConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return AdminUserInviteOut(
        keycloak_id=keycloak_id,
        username=payload.username,
        email=payload.email,
        temporary_password=payload.temporary_password,
    )


@router.put("/{keycloak_id}/roles/{role}", response_model=AdminUserOut)
def grant_role(
    keycloak_id: str, role: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    if role not in VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"role must be one of {sorted(VALID_ROLES)}")

    try:
        assign_realm_role(keycloak_id, role)
        kc_user = next((u for u in list_users() if u["id"] == keycloak_id), None)
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if kc_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _to_admin_user_out(kc_user, db)


@router.delete("/{keycloak_id}/roles/{role}", response_model=AdminUserOut)
def revoke_role(
    keycloak_id: str, role: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    if role not in VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"role must be one of {sorted(VALID_ROLES)}")
    if role == "admin" and keycloak_id == admin.keycloak_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot revoke your own admin role",
        )

    try:
        remove_realm_role(keycloak_id, role)
        kc_user = next((u for u in list_users() if u["id"] == keycloak_id), None)
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if kc_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _to_admin_user_out(kc_user, db)
