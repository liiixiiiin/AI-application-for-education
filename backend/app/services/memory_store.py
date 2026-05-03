import json

from ..db import get_connection
from ..utils import generate_id, now_iso

MAX_HISTORY_MESSAGES = 10
TITLE_MAX_LENGTH = 15


def create_conversation(user_id: str, course_id: str, title: str | None = None) -> dict:
    conv_id = generate_id("conv")
    ts = now_iso()
    conn = get_connection()
    conn.execute(
        "INSERT INTO conversations (id, user_id, course_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (conv_id, user_id, course_id, title or "新对话", ts, ts),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    conn.close()
    return dict(row)


def list_conversations(user_id: str, course_id: str | None = None) -> list[dict]:
    conn = get_connection()
    if course_id:
        rows = conn.execute(
            "SELECT * FROM conversations WHERE user_id = ? AND course_id = ? ORDER BY updated_at DESC",
            (user_id, course_id),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversation(conversation_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_conversation_with_messages(conversation_id: str) -> dict | None:
    conv = get_conversation(conversation_id)
    if not conv:
        return None
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conversation_id,),
    ).fetchall()
    conn.close()
    conv["messages"] = [_parse_message_row(r) for r in rows]
    return conv


def get_latest_conversation(user_id: str, course_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM conversations WHERE user_id = ? AND course_id = ? ORDER BY updated_at DESC LIMIT 1",
        (user_id, course_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_or_create_conversation(user_id: str, course_id: str, conversation_id: str | None = None) -> dict:
    if conversation_id:
        conv = get_conversation(conversation_id)
        if conv:
            return conv
    conv = get_latest_conversation(user_id, course_id)
    if conv:
        return conv
    return create_conversation(user_id, course_id)


def update_conversation_title(conversation_id: str, title: str) -> dict | None:
    conn = get_connection()
    conn.execute(
        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
        (title, now_iso(), conversation_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_conversation(conversation_id: str) -> bool:
    conn = get_connection()
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def add_message(conversation_id: str, role: str, content: str, citations: list | None = None) -> dict:
    msg_id = generate_id("msg")
    ts = now_iso()
    citations_json = json.dumps(citations or [], ensure_ascii=False)
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (id, conversation_id, role, content, citations, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (msg_id, conversation_id, role, content, citations_json, ts),
    )
    conn.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (ts, conversation_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM messages WHERE id = ?", (msg_id,)).fetchone()
    conn.close()
    return _parse_message_row(row)


def get_recent_messages(conversation_id: str, limit: int = MAX_HISTORY_MESSAGES) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT ?",
        (conversation_id, limit),
    ).fetchall()
    conn.close()
    messages = [_parse_message_row(r) for r in reversed(rows)]
    return messages


def auto_title_from_question(conversation_id: str, question: str) -> None:
    """Set conversation title from first user question if still default."""
    conv = get_conversation(conversation_id)
    if not conv or conv["title"] != "新对话":
        return
    title = question[:TITLE_MAX_LENGTH].strip()
    if len(question) > TITLE_MAX_LENGTH:
        title += "…"
    update_conversation_title(conversation_id, title)


def _parse_message_row(row) -> dict:
    d = dict(row)
    raw = d.get("citations", "[]")
    try:
        d["citations"] = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        d["citations"] = []
    return d
