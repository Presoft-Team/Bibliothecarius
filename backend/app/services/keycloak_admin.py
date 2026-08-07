import time

import httpx

from app.core.config import settings

_admin_token_cache: dict = {"token": None, "expires_at": 0.0}


class KeycloakAdminError(Exception):
    pass


class KeycloakAdminConflict(KeycloakAdminError):
    pass


def _get_admin_token() -> str:
    now = time.time()
    if _admin_token_cache["token"] is None or now >= _admin_token_cache["expires_at"]:
        try:
            response = httpx.post(
                f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.keycloak_admin_client_id,
                    "client_secret": settings.keycloak_admin_client_secret,
                },
                timeout=5.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise KeycloakAdminError(f"Could not authenticate with Keycloak admin API: {exc}") from exc

        data = response.json()
        _admin_token_cache["token"] = data["access_token"]
        # Refresh a few seconds early so a request never races an about-to-expire token.
        _admin_token_cache["expires_at"] = now + data.get("expires_in", 60) - 5

    return _admin_token_cache["token"]


def _admin_request(method: str, path: str, **kwargs) -> httpx.Response:
    url = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}{path}"
    base_headers = kwargs.pop("headers", {})

    def _do_request() -> httpx.Response:
        headers = {**base_headers, "Authorization": f"Bearer {_get_admin_token()}"}
        return httpx.request(method, url, headers=headers, timeout=10.0, **kwargs)

    try:
        response = _do_request()
        if response.status_code == 401:
            # The cached token can outlive its Keycloak-side session (e.g. Keycloak restarted
            # or the client secret was rotated) without us having a chance to see it expire.
            _admin_token_cache["token"] = None
            response = _do_request()
        if response.status_code == 409:
            raise KeycloakAdminConflict("A user with that username or email already exists")
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise KeycloakAdminError(f"Keycloak admin API request failed: {exc}") from exc
    except httpx.HTTPError as exc:
        raise KeycloakAdminError(f"Could not reach Keycloak admin API: {exc}") from exc
    return response


def list_users() -> list[dict]:
    return _admin_request("GET", "/users", params={"max": 500}).json()


def get_realm_roles_for_user(keycloak_user_id: str) -> list[str]:
    roles = _admin_request("GET", f"/users/{keycloak_user_id}/role-mappings/realm").json()
    return [r["name"] for r in roles]


def _get_role_representation(role_name: str) -> dict:
    return _admin_request("GET", f"/roles/{role_name}").json()


def assign_realm_role(keycloak_user_id: str, role_name: str) -> None:
    role_rep = _get_role_representation(role_name)
    _admin_request("POST", f"/users/{keycloak_user_id}/role-mappings/realm", json=[role_rep])


def remove_realm_role(keycloak_user_id: str, role_name: str) -> None:
    role_rep = _get_role_representation(role_name)
    _admin_request("DELETE", f"/users/{keycloak_user_id}/role-mappings/realm", json=[role_rep])


def create_user(username: str, email: str, temporary_password: str) -> str:
    """Creates a Keycloak user with a temporary password (reset required on first login).
    Returns the new user's Keycloak id. Caller is responsible for assigning roles."""
    response = _admin_request(
        "POST",
        "/users",
        json={
            "username": username,
            "email": email,
            "enabled": True,
            "emailVerified": True,
            "credentials": [{"type": "password", "value": temporary_password, "temporary": True}],
        },
    )
    location = response.headers["Location"]
    return location.rstrip("/").rsplit("/", 1)[-1]
