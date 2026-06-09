from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.chat.orchestrator import run_chat_turn
from app.database.message_repo import list_messages
from app.database.thread_repo import (
    create_thread,
    delete_thread,
    get_thread,
    list_threads,
    update_thread_title,
)

router = APIRouter()


class ChatStreamRequest(BaseModel):
    threadId: str
    messages: list[dict]


class CreateThreadRequest(BaseModel):
    title: str = "New Chat"


class UpdateThreadRequest(BaseModel):
    title: str


@router.post("/chat/stream")
async def chat_stream(
    body: ChatStreamRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    if not body.threadId or not body.threadId.strip():
        raise HTTPException(status_code=400, detail="threadId is required")
    if not body.messages:
        raise HTTPException(status_code=400, detail="At least one message is required")

    thread_id = uuid.UUID(body.threadId)
    thread = get_thread(thread_id, user.id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    return StreamingResponse(
        run_chat_turn(str(thread_id), body.messages, user_id=str(user.id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/threads")
async def list_threads_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
    return list_threads(user.id)


@router.post("/threads")
async def create_thread_endpoint(
    body: CreateThreadRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    return create_thread(user.id, title=body.title)


@router.get("/threads/{thread_id}")
async def get_thread_endpoint(
    thread_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
):
    thread = get_thread(thread_id, user.id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return thread


@router.patch("/threads/{thread_id}")
async def update_thread_endpoint(
    thread_id: uuid.UUID,
    body: UpdateThreadRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    thread = update_thread_title(thread_id, user.id, body.title)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return thread


@router.delete("/threads/{thread_id}")
async def delete_thread_endpoint(
    thread_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
):
    if not delete_thread(thread_id, user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return {"ok": True}


@router.get("/threads/{thread_id}/messages")
async def get_messages_endpoint(
    thread_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
):
    return list_messages(thread_id, user.id)
