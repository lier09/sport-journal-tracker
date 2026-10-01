from __future__ import annotations

import json
import html
import mimetypes
import re
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.config import DB_PATH, load_journals, load_topic_keywords
from src.coverage_audit import load_registry
from src.database import connect, init_db, load_journals_to_db
from src.user_state import article_key, load_states, save_state

ROOT = Path(__file__).resolve().parent
FRONTEND_DIST = ROOT / "frontend" / "dist"
READING_STATUSES = {"未读", "待读", "阅读中", "已读", "精读", "已引用", "不相关"}


def _journal_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def _catalog() -> list[dict]:
    frame = load_journals()
    return frame[frame["active"]].fillna("").to_dict(orient="records")


def _article_rows(params: dict[str, str]) -> dict:
    catalog = _catalog()
    journal_map = {_journal_key(row["journal_name"]): row for row in catalog}
    canonical_names = {_journal_key(row["journal_name"]): str(row["journal_name"]) for row in catalog}

    with connect(DB_PATH) as con:
        latest_date = con.execute("SELECT MAX(first_seen_date) FROM articles").fetchone()[0] or date.today().isoformat()
        end = params.get("end") or latest_date
        start = params.get("start") or (date.fromisoformat(end) - timedelta(days=6)).isoformat()
        rows = con.execute(
            """SELECT article_id,title_hash,title,journal_name,authors,publication_date,first_seen_date,
                      doi,url,fulltext_url,abstract,source,pmid,topics,matched_keywords,study_type
               FROM articles WHERE first_seen_date BETWEEN ? AND ?
               ORDER BY first_seen_date DESC, publication_date DESC, article_id DESC""",
            (start, end),
        ).fetchall()

    records = []
    for row in rows:
        item = dict(row)
        key = _journal_key(item.get("journal_name", ""))
        canonical = canonical_names.get(key, item.get("journal_name", ""))
        journal = journal_map.get(_journal_key(canonical), {})
        item["journal_name"] = canonical
        item["priority"] = str(journal.get("priority", ""))
        item["domain"] = str(journal.get("domain", ""))
        item["collection_group"] = str(journal.get("collection_group", "") or journal.get("domain", ""))
        item["abstract"] = html.unescape(re.sub(r"<[^>]*>", " ", str(item.get("abstract", "")))).strip()
        item["article_key"] = article_key(doi=item.get("doi"), title_hash=item.get("title_hash"), journal_name=canonical)
        records.append(item)

    state_map = load_states([item["article_key"] for item in records])
    for item in records:
        state = state_map.get(item["article_key"], {})
        item["status"] = state.get("status", "未读")
        item["favorite"] = int(state.get("favorite", 0))
        item["personal_tags"] = state.get("personal_tags", "")
        item["user_notes"] = state.get("user_notes", "")

    q = params.get("q", "").strip().casefold()
    journal_filter = params.get("journal", "")
    group_filter = params.get("group", "")
    topic_filter = params.get("topic", "")
    status_filter = params.get("status", "")
    favorites_only = params.get("favorites", "") == "1"
    filtered = []
    for item in records:
        if journal_filter and item["journal_name"] != journal_filter:
            continue
        if group_filter and item["collection_group"] != group_filter:
            continue
        if topic_filter and topic_filter not in str(item.get("topics", "")).split(";"):
            continue
        if status_filter and item["status"] != status_filter:
            continue
        if favorites_only and not item["favorite"]:
            continue
        if q and q not in " ".join(str(item.get(field, "")) for field in ("title", "abstract", "authors", "journal_name", "topics")).casefold():
            continue
        filtered.append(item)

    total = len(filtered)
    try:
        offset = max(0, int(params.get("offset", 0)))
        limit = min(100, max(1, int(params.get("limit", 50))))
    except ValueError:
        offset, limit = 0, 50
    return {"items": filtered[offset:offset + limit], "total": total, "start": start, "end": end, "latest_date": latest_date}


class Handler(BaseHTTPRequestHandler):
    server_version = "SportJournalTracker/1.0"

    def _send(self, status: int, body: bytes, content_type: str = "application/json; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store" if content_type.startswith("application/json") else "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"))

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:5173")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
        try:
            if parsed.path == "/api/meta":
                journals = _catalog()
                with connect(DB_PATH) as con:
                    latest = con.execute("SELECT MAX(first_seen_date) FROM articles").fetchone()[0]
                    article_count = con.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
                return self._json(200, {
                    "journals": journals,
                    "topics": list(load_topic_keywords().keys()),
                    "latest_date": latest or date.today().isoformat(),
                    "article_count": article_count,
                })
            if parsed.path == "/api/articles":
                return self._json(200, _article_rows(params))
            if parsed.path == "/api/sources":
                registry = load_registry().fillna("").to_dict(orient="records")
                with connect(DB_PATH) as con:
                    latest_run = con.execute(
                        "SELECT run_date,source,status,created_at FROM run_log ORDER BY run_id DESC LIMIT 1"
                    ).fetchone()
                    errors = con.execute(
                        "SELECT run_date,source,journal_name,error_message,created_at FROM run_log WHERE status='error' ORDER BY run_id DESC LIMIT 50"
                    ).fetchall()
                return self._json(200, {"registry": registry, "latest_run": dict(latest_run) if latest_run else None, "errors": [dict(row) for row in errors]})
            return self._static(parsed.path)
        except Exception as exc:  # Keep API errors legible in the local UI.
            return self._json(500, {"error": str(exc)})

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/article-state":
            return self._json(404, {"error": "找不到该接口。"})
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 100_000)
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            status = str(payload.get("status", "未读"))
            if status not in READING_STATUSES:
                return self._json(400, {"error": "无效的阅读状态。"})
            key = article_key(doi=payload.get("doi"), title_hash=payload.get("title_hash"), journal_name=payload.get("journal_name"))
            save_state(
                article_key_value=key,
                status=status,
                favorite=bool(payload.get("favorite", False)),
                user_notes=str(payload.get("user_notes", ""))[:20_000],
                personal_tags=str(payload.get("personal_tags", ""))[:2_000],
            )
            return self._json(200, {"ok": True})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": f"无法保存阅读状态：{exc}"})
        except Exception as exc:
            return self._json(500, {"error": str(exc)})

    def _static(self, request_path: str) -> None:
        root = FRONTEND_DIST.resolve()
        relative = request_path.lstrip("/") or "index.html"
        candidate = (root / relative).resolve()
        if root not in candidate.parents and candidate != root:
            return self._json(403, {"error": "无权访问该路径。"})
        if not candidate.is_file():
            candidate = root / "index.html"
        if not candidate.is_file():
            return self._send(503, b"Frontend not built. Run npm install and npm run build in frontend/.", "text/plain; charset=utf-8")
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self._send(200, candidate.read_bytes(), f"{content_type}; charset=utf-8" if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"} else content_type)

    def log_message(self, format: str, *args) -> None:
        print(f"{self.log_date_time_string()} {format % args}")


def main() -> None:
    init_db(DB_PATH)
    with connect(DB_PATH) as con:
        load_journals_to_db(con, load_journals())
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Sport Journal Tracker UI: http://127.0.0.1:8765")
    print("Private reading state is stored only in data/private_reading_state.sqlite3")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down local server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
