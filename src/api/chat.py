from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from api.deps import auth_service, ai_service, get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str
    query: str
    model: Optional[str] = None


@router.post("")
async def chat_message(
    req: ChatRequest, user: Dict[str, Any] = Depends(get_current_user)
):
    if not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )

    # Fetch session messages to extract context and history
    success, messages = auth_service.get_session_messages(req.session_id)
    if not success:
        messages = []

    # 1. Save user question
    auth_service.save_chat_message(
        session_id=req.session_id,
        content=req.query,
        role="user",
    )

    # 2. Extract report context from system message
    context_text = ""
    for msg in messages:
        if msg.get("role") == "system" and "__REPORT_TEXT__" in msg.get("content", ""):
            content = msg.get("content", "")
            start_tag = "__REPORT_TEXT__\n"
            end_tag = "\n__END_REPORT_TEXT__"
            start_idx = content.find(start_tag) + len(start_tag)
            end_idx = content.find(end_tag)
            if start_idx >= len(start_tag) and end_idx > start_idx:
                context_text = content[start_idx:end_idx]
                break

    # If not found in system message, check if there's an earlier analysis text
    if not context_text:
        for msg in messages:
            if msg.get("role") == "assistant" and len(msg.get("content", "")) > 100:
                context_text = msg.get("content", "")[:6000]
                break

    # 3. Generate response via Ollama
    result = await ai_service.get_chat_response_async(
        query=req.query,
        context_text=context_text,
        chat_history=messages,
        model=req.model,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to generate chat response"),
        )

    reply_content = result.get("content", "")

    # 4. Save assistant reply
    auth_service.save_chat_message(
        session_id=req.session_id,
        content=reply_content,
        role="assistant",
    )

    return {
        "success": True,
        "content": reply_content,
        "model_used": result.get("model_used"),
    }
