from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.llm import LLMTestRequest, LLMTestResponse
from app.schemas.ollama import OllamaPullRequest, OllamaPullStatus
from app.services.llm.base import ChatMessage, LLMProviderError
from app.services.llm.factory import get_provider
from app.services.llm.model_listing import list_models
from app.services.llm.ollama_management import delete_model, get_pull_status, start_pull

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/models", response_model=list[str])
def get_models(provider: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Live model list for the given provider — Ollama's own pulled models, or the cloud
    provider's catalog via the user's stored key — instead of a static guessed name."""
    try:
        return list_models(db, user, provider)
    except LLMProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/test", response_model=LLMTestResponse)
def test_generate(
    payload: LLMTestRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Exercises the provider abstraction directly; the chat endpoint (phase 6) will call the
    same factory with retrieved context instead of a bare message."""
    try:
        provider = get_provider(db, user, payload.provider, payload.model)
        reply = provider.generate(
            messages=[ChatMessage(role="user", content=payload.message)],
            system_prompt=payload.system_prompt,
            params={"temperature": payload.temperature},
        )
    except LLMProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return LLMTestResponse(reply=reply)


@router.post("/ollama/models", status_code=status.HTTP_202_ACCEPTED, response_model=OllamaPullStatus)
def pull_ollama_model(payload: OllamaPullRequest, admin: User = Depends(require_admin)):
    """Kicks off `ollama pull` in the background and returns immediately — a model can take
    minutes to download. Poll GET /llm/ollama/models/{name}/status for progress. Admin-only:
    Ollama is a shared local resource, not a per-user credential like the cloud providers."""
    start_pull(payload.name)
    return OllamaPullStatus(status="pulling")


@router.get("/ollama/models/{name}/status", response_model=OllamaPullStatus)
def ollama_pull_status(name: str, user: User = Depends(get_current_user)):
    job = get_pull_status(name)
    if job is None:
        return OllamaPullStatus(status="not_found")
    return OllamaPullStatus(**job)


@router.delete("/ollama/models/{name}", status_code=status.HTTP_204_NO_CONTENT)
def remove_ollama_model(name: str, admin: User = Depends(require_admin)):
    try:
        delete_model(name)
    except LLMProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
