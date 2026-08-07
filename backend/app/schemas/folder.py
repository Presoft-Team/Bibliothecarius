import uuid

from pydantic import BaseModel


class FolderCreate(BaseModel):
    name: str
    parent_folder_id: uuid.UUID | None = None


class FolderUpdate(BaseModel):
    name: str | None = None
    parent_folder_id: uuid.UUID | None = None


class FolderOut(BaseModel):
    id: uuid.UUID
    name: str
    parent_folder_id: uuid.UUID | None

    model_config = {"from_attributes": True}
