from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from backend.config import get_settings


def _utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _db_path() -> Path:
    path = Path(get_settings().database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(_db_path())
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login_at TEXT
            );

            CREATE TABLE IF NOT EXISTS upload_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_token TEXT NOT NULL UNIQUE,
                original_filename TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS processing_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL UNIQUE,
                upload_token TEXT,
                source_type TEXT NOT NULL,
                slide_number INTEGER NOT NULL,
                semantic_mode TEXT NOT NULL,
                chart_type_override TEXT,
                illustration_style TEXT NOT NULL,
                image_model TEXT NOT NULL,
                status TEXT NOT NULL,
                final_pptx_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS slide_outlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_token TEXT NOT NULL,
                slide_number INTEGER NOT NULL,
                text_content TEXT,
                table_count INTEGER NOT NULL,
                shape_count INTEGER NOT NULL,
                table_titles_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(upload_token, slide_number)
            );
            """
        )


def database_health() -> dict[str, Any]:
    path = _db_path()
    init_db()
    with get_connection() as connection:
        user_count = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        upload_count = connection.execute("SELECT COUNT(*) AS count FROM upload_sessions").fetchone()["count"]
        job_count = connection.execute("SELECT COUNT(*) AS count FROM processing_jobs").fetchone()["count"]
    return {
        "database_enabled": True,
        "database_engine": "sqlite",
        "database_path": str(path),
        "database_exists": path.exists(),
        "database_stats": {
            "users": user_count,
            "uploads": upload_count,
            "jobs": job_count,
        },
    }


def authenticate_or_create_user(username: str, password: str) -> dict[str, Any]:
    normalized_username = username.strip()
    if not normalized_username:
        raise ValueError("用户名不能为空。")
    if not password.strip():
        raise ValueError("密码不能为空。")

    password_hash = _hash_password(password)
    now = _utc_now()
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id, username, password_hash, display_name FROM users WHERE username = ?",
            (normalized_username,),
        ).fetchone()
        if existing is None:
            display_name = normalized_username
            connection.execute(
                """
                INSERT INTO users (username, password_hash, display_name, created_at, last_login_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (normalized_username, password_hash, display_name, now, now),
            )
            user_id = connection.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
            return {"id": user_id, "username": normalized_username, "display_name": display_name, "created": True}

        if existing["password_hash"] != password_hash:
            raise ValueError("用户名或密码错误。")

        connection.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (now, existing["id"]),
        )
        return {
            "id": existing["id"],
            "username": existing["username"],
            "display_name": existing["display_name"],
            "created": False,
        }


def record_upload_session(upload_token: str, original_filename: str, stored_path: str | Path, size_bytes: int) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO upload_sessions (upload_token, original_filename, stored_path, size_bytes, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (upload_token, original_filename, str(stored_path), size_bytes, _utc_now()),
        )


def fetch_upload_session(upload_token: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT upload_token, original_filename, stored_path, size_bytes, created_at FROM upload_sessions WHERE upload_token = ?",
            (upload_token,),
        ).fetchone()
    return dict(row) if row else None


def record_processing_job(
    request_id: str,
    upload_token: str,
    source_type: str,
    slide_number: int,
    semantic_mode: str,
    chart_type_override: str,
    illustration_style: str,
    image_model: str,
    status: str,
    final_pptx_path: str = "",
) -> None:
    timestamp = _utc_now()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO processing_jobs (
                request_id, upload_token, source_type, slide_number, semantic_mode, chart_type_override,
                illustration_style, image_model, status, final_pptx_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                upload_token,
                source_type,
                slide_number,
                semantic_mode,
                chart_type_override,
                illustration_style,
                image_model,
                status,
                final_pptx_path,
                timestamp,
                timestamp,
            ),
        )


def record_slide_outline(upload_token: str, slides: list[dict[str, Any]]) -> None:
    timestamp = _utc_now()
    with get_connection() as connection:
        for slide in slides:
            connection.execute(
                """
                INSERT OR REPLACE INTO slide_outlines (
                    upload_token, slide_number, text_content, table_count, shape_count, table_titles_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    upload_token,
                    slide["slide_number"],
                    slide.get("text_content", ""),
                    slide.get("table_count", 0),
                    slide.get("shape_count", 0),
                    json.dumps(slide.get("table_titles", []), ensure_ascii=False),
                    timestamp,
                ),
            )


def list_recent_jobs(limit: int = 30) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT request_id, upload_token, source_type, slide_number, semantic_mode, chart_type_override,
                   illustration_style, image_model, status, final_pptx_path, created_at, updated_at
            FROM processing_jobs
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
