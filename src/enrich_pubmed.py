from __future__ import annotations

import re
import time
from typing import Any

import requests

from .config import DB_PATH, get_env
from .database import connect, init_db, update_article_metadata_fields
from .fetch_pubmed import EFETCH_URL, ESEARCH_URL, _parse_pubmed_xml
from .retry_utils import with_retries


def _norm_title(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    value = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", " ", value).lower().strip()
    return re.sub(r"\s+", " ", value)


def _candidate_rows(limit: int = 100) -> list[dict[str, Any]]:
    init_db(DB_PATH)
    with connect(DB_PATH) as con:
        rows = con.execute(
            """
            SELECT article_id, title, journal_name, doi, pmid
            FROM articles
            WHERE COALESCE(abstract, '') = ''
              AND COALESCE(title, '') != ''
            ORDER BY
              CASE WHEN COALESCE(pmid, '') != '' THEN 0
                   WHEN COALESCE(doi, '') != '' THEN 1
                   ELSE 2 END,
              first_seen_date DESC,
              article_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def _api_key() -> str:
    return get_env("NCBI_API_KEY", "").strip()


def _pubmed_ids_for_doi(doi: str) -> list[str]:
    doi = str(doi or "").strip()
    if not doi:
        return []
    params = {
        "db": "pubmed",
        "term": f'"{doi}"[DOI]',
        "retmode": "json",
        "retmax": 5,
    }
    if _api_key():
        params["api_key"] = _api_key()

    def _call() -> requests.Response:
        r = requests.get(ESEARCH_URL, params=params, timeout=25)
        r.raise_for_status()
        return r

    r = with_retries(_call, attempts=3, base_delay=1.5, max_delay=8)
    return r.json().get("esearchresult", {}).get("idlist", [])


def _pubmed_ids_for_title(title: str, journal_name: str = "") -> list[str]:
    title = str(title or "").strip()
    if len(title) < 20:
        return []
    # Strict title search. The fetched result is verified again by normalized title.
    term = f'"{title}"[Title]'
    if journal_name:
        term = f'({term}) AND "{journal_name}"[Journal]'
    params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": 5,
    }
    if _api_key():
        params["api_key"] = _api_key()

    def _call() -> requests.Response:
        r = requests.get(ESEARCH_URL, params=params, timeout=25)
        r.raise_for_status()
        return r

    r = with_retries(_call, attempts=3, base_delay=1.5, max_delay=8)
    return r.json().get("esearchresult", {}).get("idlist", [])


def _fetch_by_pmids(pmids: list[str]) -> list[dict[str, Any]]:
    pmids = [str(x).strip() for x in pmids if str(x).strip()]
    if not pmids:
        return []
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
    if _api_key():
        params["api_key"] = _api_key()

    def _call() -> requests.Response:
        r = requests.get(EFETCH_URL, params=params, timeout=35)
        r.raise_for_status()
        return r

    r = with_retries(_call, attempts=3, base_delay=1.5, max_delay=10)
    return _parse_pubmed_xml(r.text, journal_name_hint="")


def enrich_abstracts(limit: int = 100, batch_size: int = 20, sleep_seconds: float = 0.34) -> dict[str, int]:
    """Fill missing official abstracts from PubMed when PMID/DOI/title matching is available.

    This does not generate summaries and does not access paywalled full text. It only fills
    empty metadata fields using public PubMed metadata, without overwriting existing non-empty values.
    """
    candidates = _candidate_rows(limit=limit)
    checked = len(candidates)
    doi_resolved = 0
    title_resolved = 0
    found = 0
    abstracts_filled = 0

    # Resolve missing PMID using DOI first, then strict title matching as fallback.
    for row in candidates:
        if row.get("pmid"):
            continue
        ids: list[str] = []
        try:
            if row.get("doi"):
                ids = _pubmed_ids_for_doi(row["doi"])
                if ids:
                    doi_resolved += 1
            if not ids:
                ids = _pubmed_ids_for_title(row.get("title", ""), row.get("journal_name", ""))
                if ids:
                    title_resolved += 1
            if ids:
                row["pmid"] = ids[0]
                with connect(DB_PATH) as con:
                    update_article_metadata_fields(con, int(row["article_id"]), pmid=ids[0])
            time.sleep(sleep_seconds)
        except Exception as exc:
            print(f"[enrich_pubmed] PMID resolution skipped for article_id={row.get('article_id')}: {exc}")
            continue

    pmid_to_rows: dict[str, list[dict[str, Any]]] = {}
    for row in candidates:
        pmid = str(row.get("pmid", "")).strip()
        if pmid:
            pmid_to_rows.setdefault(pmid, []).append(row)

    pmids = list(pmid_to_rows.keys())
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i + batch_size]
        try:
            articles = _fetch_by_pmids(batch)
            found += len(articles)
            with connect(DB_PATH) as con:
                for art in articles:
                    pmid = str(art.get("pmid", "")).strip()
                    rows = pmid_to_rows.get(pmid, [])
                    if not rows:
                        continue
                    for row in rows:
                        # Safety check for title-resolved records.
                        if not row.get("doi") and _norm_title(row.get("title", "")) != _norm_title(art.get("title", "")):
                            continue
                        if str(art.get("abstract", "")).strip():
                            abstracts_filled += 1
                        update_article_metadata_fields(
                            con,
                            int(row["article_id"]),
                            abstract=art.get("abstract", ""),
                            doi=art.get("doi", ""),
                            pmid=pmid,
                            url=art.get("url", ""),
                            fulltext_url=art.get("fulltext_url", ""),
                            authors=art.get("authors", ""),
                            publication_date=art.get("publication_date", ""),
                        )
            time.sleep(sleep_seconds)
        except Exception as exc:
            print(f"[enrich_pubmed] batch {i // batch_size + 1}: ERROR {exc}")
            continue

    return {
        "checked": checked,
        "pmids_resolved_by_doi": doi_resolved,
        "pmids_resolved_by_title": title_resolved,
        "pubmed_records_found": found,
        "abstracts_filled_or_confirmed": abstracts_filled,
    }
