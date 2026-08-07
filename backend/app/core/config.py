from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://app:app@localhost:5432/ragchat"

    keycloak_url: str = "http://localhost:8081"  # used server-side to fetch JWKS
    keycloak_issuer: str = "http://localhost:8081/realms/ragchat"  # must match the `iss` claim tokens carry
    keycloak_realm: str = "ragchat"
    keycloak_client_id: str = "ragchat-backend"

    # Service-account client scoped to realm-management's manage-users/view-users roles only —
    # deliberately not the Keycloak bootstrap superadmin, to keep the backend's admin-API blast
    # radius limited to this realm's users. Dev-only committed secret; rotate for anything beyond
    # local scratch use (see keycloak/realm-export.json).
    keycloak_admin_client_id: str = "ragchat-backend-admin"
    keycloak_admin_client_secret: str = "ragchat-backend-admin-dev-secret"

    ollama_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"

    # Dev-only default so the stack works out of the box; override in .env for anything beyond
    # local scratch use, since anyone with this repo can decrypt data encrypted under it.
    secret_encryption_key: str = "uYCiUWGe3Lo-dTnRC-F9he-yyxnyN1cjR3fYX5s7GHQ="

    upload_dir: str = "uploads"

    # PDF pages with fewer than this many extracted characters are treated as
    # image-only and re-extracted via OCR.
    ocr_fallback_char_threshold: int = 20

    # Cosine distance (0 = identical, 2 = opposite) above which a folder-scoped search is
    # considered to have found nothing relevant, triggering a fallback to an unscoped search.
    retrieval_similarity_threshold: float = 0.5
    retrieval_top_k: int = 5


settings = Settings()
