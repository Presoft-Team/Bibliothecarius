from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_admin_users import router as admin_users_router
from app.api.routes_assistant_config import router as assistant_config_router
from app.api.routes_chat import router as chat_router
from app.api.routes_documents import router as documents_router
from app.api.routes_folders import router as folders_router
from app.api.routes_llm import router as llm_router
from app.api.routes_me import router as me_router
from app.api.routes_provider_credentials import router as provider_credentials_router
from app.api.routes_tones import router as tones_router

app = FastAPI(title="RAG Chat Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me_router)
app.include_router(folders_router)
app.include_router(documents_router)
app.include_router(tones_router)
app.include_router(assistant_config_router)
app.include_router(provider_credentials_router)
app.include_router(llm_router)
app.include_router(chat_router)
app.include_router(admin_users_router)


@app.get("/health")
def health():
    return {"status": "ok"}
