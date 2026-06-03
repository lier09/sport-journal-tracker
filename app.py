from __future__ import annotations

import html
import json
import re
from datetime import date, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.config import CONFIG_DIR, DB_PATH, ROOT
from src.database import connect, init_db, update_article_user_fields

st.set_page_config(
    page_title="体育科学期刊更新监控看板",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_db(DB_PATH)

READING_STATUS = ["未读", "待读", "阅读中", "已读", "精读", "已引用", "不相关"]

st.markdown(
    """
<style>
:root {
  --jt-bg: #F6F8FC;
  --jt-panel: #FFFFFF;
  --jt-panel-2: #F8FAFC;
  --jt-line: rgba(15, 23, 42, 0.10);
  --jt-muted: #64748B;
  --jt-text: #0F172A;
  --jt-blue: #2563EB;
  --jt-cyan: #0891B2;
  --jt-green: #16A34A;
  --jt-orange: #EA580C;
  --jt-purple: #7C3AED;
  --jt-red: #DC2626;
}

html, body, [class*="css"] {
  font-family: "Inter", "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
}

.stApp {
  background:
    radial-gradient(circle at 8% 0%, rgba(37,99,235,.075), transparent 26%),
    radial-gradient(circle at 90% 4%, rgba(14,165,233,.08), transparent 28%),
    linear-gradient(180deg, #F8FAFC 0%, #EEF2F7 100%);
  color: var(--jt-text);
}

.block-container {
  padding-top: 1.35rem;
  padding-bottom: 3rem;
  max-width: 1480px;
}

[data-testid="stSidebar"] {
  background:
    linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,250,252,.96));
  border-right: 1px solid rgba(15,23,42,.08);
  box-shadow: 8px 0 30px rgba(15,23,42,.035);
}

[data-testid="stSidebar"] * {
  font-size: .93rem;
}


/* Streamlit sidebar: force readable light theme colors */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"] {
  background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
  color: #0F172A !important;
}

[data-testid="stSidebar"] *,
[data-testid="stSidebarContent"] *,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
  color: #0F172A !important;
  opacity: 1 !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
  color: #334155 !important;
}

[data-testid="stSidebar"] .sidebar-title {
  color: #0F172A !important;
}

[data-testid="stSidebar"] .sidebar-help {
  color: #64748B !important;
}

[data-testid="stSidebar"] div[role="radiogroup"] label,
[data-testid="stSidebar"] div[role="radiogroup"] label span,
[data-testid="stSidebar"] [data-testid="stRadio"] label,
[data-testid="stSidebar"] [data-testid="stCheckbox"] label,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] label,
[data-testid="stSidebar"] [data-testid="stSelectbox"] label,
[data-testid="stSidebar"] [data-testid="stDateInput"] label,
[data-testid="stSidebar"] [data-testid="stTextInput"] label {
  color: #0F172A !important;
}

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div {
  background: #FFFFFF !important;
  color: #0F172A !important;
  border-color: rgba(15,23,42,.14) !important;
}

[data-testid="stSidebar"] svg,
[data-testid="stSidebar"] path,
[data-testid="stSidebar"] circle {
  color: #334155 !important;
}

[data-testid="stHeader"] {
  background: rgba(248,250,252,.88) !important;
  backdrop-filter: blur(12px);
}

[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {
  color: #0F172A !important;
}

.hero {
  position: relative;
  border: 1px solid rgba(37,99,235,.14);
  border-radius: 28px;
  padding: 28px 32px;
  margin-bottom: 18px;
  overflow: hidden;
  background:
    radial-gradient(circle at 12% 18%, rgba(37,99,235,.14), transparent 34%),
    radial-gradient(circle at 86% 12%, rgba(14,165,233,.13), transparent 34%),
    linear-gradient(135deg, rgba(255,255,255,.98), rgba(241,245,249,.92));
  box-shadow: 0 22px 58px rgba(15,23,42,.075);
}

.hero:before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 0%, rgba(255,255,255,.75) 44%, transparent 70%);
  transform: translateX(-30%);
  pointer-events: none;
}

.hero-title {
  position: relative;
  font-size: 2.08rem;
  line-height: 1.18;
  font-weight: 880;
  letter-spacing: -.035em;
  color: #0F172A;
  margin-bottom: 9px;
}

.hero-subtitle {
  position: relative;
  font-size: .99rem;
  color: #475569;
  max-width: 1080px;
  line-height: 1.74;
}

.hero-chip {
  position: relative;
  display:inline-flex;
  align-items:center;
  gap:6px;
  padding:7px 12px;
  border-radius:999px;
  background:rgba(37,99,235,.075);
  border:1px solid rgba(37,99,235,.14);
  color:#1D4ED8;
  font-size:.8rem;
  font-weight: 650;
  margin-right:8px;
  margin-top:13px;
}

.kpi-card {
  border: 1px solid rgba(15,23,42,.08);
  border-radius: 22px;
  padding: 18px 18px;
  background:
    linear-gradient(180deg, rgba(255,255,255,1), rgba(248,250,252,.96));
  box-shadow: 0 14px 34px rgba(15,23,42,.065);
  min-height: 118px;
}

.kpi-icon {
  width: 40px;
  height: 40px;
  border-radius: 15px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size: 1.2rem;
  background: linear-gradient(135deg, rgba(37,99,235,.10), rgba(14,165,233,.08));
  border: 1px solid rgba(37,99,235,.13);
  margin-bottom: 10px;
}

.kpi-value {
  font-size: 2.06rem;
  font-weight: 880;
  color: #0F172A;
  letter-spacing: -.045em;
  line-height: 1;
}

.kpi-label {
  font-size: .88rem;
  color: #334155;
  margin-top: 8px;
  font-weight: 700;
}

.kpi-note {
  font-size: .74rem;
  color: #64748B;
  margin-top: 3px;
  line-height: 1.35;
}

.section-title {
  font-size: 1.16rem;
  font-weight: 850;
  margin: 1.18rem 0 .65rem;
  color: #0F172A;
  letter-spacing: -.015em;
}

.section-subtitle {
  font-size: .86rem;
  color: #64748B;
  margin-top: -.25rem;
  margin-bottom: .8rem;
}

.paper-card {
  border: 1px solid rgba(15,23,42,.08);
  border-radius: 23px;
  padding: 16px 18px;
  margin: 12px 0;
  background:
    linear-gradient(180deg, rgba(255,255,255,.99), rgba(248,250,252,.96));
  box-shadow: 0 16px 38px rgba(15,23,42,.065);
}

.paper-card:hover {
  border-color: rgba(37,99,235,.22);
  box-shadow: 0 20px 48px rgba(37,99,235,.10);
}

.card-title {
  font-weight: 850;
  font-size: 1.04rem;
  line-height: 1.5;
  color: #0F172A;
  margin: 7px 0 8px;
}

.card-meta {
  color:#475569;
  font-size:.84rem;
  line-height: 1.6;
}

.card-abstract {
  line-height: 1.72;
  color:#1E293B;
  padding: 13px 15px;
  border-left: 3px solid rgba(37,99,235,.50);
  background: rgba(239,246,255,.68);
  border-radius: 14px;
  margin: 8px 0 12px;
}

.badge {
  display: inline-flex;
  align-items:center;
  gap: 4px;
  border-radius: 999px;
  padding: 4px 10px;
  margin: 3px 5px 3px 0;
  font-size: 0.76rem;
  font-weight: 650;
  border: 1px solid rgba(15,23,42,.10);
  background: rgba(248,250,252,.88);
  color:#334155;
}

.badge-blue {
  background: rgba(37,99,235,.085);
  border-color: rgba(37,99,235,.16);
  color:#1D4ED8;
}

.badge-green {
  background: rgba(22,163,74,.085);
  border-color: rgba(22,163,74,.16);
  color:#15803D;
}

.badge-orange {
  background: rgba(234,88,12,.085);
  border-color: rgba(234,88,12,.16);
  color:#C2410C;
}

.badge-purple {
  background: rgba(124,58,237,.085);
  border-color: rgba(124,58,237,.16);
  color:#6D28D9;
}

.badge-red {
  background: rgba(220,38,38,.075);
  border-color: rgba(220,38,38,.15);
  color:#B91C1C;
}

.badge-muted {
  background: rgba(100,116,139,.08);
  color:#475569;
}
.badge-pending {
  background: rgba(234,179,8,.12);
  border-color: rgba(234,179,8,.22);
  color:#A16207;
}

.journal-section {
  font-size: 1.22rem;
  font-weight: 860;
  margin-top: 1.35rem;
  padding: .95rem 1rem;
  border: 1px solid rgba(15,23,42,.08);
  border-radius: 19px;
  background: linear-gradient(90deg, rgba(255,255,255,.98), rgba(239,246,255,.78));
  color: #0F172A;
  box-shadow: 0 10px 26px rgba(15,23,42,.045);
}

.small-muted {
  font-size: .82rem;
  color: #64748B;
  font-weight: 550;
}

.sidebar-title {
  font-weight: 880;
  color:#0F172A;
  font-size: 1.03rem;
  margin: .45rem 0 .35rem;
}

.sidebar-help {
  font-size:.78rem;
  color:#64748B;
  line-height:1.48;
  margin-bottom:.6rem;
}

.soft-divider {
  height:1px;
  background:rgba(15,23,42,.08);
  margin: .9rem 0;
}

.stDownloadButton > button, .stButton > button, .stLinkButton > a {
  border-radius: 13px !important;
  border-color: rgba(15,23,42,.12) !important;
  background: #FFFFFF !important;
  color: #0F172A !important;
  box-shadow: 0 6px 16px rgba(15,23,42,.045) !important;
  transition: all .18s ease !important;
}

.stDownloadButton > button:hover, .stButton > button:hover, .stLinkButton > a:hover {
  transform: translateY(-1px);
  border-color: rgba(37,99,235,.28) !important;
  box-shadow: 0 10px 22px rgba(37,99,235,.10) !important;
}

div[data-testid="stExpander"] {
  border: 1px solid rgba(15,23,42,.08);
  border-radius: 16px;
  background: rgba(255,255,255,.86);
}

div[data-testid="stAlert"] {
  border-radius: 16px;
}

hr {
  border-color: rgba(15,23,42,.08);
}

[data-testid="stMetric"] {
  background: #FFFFFF;
  border: 1px solid rgba(15,23,42,.08);
  border-radius: 18px;
  padding: 14px 16px;
}

/* v4.5 Product UI Edition */
.product-strip {
  display:grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin: 14px 0 20px;
}
.product-tile {
  border: 1px solid rgba(37,99,235,.12);
  background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,250,252,.92));
  border-radius: 22px;
  padding: 17px 18px;
  box-shadow: 0 16px 36px rgba(15,23,42,.055);
}
.product-tile-icon {
  width: 42px;
  height: 42px;
  border-radius: 16px;
  display:flex;
  align-items:center;
  justify-content:center;
  margin-bottom: 10px;
  font-size: 1.18rem;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.9), 0 10px 22px rgba(37,99,235,.10);
}
.icon-blue { background: linear-gradient(135deg, rgba(37,99,235,.14), rgba(14,165,233,.10)); border: 1px solid rgba(37,99,235,.18); color:#1D4ED8; }
.icon-green { background: linear-gradient(135deg, rgba(22,163,74,.14), rgba(34,197,94,.08)); border: 1px solid rgba(22,163,74,.18); color:#15803D; }
.icon-purple { background: linear-gradient(135deg, rgba(124,58,237,.14), rgba(168,85,247,.08)); border: 1px solid rgba(124,58,237,.18); color:#6D28D9; }
.icon-orange { background: linear-gradient(135deg, rgba(234,88,12,.14), rgba(251,146,60,.08)); border: 1px solid rgba(234,88,12,.18); color:#C2410C; }
.product-tile-title { font-weight: 840; color: #0F172A; margin-bottom: 4px; }
.product-tile-desc { color: #64748B; font-size: .80rem; line-height: 1.48; }
.dashboard-card {
  border: 1px solid rgba(15,23,42,.08);
  border-radius: 24px;
  padding: 18px 20px;
  background: rgba(255,255,255,.93);
  box-shadow: 0 18px 42px rgba(15,23,42,.06);
  margin: 12px 0;
}
.paper-topline { display:flex; flex-wrap:wrap; gap: 6px; margin-bottom: 8px; }
.card-preview {
  color:#64748B; font-size:.88rem; line-height:1.65; margin-top: 8px; padding: 10px 12px;
  border-radius: 14px; background: rgba(248,250,252,.88); border: 1px solid rgba(15,23,42,.06);
}
.detail-grid {
  display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 4px 0 12px;
}
.detail-cell {
  padding: 10px 12px; border-radius: 14px; border: 1px solid rgba(15,23,42,.08); background: rgba(248,250,252,.9);
}
.detail-label { color:#64748B; font-size:.72rem; font-weight:700; margin-bottom:3px; }
.detail-value { color:#0F172A; font-size:.86rem; font-weight:700; word-break:break-word; }
.journal-grid { display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-top: 10px; }
.journal-card {
  border: 1px solid rgba(15,23,42,.08); border-radius: 22px; padding: 16px 18px;
  background: linear-gradient(180deg, #FFFFFF, #F8FAFC); box-shadow: 0 14px 32px rgba(15,23,42,.055);
}
.journal-card-title { font-weight: 840; color:#0F172A; line-height:1.42; margin-bottom: 10px; }
.journal-card-stats { display:flex; gap:8px; flex-wrap:wrap; }
.stat-pill {
  border-radius:999px; padding:4px 9px; font-size:.75rem; font-weight:680;
  border:1px solid rgba(37,99,235,.14); background:rgba(37,99,235,.07); color:#1D4ED8;
}
.topic-grid { display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-top: 10px; }
.topic-card {
  border: 1px solid rgba(124,58,237,.12); border-radius: 22px; padding: 16px 18px;
  background: linear-gradient(180deg, #FFFFFF, #F8FAFC); box-shadow: 0 14px 32px rgba(15,23,42,.055);
}
.topic-title { font-weight: 850; color:#4C1D95; margin-bottom: 8px; }
.topic-number { font-size: 1.86rem; font-weight: 880; color:#0F172A; letter-spacing:-.04em; }
.empty-state {
  border: 1px dashed rgba(37,99,235,.22); border-radius: 22px; padding: 22px 24px;
  background: rgba(239,246,255,.55); color: #334155; line-height: 1.7;
}
@media (max-width: 1100px) {
  .product-strip, .journal-grid, .topic-grid { grid-template-columns: 1fr; }
  .detail-grid { grid-template-columns: 1fr 1fr; }
}


.focus-note {
  border: 1px solid rgba(245,158,11,.18);
  background: linear-gradient(180deg, rgba(255,251,235,.9), rgba(255,255,255,.92));
  border-radius: 18px;
  padding: 12px 14px;
  color: #92400E;
  font-size: .82rem;
  line-height: 1.55;
  margin: 8px 0 12px;
}
.focus-pill {
  border-radius:999px;
  padding:4px 9px;
  font-size:.75rem;
  font-weight:760;
  border:1px solid rgba(245,158,11,.22);
  background:rgba(245,158,11,.10);
  color:#B45309;
}


/* v4.9 restore original visual style + stable card rendering */
.stApp {
  background: linear-gradient(180deg, #F8FAFC 0%, #EEF4FB 100%);
}
.journal-card-fixed, .topic-card-fixed {
  border: 1px solid rgba(15,23,42,.08);
  border-radius: 22px;
  padding: 18px 20px;
  background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,250,252,.92));
  box-shadow: 0 14px 32px rgba(15,23,42,.055);
  min-height: 168px;
  margin-bottom: 14px;
}
.journal-card-fixed-title {
  font-weight: 850;
  color: #0F172A;
  line-height: 1.38;
  font-size: 1.04rem;
  margin-bottom: 12px;
}
.journal-card-fixed-domain {
  color:#64748B;
  font-size:.84rem;
  line-height:1.55;
  margin-top: 12px;
  word-break: break-word;
}
.metric-row-fixed {
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top: 8px;
}
.metric-pill-fixed {
  display:inline-flex;
  align-items:center;
  border-radius:999px;
  padding:5px 10px;
  font-size:.78rem;
  font-weight:720;
  border:1px solid rgba(37,99,235,.14);
  background:rgba(37,99,235,.07);
  color:#1D4ED8;
}
.focus-pill-fixed {
  display:inline-flex;
  align-items:center;
  border-radius:999px;
  padding:5px 10px;
  font-size:.78rem;
  font-weight:720;
  border:1px solid rgba(234,179,8,.24);
  background:rgba(254,249,195,.74);
  color:#A16207;
}
.topic-card-fixed-title { font-weight:850; color:#4C1D95; margin-bottom:8px; }
.topic-card-fixed-number { font-size:2rem; font-weight:900; color:#0F172A; letter-spacing:-.04em; }

</style>
""",
    unsafe_allow_html=True,
)


def esc(x) -> str:
    return html.escape(str(x or ""))


def _split_items(x: str) -> list[str]:
    return [t.strip() for t in str(x or "").split(";") if t.strip()]


def _topic_label(topics: str) -> str:
    parts = _split_items(topics)
    if not parts:
        return "未命中专题"
    if len(parts) <= 2:
        return "；".join(parts)
    return "；".join(parts[:2]) + f" 等{len(parts)}项"


def _doi_link(doi: str) -> str:
    doi = str(doi or "").strip()
    return f"https://doi.org/{doi}" if doi else ""


def _pubmed_link(pmid: str) -> str:
    pmid = str(pmid or "").strip()
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""


def _safe_filename(text: str, max_len: int = 70) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff_-]+", "_", str(text or "article")).strip("_")
    return (cleaned[:max_len] or "article")


