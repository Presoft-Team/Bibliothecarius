from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/me")
def read_current_user(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "display_name": user.display_name,
        "email": user.email,
        "role": user.role,
    }
