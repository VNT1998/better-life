import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import ai_service, auth_service, get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str
    query: str
    model: str | None = None


def _extract_context(messages: list[dict[str, Any]]) -> str:
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

    if not context_text:
        for msg in messages:
            if msg.get("role") == "assistant" and len(msg.get("content", "")) > 100:
                context_text = msg.get("content", "")[:6000]
                break

    return context_text


@router.post("")
async def chat_message(req: ChatRequest, user: dict[str, Any] = Depends(get_current_user)):
    if not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )

    success, messages = auth_service.get_session_messages(req.session_id)
    if not success:
        messages = []

    # 1. Save user question
    auth_service.save_chat_message(
        session_id=req.session_id,
        content=req.query,
        role="user",
    )

    # 2. Extract report context
    context_text = _extract_context(messages)

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


@router.post("/stream")
async def chat_message_stream(req: ChatRequest, user: dict[str, Any] = Depends(get_current_user)):
    if not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )

    success, messages = auth_service.get_session_messages(req.session_id)
    if not success:
        messages = []

    # Save user question
    auth_service.save_chat_message(
        session_id=req.session_id,
        content=req.query,
        role="user",
    )

    context_text = _extract_context(messages)

    async def event_generator():
        accumulated_chunks = []
        model_used = req.model or "primary"
        try:
            async for chunk in ai_service.stream_chat_response_async(
                query=req.query,
                context_text=context_text,
                chat_history=messages,
                model=req.model,
            ):
                token = chunk.get("token", "")
                if token:
                    accumulated_chunks.append(token)
                if chunk.get("model"):
                    model_used = chunk["model"]

                event_data = {
                    "token": token,
                    "done": chunk.get("done", False),
                    "model_used": model_used,
                    "error": chunk.get("error"),
                }
                yield f"data: {json.dumps(event_data)}\n\n"

            # Persist assistant reply after stream finishes
            full_reply = "".join(accumulated_chunks)
            if full_reply.strip():
                auth_service.save_chat_message(
                    session_id=req.session_id,
                    content=full_reply,
                    role="assistant",
                )
        except Exception as exc:
            err_data = {"token": "", "done": True, "error": str(exc)}
            yield f"data: {json.dumps(err_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
