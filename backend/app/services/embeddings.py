import httpx

from app.core.config import settings


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of strings via the local Ollama embeddings endpoint.

    Ollama's /api/embeddings takes one prompt per call, so this loops rather than
    batching; fine at scaffold scale, worth revisiting if ingestion volume grows.
    """
    embeddings = []
    with httpx.Client(base_url=settings.ollama_url, timeout=60.0) as client:
        for text in texts:
            response = client.post(
                "/api/embeddings",
                json={"model": settings.embedding_model, "prompt": text},
            )
            response.raise_for_status()
            embeddings.append(response.json()["embedding"])
    return embeddings
