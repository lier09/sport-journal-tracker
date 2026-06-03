from __future__ import annotations

import json
import re
import time
from datetime import date, datetime, timedelta
from html import unescape
from typing import Any
from urllib.parse import quote, unquote, urljoin

import requests
from bs4 import BeautifulSoup

from .normalization import normalize_doi

SPRINGER_BASE = "https://link.springer.com"

# Journal-specific publisher pages.
# Start conservative: add only journals whose Springer article-list URL has been verified.
SPRINGER_JOURNAL_IDS: dict[str, str] = {
    "European Journal of Applied Physiology": "421",
}

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

ARTICLE_TYPE_WORDS = {
    "original article",
    "review article",
    "invited review",
    "comment",
    "correction",
    "perspective",
    "brief communication",
    "editorial",
    "letter",
    "open access",
    "article",
}


def _iso_from_text(text: str) -> str:
    """Parse dates like '02 June 2026' from Springer article-list text."""
    if not text:
        return ""
    m = re.search(
        r"\b(\d{1,2})\s+("
        r"January|February|March|April|May|June|July|August|September|October|November|December"
        r")\s+(\d{4})\b",
        text,
        flags=re.I,
    )
    if not m:
        # Also accept ISO-like dates if Springer changes markup.
        m2 = re.search(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b", text)
        if not m2:
            return ""
        try:
            return date(int(m2.group(1)), int(m2.group(2)), int(m2.group(3))).isoformat()
        except Exception:
            return ""
    try:
        day = int(m.group(1))
        month = MONTHS[m.group(2).lower()]
        year = int(m.group(3))
        return date(year, month, day).isoformat()
    except Exception:
        return ""


def _in_window(pub_date: str, from_date: str, until_date: str) -> bool:
    if not pub_date:
        return True
    try:
        d = datetime.strptime(pub_date, "%Y-%m-%d").date()
        f = datetime.strptime(from_date, "%Y-%m-%d").date()
        u = datetime.strptime(until_date, "%Y-%m-%d").date()
        return f <= d <= u
    except Exception:
        return True


def _clean_text(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _doi_from_href(href: str) -> str:
    href = unquote(href or "")
    m = re.search(r"/article/(10\.[^?#\s]+)", href)
    return normalize_doi(m.group(1)) if m else ""


def _find_article_block(anchor) -> Any:
    """Find the smallest ancestor block that contains the article date."""
    current = anchor
    best = anchor.parent
    for _ in range(8):
        if current is None:
            break
        current = current.parent
        if current is None:
            break
        text = current.get_text("\n", strip=True)
        if _iso_from_text(text):
            return current
        if current.name in {"li", "article"}:
            best = current
    return best


def _authors_from_block(block, title: str) -> str:
    lines = [x.strip() for x in block.get_text("\n", strip=True).splitlines()]
    lines = [x for x in lines if x]
    title_norm = _clean_text(title).lower()
    authors: list[str] = []
    seen_title = False
    for line in lines:
        clean = _clean_text(line)
        lower = clean.lower()
        if not seen_title:
            if _clean_text(clean).lower() == title_norm or title_norm in lower:
                seen_title = True
            continue
        if _iso_from_text(clean):
            break
        if lower in ARTICLE_TYPE_WORDS:
            continue
        if lower.startswith("image"):
            continue
        if len(clean) > 90:
            continue
        # Avoid capturing navigation/filter text.
        if any(bad in lower for bad in ["open access", "volume", "sort by", "filter by"]):
            if lower != "open access":
                continue
        # Rough author-name guard: usually Springer list names have letters and not too much punctuation.
        if re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", clean):
            authors.append(clean)
        if len(authors) >= 12:
            break
    # Deduplicate while preserving order.
    out: list[str] = []
    for a in authors:
        if a not in out:
            out.append(a)
    return "; ".join(out)


def _journal_id_for(journal: dict[str, Any]) -> str:
    # Future-proof: if you later add a springer_journal_id column to config/journals.csv, it will be used.
    explicit = str(journal.get("springer_journal_id", "") or "").strip()
    if explicit:
        return explicit
    return SPRINGER_JOURNAL_IDS.get(str(journal.get("journal_name", "")).strip(), "")


def fetch_springer(
    journal: dict[str, Any],
    from_date: str | None = None,
    until_date: str | None = None,
    max_pages: int = 1,
    sleep_seconds: float = 0.5,
) -> list[dict[str, Any]]:
    """Fetch article-list pages from Springer Nature Link.

    This fills the gap where Crossref/PubMed lag behind publisher websites.
    It is currently conservative and only runs for journals with a known Springer journal ID.
    """
    journal_name = str(journal.get("journal_name", "") or "").strip()
    journal_id = _journal_id_for(journal)
    if not journal_id or not journal_name:
        return []

    until_date = until_date or date.today().isoformat()
    from_date = from_date or (date.today() - timedelta(days=10)).isoformat()

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; sport-journal-tracker/0.5; +https://github.com/lier09/sport-journal-tracker)"
    }

    articles: list[dict[str, Any]] = []
    seen: set[str] = set()

    for page in range(1, max_pages + 1):
        url = f"{SPRINGER_BASE}/journal/{journal_id}/articles"
        params = {"sortBy": "NewestFirst"}
        if page > 1:
            params["page"] = page

        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/article/10." not in href:
                continue
            title = _clean_text(a.get_text(" ", strip=True))
            if not title or len(title) < 8:
                continue

            doi = _doi_from_href(href)
            abs_url = urljoin(SPRINGER_BASE, href)
            key = doi or title.lower()
            if key in seen:
                continue
            seen.add(key)

            block = _find_article_block(a)
            block_text = block.get_text("\n", strip=True) if block else ""
            pub_date = _iso_from_text(block_text)

            # Springer's newest page can contain older articles; respect the requested window.
            if not _in_window(pub_date, from_date, until_date):
                continue

            authors = _authors_from_block(block, title) if block else ""
            article_type = ""
            low = block_text.lower()
            for t in ARTICLE_TYPE_WORDS:
                if t in low and t != "article":
                    article_type = t
                    break

            articles.append(
                {
                    "title": title,
                    "journal_name": journal_name,
                    "authors": authors,
                    "publication_date": pub_date,
                    "doi": doi,
                    "url": abs_url,
                    "fulltext_url": abs_url,
                    "abstract": "",
                    "source": "springer",
                    "study_type": article_type,
                    "raw_json": json.dumps(
                        {
                            "springer_journal_id": journal_id,
                            "article_url": abs_url,
                            "page": page,
                            "article_type": article_type,
                        },
                        ensure_ascii=False,
                    ),
                }
            )

        time.sleep(sleep_seconds)

    return articles
