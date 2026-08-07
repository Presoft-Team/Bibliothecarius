import json
import threading

import httpx

from app.core.config import settings
from app.services.llm.base import LLMProviderError

# In-memory only — fine for a single-process local deployment; a pull in progress when the
# backend restarts just needs to be re-triggered (Ollama itself resumes partial downloads).
_pull_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _run_pull(model_name: str) -> None:
    with _jobs_lock:
        _pull_jobs[model_name] = {"status": "pulling", "completed": 0, "total": 0, "error": None}

    try:
        with httpx.stream(
            "POST", f"{settings.ollama_url}/api/pull", json={"name": model_name}, timeout=None
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                with _jobs_lock:
                    job = _pull_jobs[model_name]
                    job["status"] = data.get("status", job["status"])
                    if "completed" in data:
                        job["completed"] = data["completed"]
                    if "total" in data:
                        job["total"] = data["total"]
                if data.get("error"):
                    raise LLMProviderError(data["error"])
        with _jobs_lock:
            _pull_jobs[model_name]["status"] = "success"
    except Exception as exc:
        with _jobs_lock:
            _pull_jobs[model_name] = {
                "status": "error",
                "completed": 0,
                "total": 0,
                "error": str(exc),
            }


def start_pull(model_name: str) -> None:
    existing = _pull_jobs.get(model_name)
    if existing and existing["status"] == "pulling":
        return  # already in progress, don't start a second stream for the same model
    threading.Thread(target=_run_pull, args=(model_name,), daemon=True).start()


def get_pull_status(model_name: str) -> dict | None:
    return _pull_jobs.get(model_name)


def delete_model(model_name: str) -> None:
    try:
        response = httpx.request(
            "DELETE", f"{settings.ollama_url}/api/delete", json={"name": model_name}, timeout=10.0
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LLMProviderError(f"Could not delete Ollama model: {exc}") from exc
    _pull_jobs.pop(model_name, None)
