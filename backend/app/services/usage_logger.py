import sqlite3
import time
from datetime import datetime, timedelta, timezone
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


def get_performance_metrics() -> dict:
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    with _get_conn() as conn:
        time_rows = conn.execute(
            "SELECT response_time_ms FROM usage_logs ORDER BY response_time_ms ASC"
        ).fetchall()
        times = [r[0] for r in time_rows]
        n = len(times)

        def pct(p: float) -> int | None:
            if not times:
                return None
            return times[int((n - 1) * p / 100)]

        agg = conn.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) AS failures
            FROM usage_logs
            """
        ).fetchone()
        total = agg[0] or 0
        failures = agg[1] or 0
        failure_rate = round(failures / total * 100, 1) if total > 0 else 0.0

        bucket_rows = conn.execute(
            """
            SELECT substr(timestamp, 1, 13) || ':00:00' AS hour,
                   ROUND(AVG(response_time_ms))          AS avg_latency_ms,
                   COUNT(*)                               AS total,
                   SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) AS failures
            FROM usage_logs
            WHERE timestamp >= ?
            GROUP BY hour
            ORDER BY hour
            """,
            (cutoff,),
        ).fetchall()

        failure_rows = conn.execute(
            """
            SELECT id, timestamp, query, topic, response_time_ms
            FROM usage_logs
            WHERE success = 0
            ORDER BY id DESC
            LIMIT 10
            """
        ).fetchall()

    return {
        "p50_ms": pct(50),
        "p95_ms": pct(95),
        "p99_ms": pct(99),
        "failure_rate_pct": failure_rate,
        "total_queries": total,
        "total_failures": failures,
        "hourly_buckets": [
            {"hour": r[0], "avg_latency_ms": r[1], "total": r[2], "failures": r[3]}
            for r in bucket_rows
        ],
        "recent_failures": [
            {"id": r[0], "timestamp": r[1], "query": r[2], "topic": r[3], "response_time_ms": r[4]}
            for r in failure_rows
        ],
    }
