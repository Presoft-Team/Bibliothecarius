from pydantic import BaseModel


class OllamaPullRequest(BaseModel):
    name: str


class OllamaPullStatus(BaseModel):
    status: str  # "pulling" | "success" | "error" | "not_found"
    completed: int = 0
    total: int = 0
    error: str | None = None