def make_bibtex(df: pd.DataFrame) -> str:
    entries = []
    for _, r in df.iterrows():
        title = str(r.get("title", "")).replace("{", "").replace("}", "")
        journal = str(r.get("journal_name", ""))
        year = str(r.get("publication_date", "") or r.get("first_seen_date", ""))[:4]
        doi = str(r.get("doi", ""))
        authors = str(r.get("authors", "")).replace(";", " and")
        key_source = authors.split(" and")[0] if authors else journal
        key_base = re.sub(r"[^A-Za-z0-9]+", "", key_source.split()[-1] if key_source else "article")
        key = f"{key_base}{year}{int(r.get('article_id', 0) or 0)}"
        url = r.get("fulltext_url") or r.get("url") or _doi_link(doi)
        entries.append(
            "@article{" + key + ",\n"
            f"  title = {{{title}}},\n"
            f"  author = {{{authors}}},\n"
            f"  journal = {{{journal}}},\n"
            f"  year = {{{year}}},\n"
            f"  doi = {{{doi}}},\n"
            f"  url = {{{url}}}\n"
            "}"
        )
    return "\n\n".join(entries)


def make_ris(df: pd.DataFrame) -> str:
    records = []
    for _, r in df.iterrows():
        lines = ["TY  - JOUR"]
        if r.get("title"):
            lines.append(f"TI  - {r.get('title')}")
        for author in str(r.get("authors", "")).split(";"):
            author = author.strip()
            if author:
                lines.append(f"AU  - {author}")
        if r.get("journal_name"):
            lines.append(f"JO  - {r.get('journal_name')}")
        if r.get("publication_date"):
            lines.append(f"PY  - {str(r.get('publication_date'))[:4]}")
            lines.append(f"DA  - {r.get('publication_date')}")
        if r.get("doi"):
            lines.append(f"DO  - {r.get('doi')}")
        link = r.get("fulltext_url") or r.get("url") or _doi_link(r.get("doi", ""))
        if link:
            lines.append(f"UR  - {link}")
        if r.get("abstract"):
            lines.append(f"AB  - {str(r.get('abstract'))[:4000]}")
        lines.append("ER  -")
        records.append("\n".join(lines))
    return "\n\n".join(records)


