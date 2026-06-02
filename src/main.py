from __future__ import annotations

import argparse
from datetime import date, timedelta
from typing import Callable

from .classify import classify_article
from .config import DB_PATH, load_journals, load_topic_keywords
from .database import (
    clear_fetch_failure,
    connect,
    init_db,
    insert_article,
    load_journals_to_db,
    log_run,
    upsert_fetch_failure,
)
from .normalization import today_iso

Fetcher = Callable[..., list[dict]]


def sync_journals() -> None:
    init_db(DB_PATH)
    df = load_journals()
    with connect(DB_PATH) as con:
        load_journals_to_db(con, df)
    print(f"Synced {len(df)} journals into {DB_PATH}")


def _journal_rows():
    df = load_journals()
    df = df[df["active"]].copy()
    return [row.to_dict() for _, row in df.iterrows()]


def run_daily(days_back: int = 7, sources: list[str] | None = None) -> None:
    from .fetch_crossref import fetch_crossref
    from .fetch_pubmed import fetch_pubmed
    from .fetch_rss import fetch_rss

    init_db(DB_PATH)
    sync_journals()
    topics = load_topic_keywords()
    from_date = (date.today() - timedelta(days=days_back)).isoformat()
    until_date = date.today().isoformat()
    sources = sources or ["rss", "crossref", "pubmed"]
    fetchers: dict[str, Fetcher] = {
        "rss": fetch_rss,
        "crossref": fetch_crossref,
        "pubmed": fetch_pubmed,
    }

    with connect(DB_PATH) as con:
        total_inserted = 0
        for journal in _journal_rows():
            journal_name = journal.get("journal_name", "")
            for source in sources:
                if source not in fetchers:
                    continue
                try:
                    if source == "rss":
                        articles = fetchers[source](journal)
                    else:
                        articles = fetchers[source](journal, from_date=from_date, until_date=until_date)
                    inserted = 0
                    for article in articles:
                        enriched = classify_article(article, topics)
                        if insert_article(con, enriched):
                            inserted += 1
                    con.commit()
                    total_inserted += inserted
                    clear_fetch_failure(con, source=source, journal_name=journal_name)
                    log_run(
                        con,
                        run_date=today_iso(),
                        source=source,
                        journal_name=journal_name,
                        status="ok",
                        fetched_count=len(articles),
                        inserted_count=inserted,
                    )
                    print(f"[{source}] {journal_name}: fetched={len(articles)}, inserted={inserted}")
                except Exception as e:
                    error = str(e)
                    log_run(
                        con,
                        run_date=today_iso(),
                        source=source,
                        journal_name=journal_name,
                        status="error",
                        error_message=error,
                    )
                    upsert_fetch_failure(con, run_date=today_iso(), source=source, journal_name=journal_name, error_message=error)
                    print(f"[{source}] {journal_name}: ERROR {error}")
        print(f"Daily run completed. Total new articles inserted: {total_inserted}")


def stats() -> None:
    init_db(DB_PATH)
    with connect(DB_PATH) as con:
        article_count = con.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        journal_count = con.execute("SELECT COUNT(*) FROM journals WHERE active=1").fetchone()[0]
        today_count = con.execute("SELECT COUNT(*) FROM articles WHERE first_seen_date=?", (today_iso(),)).fetchone()[0]
        favorite_count = con.execute("SELECT COUNT(*) FROM articles WHERE favorite=1").fetchone()[0]
        unread_count = con.execute("SELECT COUNT(*) FROM articles WHERE status IN ('未读','待读','阅读中')").fetchone()[0]
        print(f"Active journals: {journal_count}")
        print(f"Total articles: {article_count}")
        print(f"New articles today: {today_count}")
        print(f"Favorites: {favorite_count}")
        print(f"Unread/to-read/in-progress: {unread_count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sport Sciences Journal Tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Create SQLite database and sync journals.csv")

    daily = sub.add_parser("run-daily", help="Fetch recent articles and generate daily reports")
    daily.add_argument("--days-back", type=int, default=7, help="Publication-date lookback window for API sources")
    daily.add_argument("--sources", nargs="+", default=["rss", "crossref", "pubmed"], choices=["rss", "crossref", "pubmed"], help="Sources to run")
    daily.add_argument("--report", action="store_true", help="Generate today's daily Word/Excel report after fetching")

    dr = sub.add_parser("make-daily-report", help="Generate daily report from database")
    dr.add_argument("--day", default=None, help="YYYY-MM-DD; defaults to today")

    wr = sub.add_parser("make-weekly-report", help="Generate weekly report from database")
    wr.add_argument("--end-day", default=None, help="YYYY-MM-DD; defaults to today")

    sub.add_parser("stats", help="Show database stats")

    args = parser.parse_args()
    if args.command == "init-db":
        sync_journals()
    elif args.command == "run-daily":
        run_daily(days_back=args.days_back, sources=args.sources)
        if args.report:
            from .reports import make_daily_report
            xlsx, docx = make_daily_report()
            print(f"Daily reports: {xlsx}, {docx}")
    elif args.command == "make-daily-report":
        from .reports import make_daily_report
        xlsx, docx = make_daily_report(args.day)
        print(f"Daily reports: {xlsx}, {docx}")
    elif args.command == "make-weekly-report":
        from .reports import make_weekly_report
        xlsx, docx = make_weekly_report(args.end_day)
        print(f"Weekly reports: {xlsx}, {docx}")
    elif args.command == "stats":
        stats()


if __name__ == "__main__":
    main()
