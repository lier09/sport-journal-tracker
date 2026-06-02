from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .config import DB_PATH
from .normalization import normalize_doi, title_hash, today_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS journals (
    journal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_name TEXT NOT NULL UNIQUE,
    issn TEXT DEFAULT '',
    eissn TEXT DEFAULT '',
    priority TEXT DEFAULT '',
    domain TEXT DEFAULT '',
    frequency TEXT DEFAULT 'daily',
    active INTEGER DEFAULT 1,
    rss_url TEXT DEFAULT '',
    crossref_query TEXT DEFAULT '',
    pubmed_query TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS articles (
    article_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    title_hash TEXT NOT NULL,
    journal_name TEXT DEFAULT '',
    authors TEXT DEFAULT '',
    publication_date TEXT DEFAULT '',
    first_seen_date TEXT DEFAULT '',
    doi TEXT DEFAULT '',
    url TEXT DEFAULT '',
    abstract TEXT DEFAULT '',
    source TEXT DEFAULT '',
    pmid TEXT DEFAULT '',
    topics TEXT DEFAULT '',
    matched_keywords TEXT DEFAULT '',
    relevance_score INTEGER DEFAULT 0,
    relevance_level TEXT DEFAULT '',
    study_type TEXT DEFAULT '',
    status TEXT DEFAULT '未读',
    favorite INTEGER DEFAULT 0,
    user_notes TEXT DEFAULT '',
    personal_tags TEXT DEFAULT '',
    fulltext_url TEXT DEFAULT '',
    raw_json TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_doi ON articles(doi) WHERE doi != '';
CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_title_journal ON articles(title_hash, journal_name);
CREATE INDEX IF NOT EXISTS idx_articles_first_seen ON articles(first_seen_date);
CREATE INDEX IF NOT EXISTS idx_articles_journal ON articles(journal_name);

CREATE TABLE IF NOT EXISTS run_log (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL,
    source TEXT DEFAULT '',
    journal_name TEXT DEFAULT '',
    status TEXT DEFAULT '',
    fetched_count INTEGER DEFAULT 0,
    inserted_count INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fetch_retry_queue (
    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT DEFAULT '',
    source TEXT DEFAULT '',
    journal_name TEXT DEFAULT '',
    first_failed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_failed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    failure_count INTEGER DEFAULT 1,
    last_error_message TEXT DEFAULT '',
    resolved INTEGER DEFAULT 0,
    resolved_at TEXT DEFAULT ''
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fetch_retry_unique
ON fetch_retry_queue(source, journal_name, resolved)
WHERE resolved = 0;
"""

ARTICLE_EXTRA_COLUMNS: dict[str, str] = {
    "matched_keywords": "TEXT DEFAULT ''",
    "favorite": "INTEGER DEFAULT 0",
    "user_notes": "TEXT DEFAULT ''",
    "personal_tags": "TEXT DEFAULT ''",
    "fulltext_url": "TEXT DEFAULT ''",
}
RUN_LOG_EXTRA_COLUMNS: dict[str, str] = {
    "retry_count": "INTEGER DEFAULT 0",
}


def connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def _has_column(con: sqlite3.Connection, table: str, column: str) -> bool:
    cols = [row[1] for row in con.execute(f"PRAGMA table_info({table})").fetchall()]
    return column in cols


def _add_column_if_missing(con: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    if not _has_column(con, table, column):
        con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def migrate_db(con: sqlite3.Connection) -> None:
    """Keep older local databases compatible with newer dashboard features."""
    for col, ddl in ARTICLE_EXTRA_COLUMNS.items():
        _add_column_if_missing(con, "articles", col, ddl)
    for col, ddl in RUN_LOG_EXTRA_COLUMNS.items():
        _add_column_if_missing(con, "run_log", col, ddl)
    # Normalize old English statuses to the Chinese labels used in v4.
    con.execute("UPDATE articles SET status='未读' WHERE status IS NULL OR status='' OR status='unread'")
    con.execute("UPDATE articles SET status='待读' WHERE status='to_read'")
    con.execute("UPDATE articles SET status='已读' WHERE status='read'")
    con.execute("UPDATE articles SET status='精读' WHERE status='deep_read'")
    con.execute("UPDATE articles SET status='已引用' WHERE status='cited'")
    con.execute("UPDATE articles SET status='不相关' WHERE status='irrelevant'")
    con.commit()


def init_db(db_path: Path | str = DB_PATH) -> None:
    with connect(db_path) as con:
        con.executescript(SCHEMA)
        migrate_db(con)
        con.commit()


def upsert_journal(con: sqlite3.Connection, row: dict[str, Any]) -> None:
    con.execute(
        """
        INSERT INTO journals (
            journal_name, issn, eissn, priority, domain, frequency, active,
            rss_url, crossref_query, pubmed_query, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(journal_name) DO UPDATE SET
            issn=excluded.issn,
            eissn=excluded.eissn,
            priority=excluded.priority,
            domain=excluded.domain,
            frequency=excluded.frequency,
            active=excluded.active,
            rss_url=excluded.rss_url,
            crossref_query=excluded.crossref_query,
            pubmed_query=excluded.pubmed_query,
            notes=excluded.notes,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            row.get("journal_name", ""),
            row.get("issn", ""),
            row.get("eissn", ""),
            row.get("priority", ""),
            row.get("domain", ""),
            row.get("frequency", "daily"),
            1 if row.get("active", True) else 0,
            row.get("rss_url", ""),
            row.get("crossref_query", "") or row.get("journal_name", ""),
            row.get("pubmed_query", ""),
            row.get("notes", ""),
        ),
    )


def load_journals_to_db(con: sqlite3.Connection, journals_df) -> None:
    for _, row in journals_df.iterrows():
        upsert_journal(con, row.to_dict())
    con.commit()


def insert_article(con: sqlite3.Connection, article: dict[str, Any]) -> bool:
    doi = normalize_doi(article.get("doi", ""))
    thash = title_hash(article.get("title", ""))
    if not article.get("title") or not thash:
        return False

    payload = {
        "title": article.get("title", "").strip(),
        "title_hash": thash,
        "journal_name": article.get("journal_name", "").strip(),
        "authors": article.get("authors", ""),
        "publication_date": article.get("publication_date", ""),
        "first_seen_date": article.get("first_seen_date", "") or today_iso(),
        "doi": doi,
        "url": article.get("url", ""),
        "abstract": article.get("abstract", ""),
        "source": article.get("source", ""),
        "pmid": article.get("pmid", ""),
        "topics": article.get("topics", ""),
        "matched_keywords": article.get("matched_keywords", ""),
        # Compatibility fields remain in DB but v4 no longer uses AI/relevance scoring.
        "relevance_score": 0,
        "relevance_level": "",
        "study_type": article.get("study_type", ""),
        "fulltext_url": article.get("fulltext_url", article.get("url", "")),
        "raw_json": article.get("raw_json", ""),
    }

    try:
        con.execute(
            """
            INSERT INTO articles (
                title, title_hash, journal_name, authors, publication_date,
                first_seen_date, doi, url, abstract, source, pmid, topics,
                matched_keywords, relevance_score, relevance_level, study_type,
                fulltext_url, raw_json
            ) VALUES (
                :title, :title_hash, :journal_name, :authors, :publication_date,
                :first_seen_date, :doi, :url, :abstract, :source, :pmid, :topics,
                :matched_keywords, :relevance_score, :relevance_level, :study_type,
                :fulltext_url, :raw_json
            )
            """,
            payload,
        )
        return True
    except sqlite3.IntegrityError:
        con.execute(
            """
            UPDATE articles SET
                url=COALESCE(NULLIF(url, ''), :url),
                fulltext_url=COALESCE(NULLIF(fulltext_url, ''), :fulltext_url),
                abstract=COALESCE(NULLIF(abstract, ''), :abstract),
                authors=COALESCE(NULLIF(authors, ''), :authors),
                publication_date=COALESCE(NULLIF(publication_date, ''), :publication_date),
                pmid=COALESCE(NULLIF(pmid, ''), :pmid),
                topics=CASE WHEN COALESCE(topics, '')='' THEN :topics ELSE topics END,
                matched_keywords=CASE WHEN COALESCE(matched_keywords, '')='' THEN :matched_keywords ELSE matched_keywords END,
                study_type=COALESCE(NULLIF(study_type, ''), :study_type),
                updated_at=CURRENT_TIMESTAMP
            WHERE (doi != '' AND doi = :doi)
               OR (title_hash = :title_hash AND journal_name = :journal_name)
            """,
            payload,
        )
        return False


def log_run(
    con: sqlite3.Connection,
    *,
    run_date: str,
    source: str,
    journal_name: str,
    status: str,
    fetched_count: int = 0,
    inserted_count: int = 0,
    error_message: str = "",
    retry_count: int = 0,
) -> None:
    con.execute(
        """
        INSERT INTO run_log (run_date, source, journal_name, status, fetched_count, inserted_count, retry_count, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_date, source, journal_name, status, fetched_count, inserted_count, retry_count, error_message[:2000]),
    )
    con.commit()


def upsert_fetch_failure(con: sqlite3.Connection, *, run_date: str, source: str, journal_name: str, error_message: str) -> None:
    existing = con.execute(
        """
        SELECT queue_id FROM fetch_retry_queue
        WHERE source=? AND journal_name=? AND resolved=0
        """,
        (source, journal_name),
    ).fetchone()
    if existing:
        con.execute(
            """
            UPDATE fetch_retry_queue SET
                run_date=?, last_failed_at=CURRENT_TIMESTAMP,
                failure_count=failure_count+1,
                last_error_message=?
            WHERE queue_id=?
            """,
            (run_date, error_message[:2000], existing["queue_id"]),
        )
    else:
        con.execute(
            """
            INSERT INTO fetch_retry_queue (run_date, source, journal_name, last_error_message)
            VALUES (?, ?, ?, ?)
            """,
            (run_date, source, journal_name, error_message[:2000]),
        )
    con.commit()


def clear_fetch_failure(con: sqlite3.Connection, *, source: str, journal_name: str) -> None:
    con.execute(
        """
        UPDATE fetch_retry_queue SET resolved=1, resolved_at=CURRENT_TIMESTAMP
        WHERE source=? AND journal_name=? AND resolved=0
        """,
        (source, journal_name),
    )
    con.commit()


def update_article_user_fields(
    con: sqlite3.Connection,
    article_id: int,
    *,
    status: str | None = None,
    favorite: int | None = None,
    user_notes: str | None = None,
    personal_tags: str | None = None,
) -> None:
    fields: list[str] = []
    params: list[Any] = []
    if status is not None:
        fields.append("status=?")
        params.append(status)
    if favorite is not None:
        fields.append("favorite=?")
        params.append(1 if favorite else 0)
    if user_notes is not None:
        fields.append("user_notes=?")
        params.append(user_notes)
    if personal_tags is not None:
        fields.append("personal_tags=?")
        params.append(personal_tags)
    if not fields:
        return
    fields.append("updated_at=CURRENT_TIMESTAMP")
    params.append(article_id)
    con.execute(f"UPDATE articles SET {', '.join(fields)} WHERE article_id=?", params)
    con.commit()


def update_article_metadata_fields(
    con: sqlite3.Connection,
    article_id: int,
    *,
    abstract: str | None = None,
    doi: str | None = None,
    pmid: str | None = None,
    url: str | None = None,
    fulltext_url: str | None = None,
    authors: str | None = None,
    publication_date: str | None = None,
) -> None:
    """Fill missing metadata fields for an existing article without overwriting existing non-empty values."""
    fields: list[str] = []
    params: list[Any] = []
    mapping = {
        "abstract": abstract,
        "doi": normalize_doi(doi or "") if doi is not None else None,
        "pmid": pmid,
        "url": url,
        "fulltext_url": fulltext_url,
        "authors": authors,
        "publication_date": publication_date,
    }
    for col, val in mapping.items():
        if val is None:
            continue
        val = str(val).strip()
        if not val:
            continue
        fields.append(f"{col}=COALESCE(NULLIF({col}, ''), ?)")
        params.append(val)
    if not fields:
        return
    fields.append("updated_at=CURRENT_TIMESTAMP")
    params.append(article_id)
    con.execute(f"UPDATE articles SET {', '.join(fields)} WHERE article_id=?", params)
    con.commit()
