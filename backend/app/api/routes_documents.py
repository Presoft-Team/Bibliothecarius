import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_folder
from app.db.session import SessionLocal, get_db
from app.models.document import Document, DocumentChunk, DocumentPage
from app.models.user import User
from app.schemas.document import (
    DocumentConfirmResult,
    DocumentMove,
    DocumentOut,
    DocumentPreviewOut,
)
from app.services import storage
from app.services.chunking import chunk_text
from app.services.embeddings import embed_texts
from app.services.extraction import extract_document

router = APIRouter(prefix="/documents", tags=["documents"])


def _get_owned_document(db: Session, user: User, document_id: uuid.UUID) -> Document:
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.owner_id == user.id)
        .one_or_none()
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


def _run_extraction(document_id: uuid.UUID, file_path: str, content_type: str) -> None:
    """Runs in a FastAPI background task, after the request's DB session has closed."""
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:
            return
        try:
            pages = extract_document(file_path, content_type)
        except Exception as exc:  # extraction failures shouldn't crash the worker
            document.status = "extraction_failed"
            db.add(DocumentPage(document_id=document.id, page_number=1, extracted_text=str(exc),
                                 extraction_method="native", confidence=0.0))
            db.commit()
            return

        for page in pages:
            db.add(
                DocumentPage(
                    document_id=document.id,
                    page_number=page.page_number,
                    extracted_text=page.text,
                    extraction_method=page.method,
                    confidence=page.confidence,
                )
            )
        document.status = "previewing"
        db.commit()
    finally:
        db.close()


@router.get("", response_model=list[DocumentOut])
def list_documents(
    folder_id: uuid.UUID | None = None,
    unfiled: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Document).filter(Document.owner_id == user.id)
    if unfiled:
        query = query.filter(Document.folder_id.is_(None))
    elif folder_id is not None:
        query = query.filter(Document.folder_id == folder_id)
    return query.order_by(Document.uploaded_at.desc()).all()


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    folder_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if folder_id is not None:
        get_owned_folder(db, user, folder_id)

    try:
        content_type = storage.detect_content_type(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    document = Document(
        owner_id=user.id,
        folder_id=folder_id,
        filename=file.filename,
        content_type=content_type,
        status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    file_path = storage.save_upload(document.id, file.filename, file.file)
    background_tasks.add_task(_run_extraction, document.id, file_path, content_type)

    return document


@router.get("/{document_id}/preview", response_model=DocumentPreviewOut)
def preview_document(
    document_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    document = _get_owned_document(db, user, document_id)
    pages = (
        db.query(DocumentPage)
        .filter(DocumentPage.document_id == document.id)
        .order_by(DocumentPage.page_number)
        .all()
    )
    return DocumentPreviewOut(document=document, pages=pages)


@router.post("/{document_id}/confirm", response_model=DocumentConfirmResult)
def confirm_document(
    document_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    document = _get_owned_document(db, user, document_id)
    if document.status not in ("previewing", "ingested"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document is not ready to confirm (status={document.status})",
        )

    pages = (
        db.query(DocumentPage)
        .filter(DocumentPage.document_id == document.id)
        .order_by(DocumentPage.page_number)
        .all()
    )

    chunk_texts: list[str] = []
    chunk_page_refs: list[int] = []
    for page in pages:
        for chunk in chunk_text(page.extracted_text):
            chunk_texts.append(chunk)
            chunk_page_refs.append(page.page_number)

    # Re-confirming (e.g. after re-uploading) replaces the prior chunk set rather than duplicating it.
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()

    if chunk_texts:
        vectors = embed_texts(chunk_texts)
        for text, page_ref, vector in zip(chunk_texts, chunk_page_refs, vectors):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    folder_id=document.folder_id,
                    chunk_text=text,
                    embedding=vector,
                    page_ref=page_ref,
                )
            )

    document.status = "ingested"
    db.commit()
    db.refresh(document)
    return DocumentConfirmResult(document=document, chunk_count=len(chunk_texts))


@router.patch("/{document_id}", response_model=DocumentOut)
def move_document(
    document_id: uuid.UUID,
    payload: DocumentMove,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = _get_owned_document(db, user, document_id)
    if payload.folder_id is not None:
        get_owned_folder(db, user, payload.folder_id)
    document.folder_id = payload.folder_id
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).update(
        {"folder_id": payload.folder_id}
    )
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    document = _get_owned_document(db, user, document_id)
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
    db.query(DocumentPage).filter(DocumentPage.document_id == document.id).delete()
    db.delete(document)
    db.commit()
    storage.delete_document_files(document_id)
