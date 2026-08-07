from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class DecryptionError(Exception):
    pass


@lru_cache
def _fernet() -> Fernet:
    return Fernet(settings.secret_encryption_key.encode())


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise DecryptionError("Stored credential could not be decrypted") from exc
