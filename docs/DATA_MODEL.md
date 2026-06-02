# Data Model｜数据模型

## journals

期刊配置表，从 `config/journals.csv` 同步而来。

| 字段 | 说明 |
|---|---|
| journal_name | 期刊名称，唯一 |
| issn | 印刷版 ISSN |
| eissn | 电子版 ISSN |
| priority | S/A/B/C |
| domain | 主要研究方向 |
| frequency | 监测频率 |
| active | 是否启用 |
| rss_url | RSS 地址 |
| crossref_query | Crossref 检索词 |
| pubmed_query | PubMed 检索式 |

## articles

论文主表。

| 字段 | 说明 |
|---|---|
| title | 论文题名 |
| title_hash | 标准化题名 hash，用于无 DOI 去重 |
| journal_name | 期刊名 |
| authors | 作者 |
| publication_date | 发表日期 |
| first_seen_date | 系统首次发现日期，日报/周报统计以此为准 |
| doi | DOI，唯一索引 |
| url | 论文链接 |
| abstract | 摘要 |
| source | rss/crossref/pubmed |
| pmid | PubMed ID |
| topics | 主题标签 |
| relevance_score | 相关性分数 |
| relevance_level | high/medium/low/unclassified |
| study_type | 研究类型 |
| status | unread/read/deep_read/cited |

## run_log

抓取运行日志。

| 字段 | 说明 |
|---|---|
| run_date | 运行日期 |
| source | 数据源 |
| journal_name | 期刊名 |
| status | ok/error |
| fetched_count | 抓取数量 |
| inserted_count | 新增入库数量 |
| error_message | 错误信息 |
