import os
import shutil
import uuid

from app.core.config import settings

CONTENT_TYPE_BY_EXTENSION = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".txt": "txt",
}


def detect_content_type(filename: str) -> str:
    _, ext = os.path.splitext(filename.lower())
    content_type = CONTENT_TYPE_BY_EXTENSION.get(ext)
    if content_type is None:
        raise ValueError(f"Unsupported file extension: {ext or '(none)'}")
    return content_type


def document_dir(document_id: uuid.UUID) -> str:
    return os.path.join(settings.upload_dir, str(document_id))


def document_file_path(document_id: uuid.UUID, filename: str) -> str:
    return os.path.join(document_dir(document_id), filename)


def save_upload(document_id: uuid.UUID, filename: str, file_obj) -> str:
    directory = document_dir(document_id)
    os.makedirs(directory, exist_ok=True)
    path = document_file_path(document_id, filename)
    with open(path, "wb") as out:
        shutil.copyfileobj(file_obj, out)
    return path


def delete_document_files(document_id: uuid.UUID) -> None:
    shutil.rmtree(document_dir(document_id), ignore_errors=True)
