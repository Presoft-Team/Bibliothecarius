from pydantic import BaseModel

VALID_ROLES = {"admin", "user"}


class AdminUserOut(BaseModel):
    keycloak_id: str
    username: str
    email: str | None
    enabled: bool
    roles: list[str]
    provisioned: bool  # has a local `users` row, i.e. has logged into the app at least once


class AdminUserInvite(BaseModel):
    username: str
    email: str
    temporary_password: str


class AdminUserInviteOut(BaseModel):
    keycloak_id: str
    username: str
    email: str
    temporary_password: str
