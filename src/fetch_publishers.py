from __future__ import annotations

import csv
import json
import re
import time
from datetime import date, datetime, timedelta
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

from .config import ROOT
from .fetch_springer import fetch_springer
from .normalization import normalize_doi

PUBLISHER_SOURCES_PATH = ROOT / "config" / "publisher_sources.csv"

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; sport-journal-tracker/0.5; "
        "+https://github.com/lier09/sport-journal-tracker)"
    )
}


def _yes(value: Any) -> bool:
    return str(value or "").strip().lower() in {"yes", "y", "true", "1", "active"}


def _clean(text: str) -> str:
    text = unescape(text or "")
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(text: str) -> str:
    if not text:
        return ""
    m = re.search(
        r"\b(\d{1,2})\s+("
        r"January|February|March|April|May|June|July|August|September|October|November|December"
        r")\s+(\d{4})\b",
        text,
        flags=re.I,
    )
    if m:
        try:
            return date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))).isoformat()
        except Exception:
            return ""
    m2 = re.search(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b", text)
    if m2:
        try:
            return date(int(m2.group(1)), int(m2.group(2)), int(m2.group(3))).isoformat()
        except Exception:
            return ""
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


def load_publisher_sources(path: Path = PUBLISHER_SOURCES_PATH) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _sources_for_journal(journal_name: str) -> list[dict[str, str]]:
    target = _clean(journal_name).lower()
    rows = []
    for row in load_publisher_sources():
        if not _yes(row.get("active")):
            continue
        if _clean(row.get("journal_name", "")).lower() == target:
            rows.append(row)
    return rows


def _doi_from_any_url(href: str) -> str:
    href = unquote(href or "")
    patterns = [
        r"/article/(10\.[^?#\s]+)",
        r"/doi/(?:abs|full|pdf|epdf)?/?(10\.[^?#\s]+)",
        r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)",
    ]
    for pat in patterns:
        m = re.search(pat, href, flags=re.I)
        if m:
            return normalize_doi(m.group(1))
    return ""


def _nearest_text_block(anchor) -> str:
    current = anchor
    best = ""
    for _ in range(8):
        if current is None:
            break
        current = current.parent
        if current is None:
            break
        text = current.get_text("\n", strip=True)
        if len(text) > len(best):
            best = text
        if _parse_date(text):
            return text
    return best


def _authors_from_lines(lines: list[str], title: str) -> str:
    title_l = _clean(title).lower()
    out = []
    seen = False
    for line in lines:
        s = _clean(line)
        l = s.lower()
        if not seen:
            if title_l and (title_l == l or title_l in l):
                seen = True
            continue
        if _parse_date(s):
            break
        if len(s) > 100:
            continue
        if any(bad in l for bad in ["open access", "latest", "rss", "article", "issue"]):
            continue
        if re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", s):
            out.append(s)
        if len(out) >= 10:
            break
    # Deduplicate.
    dedup = []
    for a in out:
        if a not in dedup:
            dedup.append(a)
    return "; ".join(dedup)


def fetch_official_rss(source: dict[str, str], *, journal_name: str, from_date: str, until_date: str) -> list[dict[str, Any]]:
    url = source.get("source_url", "").strip()
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        title = _clean(getattr(entry, "title", ""))
        if not title:
            continue
        link = getattr(entry, "link", "") or ""
        doi = _doi_from_any_url(link)
        pub = ""
        for attr in ["published", "updated"]:
            val = getattr(entry, attr, "")
            if val:
                pub = _parse_date(val)
                if pub:
                    break
        if not _in_window(pub, from_date, until_date):
            continue
        authors = ""
        if hasattr(entry, "authors"):
            try:
                authors = "; ".join([a.get("name", "") for a in entry.authors if a.get("name")])
            except Exception:
                pass
        articles.append({
            "title": title,
            "journal_name": journal_name,
            "authors": authors,
            "publication_date": pub,
            "doi": doi,
            "url": link,
            "fulltext_url": link,
            "abstract": _clean(getattr(entry, "summary", "")),
            "source": "publisher_rss",
            "study_type": "",
            "raw_json": json.dumps({"publisher_source": source, "feed_entry": dict(entry)}, ensure_ascii=False, default=str),
        })
    return articles


