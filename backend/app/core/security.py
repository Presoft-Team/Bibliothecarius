import time

import httpx
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import settings

_jwks_cache: dict = {"keys": None, "fetched_at": 0.0}
_JWKS_TTL_SECONDS = 300


class TokenError(Exception):
    pass


def _jwks_url() -> str:
    return f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"


def _get_jwks() -> dict:
    now = time.time()
    if _jwks_cache["keys"] is None or now - _jwks_cache["fetched_at"] > _JWKS_TTL_SECONDS:
        response = httpx.get(_jwks_url(), timeout=5.0)
        response.raise_for_status()
        _jwks_cache["keys"] = response.json()
        _jwks_cache["fetched_at"] = now
    return _jwks_cache["keys"]


def decode_token(token: str) -> dict:
    """Validate a Keycloak-issued access token and return its claims.

    Raises TokenError on any signature, expiry, or issuer mismatch.
    """
    try:
        jwks = _get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        key = next((k for k in jwks["keys"] if k["kid"] == unverified_header.get("kid")), None)
        if key is None:
            # JWKS may have rotated since our cache was populated; refresh once and retry.
            _jwks_cache["keys"] = None
            jwks = _get_jwks()
            key = next((k for k in jwks["keys"] if k["kid"] == unverified_header.get("kid")), None)
        if key is None:
            raise TokenError("Unable to find matching signing key")

        claims = jwt.decode(
            token,
            key,
            algorithms=[unverified_header.get("alg", "RS256")],
            issuer=settings.keycloak_issuer,
            options={"verify_aud": False},
        )
        return claims
    except JWTError as exc:
        raise TokenError(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise TokenError(f"Could not fetch signing keys: {exc}") from exc


def extract_realm_roles(claims: dict) -> list[str]:
    return claims.get("realm_access", {}).get("roles", [])
