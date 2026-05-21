from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.auth_service import get_current_user
from app.services.chat_service import answer_chat, reindex_user_receipts

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return answer_chat(request, user.id, db)


@router.post("/reindex")
def reindex_chat(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    indexed = reindex_user_receipts(user.id, db)
    return {"indexed": indexed}
