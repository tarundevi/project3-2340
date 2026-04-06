import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "usage_logs.db"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                topic TEXT NOT NULL DEFAULT '',
                response_time_ms INTEGER NOT NULL,
                success INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conn.commit()


def log_query(query: str, topic: str, response_time_ms: int, success: bool) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO usage_logs (timestamp, query, topic, response_time_ms, success) VALUES (?, ?, ?, ?, ?)",
            (ts, query, topic, response_time_ms, int(success)),
        )
        conn.commit()


def get_logs(limit: int = 100) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, query, topic, response_time_ms, success FROM usage_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_stats() -> dict:
    with _get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_queries,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS successful_queries,
                ROUND(AVG(response_time_ms)) AS avg_response_time_ms,
                MIN(response_time_ms) AS min_response_time_ms,
                MAX(response_time_ms) AS max_response_time_ms
            FROM usage_logs
            """
        ).fetchone()
    return dict(row) if row else {}
