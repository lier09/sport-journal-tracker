# v5.2 Coverage First Edition

本次更新目标是“覆盖优先”，不是继续美化页面。

## 核心思想

系统要追踪的不是“能抓到一点文章”，而是 86 本目标期刊的覆盖状态。v5.2 增加：

```text
config/journal_source_registry.csv
config/publisher_sources.csv
src/fetch_publishers.py
src/coverage_audit.py
```

## 数据源层级

每日抓取顺序变为：

```text
publisher 官方源 → RSS → PubMed → Crossref
```

官方源用于弥补 PubMed / Crossref 滞后。

## 当前已启用的官方源

```text
British Journal of Sports Medicine → BMJ Online First
European Journal of Applied Physiology → Springer Articles
Sports Medicine → Springer Articles
Sports Medicine-Open → Springer Articles
```

其余期刊全部列入 `journal_source_registry.csv`，默认标记为 `database_fallback_only`，即暂时依靠 PubMed/Crossref 兜底，并等待后续逐本验证官网源。

## 覆盖审计

运行：

```powershell
python -m src.main audit-sources
```

会输出：

```text
Target journals
Active official sources
Verified official sources
Fallback-only journals
```

同时生成：

```text
reports/source_coverage_audit_YYYY-MM-DD.csv
```

## 测试官方源

```powershell
python -m src.main run-daily --days-back 7 --sources publisher --report
```

## 如何继续补其它期刊

编辑：

```text
config/publisher_sources.csv
```

增加或启用期刊官方源。字段说明：

```text
journal_name       必须与 config/journals.csv 完全一致
publisher          出版社/平台
source_type        springer_journal / bmj_online_first / official_rss / generic_doi_list
source_id          Springer 等平台的 journal ID，可为空
source_url         官网最新文章页或 RSS 地址
active             yes/no
verified           yes/pending/no
max_pages          抓取页数，默认 1
notes              备注
```

## 重要原则

不要把未验证的官网源直接设为 active=yes。否则可能误抓、重复抓或污染数据库。正确流程是：

```text
添加候选 URL → 本地测试 publisher 源 → 确认结果正常 → active=yes → 推送上线
```
