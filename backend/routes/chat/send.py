import json
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.config.auth import get_current_user
from backend.config.settings import get_settings
from backend.database.db import get_supabase
from backend.graph.graph import get_rag_graph
from backend.models.chat import ChatMessageRequest, ChatMessageResponse
from backend.routes.chat._shared import _own_chat
from backend.services.quota import DailyQuotaExceeded, enforce_daily_quota

router = APIRouter()


@router.post("/chats/{chat_id}/message", response_model=ChatMessageResponse)
async def send_message(
    chat_id: str,
    body: ChatMessageRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    1. Fetch existing history (before inserting the new message).
    2. Persist the user message.
    3. Run the agentic RAG graph (router -> [refine -> retrieve -> validate]* -> generate).
    4. Persist the assistant reply.
    5. Return the reply.
    """
    chat = _own_chat(chat_id, current_user["sub"])
    db = get_supabase()
    settings = get_settings()

    try:
        enforce_daily_quota(current_user["sub"])
    except DailyQuotaExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "quota_exceeded",
                "message": str(exc),
                "used": exc.used,
                "limit": exc.limit,
                "reset_at": exc.reset_at.isoformat(),
            },
        )

    hist = (
        db.table("messages")
        .select("role, content")
        .eq("chat_id", chat_id)
        .order("created_at", desc=True)
        .limit(settings.llm_context_limit)
        .execute()
    )
    history = cast(list[dict[str, Any]], list(reversed(hist.data)))

    db.table("messages").insert(
        {"chat_id": chat_id, "role": "user", "content": body.message}
    ).execute()

    try:
        graph = get_rag_graph()
        result = graph.invoke({
            "project_id": chat["project_id"],
            "chat_id": chat_id,
            "user_id": current_user["sub"],
            "query": body.message,
            "history": history,
            "retrieval_mode": body.retrieval_mode,
            "retrieval_attempts": 0,
            "needs_retrieval": False,
            "validation_passed": False,
            "context_chunks": [],
            "retrieved_pool": [],
        })
        reply = result.get("answer") or "⚠️ The model did not return a response."
    except Exception as exc:
        print(f"[RAG] /message error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    db.table("messages").insert(
        {"chat_id": chat_id, "role": "assistant", "content": reply}
    ).execute()

    return ChatMessageResponse(response=reply)


@router.post("/chats/{chat_id}/message/stream")
async def send_message_stream(
    chat_id: str,
    body: ChatMessageRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Same as /message, but streams Server-Sent Events as each graph node
    finishes, so the frontend can show live progress ("router", "retrieve",
    "generate", ...) instead of one opaque spinner. Each node also prints to
    the backend terminal (see backend/graph/nodes/*.py) for local debugging.

    Event shapes:
      {"type": "node", "node": "<node_name>"}
      {"type": "done", "answer": "<final answer>"}
      {"type": "error", "detail": "<message>"}
    """
    chat = _own_chat(chat_id, current_user["sub"])
    db = get_supabase()
    settings = get_settings()

    try:
        enforce_daily_quota(current_user["sub"])
    except DailyQuotaExceeded as exc:
        payload = {
            "type": "error",
            "code": "quota_exceeded",
            "detail": str(exc),
            "used": exc.used,
            "limit": exc.limit,
            "reset_at": exc.reset_at.isoformat(),
        }

        def quota_error_stream():
            yield f"data: {json.dumps(payload)}\n\n"

        return StreamingResponse(quota_error_stream(), media_type="text/event-stream")

    hist = (
        db.table("messages")
        .select("role, content")
        .eq("chat_id", chat_id)
        .order("created_at", desc=True)
        .limit(settings.llm_context_limit)
        .execute()
    )
    history = cast(list[dict[str, Any]], list(reversed(hist.data)))

    db.table("messages").insert(
        {"chat_id": chat_id, "role": "user", "content": body.message}
    ).execute()

    initial_state = {
        "project_id": chat["project_id"],
        "chat_id": chat_id,
        "user_id": current_user["sub"],
        "query": body.message,
        "history": history,
        "retrieval_mode": body.retrieval_mode,
        "retrieval_attempts": 0,
        "needs_retrieval": False,
        "validation_passed": False,
        "context_chunks": [],
        "retrieved_pool": [],
    }

    def event_stream():
        graph = get_rag_graph()
        answer = "⚠️ The model did not return a response."
        try:
            for update in graph.stream(initial_state, stream_mode="updates"): # type: ignore
                node_name = next(iter(update))
                node_output = update[node_name] or {}
                print(f"[RAG] stream: {node_name} finished")
                yield f"data: {json.dumps({'type': 'node', 'node': node_name})}\n\n"
                if "answer" in node_output:
                    answer = node_output["answer"]
        except Exception as exc:
            print(f"[RAG] stream error: {exc}")
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"
            return

        db.table("messages").insert(
            {"chat_id": chat_id, "role": "assistant", "content": answer}
        ).execute()
        yield f"data: {json.dumps({'type': 'done', 'answer': answer})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")