from __future__ import annotations

import json
import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Any

import requests

from .config import get_env
from .retry_utils import with_retries

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def _text(node, default: str = "") -> str:
    return "".join(node.itertext()).strip() if node is not None else default


def _article_date(article) -> str:
    for path in [".//ArticleDate", ".//JournalIssue/PubDate"]:
        node = article.find(path)
        if node is not None:
            y = _text(node.find("Year"))
            m = _text(node.find("Month")) or "1"
            d = _text(node.find("Day")) or "1"
            month_map = {
                "Jan": "1", "Feb": "2", "Mar": "3", "Apr": "4", "May": "5", "Jun": "6",
                "Jul": "7", "Aug": "8", "Sep": "9", "Oct": "10", "Nov": "11", "Dec": "12",
            }
            m = month_map.get(m[:3], m)
            try:
                return date(int(y), int(m), int(d)).isoformat()
            except Exception:
                if y:
                    return y
    return ""


def _parse_pubmed_xml(xml_text: str, journal_name_hint: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    articles = []
    for medline in root.findall(".//PubmedArticle"):
        article = medline.find(".//Article")
        if article is None:
            continue
        title = _text(article.find("ArticleTitle"))
        if not title:
            continue
        journal_title = _text(article.find(".//Journal/Title")) or journal_name_hint
        pmid = _text(medline.find(".//PMID"))
        doi = ""
        for aid in medline.findall(".//ArticleId"):
            if aid.attrib.get("IdType") == "doi":
                doi = _text(aid)
                break
        authors = []
        all_authors = article.findall(".//AuthorList/Author")
        for a in all_authors[:12]:
            last = _text(a.find("LastName"))
            fore = _text(a.find("ForeName"))
            collective = _text(a.find("CollectiveName"))
            name = " ".join(x for x in [fore, last] if x).strip() or collective
            if name:
                authors.append(name)
        if len(all_authors) > 12:
            authors.append("et al.")
        abstract_parts = [_text(x) for x in article.findall(".//Abstract/AbstractText")]
        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
        doi_url = f"https://doi.org/{doi}" if doi else ""
        articles.append(
            {
                "title": title,
                "journal_name": journal_title,
                "authors": "; ".join(authors),
                "publication_date": _article_date(article),
                "doi": doi,
                "url": pubmed_url or doi_url,
                "fulltext_url": doi_url or pubmed_url,
                "abstract": "\n".join(x for x in abstract_parts if x),
                "source": "pubmed",
                "pmid": pmid,
                "raw_json": json.dumps({"pmid": pmid, "journal_hint": journal_name_hint}, ensure_ascii=False),
            }
        )
    return articles


def fetch_pubmed(
    journal: dict[str, Any],
    from_date: str | None = None,
    until_date: str | None = None,
    retmax: int = 30,
    sleep_seconds: float = 0.34,
) -> list[dict[str, Any]]:
    journal_name = journal.get("journal_name", "")
    term = (journal.get("pubmed_query") or f'"{journal_name}"[Journal]').strip()
    if not term or not journal_name:
        return []

    until_date = until_date or date.today().isoformat()
    from_date = from_date or (date.today() - timedelta(days=10)).isoformat()
    api_key = get_env("NCBI_API_KEY", "").strip()

    params = {
        "db": "pubmed",
        "term": f"({term}) AND ({from_date}:{until_date}[Date - Publication])",
        "retmode": "json",
        "retmax": retmax,
        "sort": "pub date",
    }
    if api_key:
        params["api_key"] = api_key

    def _esearch() -> requests.Response:
        r = requests.get(ESEARCH_URL, params=params, timeout=35)
        r.raise_for_status()
        return r

    r = with_retries(_esearch, attempts=3, base_delay=2.0, max_delay=12.0)
    ids = r.json().get("esearchresult", {}).get("idlist", [])
    time.sleep(sleep_seconds)
    if not ids:
        return []

    params2 = {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}
    if api_key:
        params2["api_key"] = api_key

    def _efetch() -> requests.Response:
        r2 = requests.get(EFETCH_URL, params=params2, timeout=35)
        r2.raise_for_status()
        return r2

    r2 = with_retries(_efetch, attempts=3, base_delay=2.0, max_delay=12.0)
    time.sleep(sleep_seconds)
    return _parse_pubmed_xml(r2.text, journal_name)
