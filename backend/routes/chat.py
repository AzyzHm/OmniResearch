import json
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.config.auth import get_current_user
from backend.config.settings import get_settings
from backend.database.db import get_supabase
from backend.graph.graph import get_rag_graph
from backend.models.chat import (
    ChatCreate,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatOut,
    ChatUpdate,
    MessageOut,
)

router = APIRouter(tags=["Chats"])


def _verify_project_owner(project_id: str, user_id: str) -> None:
    """Raise 404 if the project doesn't belong to the user."""
    db = get_supabase()
    result = (
        db.table("projects")
        .select("id")
        .eq("id", project_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")


def _own_chat(chat_id: str, user_id: str) -> dict:
    """
    Fetch a chat and verify through its project that it belongs to the user.
    Returns the chat row.
    """
    db = get_supabase()
    result = (
        db.table("chats")
        .select("*, projects(user_id)")
        .eq("id", chat_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    row: Any = result.data[0]
    project: Any = row.get("projects") or {}
    if project.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    return row


@router.get("/projects/{project_id}/chats", response_model=list[ChatOut])
async def list_chats(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    _verify_project_owner(project_id, current_user["sub"])
    db = get_supabase()
    result = (
        db.table("chats")
        .select("id, project_id, name, created_at")
        .eq("project_id", project_id)
        .order("created_at", desc=False)
        .execute()
    )
    return result.data


@router.post(
    "/projects/{project_id}/chats",
    response_model=ChatOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat(
    project_id: str,
    body: ChatCreate,
    current_user: dict = Depends(get_current_user),
):
    _verify_project_owner(project_id, current_user["sub"])
    db = get_supabase()
    result = db.table("chats").insert(
        {"project_id": project_id, "name": body.name}
    ).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create chat.")
    row: Any = result.data[0]
    return row


@router.put("/chats/{chat_id}", response_model=ChatOut)
async def rename_chat(
    chat_id: str,
    body: ChatUpdate,
    current_user: dict = Depends(get_current_user),
):
    _own_chat(chat_id, current_user["sub"])
    db = get_supabase()
    result = (
        db.table("chats")
        .update({"name": body.name})
        .eq("id", chat_id)
        .execute()
    )
    row: Any = result.data[0]
    return row


@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    _own_chat(chat_id, current_user["sub"])
    db = get_supabase()
    db.table("chats").delete().eq("id", chat_id).execute()

@router.get("/chats/{chat_id}/messages", response_model=list[MessageOut])
async def get_messages(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Return the most recent ui_history_limit messages for a chat, oldest first."""
    _own_chat(chat_id, current_user["sub"])
    db = get_supabase()
    settings = get_settings()

    result = (
        db.table("messages")
        .select("id, chat_id, role, content, created_at")
        .eq("chat_id", chat_id)
        .order("created_at", desc=True)
        .limit(settings.ui_history_limit)
        .execute()
    )
    return list(reversed(result.data))


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