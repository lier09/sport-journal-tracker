from __future__ import annotations

import json
import time
from datetime import date, timedelta
from typing import Any

import requests

from .config import get_env
from .normalization import date_from_parts, join_names, normalize_doi, safe_first
from .retry_utils import with_retries

API_URL = "https://api.crossref.org/works"


def fetch_crossref(
    journal: dict[str, Any],
    from_date: str | None = None,
    until_date: str | None = None,
    rows: int = 30,
    sleep_seconds: float = 0.25,
) -> list[dict[str, Any]]:
    """Fetch recent works from Crossref by ISSN if available, else container-title query."""
    until_date = until_date or date.today().isoformat()
    from_date = from_date or (date.today() - timedelta(days=10)).isoformat()

    issn = (journal.get("issn") or journal.get("eissn") or "").strip()
    query = (journal.get("crossref_query") or journal.get("journal_name") or "").strip()
    mailto = get_env("CROSSREF_MAILTO", "").strip()

    params = {
        "rows": rows,
        "sort": "published",
        "order": "desc",
        "filter": f"from-pub-date:{from_date},until-pub-date:{until_date},type:journal-article",
        "select": "DOI,title,container-title,author,published-print,published-online,published,created,URL,abstract,ISSN,subject,type",
    }
    if issn:
        params["filter"] += f",issn:{issn}"
    else:
        params["query.container-title"] = query

    headers = {"User-Agent": "sport-journal-tracker/0.4"}
    if mailto:
        headers["User-Agent"] += f" (mailto:{mailto})"
        params["mailto"] = mailto

    def _request() -> requests.Response:
        resp = requests.get(API_URL, params=params, headers=headers, timeout=35)
        resp.raise_for_status()
        return resp

    resp = with_retries(_request, attempts=3, base_delay=2.0, max_delay=12.0)
    data = resp.json().get("message", {}).get("items", [])
    time.sleep(sleep_seconds)

    articles: list[dict[str, Any]] = []
    for item in data:
        title = safe_first(item.get("title")) or ""
        if not title:
            continue
        container = safe_first(item.get("container-title")) or journal.get("journal_name", "")
        if not issn and query and container and query.lower() not in container.lower() and container.lower() not in query.lower():
            continue
        pub_date = (
            date_from_parts(item.get("published-online"))
            or date_from_parts(item.get("published-print"))
            or date_from_parts(item.get("published"))
            or date_from_parts(item.get("created"))
        )
        url = item.get("URL", "")
        doi = normalize_doi(item.get("DOI", ""))
        if doi and not url:
            url = f"https://doi.org/{doi}"
        articles.append(
            {
                "title": title,
                "journal_name": container,
                "authors": join_names(item.get("author", [])),
                "publication_date": pub_date,
                "doi": doi,
                "url": url,
                "fulltext_url": url,
                "abstract": item.get("abstract", "") or "",
                "source": "crossref",
                "raw_json": json.dumps(item, ensure_ascii=False, default=str)[:5000],
            }
        )
    return articles
