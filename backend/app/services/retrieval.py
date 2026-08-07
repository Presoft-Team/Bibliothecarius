import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.services.embeddings import embed_texts


@dataclass
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page_ref: int | None
    chunk_text: str
    distance: float


def _search(
    db: Session,
    owner_id: uuid.UUID,
    query_embedding: list[float],
    folder_ids: list[uuid.UUID] | None,
    top_k: int,
) -> list[RetrievedChunk]:
    distance = DocumentChunk.embedding.cosine_distance(query_embedding)
    query = (
        db.query(DocumentChunk, Document.filename, distance.label("distance"))
        .join(Document, Document.id == DocumentChunk.document_id)
        .filter(Document.owner_id == owner_id)
    )
    if folder_ids is not None:
        query = query.filter(DocumentChunk.folder_id.in_(folder_ids))

    rows = query.order_by(distance).limit(top_k).all()
    return [
        RetrievedChunk(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            filename=filename,
            page_ref=chunk.page_ref,
            chunk_text=chunk.chunk_text,
            distance=dist,
        )
        for chunk, filename, dist in rows
    ]


def _filter_relevant(results: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """`_search` always returns top_k regardless of how relevant they actually are — for a query
    with no real match (a bare "hi", a question outside the corpus entirely) that means attaching
    5 essentially-random chunks as "context" and citations. Drop anything past the relevance
    threshold instead of forcing every reply to cite something."""
    return [r for r in results if r.distance <= settings.retrieval_similarity_threshold]


def retrieve(
    db: Session,
    owner_id: uuid.UUID,
    query_text: str,
    folder_ids: list[uuid.UUID] | None,
    top_k: int | None = None,
) -> tuple[list[RetrievedChunk], bool]:
    """Returns (chunks, fallback_used). folder_ids=None means search everything.

    When folder_ids is given but nothing in-scope is similar enough (per
    RETRIEVAL_SIMILARITY_THRESHOLD), transparently falls back to an unscoped search
    rather than returning an empty/unhelpful answer.
    """
    top_k = top_k or settings.retrieval_top_k
    query_embedding = embed_texts([query_text])[0]

    if folder_ids is None:
        return _filter_relevant(_search(db, owner_id, query_embedding, folder_ids=None, top_k=top_k)), False

    scoped_results = _search(db, owner_id, query_embedding, folder_ids=folder_ids, top_k=top_k)
    if scoped_results and scoped_results[0].distance <= settings.retrieval_similarity_threshold:
        return _filter_relevant(scoped_results), False

    unscoped_results = _search(db, owner_id, query_embedding, folder_ids=None, top_k=top_k)
    return _filter_relevant(unscoped_results), True