def fetch_bmj_online_first(source: dict[str, str], *, journal_name: str, from_date: str, until_date: str) -> list[dict[str, Any]]:
    url = source.get("source_url", "").strip()
    if not url:
        return []
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []
    seen = set()

    # BMJ article links usually include /content/early/ or article DOI-ish paths.
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        text = _clean(a.get_text(" ", strip=True))
        if not text or len(text) < 8:
            continue
        if "content/early" not in href and "/content/" not in href:
            continue
        full_url = urljoin(url, href)
        key = full_url.split("?")[0]
        if key in seen:
            continue
        seen.add(key)
        block_text = _nearest_text_block(a)
        pub = _parse_date(block_text)
        if not _in_window(pub, from_date, until_date):
            continue
        lines = [x for x in block_text.splitlines() if _clean(x)]
        articles.append({
            "title": text,
            "journal_name": journal_name,
            "authors": _authors_from_lines(lines, text),
            "publication_date": pub,
            "doi": _doi_from_any_url(full_url),
            "url": full_url,
            "fulltext_url": full_url,
            "abstract": "",
            "source": "bmj",
            "study_type": "",
            "raw_json": json.dumps({"publisher_source": source}, ensure_ascii=False),
        })
    return articles


def fetch_generic_doi_list(source: dict[str, str], *, journal_name: str, from_date: str, until_date: str) -> list[dict[str, Any]]:
    url = source.get("source_url", "").strip()
    if not url:
        return []
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    articles: list[dict[str, Any]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        doi = _doi_from_any_url(href)
        if not doi:
            continue
        full_url = urljoin(url, href)
        title = _clean(a.get_text(" ", strip=True))
        block_text = _nearest_text_block(a)
        if not title or len(title) < 8:
            first_line = next((x for x in block_text.splitlines() if len(_clean(x)) >= 8), "")
            title = _clean(first_line)
        if not title or len(title) < 8:
            continue
        key = doi or full_url
        if key in seen:
            continue
        seen.add(key)
        pub = _parse_date(block_text)
        if not _in_window(pub, from_date, until_date):
            continue
        articles.append({
            "title": title,
            "journal_name": journal_name,
            "authors": _authors_from_lines(block_text.splitlines(), title),
            "publication_date": pub,
            "doi": doi,
            "url": full_url,
            "fulltext_url": full_url,
            "abstract": "",
            "source": "publisher",
            "study_type": "",
            "raw_json": json.dumps({"publisher_source": source}, ensure_ascii=False),
        })
    return articles


def fetch_publishers(journal: dict[str, Any], from_date: str | None = None, until_date: str | None = None, sleep_seconds: float = 0.5) -> list[dict[str, Any]]:
    journal_name = str(journal.get("journal_name", "") or "").strip()
    if not journal_name:
        return []
    until_date = until_date or date.today().isoformat()
    from_date = from_date or (date.today() - timedelta(days=7)).isoformat()
    sources = _sources_for_journal(journal_name)
    if not sources:
        return []
    articles: list[dict[str, Any]] = []
    for source in sources:
        stype = str(source.get("source_type", "") or "").strip().lower()
        try:
            if stype == "springer_journal":
                j2 = dict(journal)
                j2["springer_journal_id"] = source.get("source_id", "")
                max_pages = int(source.get("max_pages") or "1")
                articles.extend(fetch_springer(j2, from_date=from_date, until_date=until_date, max_pages=max_pages, sleep_seconds=sleep_seconds))
            elif stype == "official_rss":
                articles.extend(fetch_official_rss(source, journal_name=journal_name, from_date=from_date, until_date=until_date))
            elif stype == "bmj_online_first":
                articles.extend(fetch_bmj_online_first(source, journal_name=journal_name, from_date=from_date, until_date=until_date))
            elif stype == "generic_doi_list":
                articles.extend(fetch_generic_doi_list(source, journal_name=journal_name, from_date=from_date, until_date=until_date))
        finally:
            time.sleep(sleep_seconds)
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for a in articles:
        key = normalize_doi(a.get("doi", "")) or f"{a.get('journal_name','')}::{_clean(a.get('title','')).lower()}"
        if key and key not in seen:
            seen.add(key)
            out.append(a)
    return out
