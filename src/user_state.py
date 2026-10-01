"""Private, local-only reading state for a single workstation user."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any

from .config import DATA_DIR
from .normalization import normalize_doi

USER_STATE_DB = DATA_DIR / "private_reading_state.sqlite3"


def article_key(*, doi: Any, title_hash: Any, journal_name: Any) -> str:
    normalized_doi = normalize_doi(str(doi or ""))
    if normalized_doi:
        return f"doi:{normalized_doi}"
    source = f"{str(title_hash or '').strip()}|{str(journal_name or '').strip().casefold()}"
    return "title:" + hashlib.sha256(source.encode("utf-8")).hexdigest()


def _connect(path: Path = USER_STATE_DB) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def load_states(keys: list[str], path: Path = USER_STATE_DB) -> dict[str, dict[str, Any]]:
    if not keys or not path.exists():
        return {}
    placeholders = ",".join("?" for _ in keys)
    with _connect(path) as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS article_state (
                article_key TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT '未读',
                favorite INTEGER NOT NULL DEFAULT 0,
                user_notes TEXT NOT NULL DEFAULT '',
                personal_tags TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        rows = con.execute(
            f"SELECT article_key,status,favorite,user_notes,personal_tags FROM article_state WHERE article_key IN ({placeholders})",
            keys,
        ).fetchall()
    return {row["article_key"]: dict(row) for row in rows}


def save_state(
    *, article_key_value: str, status: str, favorite: bool, user_notes: str, personal_tags: str,
    path: Path = USER_STATE_DB,
) -> None:
    with _connect(path) as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS article_state (
                article_key TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT '未读',
                favorite INTEGER NOT NULL DEFAULT 0,
                user_notes TEXT NOT NULL DEFAULT '',
                personal_tags TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        con.execute(
            """INSERT INTO article_state(article_key,status,favorite,user_notes,personal_tags)
               VALUES(?,?,?,?,?)
               ON CONFLICT(article_key) DO UPDATE SET
                 status=excluded.status,
                 favorite=excluded.favorite,
                 user_notes=excluded.user_notes,
                 personal_tags=excluded.personal_tags,
                 updated_at=CURRENT_TIMESTAMP""",
            (article_key_value, status, 1 if favorite else 0, user_notes, personal_tags),
        )
