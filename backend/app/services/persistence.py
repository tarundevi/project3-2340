import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings


class PersistenceError(Exception):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _persistence_db_path() -> Path:
    path = Path(settings.persistence_db_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent.parent / path
    return path


def _get_local_conn() -> sqlite3.Connection:
    db_path = _persistence_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_persistence() -> None:
    if settings.persistence_mode != "aws":
        with _get_local_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    topic TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_message_preview TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    topic TEXT NOT NULL DEFAULT '',
                    sources_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, updated_at DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at ASC)"
            )
            conn.commit()


def _conversation_summary_from_row(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "topic": row["topic"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_message_preview": row["last_message_preview"],
    }


def _message_from_row(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    return {
        "role": row["role"],
        "content": row["content"],
        "topic": row["topic"],
        "created_at": row["created_at"],
        "sources": json.loads(row["sources_json"]) if row["sources_json"] else [],
    }


def _ensure_local_conversation(user_id: str, conversation_id: str) -> dict[str, Any]:
    with _get_local_conn() as conn:
        row = conn.execute(
            """
            SELECT id, title, topic, created_at, updated_at, last_message_preview
            FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        ).fetchone()
    if not row:
        raise PersistenceError("Conversation not found.")
    return _conversation_summary_from_row(row)


def _derive_title(message: str) -> str:
    compact = " ".join(message.split()).strip()
    if not compact:
        return "New Chat"
    return compact[:48] + ("…" if len(compact) > 48 else "")


def create_conversation(user_id: str, title: str = "", topic: str = "") -> dict[str, Any]:
    if settings.persistence_mode == "aws":
        return _create_aws_conversation(user_id, title=title, topic=topic)
    return _create_local_conversation(user_id, title=title, topic=topic)


def _create_local_conversation(user_id: str, title: str = "", topic: str = "") -> dict[str, Any]:
    conversation_id = str(uuid.uuid4())
    now = _utc_now()
    cleaned_title = " ".join(title.split()).strip() or "New Chat"
    conversation = {
        "id": conversation_id,
        "user_id": user_id,
        "title": cleaned_title,
        "topic": topic,
        "created_at": now,
        "updated_at": now,
        "last_message_preview": "",
    }
    with _get_local_conn() as conn:
        conn.execute(
            """
            INSERT INTO conversations (id, user_id, title, topic, created_at, updated_at, last_message_preview)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation["id"],
                conversation["user_id"],
                conversation["title"],
                conversation["topic"],
                conversation["created_at"],
                conversation["updated_at"],
                conversation["last_message_preview"],
            ),
        )
        conn.commit()
    return {key: conversation[key] for key in ("id", "title", "topic", "created_at", "updated_at", "last_message_preview")}


def list_conversations(user_id: str) -> list[dict[str, Any]]:
    if settings.persistence_mode == "aws":
        return _list_aws_conversations(user_id)
    with _get_local_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, title, topic, created_at, updated_at, last_message_preview
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [_conversation_summary_from_row(row) for row in rows]


def get_conversation(user_id: str, conversation_id: str) -> dict[str, Any]:
    if settings.persistence_mode == "aws":
        return _get_aws_conversation(user_id, conversation_id)
    conversation = _ensure_local_conversation(user_id, conversation_id)
    with _get_local_conn() as conn:
        rows = conn.execute(
            """
            SELECT role, content, topic, created_at, sources_json
            FROM messages
            WHERE conversation_id = ? AND user_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id, user_id),
        ).fetchall()
    return {"conversation": conversation, "messages": [_message_from_row(row) for row in rows]}


def append_chat_exchange(
    user_id: str,
    conversation_id: str,
    user_message: str,
    assistant_message: str,
    topic: str = "",
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if settings.persistence_mode == "aws":
        return _append_aws_chat_exchange(
            user_id,
            conversation_id,
            user_message=user_message,
            assistant_message=assistant_message,
            topic=topic,
            sources=sources or [],
        )
    return _append_local_chat_exchange(
        user_id,
        conversation_id,
        user_message=user_message,
        assistant_message=assistant_message,
        topic=topic,
        sources=sources or [],
    )


def ensure_conversation(user_id: str, conversation_id: str = "", topic: str = "", first_message: str = "") -> dict[str, Any]:
    if conversation_id:
        return get_conversation(user_id, conversation_id)["conversation"]
    title = _derive_title(first_message)
    return create_conversation(user_id, title=title, topic=topic)


def _append_local_chat_exchange(
    user_id: str,
    conversation_id: str,
    user_message: str,
    assistant_message: str,
    topic: str = "",
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    conversation = _ensure_local_conversation(user_id, conversation_id)
    now_user = _utc_now()
    now_assistant = _utc_now()
    title = conversation["title"]
    if title == "New Chat":
        title = _derive_title(user_message)
    preview = " ".join(user_message.split()).strip()[:80]

    with _get_local_conn() as conn:
        conn.execute(
            """
            INSERT INTO messages (id, conversation_id, user_id, role, content, topic, sources_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), conversation_id, user_id, "user", user_message, topic, "[]", now_user),
        )
        conn.execute(
            """
            INSERT INTO messages (id, conversation_id, user_id, role, content, topic, sources_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                conversation_id,
                user_id,
                "bot",
                assistant_message,
                topic,
                json.dumps(sources or []),
                now_assistant,
            ),
        )
        conn.execute(
            """
            UPDATE conversations
            SET title = ?, topic = ?, updated_at = ?, last_message_preview = ?
            WHERE id = ? AND user_id = ?
            """,
            (title, topic or conversation["topic"], now_assistant, preview, conversation_id, user_id),
        )
        conn.commit()

    return get_conversation(user_id, conversation_id)


def _aws_dynamodb():
    import boto3

    return boto3.resource("dynamodb", region_name=settings.aws_region)


def _aws_s3():
    import boto3

    return boto3.client("s3", region_name=settings.aws_region)


def _conversations_table():
    return _aws_dynamodb().Table(settings.dynamodb_conversations_table)


def _messages_table():
    return _aws_dynamodb().Table(settings.dynamodb_messages_table)


def _aws_snapshot_key(user_id: str, conversation_id: str) -> str:
    prefix = settings.s3_conversation_prefix.strip("/ ")
    return f"{prefix}/{user_id}/{conversation_id}.json"


def _create_aws_conversation(user_id: str, title: str = "", topic: str = "") -> dict[str, Any]:
    conversation_id = str(uuid.uuid4())
    now = _utc_now()
    item = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "title": " ".join(title.split()).strip() or "New Chat",
        "topic": topic,
        "created_at": now,
        "updated_at": now,
        "last_message_preview": "",
    }
    _conversations_table().put_item(Item=item)
    return {
        "id": item["conversation_id"],
        "title": item["title"],
        "topic": item["topic"],
        "created_at": item["created_at"],
        "updated_at": item["updated_at"],
        "last_message_preview": item["last_message_preview"],
    }


def _list_aws_conversations(user_id: str) -> list[dict[str, Any]]:
    from boto3.dynamodb.conditions import Key

    response = _conversations_table().query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,
    )
    items = response.get("Items", [])
    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return [
        {
            "id": item["conversation_id"],
            "title": item.get("title", "New Chat"),
            "topic": item.get("topic", ""),
            "created_at": item.get("created_at", ""),
            "updated_at": item.get("updated_at", ""),
            "last_message_preview": item.get("last_message_preview", ""),
        }
        for item in items
    ]


def _get_aws_conversation(user_id: str, conversation_id: str) -> dict[str, Any]:
    from boto3.dynamodb.conditions import Key

    conversation_response = _conversations_table().get_item(
        Key={"user_id": user_id, "conversation_id": conversation_id}
    )
    item = conversation_response.get("Item")
    if not item:
        raise PersistenceError("Conversation not found.")

    messages_response = _messages_table().query(
        KeyConditionExpression=Key("conversation_id").eq(conversation_id),
        ScanIndexForward=True,
    )
    messages = []
    for message in messages_response.get("Items", []):
        if message.get("user_id") != user_id:
            continue
        messages.append(
            {
                "role": message["role"],
                "content": message["content"],
                "topic": message.get("topic", ""),
                "created_at": message["created_at"],
                "sources": message.get("sources", []),
            }
        )

    return {
        "conversation": {
            "id": item["conversation_id"],
            "title": item.get("title", "New Chat"),
            "topic": item.get("topic", ""),
            "created_at": item.get("created_at", ""),
            "updated_at": item.get("updated_at", ""),
            "last_message_preview": item.get("last_message_preview", ""),
        },
        "messages": messages,
    }


def _append_aws_chat_exchange(
    user_id: str,
    conversation_id: str,
    user_message: str,
    assistant_message: str,
    topic: str = "",
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    conversation = _get_aws_conversation(user_id, conversation_id)["conversation"]
    user_timestamp = _utc_now()
    assistant_timestamp = _utc_now()
    title = conversation["title"] if conversation["title"] != "New Chat" else _derive_title(user_message)
    preview = " ".join(user_message.split()).strip()[:80]

    _messages_table().put_item(
        Item={
            "conversation_id": conversation_id,
            "created_at": user_timestamp,
            "message_id": str(uuid.uuid4()),
            "user_id": user_id,
            "role": "user",
            "content": user_message,
            "topic": topic,
            "sources": [],
        }
    )
    _messages_table().put_item(
        Item={
            "conversation_id": conversation_id,
            "created_at": assistant_timestamp,
            "message_id": str(uuid.uuid4()),
            "user_id": user_id,
            "role": "bot",
            "content": assistant_message,
            "topic": topic,
            "sources": sources or [],
        }
    )
    _conversations_table().put_item(
        Item={
            "user_id": user_id,
            "conversation_id": conversation_id,
            "title": title,
            "topic": topic or conversation["topic"],
            "created_at": conversation["created_at"],
            "updated_at": assistant_timestamp,
            "last_message_preview": preview,
        }
    )

    detail = _get_aws_conversation(user_id, conversation_id)
    _write_aws_snapshot(user_id, conversation_id, detail)
    return detail


def _write_aws_snapshot(user_id: str, conversation_id: str, detail: dict[str, Any]) -> None:
    if not settings.s3_bucket_name:
        return
    _aws_s3().put_object(
        Bucket=settings.s3_bucket_name,
        Key=_aws_snapshot_key(user_id, conversation_id),
        Body=json.dumps(detail).encode("utf-8"),
        ContentType="application/json",
    )