@st.cache_data(ttl=60)
def load_journals() -> pd.DataFrame:
    with connect(DB_PATH) as con:
        return pd.read_sql_query(
            """
            SELECT journal_name, priority, domain, frequency, issn, eissn, rss_url, active
            FROM journals
            WHERE active=1
            ORDER BY
                CASE priority WHEN 'S' THEN 1 WHEN 'A' THEN 2 WHEN 'B' THEN 3 WHEN 'C' THEN 4 ELSE 9 END,
                journal_name
            """,
            con,
        )


@st.cache_data(ttl=60)
def load_articles(start: str, end: str) -> pd.DataFrame:
    with connect(DB_PATH) as con:
        df = pd.read_sql_query(
            """
            SELECT a.article_id, a.first_seen_date, a.publication_date, a.journal_name, j.priority,
                   j.domain, a.title, a.authors, a.doi, a.url, a.fulltext_url, a.source, a.pmid,
                   a.abstract, a.topics, a.matched_keywords, a.study_type, a.status,
                   a.favorite, a.user_notes, a.personal_tags, a.created_at, a.updated_at
            FROM articles a
            LEFT JOIN journals j ON a.journal_name = j.journal_name
            WHERE a.first_seen_date BETWEEN ? AND ?
            ORDER BY a.first_seen_date DESC, a.publication_date DESC, a.journal_name, a.title
            """,
            con,
            params=(start, end),
        )
    return normalize_article_df(df)


