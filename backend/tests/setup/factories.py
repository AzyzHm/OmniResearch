from datetime import UTC, datetime

NOW = datetime.now(UTC).isoformat()


def project_row(project_id="proj-1", user_id="user-123", name="My Project"):
    return {"id": project_id, "user_id": user_id, "name": name,
            "created_at": NOW, "updated_at": NOW}


def collection_row(collection_id="col-1", project_id="proj-1", name="My Coll"):
    return {"id": collection_id, "project_id": project_id, "name": name,
            "created_at": NOW, "projects": {"user_id": "user-123"}}


def chat_row(chat_id="chat-1", project_id="proj-1", name="My Chat"):
    return {"id": chat_id, "project_id": project_id, "name": name,
            "created_at": NOW, "projects": {"user_id": "user-123"}}


def message_row(msg_id="msg-1", chat_id="chat-1", role="user", content="Hello"):
    return {"id": msg_id, "chat_id": chat_id, "role": role, "content": content,
            "created_at": NOW}


def note_row(note_id="note-1", project_id="proj-1", name="My Note"):
    return {"id": note_id, "project_id": project_id, "name": name,
            "created_at": NOW, "projects": {"user_id": "user-123"}}


def note_item_row(item_id="item-1", note_id="note-1", message_id="msg-1",
                   chat_id="chat-1", role="assistant", content="Hi there!", sources=None):
    return {"id": item_id, "note_id": note_id, "message_id": message_id,
            "created_at": NOW,
            "messages": {"chat_id": chat_id, "role": role, "content": content, "sources": sources}}


def user_row(user_id="user-abc", username="alice", role="user", is_approved=True, daily_token_limit=80_000):
    return {"id": user_id, "username": username, "role": role,
            "is_approved": is_approved, "created_at": NOW,
            "daily_token_limit": daily_token_limit}