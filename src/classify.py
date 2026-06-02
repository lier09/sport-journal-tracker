from __future__ import annotations

import re
from typing import Any

from .config import load_topic_keywords

STUDY_PATTERNS = {
    "系统综述/Meta分析": ["systematic review", "meta-analysis", "meta analysis", "prisma"],
    "综述/共识/指南": ["review", "consensus", "position stand", "guideline", "statement"],
    "随机对照试验": ["randomized", "randomised", "controlled trial", "rct", "double-blind", "placebo"],
    "交叉试验": ["crossover", "cross-over"],
    "动物实验": ["mouse", "mice", "rat", "rats", "murine", "animal model"],
    "观察性研究": ["cohort", "cross-sectional", "case-control", "observational", "survey"],
    "机制研究": ["mechanism", "signaling", "mitochondrial", "pathway", "molecular", "protein", "gene expression"],
    "方法学/设备研究": ["validity", "reliability", "measurement", "device", "wearable", "algorithm", "protocol"],
}


def _contains(text: str, keyword: str) -> bool:
    keyword = keyword.strip().lower()
    if not keyword:
        return False
    pattern = re.escape(keyword).replace(r"\ ", r"\s+")
    return re.search(pattern, text) is not None


def classify_article(article: dict[str, Any], topic_keywords: dict[str, list[str]] | None = None) -> dict[str, Any]:
    """Rule-based topic matching only. No AI scoring and no relevance score."""
    topic_keywords = topic_keywords or load_topic_keywords()
    haystack = " ".join(
        [
            str(article.get("title", "")),
            str(article.get("abstract", "")),
            str(article.get("journal_name", "")),
        ]
    ).lower()

    matched_topics: list[str] = []
    matched_keywords: list[str] = []
    for topic, keywords in topic_keywords.items():
        hits = [kw for kw in keywords if _contains(haystack, kw)]
        if hits:
            matched_topics.append(topic)
            matched_keywords.extend([f"{topic}:{kw}" for kw in hits[:8]])

    study_type = ""
    for label, patterns in STUDY_PATTERNS.items():
        if any(_contains(haystack, p) for p in patterns):
            study_type = label
            break

    enriched = dict(article)
    enriched["topics"] = ";".join(matched_topics)
    enriched["matched_keywords"] = ";".join(matched_keywords)
    enriched["study_type"] = study_type
    # Compatibility only: keep old DB columns neutral.
    enriched["relevance_score"] = 0
    enriched["relevance_level"] = ""
    return enriched