@st.cache_data(ttl=60)
def load_all_topics() -> list[str]:
    with connect(DB_PATH) as con:
        values = pd.read_sql_query("SELECT DISTINCT topics FROM articles WHERE COALESCE(topics,'') != ''", con)
    topic_set: set[str] = set()
    for x in values.get("topics", []):
        topic_set.update(_split_items(x))
    return sorted(topic_set)


@st.cache_data(ttl=60)
def load_recent_errors(limit: int = 120) -> pd.DataFrame:
    with connect(DB_PATH) as con:
        return pd.read_sql_query(
            """
            SELECT run_date, source, journal_name, status, error_message, created_at
            FROM run_log
            WHERE status='error'
            ORDER BY created_at DESC
            LIMIT ?
            """,
            con,
            params=(limit,),
        )


@st.cache_data(ttl=60)
def load_last_run_time() -> str:
    with connect(DB_PATH) as con:
        row = con.execute("SELECT MAX(created_at) AS last_run FROM run_log").fetchone()
    return str(row["last_run"] or "") if row else ""


def normalize_article_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        for col in ["topic_count", "has_topic", "favorite", "status", "has_abstract", "has_doi", "has_pmid", "has_link"]:
            df[col] = []
        return df
    df = df.copy()
    df["topic_count"] = df["topics"].fillna("").apply(lambda x: len(_split_items(x)))
    df["has_topic"] = df["topic_count"] > 0
    df["favorite"] = df["favorite"].fillna(0).astype(int)
    df["status"] = df["status"].fillna("未读").replace("", "未读")
    df["has_abstract"] = df["abstract"].fillna("").astype(str).str.strip().ne("")
    df["has_doi"] = df["doi"].fillna("").astype(str).str.strip().ne("")
    df["has_pmid"] = df["pmid"].fillna("").astype(str).str.strip().ne("")
    df["has_link"] = (
        df["fulltext_url"].fillna("").astype(str).str.strip().ne("")
        | df["url"].fillna("").astype(str).str.strip().ne("")
        | df["has_doi"]
        | df["has_pmid"]
    )
    return df


def apply_filters(df: pd.DataFrame, *, selected_journal: str, priorities=None, statuses=None, topics=None, keyword="", favorites_only=False, topic_only=False, focus_journals=None, focus_only=False) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return out
    if selected_journal and selected_journal != "全部期刊":
        out = out[out["journal_name"] == selected_journal]
    if focus_only and focus_journals:
        out = out[out["journal_name"].isin(focus_journals)]
    if priorities:
        out = out[out["priority"].fillna("").isin(priorities)]
    if statuses:
        out = out[out["status"].fillna("未读").isin(statuses)]
    if topics:
        out = out[out["topics"].fillna("").apply(lambda x: any(t in _split_items(x) for t in topics))]
    if favorites_only:
        out = out[out["favorite"].astype(int) == 1]
    if topic_only:
        out = out[out["topics"].fillna("").astype(str) != ""]
    if keyword:
        kw = keyword.lower().strip()
        hay = (
            out["title"].fillna("")
            + " " + out["abstract"].fillna("")
            + " " + out["journal_name"].fillna("")
            + " " + out["matched_keywords"].fillna("")
            + " " + out["authors"].fillna("")
        ).str.lower()
        out = out[hay.str.contains(re.escape(kw), regex=True, na=False)]
    return out


def topic_counts(df: pd.DataFrame) -> pd.Series:
    rows: list[str] = []
    for _, r in df.iterrows():
        topics = _split_items(r.get("topics", ""))
        rows.extend(topics if topics else ["未命中专题"])
    return pd.Series(rows).value_counts() if rows else pd.Series(dtype=int)



def light_bar_chart(data, *, x_title: str = "", y_title: str = "数量", height: int = 330) -> None:
    """Render a light-theme Altair bar chart instead of Streamlit's default dark chart."""
    if data is None or len(data) == 0:
        st.info("当前范围暂无可绘制数据。")
        return
    if isinstance(data, pd.Series):
        df = data.reset_index()
        df.columns = [x_title or "类别", y_title or "数量"]
    else:
        df = data.reset_index()
        if len(df.columns) >= 2:
            df = df.rename(columns={df.columns[0]: x_title or "类别", df.columns[1]: y_title or "数量"})
        else:
            st.dataframe(df, use_container_width=True)
            return
    x_col, y_col = df.columns[0], df.columns[1]
    df[x_col] = df[x_col].astype(str)
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color="#93C5FD")
        .encode(
            x=alt.X(f"{x_col}:N", title=x_title or None, sort=None, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y(f"{y_col}:Q", title=y_title or None),
            tooltip=[alt.Tooltip(f"{x_col}:N", title=x_title or "类别"), alt.Tooltip(f"{y_col}:Q", title=y_title or "数量")],
        )
        .properties(height=height, background="transparent")
        .configure_view(strokeWidth=0)
        .configure_axis(labelColor="#334155", titleColor="#0F172A", gridColor="rgba(15,23,42,.08)", domainColor="rgba(15,23,42,.18)", tickColor="rgba(15,23,42,.18)")
    )
    st.altair_chart(chart, use_container_width=True)


