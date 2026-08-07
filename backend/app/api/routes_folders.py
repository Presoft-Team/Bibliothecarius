import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_folder
from app.db.session import get_db
from app.models.folder import Folder
from app.models.user import User
from app.schemas.folder import FolderCreate, FolderOut, FolderUpdate

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("", response_model=list[FolderOut])
def list_folders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Folder).filter(Folder.owner_id == user.id).order_by(Folder.name).all()


@router.post("", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: FolderCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if payload.parent_folder_id is not None:
        get_owned_folder(db, user, payload.parent_folder_id)

    folder = Folder(owner_id=user.id, name=payload.name, parent_folder_id=payload.parent_folder_id)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.patch("/{folder_id}", response_model=FolderOut)
def update_folder(
    folder_id: uuid.UUID,
    payload: FolderUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    folder = get_owned_folder(db, user, folder_id)

    if payload.parent_folder_id is not None:
        if payload.parent_folder_id == folder.id:
            raise HTTPException(status_code=400, detail="A folder cannot be its own parent")
        get_owned_folder(db, user, payload.parent_folder_id)
        folder.parent_folder_id = payload.parent_folder_id

    if payload.name is not None:
        folder.name = payload.name

    db.commit()
    db.refresh(folder)
    return folder


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    folder = get_owned_folder(db, user, folder_id)
    # Documents inside are unfiled rather than deleted; sub-folders are reparented to
    # the deleted folder's parent so nothing is silently lost.
    from app.models.document import Document

    db.query(Document).filter(Document.folder_id == folder.id).update({"folder_id": None})
    db.query(Folder).filter(Folder.parent_folder_id == folder.id).update(
        {"parent_folder_id": folder.parent_folder_id}
    )
    db.delete(folder)
    db.commit()
