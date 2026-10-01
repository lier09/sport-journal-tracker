from __future__ import annotations

import html
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.config import CONFIG_DIR, DB_PATH, ROOT, load_journals
from src.coverage_audit import load_registry
from src.database import connect, init_db, load_journals_to_db
from src.user_state import article_key as make_article_key, load_states, save_state

st.set_page_config(
    page_title="体育科学期刊更新监控看板",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)
@st.cache_resource
def initialize_dashboard_database() -> None:
    init_db(DB_PATH)
    with connect(DB_PATH) as con:
        load_journals_to_db(con, load_journals())


initialize_dashboard_database()

READING_STATUS = ["未读", "待读", "阅读中", "已读", "精读", "已引用", "不相关"]
PRIVATE_READING_MODE = os.environ.get("APP_PRIVATE_MODE", "").strip() == "1"

st.markdown(
    """
<style>
:root {
  --ink:#182b3b; --muted:#526270; --line:#d9e1e7; --paper:#ffffff;
  --canvas:#f3f6f8; --navy:#21445d; --blue:#2b6f91; --soft:#eaf1f5;
  --green:#176b52; --amber:#815a13; --purple:#63547a;
}
html, body, [class*="css"] { font-family:"Segoe UI","Microsoft YaHei",Arial,sans-serif; }
.stApp { background:var(--canvas); color:var(--ink); }
.block-container { max-width:1320px; padding-top:1.35rem; padding-bottom:3rem; }
[data-testid="stSidebar"] { background:#edf2f5; border-right:1px solid var(--line); }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:var(--muted); }
[data-testid="stHeader"] { background:rgba(243,246,248,.94); }
.hero { background:var(--paper); border:1px solid var(--line); border-left:5px solid var(--navy); border-radius:12px; padding:22px 26px; margin:0 0 18px; box-shadow:0 2px 10px rgba(24,43,59,.035); }
.hero-title { font-size:1.8rem; line-height:1.25; font-weight:750; letter-spacing:-.02em; color:var(--ink); margin:0 0 7px; }
.hero-subtitle { font-size:.96rem; color:var(--muted); line-height:1.65; max-width:880px; }
.hero-chip { display:none; }
.kpi-card { height:100%; min-height:100px; background:var(--paper); border:1px solid var(--line); border-radius:10px; padding:15px 17px; box-shadow:none; }
.kpi-icon { display:none; }
.kpi-value { font-size:1.75rem; font-weight:760; letter-spacing:-.03em; color:var(--navy); line-height:1.1; }
.kpi-label { font-size:.9rem; color:var(--ink); margin-top:8px; font-weight:650; }
.kpi-note,.small-muted { font-size:.78rem; color:var(--muted); line-height:1.5; }
.section-title { font-size:1.12rem; font-weight:720; margin:1.25rem 0 .45rem; color:var(--ink); }
.section-subtitle { font-size:.88rem; color:var(--muted); margin:0 0 .75rem; line-height:1.55; }
.paper-card { background:var(--paper); border:1px solid var(--line); border-radius:12px; padding:16px 19px; margin:12px 0; box-shadow:0 2px 8px rgba(24,43,59,.035); }
.paper-card:hover { border-color:#9bb1bf; box-shadow:0 4px 14px rgba(24,43,59,.07); }
.paper-topline { display:flex; flex-wrap:wrap; align-items:center; gap:6px; margin-bottom:6px; }
.badge { display:inline-flex; align-items:center; border-radius:5px; padding:4px 8px; font-size:.75rem; font-weight:600; border:1px solid var(--line); background:#f5f8fa; color:#405767; }
.badge-blue { background:#edf4f8; color:#244e67; border-color:#d0e0e8; }
.badge-green { background:#edf6f2; color:var(--green); border-color:#d2e9df; }
.badge-orange { background:#faf4e8; color:var(--amber); border-color:#eee0bd; }
.badge-purple { background:#f4f1f7; color:var(--purple); border-color:#e2dbea; }
.badge-pending { background:#f5f6f7; color:var(--muted); }
.card-title { font-size:1.03rem; font-weight:700; line-height:1.5; color:var(--ink); margin:8px 0 5px; }
.card-meta { font-size:.83rem; color:var(--muted); line-height:1.55; }
.card-preview { font-size:.91rem; color:#2d3e4b; line-height:1.62; margin-top:8px; }
.card-abstract { border-left:3px solid #8ca9ba; background:#f5f8fa; border-radius:0 8px 8px 0; padding:12px 15px; line-height:1.7; color:#243845; }
.detail-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:8px; margin:8px 0; }
.detail-cell { background:#f5f8fa; border:1px solid var(--line); border-radius:8px; padding:9px 11px; }
.detail-label { color:var(--muted); font-size:.76rem; margin-bottom:3px; }
.detail-value { color:var(--ink); font-size:.86rem; overflow-wrap:anywhere; }
.sidebar-title { font-size:1rem; font-weight:720; color:var(--ink); margin:.35rem 0; }
.sidebar-help { font-size:.82rem; color:var(--muted); line-height:1.5; }
.soft-divider { height:1px; background:var(--line); margin:14px 0; }
.empty-state { background:var(--paper); border:1px dashed #bbc9d2; border-radius:10px; padding:20px; color:var(--muted); }
.journal-section { border-bottom:1px solid var(--line); padding:10px 0 6px; margin-top:8px; color:var(--navy); font-weight:700; }
.journal-card-fixed,.topic-card-fixed,.dashboard-card { background:var(--paper); border:1px solid var(--line); border-radius:10px; padding:13px 15px; margin:7px 0; }
.journal-card-fixed-title,.topic-card-fixed-title { color:var(--ink); font-weight:680; line-height:1.45; }
.metric-row-fixed { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
.metric-pill-fixed,.focus-pill-fixed { display:inline-flex; align-items:center; padding:4px 8px; border:1px solid var(--line); border-radius:5px; background:#f5f8fa; color:#405767; font-size:.76rem; font-weight:600; }
.focus-pill-fixed { background:#fbf5e9; color:var(--amber); border-color:#eee0bd; }
.topic-card-fixed-number { font-size:1.7rem; font-weight:750; color:var(--navy); }
button, [role="button"], input, textarea { border-radius:7px !important; }
:focus-visible { outline:3px solid #2b6f91 !important; outline-offset:2px !important; }
@media (max-width:768px) {
  .block-container { padding:1rem .8rem 2rem; }
  .hero { padding:17px 18px; }
  .hero-title { font-size:1.45rem; }
  .paper-card { padding:14px; }
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
            SELECT journal_name, priority, domain, frequency, issn, eissn, rss_url, active,
                   collection_group, collection_mode, scope_keywords
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
            SELECT a.article_id, a.title_hash, a.first_seen_date, a.publication_date, a.journal_name, j.priority,
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
        journal_catalog = pd.read_sql_query("SELECT journal_name FROM journals", con)
    if df.empty:
        return normalize_article_df(df)
    df = df.copy()
    canonical_journals = {
        re.sub(r"[^a-z0-9]+", "", str(name).casefold()): str(name)
        for name in journal_catalog["journal_name"].dropna().tolist()
    }
    df["journal_name"] = df["journal_name"].map(
        lambda name: canonical_journals.get(
            re.sub(r"[^a-z0-9]+", "", str(name).casefold()), name
        )
    )
    if PRIVATE_READING_MODE:
        keys = [
            make_article_key(doi=r.doi, title_hash=r.title_hash, journal_name=r.journal_name)
            for r in df.itertuples(index=False)
        ]
        state_by_key = load_states(keys)
        states = [state_by_key.get(key, {}) for key in keys]
        df["status"] = [s.get("status", "未读") for s in states]
        df["favorite"] = [s.get("favorite", 0) for s in states]
        df["user_notes"] = [s.get("user_notes", "") for s in states]
        df["personal_tags"] = [s.get("personal_tags", "") for s in states]
    else:
        # Public deployments never read or write personal fields in the shared database.
        df["status"] = "未读"
        df["favorite"] = 0
        df["user_notes"] = ""
        df["personal_tags"] = ""
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
            if not PRIVATE_READING_MODE:
                st.info("公开看板为只读模式。阅读状态、收藏和备注仅在本机版保存，避免进入共享数据库。")
            else:
                st.caption("阅读信息仅保存到本机 private_reading_state.sqlite3，不会随公开数据库同步。")
                current_status = row.get("status", "未读") if row.get("status", "未读") in READING_STATUS else "未读"
                with st.form(f"{key_prefix}_reading_form_{article_id}"):
                    s_col, f_col = st.columns([2, 1])
                    new_status = s_col.selectbox("阅读状态", READING_STATUS, index=READING_STATUS.index(current_status), key=f"{key_prefix}_status_{article_id}")
                    new_fav = f_col.checkbox("收藏", value=bool(row.get("favorite", 0)), key=f"{key_prefix}_fav_{article_id}")
                    new_tags = st.text_input("个人标签", value=str(row.get("personal_tags", "") or ""), key=f"{key_prefix}_tags_{article_id}", placeholder="如：低氧训练；可用于讨论；精读")
                    new_notes = st.text_area("个人备注", value=str(row.get("user_notes", "") or ""), key=f"{key_prefix}_notes_{article_id}", height=80)
                    save_reading = st.form_submit_button("保存到本机", type="primary")
                if save_reading:
                    save_state(
                        article_key_value=make_article_key(doi=row.get("doi", ""), title_hash=row.get("title_hash", ""), journal_name=journal),
                        status=new_status,
                        favorite=new_fav,
                        user_notes=new_notes,
                        personal_tags=new_tags,
                    )
                    st.success("已保存到本机。")
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
        "fulltext_url", "source", "pmid", "topics", "matched_keywords", "study_type", "abstract",
    ]
    if PRIVATE_READING_MODE:
        export_cols += ["status", "favorite", "personal_tags", "user_notes"]
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
    page_size = 12
    page_key = f"article_page_{key_prefix}"
    page_count = max(1, (len(df) + page_size - 1) // page_size)
    page = min(max(int(st.session_state.get(page_key, 0)), 0), page_count - 1)
    st.session_state[page_key] = page
    st.caption(f"共 {len(df)} 篇 · 第 {page + 1}/{page_count} 页 · 每页 {page_size} 篇")
    if page_count > 1:
        prev_col, page_col, next_col = st.columns([1, 2, 1])
        if prev_col.button("上一页", key=f"{page_key}_prev", disabled=page == 0, use_container_width=True):
            st.session_state[page_key] = page - 1
            st.rerun()
        page_col.markdown(f"<div style='text-align:center;padding:.45rem'>第 {page + 1} 页 / 共 {page_count} 页</div>", unsafe_allow_html=True)
        if next_col.button("下一页", key=f"{page_key}_next", disabled=page >= page_count - 1, use_container_width=True):
            st.session_state[page_key] = page + 1
            st.rerun()
    start = page * page_size
    for _, row in df.iloc[start:start + page_size].iterrows():
        render_article_card(row, key_prefix=key_prefix)


def render_journal_library(journals_df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">期刊库</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">按研究方向浏览追踪目录。专门运动期刊按刊检索；跨学科期刊用题名/摘要关键词限制范围。S/A/B/C 是项目内关注级别，不代表 JCR 分区。</div>',
        unsafe_allow_html=True,
    )
    if journals_df.empty:
        render_empty("期刊目录为空。")
        return
    groups = sorted(x for x in journals_df.get("collection_group", pd.Series(dtype=str)).fillna("").unique() if x)
    f1, f2 = st.columns([1, 2])
    selected_group = f1.selectbox("研究方向", ["全部方向"] + groups)
    search = f2.text_input("搜索期刊", placeholder="输入期刊名或研究领域")
    view = journals_df.copy()
    if selected_group != "全部方向":
        view = view[view["collection_group"] == selected_group]
    if search.strip():
        needle = re.escape(search.strip().casefold())
        mask = (
            view["journal_name"].fillna("").str.casefold().str.contains(needle, na=False)
            | view["domain"].fillna("").str.casefold().str.contains(needle, na=False)
            | view.get("collection_group", pd.Series("", index=view.index)).fillna("").str.casefold().str.contains(needle, na=False)
        )
        view = view[mask]
    registry = load_registry()
    if not registry.empty and "journal_name" in registry:
        coverage = registry.set_index("journal_name").to_dict("index")
    else:
        coverage = {}
    out = view.copy()
    out["来源状态"] = out["journal_name"].map(
        lambda name: "已核验出版社源" if str(coverage.get(name, {}).get("official_source_verified", "")).casefold() in {"yes", "true", "1"}
        else "待核验；Crossref/PubMed 兜底"
    )
    out["抓取策略"] = out.get("collection_mode", pd.Series("journal_all", index=out.index)).map(
        lambda value: "运动相关条目筛选" if value == "keyword_filter" else "按刊检索"
    )
    show_cols = ["journal_name", "collection_group", "domain", "priority", "issn", "eissn", "抓取策略", "来源状态"]
    labels = {"journal_name": "期刊", "collection_group": "研究方向", "domain": "细分主题", "priority": "关注级别", "issn": "ISSN", "eissn": "eISSN"}
    st.caption(f"显示 {len(out)} / {len(journals_df)} 本期刊")
    st.dataframe(out[[c for c in show_cols if c in out.columns]].rename(columns=labels), use_container_width=True, hide_index=True)
    verified = int(out["来源状态"].eq("已核验出版社源").sum())
    st.caption(f"当前筛选范围：{verified} 本已有核验出版社源，其余暂用 Crossref / PubMed，并标记为待核验。")


def render_by_journal(df: pd.DataFrame, *, key_prefix: str) -> None:
    if df.empty:
        st.info("当前条件下暂无更新论文。")
        return
    counts = df.groupby("journal_name").size().sort_values(ascending=False)
    labels = {f"{name} · {int(count)} 篇": name for name, count in counts.items()}
    selected = st.selectbox("选择期刊", list(labels), key=f"{key_prefix}_journal_choice", label_visibility="collapsed")
    journal = labels[selected]
    render_article_cards(df[df["journal_name"] == journal], key_prefix=f"{key_prefix}_{re.sub(r'[^A-Za-z0-9]+','_',str(journal))}")


def render_by_topic(df: pd.DataFrame, *, key_prefix: str) -> None:
    if df.empty:
        st.info("当前条件下暂无更新论文。")
        return
    counts = topic_counts(df)
    labels = {f"{topic} · {int(count)} 篇": topic for topic, count in counts.items()}
    selected = st.selectbox("选择专题", list(labels), key=f"{key_prefix}_topic_choice", label_visibility="collapsed")
    topic = labels[selected]
    if topic == "未命中专题":
        sub = df[df["topics"].fillna("").astype(str).str.strip() == ""]
    else:
        sub = df[df["topics"].fillna("").apply(lambda x: topic in _split_items(x))]
    render_article_cards(sub, key_prefix=f"{key_prefix}_{re.sub(r'[^A-Za-z0-9]+','_',str(topic))}")


journals_df = load_journals()
journal_names = journals_df["journal_name"].tolist() if not journals_df.empty else []

with st.sidebar:
    st.markdown('<div class="sidebar-title">体育科学文献台</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-help">按首次收录日期浏览文献。首次收录日期不同于期刊正式发表日期。</div>', unsafe_allow_html=True)

    page = st.radio(
        "导航",
        ["文献流", "今日文献", "日期检索", "期刊库", "重点期刊", "专题", "导出", "阅读队列", "数据源状态"],
        label_visibility="collapsed",
    )

    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = date.today()
    date_cols = st.columns(3)
    if date_cols[0].button("前一天", key="date_prev", use_container_width=True):
        st.session_state.selected_date = st.session_state.selected_date - timedelta(days=1)
        st.rerun()
    if date_cols[1].button("今天", key="date_today", use_container_width=True):
        st.session_state.selected_date = date.today()
        st.rerun()
    if date_cols[2].button("后一天", key="date_next", use_container_width=True):
        st.session_state.selected_date = st.session_state.selected_date + timedelta(days=1)
        st.rerun()

    selected_date = st.date_input("首次收录日期", key="selected_date")
    lookback_days = st.slider("趋势范围（天）", min_value=7, max_value=90, value=30, step=1)
    selected_day_raw = load_articles(selected_date.isoformat(), selected_date.isoformat())
    day_counts_by_journal = selected_day_raw.groupby("journal_name").size().to_dict() if not selected_day_raw.empty else {}
    journal_options = ["全部期刊"] + [
        f"{name} · {int(day_counts_by_journal.get(name, 0))} 篇"
        for name in journal_names
    ]
    journal_label_map = {"全部期刊": "全部期刊"}
    journal_label_map.update({label: label.rsplit(" · ", 1)[0] for label in journal_options[1:]})
    selected_journal_label = st.selectbox(
        "期刊（可输入名称搜索）", journal_options, key="selected_journal_label"
    )
    selected_journal = journal_label_map[selected_journal_label]

    with st.expander("更多筛选", expanded=False):
        focus_journals = st.multiselect(
            "重点期刊",
            journal_names,
            default=st.session_state.get("focus_journals", []),
            placeholder="搜索并选择期刊",
        )
        st.session_state.focus_journals = focus_journals
        focus_only = st.checkbox("只看重点期刊", value=False, disabled=(len(focus_journals) == 0))
        all_topics = load_all_topics()
        selected_topics = st.multiselect("专题标签", all_topics, default=[])
        priorities = st.multiselect("关注等级（S/A/B/C）", ["S", "A", "B", "C"], default=[])
        if PRIVATE_READING_MODE:
            statuses = st.multiselect("阅读状态", READING_STATUS, default=[])
            favorites_only = st.checkbox("只看收藏", value=False)
        else:
            statuses = []
            favorites_only = False
            st.caption("个人阅读状态仅在本机版可用。")
        keyword = st.text_input("检索题名、摘要、作者", placeholder="如 hypoxia / VO2max / recovery")
        topic_only = st.checkbox("只看专题命中文献", value=False)

    if st.button("刷新数据", use_container_width=True):
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
      <div class="hero-title">运动科学文献台</div>
      <div class="hero-subtitle">把训练、教练、运动表现、特殊环境、营养与恢复研究放进一个可筛选的阅读流。日期按系统首次收录统计；正式发表日期单独展示。</div>
    </div>
    """,
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi("", len(today_filtered), "今日首次收录", "系统今天新发现")
with k2:
    kpi("", len(display_df), "所选日期收录", selected_date.isoformat())
with k3:
    kpi("", len(journals_df), "追踪期刊", "核心目录 + 跨领域扩展")
with k4:
    kpi("", int(display_df["has_topic"].sum()) if not display_df.empty else 0, "专题命中", "透明关键词筛选")

focus_note = f" · 重点关注 {len(focus_journals)} 本" if focus_journals else ""
st.caption(f"当前视图：{selected_date.isoformat()} · {selected_journal}{focus_note}")

export_cols = [
    "first_seen_date", "publication_date", "journal_name", "priority", "title", "authors", "doi", "url",
    "fulltext_url", "source", "pmid", "topics", "matched_keywords", "study_type", "abstract",
]
if PRIVATE_READING_MODE:
    export_cols += ["status", "favorite", "personal_tags", "user_notes"]
export_df = display_df[[c for c in export_cols if c in display_df.columns]].copy() if not display_df.empty else pd.DataFrame(columns=export_cols)

with st.expander("⬇️ 导出当前显示结果", expanded=False):
    d1, d2, d3 = st.columns(3)
    d1.download_button("CSV", export_df.to_csv(index=False).encode("utf-8-sig"), file_name=f"journal_updates_{selected_date.isoformat()}.csv", mime="text/csv", use_container_width=True)
    d2.download_button("BibTeX", make_bibtex(display_df).encode("utf-8"), file_name=f"journal_updates_{selected_date.isoformat()}.bib", mime="text/plain", use_container_width=True)
    d3.download_button("RIS", make_ris(display_df).encode("utf-8"), file_name=f"journal_updates_{selected_date.isoformat()}.ris", mime="application/x-research-info-systems", use_container_width=True)

if page == "文献流":
    st.markdown('<div class="section-title">所选日期的文献</div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["阅读列表", "按期刊", "按专题"])
    with t1:
        render_article_cards(display_df, key_prefix="stream_cards")
    with t2:
        render_by_journal(display_df, key_prefix="stream_journal")
    with t3:
        render_by_topic(display_df, key_prefix="stream_topic")
    with st.expander("查看近期更新趋势", expanded=False):
        if trend_filtered.empty:
            render_empty("当前范围暂无趋势数据。")
        else:
            trend = trend_filtered.groupby("first_seen_date").size().reset_index(name="入库记录数").set_index("first_seen_date")
            light_bar_chart(trend, x_title="首次收录日期", y_title="新增记录")
elif page == "今日文献":
    st.markdown(f'<div class="section-title">今日首次收录 · {date.today().isoformat()}</div>', unsafe_allow_html=True)
    render_article_cards(today_filtered, key_prefix="today_cards")
elif page == "日期检索":
    st.markdown(f'<div class="section-title">首次收录于 {selected_date.isoformat()} 的文献</div>', unsafe_allow_html=True)
    st.caption("首次收录日期表示系统第一次抓到该记录，不等同于期刊正式发表日期。")
    render_article_cards(display_df, key_prefix="date_cards")
elif page == "期刊库":
    render_journal_library(journals_df)
    if selected_journal != "全部期刊":
        selected_journal_articles = display_df[display_df["journal_name"] == selected_journal] if not display_df.empty else display_df
        st.markdown(f'<div class="section-title">{esc(selected_journal)} · {selected_date.isoformat()}</div>', unsafe_allow_html=True)
        render_article_cards(selected_journal_articles, key_prefix="journal_library_articles")
elif page == "重点期刊":
    if not focus_journals:
        render_empty("在左侧筛选中选择需要重点关注的期刊。")
    else:
        focus_rows = journals_df[journals_df["journal_name"].isin(focus_journals)]
        render_journal_library(focus_rows)
        focus_articles = display_df[display_df["journal_name"].isin(focus_journals)] if not display_df.empty else display_df
        render_article_cards(focus_articles, key_prefix="focus_articles")
elif page == "专题":
    render_topic_center(display_df, trend_filtered)
    st.markdown(f'<div class="section-title">{selected_date.isoformat()} 专题文献</div>', unsafe_allow_html=True)
    render_by_topic(display_df, key_prefix="topic_center")
elif page == "导出":
    render_export_center(display_df, selected_date)
    st.markdown('<div class="section-title">当前筛选的记录</div>', unsafe_allow_html=True)
    preview_cols = [c for c in ["publication_date", "journal_name", "title", "doi", "pmid", "topics"] if c in display_df.columns]
    st.dataframe(display_df[preview_cols].head(100), use_container_width=True, hide_index=True)
elif page == "阅读队列":
    st.markdown('<div class="section-title">本机阅读队列</div>', unsafe_allow_html=True)
    if not PRIVATE_READING_MODE:
        st.info("公开看板不保存个人阅读信息。运行本机版后，可在每篇文献的详情中保存状态、收藏与备注。")
    else:
        read_df = trend_raw[(trend_raw["favorite"] == 1) | (trend_raw["status"].isin(["待读", "阅读中", "精读", "已引用"]))].copy()
        read_df = apply_filters(read_df, selected_journal=selected_journal, priorities=priorities, statuses=statuses, topics=selected_topics, keyword=keyword, favorites_only=False, topic_only=False, focus_journals=focus_journals, focus_only=focus_only)
        if read_df.empty:
            render_empty("当前趋势范围内还没有收藏或待读/精读文献。")
        else:
            read_cols = [c for c in ["first_seen_date", "status", "favorite", "journal_name", "title", "topics", "personal_tags", "user_notes", "doi", "fulltext_url"] if c in read_df.columns]
            st.dataframe(read_df[read_cols], use_container_width=True, hide_index=True)
            st.download_button("导出阅读队列 CSV", read_df[read_cols].to_csv(index=False).encode("utf-8-sig"), file_name="journal_tracker_reading_list.csv", mime="text/csv")
elif page == "数据源状态":
    st.markdown('<div class="section-title">目录覆盖与数据源</div>', unsafe_allow_html=True)
    registry = load_registry()
    verified_names = set(registry.loc[registry.get("official_source_verified", pd.Series(index=registry.index, dtype=str)).astype(str).str.casefold().isin(["yes", "true", "1"]), "journal_name"].astype(str)) if not registry.empty else set()
    c1, c2, c3 = st.columns(3)
    c1.metric("目录期刊", len(journals_df))
    c2.metric("已核验出版社源", len(verified_names))
    c3.metric("待核验来源", max(0, len(journals_df) - len(verified_names)))
    st.caption("新增扩展期刊先通过 Crossref / PubMed 按刊检索；出版社 RSS 或 API 仍需逐刊验证。")
    st.info(f"最近抓取记录：{load_last_run_time() or '暂无'}")
    if not registry.empty:
        view_cols = [c for c in ["journal_name", "collection_group", "coverage_status", "official_source_verified", "next_action"] if c in registry.columns]
        st.dataframe(registry[view_cols], use_container_width=True, hide_index=True)
    errors = load_recent_errors(120)
    if errors.empty:
        st.success("最近没有记录到抓取失败。")
    else:
        st.warning(f"最近有 {len(errors)} 条抓取失败记录。")
        st.dataframe(errors, use_container_width=True, hide_index=True)
    log_path = ROOT / "logs" / "daily_run.log"
    with st.expander("查看本地日志末尾", expanded=False):
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8", errors="ignore")[-6000:]
            st.text_area("daily_run.log", log_text, height=260)
        else:
            st.caption("此部署未提供本地运行日志。")

with st.expander("专题词库说明", expanded=False):
    topic_path = CONFIG_DIR / "topic_keywords.json"
    if topic_path.exists():
        data = json.loads(topic_path.read_text(encoding="utf-8"))
        st.caption("专题分类基于关键词命中，不进行 AI 相关性评分。")
        st.json(data)
    else:
        st.warning("未找到 config/topic_keywords.json。")
