from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pandas as pd

from .config import CONFIG_DIR, REPORT_DIR, ROOT, load_journals

REGISTRY_PATH = CONFIG_DIR / "journal_source_registry.csv"
PUBLISHER_SOURCES_PATH = CONFIG_DIR / "publisher_sources.csv"


def _yes(value: str) -> bool:
    return str(value or "").strip().lower() in {"yes", "y", "true", "1", "active"}


def load_registry() -> pd.DataFrame:
    if REGISTRY_PATH.exists():
        return pd.read_csv(REGISTRY_PATH).fillna("")
    journals = load_journals().fillna("")
    return pd.DataFrame({
        "journal_name": journals["journal_name"],
        "coverage_status": "missing_registry",
        "official_source_verified": "no",
    })


def load_publisher_sources() -> pd.DataFrame:
    if PUBLISHER_SOURCES_PATH.exists():
        return pd.read_csv(PUBLISHER_SOURCES_PATH).fillna("")
    return pd.DataFrame(columns=["journal_name", "active", "verified", "source_type", "source_url"])


def audit_sources(write_report: bool = True) -> dict[str, int | str]:
    registry = load_registry()
    sources = load_publisher_sources()
    total = len(registry)
    active_official = sources[sources["active"].astype(str).str.lower().isin(["yes", "true", "1", "y", "active"])]
    active_verified = active_official[active_official["verified"].astype(str).str.lower().isin(["yes", "true", "1", "y"])]
    configured_names = set(active_official["journal_name"].astype(str))
    verified_names = set(active_verified["journal_name"].astype(str))

    registry = registry.copy()
    registry["active_official_source"] = registry["journal_name"].astype(str).isin(configured_names).map({True: "yes", False: "no"})
    registry["verified_official_source"] = registry["journal_name"].astype(str).isin(verified_names).map({True: "yes", False: "no"})
    registry["coverage_level"] = registry.apply(
        lambda r: "official_verified" if r["verified_official_source"] == "yes" else ("official_configured" if r["active_official_source"] == "yes" else "fallback_only"),
        axis=1,
    )

    report_path = ""
    if write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = str(REPORT_DIR / f"source_coverage_audit_{date.today().isoformat()}.csv")
        registry.to_csv(report_path, index=False, encoding="utf-8-sig")

    result = {
        "target_journals": int(total),
        "active_official_sources": int(len(configured_names)),
        "verified_official_sources": int(len(verified_names)),
        "fallback_only_journals": int(total - len(configured_names)),
        "report_path": report_path,
    }
    return result


def print_audit() -> None:
    result = audit_sources(write_report=True)
    print("Coverage audit completed.")
    print(f"Target journals: {result['target_journals']}")
    print(f"Active official sources: {result['active_official_sources']}")
    print(f"Verified official sources: {result['verified_official_sources']}")
    print(f"Fallback-only journals: {result['fallback_only_journals']}")
    print(f"Report: {result['report_path']}")