def kpi(icon: str, value, label: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-icon">{esc(icon)}</div>
          <div class="kpi-value">{esc(value)}</div>
          <div class="kpi-label">{esc(label)}</div>
          <div class="kpi-note">{esc(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_links(row) -> None:
    doi_url = _doi_link(row.get("doi", ""))
    pubmed_url = _pubmed_link(row.get("pmid", ""))
    full_url = row.get("fulltext_url") or row.get("url") or ""
    cols = st.columns(4)
    idx = 0
    if doi_url:
        cols[idx].link_button("🔗 DOI", doi_url, use_container_width=True); idx += 1
    if pubmed_url and idx < len(cols):
        cols[idx].link_button("🧬 PubMed", pubmed_url, use_container_width=True); idx += 1
    if full_url and idx < len(cols):
        cols[idx].link_button("📄 原文 / 数据库页", full_url, use_container_width=True); idx += 1
    if idx == 0:
        st.caption("暂无可跳转链接。")


def render_article_card(row, *, key_prefix: str = "card") -> None:
    title = str(row.get("title", "") or "未命名论文")
    journal = str(row.get("journal_name", "") or "未知期刊")
    topics = str(row.get("topics", "") or "")
    source = str(row.get("source", "") or "")
    star = "⭐" if int(row.get("favorite", 0) or 0) else "☆"
    article_id = int(row.article_id)
    abstract = str(row.get("abstract", "") or "").strip()
    preview = (abstract[:210] + "……") if len(abstract) > 210 else abstract
    meta_status = [
        "摘要✓" if row.get("has_abstract", False) else "摘要待补全",
        "DOI✓" if row.get("has_doi", False) else "DOI暂缺",
        "PMID✓" if row.get("has_pmid", False) else "PMID暂缺",
        "链接✓" if row.get("has_link", False) else "链接暂缺",
    ]

    st.markdown('<div class="paper-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="paper-topline">
          <span class="badge badge-blue">📚 {esc(journal)}</span>
          <span class="badge badge-green">🗓 更新：{esc(row.get('first_seen_date',''))}</span>
          <span class="badge badge-orange">📝 发表：{esc(row.get('publication_date','') or '日期暂缺')}</span>
          <span class="badge badge-purple">🏷 {_topic_label(topics)}</span>
          <span class="badge {'badge-green' if row.get('has_abstract', False) else 'badge-pending'}">{'📄 摘要已收录' if row.get('has_abstract', False) else '📄 摘要待补全'}</span>
        </div>
        <div class="card-title">{esc(star)} {esc(title)}</div>
        <div class="card-meta">{esc(row.get('authors','') or '作者未获取')}</div>
        <div class="card-preview">{esc(preview or '摘要状态：待补全。系统会在每日元数据补全任务中继续尝试通过 PMID / DOI 回填官方摘要。')}</div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("展开详情｜摘要｜引用｜链接｜备注"):
        st.markdown(
            f"""
            <div class="detail-grid">
              <div class="detail-cell"><div class="detail-label">期刊</div><div class="detail-value">{esc(journal)}</div></div>
              <div class="detail-cell"><div class="detail-label">首次发现</div><div class="detail-value">{esc(row.get('first_seen_date',''))}</div></div>
              <div class="detail-cell"><div class="detail-label">发表日期</div><div class="detail-value">{esc(row.get('publication_date','') or '暂缺')}</div></div>
              <div class="detail-cell"><div class="detail-label">来源</div><div class="detail-value">{esc(source)}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        tab_abs, tab_cite, tab_link, tab_note = st.tabs(["📄 摘要", "⬇️ 引用", "🔗 链接", "📝 备注"])
        with tab_abs:
            st.markdown(f"**专题标签**：{esc(topics or '未命中专题词库')}")
            st.markdown(f"**命中关键词**：{esc(row.get('matched_keywords','') or '无')}")
            st.markdown(f"**研究类型**：{esc(row.get('study_type','') or '未识别')}")
            st.markdown("**元数据状态**：" + " ｜ ".join(meta_status))
            if abstract:
                st.markdown(f'<div class="card-abstract">{esc(abstract)}</div>', unsafe_allow_html=True)
            else:
                st.info("摘要状态：待补全。当前记录尚未获取官方摘要；系统会在后续元数据补全任务中继续尝试通过 PMID / DOI 回填。")
        with tab_cite:
            one_df = pd.DataFrame([row])
            d1, d2, d3 = st.columns(3)
            fname = _safe_filename(title)
            d1.download_button("⬇️ 本篇 RIS", make_ris(one_df).encode("utf-8"), file_name=f"{fname}.ris", mime="application/x-research-info-systems", use_container_width=True, key=f"{key_prefix}_ris_{article_id}")
            d2.download_button("⬇️ 本篇 BibTeX", make_bibtex(one_df).encode("utf-8"), file_name=f"{fname}.bib", mime="text/plain", use_container_width=True, key=f"{key_prefix}_bib_{article_id}")
            if row.get("doi"):
                d3.link_button("🌐 DOI 引用页", _doi_link(row.get("doi", "")), use_container_width=True)
            st.caption("RIS 可导入 Zotero / EndNote / NoteExpress；BibTeX 适合 LaTeX 或学术写作管理。")
        with tab_link:
            render_links(row)
        with tab_note:
            st.caption("公开部署版中，阅读状态/备注属于公共数据库字段；如果多人共同使用，建议主要用于管理员维护。")
            s_col, f_col = st.columns([2, 1])
            current_status = row.get("status", "未读") if row.get("status", "未读") in READING_STATUS else "未读"
            new_status = s_col.selectbox("阅读状态", READING_STATUS, index=READING_STATUS.index(current_status), key=f"{key_prefix}_status_{article_id}")
            new_fav = f_col.checkbox("收藏", value=bool(row.get("favorite", 0)), key=f"{key_prefix}_fav_{article_id}")
            new_tags = st.text_input("个人标签", value=str(row.get("personal_tags", "") or ""), key=f"{key_prefix}_tags_{article_id}", placeholder="如：低氧训练；可用于讨论；精读")
            new_notes = st.text_area("个人备注", value=str(row.get("user_notes", "") or ""), key=f"{key_prefix}_notes_{article_id}", height=80)
            if st.button("保存阅读信息", key=f"{key_prefix}_save_{article_id}"):
                with connect(DB_PATH) as con:
                    update_article_user_fields(con, article_id, status=new_status, favorite=1 if new_fav else 0, user_notes=new_notes, personal_tags=new_tags)
                st.success("已保存。")
                st.cache_data.clear()
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_empty(message: str) -> None:
    st.markdown(f'<div class="empty-state">🫙 {esc(message)}</div>', unsafe_allow_html=True)


def render_product_tiles() -> None:
    st.markdown(
        '''
        <div class="product-strip">
          <div class="product-tile"><div class="product-tile-icon icon-blue">🗓️</div><div class="product-tile-title">每日更新</div><div class="product-tile-desc">以系统首次发现日期为核心口径，清晰展示每日新增文献记录。</div></div>
          <div class="product-tile"><div class="product-tile-icon icon-green">🏛️</div><div class="product-tile-title">期刊导航</div><div class="product-tile-desc">按 Sport Sciences-SCIE 期刊追踪更新，支持单刊查看。</div></div>
          <div class="product-tile"><div class="product-tile-icon icon-purple">🧬</div><div class="product-tile-title">专题情报</div><div class="product-tile-desc">基于透明关键词词库归类，不使用 AI 相关性评分。</div></div>
          <div class="product-tile"><div class="product-tile-icon icon-orange">📥</div><div class="product-tile-title">引用导出</div><div class="product-tile-desc">支持 RIS / BibTeX / CSV，方便导入 Zotero、EndNote 或 NoteExpress。</div></div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_journal_center(day_df: pd.DataFrame, trend_df: pd.DataFrame, journals_df: pd.DataFrame, focus_journals: list[str] | None = None) -> None:
    focus_journals = focus_journals or []
    st.markdown('<div class="section-title">📚 期刊中心</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">按期刊查看今日、近 7 日与当前趋势范围的更新强度；可在左侧自定义重点关注期刊。</div>', unsafe_allow_html=True)
    if focus_journals:
        st.markdown(
            f'<div class="focus-note">⭐ 当前已设置 {len(focus_journals)} 本重点关注期刊。重点关注只影响你的当前浏览会话，不会改动公共数据库。</div>',
            unsafe_allow_html=True,
        )
    if journals_df.empty:
        render_empty("暂无期刊配置。")
        return

    last7_start = (date.today() - timedelta(days=6)).isoformat()
    last7 = trend_df[trend_df["first_seen_date"] >= last7_start] if not trend_df.empty else trend_df
    day_counts = day_df.groupby("journal_name").size().to_dict() if not day_df.empty else {}
    week_counts = last7.groupby("journal_name").size().to_dict() if not last7.empty else {}
    trend_counts = trend_df.groupby("journal_name").size().to_dict() if not trend_df.empty else {}

    cards = []
    for _, jr in journals_df.iterrows():
        name = jr.get("journal_name", "")
        d = int(day_counts.get(name, 0))
        w = int(week_counts.get(name, 0))
        t = int(trend_counts.get(name, 0))
        if d == 0 and w == 0 and t == 0 and name not in focus_journals:
            continue
        cards.append((1 if name in focus_journals else 0, d, w, t, name, jr.get("domain", "")))
    cards = sorted(cards, key=lambda x: (x[0], x[1], x[2], x[3], x[4]), reverse=True)[:48]

    if not cards:
        render_empty("当前日期和趋势范围内没有期刊更新。")
        return

    # Use Streamlit columns + single-line HTML cards to avoid Markdown treating indented HTML as code blocks.
    for i in range(0, len(cards), 3):
        cols = st.columns(3)
        for col, item in zip(cols, cards[i:i + 3]):
            is_focus, d, w, t, name, domain = item
            focus_badge = '<span class="focus-pill-fixed">⭐ 重点关注</span>' if is_focus else ''
            html_card = (
                f'<div class="journal-card-fixed">'
                f'<div class="journal-card-fixed-title">📚 {esc(name)}</div>'
                f'<div class="metric-row-fixed">'
                f'<span class="metric-pill-fixed">今日 {d}</span>'
                f'<span class="metric-pill-fixed">近7日 {w}</span>'
                f'<span class="metric-pill-fixed">趋势范围 {t}</span>'
                f'{focus_badge}'
                f'</div>'
                f'<div class="journal-card-fixed-domain">{esc(domain or "未配置方向")}</div>'
                f'</div>'
            )
            col.markdown(html_card, unsafe_allow_html=True)

def render_topic_center(df: pd.DataFrame, trend_df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">🏷 专题中心</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">展示所选日期与当前趋势范围内的专题命中分布。</div>', unsafe_allow_html=True)
    if df.empty:
        render_empty("当前筛选条件下暂无专题命中文献。")
        return
    counts = topic_counts(df)
    trend_counts = topic_counts(trend_df) if not trend_df.empty else pd.Series(dtype=int)

    topic_items = list(counts.head(16).items())
    for i in range(0, len(topic_items), 4):
        cols = st.columns(4)
        for col, (topic, count) in zip(cols, topic_items[i:i + 4]):
            tcount = int(trend_counts.get(topic, 0)) if len(trend_counts) else 0
            html_card = (
                f'<div class="topic-card-fixed">'
                f'<div class="topic-card-fixed-title">🏷 {esc(topic)}</div>'
                f'<div class="topic-card-fixed-number">{int(count)}</div>'
                f'<div class="small-muted">所选日期命中</div>'
                f'<div style="margin-top:8px;"><span class="metric-pill-fixed">趋势范围 {tcount}</span></div>'
                f'</div>'
            )
            col.markdown(html_card, unsafe_allow_html=True)

def render_focus_center(day_df: pd.DataFrame, trend_df: pd.DataFrame, journals_df: pd.DataFrame, focus_journals: list[str]) -> None:
    st.markdown('<div class="section-title">🎯 重点关注期刊</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">由用户在左侧自行选择。本功能用于当前浏览会话的个性化查看，不写入公共数据库。</div>', unsafe_allow_html=True)
    if not focus_journals:
        render_empty("你还没有设置重点关注期刊。请在左侧『重点关注期刊』中选择若干期刊。")
        return
    focus_day = day_df[day_df["journal_name"].isin(focus_journals)] if not day_df.empty else day_df
    focus_trend = trend_df[trend_df["journal_name"].isin(focus_journals)] if not trend_df.empty else trend_df
    render_journal_center(focus_day, focus_trend, journals_df[journals_df["journal_name"].isin(focus_journals)], focus_journals=focus_journals)
    st.markdown('<div class="section-title">📰 重点关注期刊的所选日期更新</div>', unsafe_allow_html=True)
    if focus_day.empty:
        render_empty("所选日期下，重点关注期刊暂无更新论文。")
    else:
        render_by_journal(focus_day, key_prefix="focus_journals")


def render_export_center(df: pd.DataFrame, selected_date: date) -> None:
    st.markdown('<div class="section-title">⬇️ 导出中心</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">导出当前筛选结果，适合导入 Zotero、EndNote、NoteExpress 或进一步整理。</div>', unsafe_allow_html=True)
    export_cols = [
        "first_seen_date", "publication_date", "journal_name", "priority", "title", "authors", "doi", "url",
        "fulltext_url", "source", "pmid", "topics", "matched_keywords", "study_type", "status",
        "favorite", "personal_tags", "user_notes", "abstract",
    ]
    export_df = df[[c for c in export_cols if c in df.columns]].copy() if not df.empty else pd.DataFrame(columns=export_cols)
    e1, e2, e3 = st.columns(3)
    e1.download_button("⬇️ 当前筛选 CSV", export_df.to_csv(index=False).encode("utf-8-sig"), file_name=f"journal_updates_{selected_date.isoformat()}.csv", mime="text/csv", use_container_width=True)
    e2.download_button("⬇️ 当前筛选 BibTeX", make_bibtex(df).encode("utf-8"), file_name=f"journal_updates_{selected_date.isoformat()}.bib", mime="text/plain", use_container_width=True)
    e3.download_button("⬇️ 当前筛选 RIS", make_ris(df).encode("utf-8"), file_name=f"journal_updates_{selected_date.isoformat()}.ris", mime="application/x-research-info-systems", use_container_width=True)
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("**导出说明**")
    st.markdown("- RIS：推荐用于 Zotero、EndNote、NoteExpress。")
    st.markdown("- BibTeX：适合 LaTeX 写作与文献库迁移。")
    st.markdown("- CSV：适合 Excel、进一步筛选和二次统计。")
    st.markdown("</div>", unsafe_allow_html=True)


def render_article_cards(df: pd.DataFrame, *, key_prefix: str) -> None:
    if df.empty:
        st.info("当前条件下暂无更新论文。")
        return
    for _, row in df.iterrows():
        render_article_card(row, key_prefix=key_prefix)


def render_by_journal(df: pd.DataFrame, *, key_prefix: str) -> None:
    if df.empty:
        st.info("当前条件下暂无更新论文。")
        return
    counts = df.groupby("journal_name").size().sort_values(ascending=False)
    for journal, count in counts.items():
        st.markdown(f'<div class="journal-section">📚 {esc(journal)} <span class="small-muted">{count} 篇</span></div>', unsafe_allow_html=True)
        render_article_cards(df[df["journal_name"] == journal], key_prefix=f"{key_prefix}_{re.sub(r'[^A-Za-z0-9]+','_',str(journal))}")


def render_by_topic(df: pd.DataFrame, *, key_prefix: str) -> None:
    if df.empty:
        st.info("当前条件下暂无更新论文。")
        return
    counts = topic_counts(df)
    for topic, count in counts.items():
        st.markdown(f'<div class="journal-section">🏷 {esc(topic)} <span class="small-muted">{int(count)} 篇</span></div>', unsafe_allow_html=True)
        if topic == "未命中专题":
            sub = df[df["topics"].fillna("").astype(str).str.strip() == ""]
        else:
            sub = df[df["topics"].fillna("").apply(lambda x: topic in _split_items(x))]
        render_article_cards(sub, key_prefix=f"{key_prefix}_{re.sub(r'[^A-Za-z0-9]+','_',str(topic))}")


journals_df = load_journals()
journal_names = journals_df["journal_name"].tolist() if not journals_df.empty else []

with st.sidebar:
    st.markdown('<div class="sidebar-title">📡 期刊监控</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-help">按日期、期刊与专题查看每日新增。统计口径为 first_seen_date，即系统首次发现日期。</div>', unsafe_allow_html=True)

    page = st.radio(
        "导航",
        ["🏠 首页总览", "📰 今日更新", "🗓 日期检索", "📚 期刊中心", "🎯 重点关注", "🏷 专题中心", "⬇️ 导出中心", "⭐ 阅读管理", "⚙️ 系统状态"],
        label_visibility="collapsed",
    )

    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = date.today()

    dc1, dc2, dc3 = st.columns(3)
    if dc1.button("← 前日", use_container_width=True):
        st.session_state.selected_date = st.session_state.selected_date - timedelta(days=1)
        st.rerun()
    if dc2.button("今天", use_container_width=True):
        st.session_state.selected_date = date.today()
        st.rerun()
    if dc3.button("后日 →", use_container_width=True):
        st.session_state.selected_date = st.session_state.selected_date + timedelta(days=1)
        st.rerun()

    selected_date = st.date_input("选择更新日期", key="selected_date", help="按系统首次发现日期查看当天更新论文。")
    lookback_days = st.slider("趋势统计范围", min_value=7, max_value=90, value=30, step=1)

    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">📚 期刊列表</div>', unsafe_allow_html=True)
    selected_day_raw = load_articles(selected_date.isoformat(), selected_date.isoformat())
    day_counts_by_journal = selected_day_raw.groupby("journal_name").size().to_dict() if not selected_day_raw.empty else {}
    journal_label_map: dict[str, str] = {"全部期刊": "全部期刊"}
    journal_options = ["全部期刊"]
    for name in journal_names:
        cnt = int(day_counts_by_journal.get(name, 0))
        label = f"{name}（{cnt}）"
        journal_options.append(label)
        journal_label_map[label] = name
    selected_journal_label = st.radio("点击期刊查看更新论文", journal_options, label_visibility="collapsed")
    selected_journal = journal_label_map.get(selected_journal_label, "全部期刊")

    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">🎯 重点关注期刊</div>', unsafe_allow_html=True)
    focus_journals = st.multiselect(
        "选择你重点关注的期刊",
        journal_names,
        default=st.session_state.get("focus_journals", []),
        placeholder="输入期刊名检索并选择",
        help="该选择只保存在当前浏览会话中，不会影响其他访问者。",
    )
    st.session_state.focus_journals = focus_journals
    focus_only = st.checkbox("仅显示重点关注期刊", value=False, disabled=(len(focus_journals) == 0))

    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">🔎 筛选器</div>', unsafe_allow_html=True)
    priorities = []
    all_topics = load_all_topics()
    selected_topics = st.multiselect("专题标签", all_topics, default=[])
    statuses = st.multiselect("阅读状态", READING_STATUS, default=[])
    keyword = st.text_input("关键词检索", placeholder="如 hypoxia / VO2max / recovery")
    favorites_only = st.checkbox("只看收藏", value=False)
    topic_only = st.checkbox("只看专题命中论文", value=False)

    if st.button("刷新看板缓存", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

trend_start = (date.today() - timedelta(days=lookback_days - 1)).isoformat()
trend_end = date.today().isoformat()
trend_raw = load_articles(trend_start, trend_end)
selected_raw = selected_day_raw

display_df = apply_filters(
    selected_raw,
    selected_journal=selected_journal,
    priorities=priorities,
    statuses=statuses,
    topics=selected_topics,
    keyword=keyword,
    favorites_only=favorites_only,
    topic_only=topic_only,
    focus_journals=focus_journals,
    focus_only=focus_only,
)

trend_filtered = apply_filters(
    trend_raw,
    selected_journal=selected_journal,
    priorities=priorities,
    statuses=[],
    topics=selected_topics,
    keyword="",
    favorites_only=False,
    topic_only=False,
    focus_journals=focus_journals,
    focus_only=focus_only,
)

today_df = load_articles(date.today().isoformat(), date.today().isoformat())
today_filtered = apply_filters(
    today_df,
    selected_journal=selected_journal,
    priorities=priorities,
    statuses=[],
    topics=selected_topics,
    keyword="",
    favorites_only=False,
    topic_only=False,
    focus_journals=focus_journals,
    focus_only=focus_only,
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-title">体育科学期刊更新情报平台</div>
      <div class="hero-subtitle">面向 Sport Sciences 相关期刊的每日论文更新监控系统。页面以系统首次发现日期为每日更新口径，支持按日期、期刊、专题浏览，并提供 RIS / BibTeX / CSV 引用导出。</div>
      <span class="hero-chip">🗓️ 日期情报</span>
      <span class="hero-chip">🏛️ 期刊中心</span>
      <span class="hero-chip">🧬 专题中心</span>
      <span class="hero-chip">📥 引用导出</span>
    </div>
    """,
    unsafe_allow_html=True,
)
render_product_tiles()

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    kpi("🆕", len(today_filtered), "今日更新", "今天首次发现并入库")
with k2:
    kpi("🗓", len(display_df), "所选日期更新", selected_date.isoformat())
with k3:
    kpi("📚", int(display_df["journal_name"].nunique()) if not display_df.empty else 0, "覆盖期刊", "当前筛选范围")
with k4:
    kpi("🏷", int(display_df["has_topic"].sum()) if not display_df.empty else 0, "专题命中", "基于关键词词库")
with k5:
    kpi("🎯", len(focus_journals), "重点关注", "当前会话自定义")

focus_note = f"｜重点关注 {len(focus_journals)} 本" if focus_journals else ""
st.caption(f"当前查看范围：{selected_date.isoformat()}｜{selected_journal}{focus_note}")

export_cols = [
    "first_seen_date", "publication_date", "journal_name", "priority", "title", "authors", "doi", "url",
    "fulltext_url", "source", "pmid", "topics", "matched_keywords", "study_type", "status",
    "favorite", "personal_tags", "user_notes", "abstract",
]
export_df = display_df[[c for c in export_cols if c in display_df.columns]].copy() if not display_df.empty else pd.DataFrame(columns=export_cols)

with st.expander("⬇️ 导出当前显示结果", expanded=False):
    d1, d2, d3 = st.columns(3)
    d1.download_button("CSV", export_df.to_csv(index=False).encode("utf-8-sig"), file_name=f"journal_updates_{selected_date.isoformat()}.csv", mime="text/csv", use_container_width=True)
    d2.download_button("BibTeX", make_bibtex(display_df).encode("utf-8"), file_name=f"journal_updates_{selected_date.isoformat()}.bib", mime="text/plain", use_container_width=True)
    d3.download_button("RIS", make_ris(display_df).encode("utf-8"), file_name=f"journal_updates_{selected_date.isoformat()}.ris", mime="application/x-research-info-systems", use_container_width=True)

if page == "🏠 首页总览":
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="section-title">📈 每日更新趋势</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">按系统首次发现日期统计，不含接口原始 fetched 条目。</div>', unsafe_allow_html=True)
        if trend_filtered.empty:
            render_empty("当前趋势范围暂无更新记录。")
        else:
            trend = trend_filtered.groupby("first_seen_date").size().reset_index(name="更新论文数").set_index("first_seen_date")
            light_bar_chart(trend, x_title="更新日期", y_title="更新论文数")
    with right:
        st.markdown('<div class="section-title">📚 所选日期期刊更新 Top 15</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">显示当前日期与筛选条件下更新最多的期刊。</div>', unsafe_allow_html=True)
        if display_df.empty:
            render_empty("所选日期暂无更新。")
        else:
            top_j = display_df.groupby("journal_name").size().sort_values(ascending=False).head(15)
            light_bar_chart(top_j, x_title="期刊", y_title="更新论文数")

    st.markdown('<div class="section-title">🧭 期刊活跃概览</div>', unsafe_allow_html=True)
    render_journal_center(display_df, trend_filtered, journals_df, focus_journals=focus_journals)
    st.markdown('<div class="section-title">📰 所选日期更新论文</div>', unsafe_allow_html=True)
    view_mode = st.radio("展示方式", ["卡片", "按期刊", "按主题"], horizontal=True, label_visibility="collapsed")
    if view_mode == "卡片":
        render_article_cards(display_df, key_prefix="home_cards")
    elif view_mode == "按期刊":
        render_by_journal(display_df, key_prefix="home_journal")
    else:
        render_by_topic(display_df, key_prefix="home_topic")

elif page == "📰 今日更新":
    st.markdown(f'<div class="section-title">📰 今日更新｜{date.today().isoformat()}</div>', unsafe_allow_html=True)
    today_view = today_filtered
    if today_view.empty:
        render_empty("今日暂无符合当前筛选条件的更新。")
    else:
        t1, t2, t3 = st.tabs(["全部卡片", "按期刊", "按主题"])
        with t1:
            render_article_cards(today_view, key_prefix="today_cards")
        with t2:
            render_by_journal(today_view, key_prefix="today_journal")
        with t3:
            render_by_topic(today_view, key_prefix="today_topic")

elif page == "🗓 日期检索":
    st.markdown(f'<div class="section-title">🗓 {selected_date.isoformat()} 更新论文</div>', unsafe_allow_html=True)
    st.caption("这里严格按 first_seen_date 统计，也就是系统首次发现并入库的日期。")
    t1, t2, t3 = st.tabs(["全部卡片", "按期刊", "按主题"])
    with t1:
        render_article_cards(display_df, key_prefix="date_cards")
    with t2:
        render_by_journal(display_df, key_prefix="date_journal")
    with t3:
        render_by_topic(display_df, key_prefix="date_topic")

elif page == "📚 期刊中心":
    render_journal_center(display_df, trend_filtered, journals_df, focus_journals=focus_journals)
    st.markdown('<div class="section-title">📚 当前选择期刊的更新论文</div>', unsafe_allow_html=True)
    if selected_journal == "全部期刊":
        st.info("可在左侧点击具体期刊，查看单本期刊在所选日期的更新论文。")
        render_by_journal(display_df, key_prefix="journal_center_all")
    else:
        render_article_cards(display_df, key_prefix="journal_center_cards")

elif page == "🎯 重点关注":
    render_focus_center(selected_raw, trend_raw, journals_df, focus_journals)

elif page == "🏷 专题中心":
    render_topic_center(display_df, trend_filtered)
    st.markdown(f'<div class="section-title">🏷 {selected_date.isoformat()} 专题论文</div>', unsafe_allow_html=True)
    if display_df.empty:
        render_empty("当前条件下暂无更新论文。")
    else:
        render_by_topic(display_df, key_prefix="topic_center")

elif page == "⬇️ 导出中心":
    render_export_center(display_df, selected_date)
    st.markdown('<div class="section-title">📦 当前可导出论文预览</div>', unsafe_allow_html=True)
    if display_df.empty:
        render_empty("当前筛选条件下暂无可导出论文。")
    else:
        st.dataframe(display_df[["first_seen_date", "publication_date", "journal_name", "title", "doi", "pmid", "topics"]], use_container_width=True, hide_index=True)

elif page == "⭐ 阅读管理":
    st.markdown('<div class="section-title">⭐ 收藏 / 待读 / 精读管理</div>', unsafe_allow_html=True)
    st.caption("公开部署版中，阅读状态、收藏和备注属于公共字段；多人使用时建议谨慎修改。")
    read_df = trend_raw[(trend_raw["favorite"] == 1) | (trend_raw["status"].isin(["待读", "阅读中", "精读", "已引用"]))].copy()
    read_df = apply_filters(read_df, selected_journal=selected_journal, priorities=priorities, statuses=statuses, topics=selected_topics, keyword=keyword, favorites_only=False, topic_only=False, focus_journals=focus_journals, focus_only=focus_only)
    if read_df.empty:
        render_empty("当前趋势范围内还没有收藏或待读/精读论文。")
    else:
        st.dataframe(read_df[["first_seen_date", "status", "favorite", "journal_name", "title", "topics", "personal_tags", "user_notes", "doi", "fulltext_url"]], use_container_width=True, hide_index=True)
        st.download_button("导出阅读管理清单 CSV", read_df.to_csv(index=False).encode("utf-8-sig"), file_name="journal_tracker_reading_list.csv", mime="text/csv")

elif page == "⚙️ 系统状态":
    st.markdown('<div class="section-title">⚙️ 系统状态</div>', unsafe_allow_html=True)
    st.caption("此页仅用于排查运行问题，不展示 fetched 次数。日常展示建议使用『首页总览』或『日期检索』。")
    st.info(f"最近运行时间：{load_last_run_time() or '暂无运行记录'}")
    errors = load_recent_errors(120)
    if errors.empty:
        st.success("最近未记录接口错误。")
    else:
        today_errors = errors[errors["run_date"] == date.today().isoformat()]
        if not today_errors.empty:
            st.warning(f"今日有 {len(today_errors)} 条接口错误记录，可能由网络或接口临时波动导致。")
        st.dataframe(errors, use_container_width=True, hide_index=True)
    log_path = ROOT / "logs" / "daily_run.log"
    with st.expander("查看本地日志末尾", expanded=False):
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8", errors="ignore")[-6000:]
            st.text_area("daily_run.log", text, height=260)
        else:
            st.info("尚未发现 logs/daily_run.log。")


with st.expander("专题词库说明", expanded=False):
    topic_path = CONFIG_DIR / "topic_keywords.json"
    if topic_path.exists():
        data = json.loads(topic_path.read_text(encoding="utf-8"))
        st.caption("专题分类基于关键词命中，不进行 AI 相关性评分。")
        st.json(data)
    else:
        st.warning("未找到 config/topic_keywords.json。")
