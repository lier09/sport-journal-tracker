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


def apply_filters(df: pd.DataFrame, *, selected_journal: str, priorities, statuses, topics, keyword, favorites_only, topic_only) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return out
    if selected_journal and selected_journal != "全部期刊":
        out = out[out["journal_name"] == selected_journal]
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
    meta_status = [
        "摘要✓" if row.get("has_abstract", False) else "摘要暂缺",
        "DOI✓" if row.get("has_doi", False) else "DOI暂缺",
        "PMID✓" if row.get("has_pmid", False) else "PMID暂缺",
        "链接✓" if row.get("has_link", False) else "链接暂缺",
    ]

    st.markdown('<div class="paper-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div>
          <span class="badge badge-blue">📚 {esc(journal)}</span>
          <span class="badge badge-green">🗓 更新：{esc(row.get('first_seen_date',''))}</span>
          <span class="badge badge-orange">📝 发表：{esc(row.get('publication_date','') or '日期暂缺')}</span>
          <span class="badge badge-purple">🏷 {_topic_label(topics)}</span>
        </div>
        <div class="card-title">{esc(star)} {esc(title)}</div>
        <div class="card-meta">{esc(row.get('authors','') or '作者未获取')}</div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("展开详情 / 摘要 / 下载引用"):
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"**期刊**：{esc(journal)}")
        c2.markdown(f"**首次发现**：{esc(row.get('first_seen_date',''))}")
        c3.markdown(f"**发表日期**：{esc(row.get('publication_date','') or '暂缺')}")
        c4.markdown(f"**来源**：{esc(source)}")
        st.markdown(f"**专题标签**：{esc(topics or '未命中专题词库')}")
        st.markdown(f"**命中关键词**：{esc(row.get('matched_keywords','') or '无')}")
        st.markdown(f"**研究类型**：{esc(row.get('study_type','') or '未识别')}")
        st.markdown("**元数据状态**：" + " ｜ ".join(meta_status))
        st.markdown("**摘要**")
        abstract = str(row.get("abstract", "") or "").strip()
        if abstract:
            st.markdown(f'<div class="card-abstract">{esc(abstract)}</div>', unsafe_allow_html=True)
        else:
            st.info("摘要暂缺：当前入库来源未提供摘要，或该文献尚未进行摘要补全。可通过 DOI / PubMed / 原文链接查看。")

        render_links(row)
        st.markdown("**下载引用**")
        one_df = pd.DataFrame([row])
        d1, d2, d3 = st.columns(3)
        fname = _safe_filename(title)
        d1.download_button(
            "⬇️ 本篇 RIS",
            make_ris(one_df).encode("utf-8"),
            file_name=f"{fname}.ris",
            mime="application/x-research-info-systems",
            use_container_width=True,
            key=f"{key_prefix}_ris_{article_id}",
        )
        d2.download_button(
            "⬇️ 本篇 BibTeX",
            make_bibtex(one_df).encode("utf-8"),
            file_name=f"{fname}.bib",
            mime="text/plain",
            use_container_width=True,
            key=f"{key_prefix}_bib_{article_id}",
        )
        if row.get("doi"):
            d3.link_button("🌐 DOI 引用页", _doi_link(row.get("doi", "")), use_container_width=True)

        st.divider()
        st.markdown("**阅读管理**")
        s_col, f_col = st.columns([2, 1])
        current_status = row.get("status", "未读") if row.get("status", "未读") in READING_STATUS else "未读"
        new_status = s_col.selectbox("阅读状态", READING_STATUS, index=READING_STATUS.index(current_status), key=f"{key_prefix}_status_{article_id}")
        new_fav = f_col.checkbox("收藏", value=bool(row.get("favorite", 0)), key=f"{key_prefix}_fav_{article_id}")
        new_tags = st.text_input("个人标签", value=str(row.get("personal_tags", "") or ""), key=f"{key_prefix}_tags_{article_id}", placeholder="如：低氧训练；可用于讨论；精读")
        new_notes = st.text_area("个人备注", value=str(row.get("user_notes", "") or ""), key=f"{key_prefix}_notes_{article_id}", height=80)
        if st.button("保存阅读信息", key=f"{key_prefix}_save_{article_id}"):
            with connect(DB_PATH) as con:
                update_article_user_fields(
                    con,
                    article_id,
                    status=new_status,
                    favorite=1 if new_fav else 0,
                    user_notes=new_notes,
                    personal_tags=new_tags,
                )
            st.success("已保存。")
            st.cache_data.clear()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


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
    st.markdown('<div class="sidebar-help">按日期与期刊查看每日新增。统计口径为 first_seen_date，即系统首次发现日期。</div>', unsafe_allow_html=True)
    page = st.radio("导航", ["🏠 总览", "🗓 按日期查看", "🏷 按主题查看", "⭐ 阅读管理", "⚙️ 系统状态"], label_visibility="collapsed")
    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
    selected_date = st.date_input("选择更新日期", value=date.today(), help="按系统首次发现日期查看当天更新论文。")
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
    priorities = st.multiselect("期刊优先级", ["S", "A", "B", "C"], default=["S", "A", "B", "C"])
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
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-title">体育科学期刊更新监控看板</div>
      <div class="hero-subtitle">每天自动汇聚 Sport Sciences 相关期刊更新，按日期、期刊与专题进行卡片化展示。系统展示的是去重后的入库更新记录，不展示接口 fetched 次数，避免造成原始抓取量与论文更新量混淆。</div>
      <span class="hero-chip">📅 日期选择</span>
      <span class="hero-chip">📚 期刊导航</span>
      <span class="hero-chip">🏷 专题分类</span>
      <span class="hero-chip">⬇️ RIS / BibTeX 下载</span>
    </div>
    """,
    unsafe_allow_html=True,
)

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
    kpi("⭐", int(display_df["favorite"].sum()) if not display_df.empty else 0, "收藏", "当前筛选范围")

st.caption(f"当前查看范围：{selected_date.isoformat()}｜{selected_journal}")

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

if page == "🏠 总览":
    left, right = st.columns([1.25, 1])
    with left:
        st.markdown('<div class="section-title">📈 每日更新趋势</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">按系统首次发现日期统计，不含接口原始 fetched 条目。</div>', unsafe_allow_html=True)
        if trend_filtered.empty:
            st.info("当前趋势范围暂无更新记录。")
        else:
            trend = trend_filtered.groupby("first_seen_date").size().reset_index(name="更新论文数").set_index("first_seen_date")
            light_bar_chart(trend, x_title="更新日期", y_title="更新论文数")
    with right:
        st.markdown('<div class="section-title">📚 所选日期期刊更新</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">显示当前日期与筛选条件下更新最多的期刊。</div>', unsafe_allow_html=True)
        if display_df.empty:
            st.info("所选日期暂无更新。")
        else:
            top_j = display_df.groupby("journal_name").size().sort_values(ascending=False).head(15)
            light_bar_chart(top_j, x_title="期刊", y_title="更新论文数")

    st.markdown('<div class="section-title">📰 所选日期更新论文</div>', unsafe_allow_html=True)
    view_mode = st.radio("展示方式", ["卡片", "按期刊", "按主题"], horizontal=True, label_visibility="collapsed")
    if view_mode == "卡片":
        render_article_cards(display_df, key_prefix="overview_cards")
    elif view_mode == "按期刊":
        render_by_journal(display_df, key_prefix="overview_journal")
    else:
        render_by_topic(display_df, key_prefix="overview_topic")

elif page == "🗓 按日期查看":
    st.markdown(f'<div class="section-title">🗓 {selected_date.isoformat()} 更新论文</div>', unsafe_allow_html=True)
    st.caption("这里严格按 first_seen_date 统计，也就是系统首次发现并入库的日期。")
    t1, t2, t3 = st.tabs(["全部卡片", "按期刊", "按主题"])
    with t1:
        render_article_cards(display_df, key_prefix="date_cards")
    with t2:
        render_by_journal(display_df, key_prefix="date_journal")
    with t3:
        render_by_topic(display_df, key_prefix="date_topic")

elif page == "🏷 按主题查看":
    st.markdown(f'<div class="section-title">🏷 {selected_date.isoformat()} 按专题查看</div>', unsafe_allow_html=True)
    st.caption("专题来自关键词词库命中，不使用 AI 相关性评分。")
    if display_df.empty:
        st.info("当前条件下暂无更新论文。")
    else:
        counts = topic_counts(display_df)
        light_bar_chart(counts, x_title="专题", y_title="论文数")
        render_by_topic(display_df, key_prefix="topic_page")

elif page == "⭐ 阅读管理":
    st.markdown('<div class="section-title">⭐ 收藏 / 待读 / 精读管理</div>', unsafe_allow_html=True)
    read_df = trend_raw[(trend_raw["favorite"] == 1) | (trend_raw["status"].isin(["待读", "阅读中", "精读", "已引用"]))].copy()
    read_df = apply_filters(
        read_df,
        selected_journal=selected_journal,
        priorities=priorities,
        statuses=statuses,
        topics=selected_topics,
        keyword=keyword,
        favorites_only=False,
        topic_only=False,
    )
    if read_df.empty:
        st.info("当前趋势范围内还没有收藏或待读/精读论文。")
    else:
        st.dataframe(
            read_df[["first_seen_date", "status", "favorite", "journal_name", "title", "topics", "personal_tags", "user_notes", "doi", "fulltext_url"]],
            use_container_width=True,
            hide_index=True,
        )
        st.download_button("导出阅读管理清单 CSV", read_df.to_csv(index=False).encode("utf-8-sig"), file_name="journal_tracker_reading_list.csv", mime="text/csv")

elif page == "⚙️ 系统状态":
    st.markdown('<div class="section-title">⚙️ 系统状态</div>', unsafe_allow_html=True)
    st.caption("此页仅用于排查运行问题，不展示 fetched 次数。日常展示建议使用『总览』或『按日期查看』。")
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
