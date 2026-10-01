from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
REPORT_DIR = ROOT / "reports"
DB_PATH = DATA_DIR / "journal_tracker.db"

load_dotenv(ROOT / ".env")


def load_journals(path: Path | None = None) -> pd.DataFrame:
    path = path or CONFIG_DIR / "journals.csv"
    df = pd.read_csv(path).fillna("")
    expansion_path = CONFIG_DIR / "journal_expansion.csv"
    if expansion_path.exists():
        expanded = pd.read_csv(expansion_path).fillna("")
        df = pd.concat([df, expanded], ignore_index=True, sort=False)
        # Keep the base catalogue authoritative if a title appears in both files.
        normalized_names = df["journal_name"].astype(str).str.casefold().str.replace(r"[^a-z0-9]", "", regex=True)
        df = df.loc[~normalized_names.duplicated(keep="first")].copy()
    required = {"journal_name", "priority", "domain", "frequency", "active"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"journals.csv missing required columns: {sorted(missing)}")
    df["active"] = df["active"].astype(str).str.lower().isin(["yes", "true", "1", "y"])
    return df


def load_topic_keywords(path: Path | None = None) -> dict[str, list[str]]:
    path = path or CONFIG_DIR / "topic_keywords.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default)
