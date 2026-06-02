from __future__ import annotations

import json
from typing import Any

import feedparser

from .normalization import normalize_doi, parse_date


def fetch_rss(journal: dict[str, Any], timeout: int = 20) -> list[dict[str, Any]]:
    """Fetch articles from a journal RSS feed.

    Returns normalized article dictionaries. Empty rss_url returns [].
    """
    rss_url = (journal.get("rss_url") or "").strip()
    if not rss_url:
        return []

    parsed = feedparser.parse(rss_url, request_headers={"User-Agent": "sport-journal-tracker/0.1"})
    articles: list[dict[str, Any]] = []

    for entry in parsed.entries:
        title = entry.get("title", "").strip()
        if not title:
            continue
        doi = ""
        for key in ["doi", "dc_identifier", "prism_doi"]:
            value = entry.get(key)
            if value:
                doi = normalize_doi(str(value))
                break
        if not doi:
            # Some feeds put DOI inside links or identifiers.
            for link in entry.get("links", []):
                href = link.get("href", "")
                if "doi.org/" in href:
                    doi = normalize_doi(href)
                    break
        authors = []
        for a in entry.get("authors", []) or []:
            name = a.get("name") if isinstance(a, dict) else str(a)
            if name:
                authors.append(name)

        articles.append(
            {
                "title": title,
                "journal_name": journal.get("journal_name", ""),
                "authors": "; ".join(authors),
                "publication_date": parse_date(entry.get("published") or entry.get("updated")),
                "doi": doi,
                "url": entry.get("link", ""),
                "abstract": entry.get("summary", ""),
                "source": "rss",
                "raw_json": json.dumps(dict(entry), ensure_ascii=False, default=str)[:5000],
            }
        )
    return articles
