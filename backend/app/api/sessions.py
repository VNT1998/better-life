from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import auth_service, get_current_user

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    title: str | None = None


class SaveMessageRequest(BaseModel):
    content: str
    role: str = "user"


@router.get("")
def list_sessions(user: dict[str, Any] = Depends(get_current_user)):
    user_id = user["id"]
    success, sessions = auth_service.get_user_sessions(user_id)
    if not success:
        return []
    return sessions


@router.post("")
def create_session(req: CreateSessionRequest, user: dict[str, Any] = Depends(get_current_user)):
    user_id = user["id"]
    success, session = auth_service.create_session(user_id, title=req.title)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {session}",
        )
    return session


@router.delete("/{session_id}")
def delete_session(session_id: str, user: dict[str, Any] = Depends(get_current_user)):
    success, error = auth_service.delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete session: {error}",
        )
    return {"message": "Session deleted"}


@router.get("/{session_id}/messages")
def get_session_messages(session_id: str, user: dict[str, Any] = Depends(get_current_user)):
    success, messages = auth_service.get_session_messages(session_id)
    if not success:
        return []
    return messages


@router.post("/{session_id}/messages")
def save_session_message(
    session_id: str,
    req: SaveMessageRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    success, msg = auth_service.save_chat_message(
        session_id=session_id, content=req.content, role=req.role
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save message",
        )
    return msg
