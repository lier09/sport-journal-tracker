from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from typing import Any, Iterable


def normalize_doi(doi: str | None) -> str:
    if not doi:
        return ""
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    doi = doi.replace("doi:", "").strip()
    return doi


def normalize_title(title: str | None) -> str:
    if not title:
        return ""
    title = re.sub(r"<[^>]+>", " ", title)
    title = re.sub(r"\s+", " ", title).strip().lower()
    title = re.sub(r"[^a-z0-9\u4e00-\u9fff ]+", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def title_hash(title: str | None) -> str:
    normalized = normalize_title(title)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]


def safe_first(value: Any) -> Any:
    if isinstance(value, list) and value:
        return value[0]
    return value


def date_from_parts(parts: Any) -> str:
    """Convert Crossref date-parts value into ISO date string."""
    try:
        parts = parts.get("date-parts", parts) if isinstance(parts, dict) else parts
        row = parts[0]
        year = int(row[0])
        month = int(row[1]) if len(row) > 1 else 1
        day = int(row[2]) if len(row) > 2 else 1
        return date(year, month, day).isoformat()
    except Exception:
        return ""


def parse_date(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict) and "date-parts" in value:
        return date_from_parts(value)
    if isinstance(value, (list, tuple)):
        return date_from_parts(value)
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y/%m", "%Y"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt).date().isoformat()
        except Exception:
            pass
    return text[:10]


def join_names(authors: Iterable[dict[str, Any]] | None, limit: int = 12) -> str:
    if not authors:
        return ""
    author_list = list(authors)
    names = []
    for a in author_list[:limit]:
        given = a.get("given", "")
        family = a.get("family", "")
        name = " ".join(x for x in [given, family] if x).strip()
        if name:
            names.append(name)
    if len(author_list) > limit:
        names.append("et al.")
    return "; ".join(names)


def today_iso() -> str:
    return date.today().isoformat()
