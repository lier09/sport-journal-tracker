# Journal Tracker v4.6 Abstract Enrichment Edition

本次更新补齐“自动补摘要 / 元数据增强”功能，并继续优化图标质感。

## 核心变化

1. 新增自动补摘要模块：`src/enrich_pubmed.py`
   - 自动扫描摘要为空的入库记录；
   - 优先用 PMID 从 PubMed 获取官方摘要；
   - 没有 PMID 时，先尝试 DOI → PMID；
   - DOI 不可用时，使用题名 + 期刊进行严格匹配；
   - 只回填公开官方元数据，不生成 AI 摘要，不下载付费全文。

2. 新增命令：

```powershell
python -m src.main enrich-abstracts --limit 100 --batch-size 20
```

3. GitHub Actions 自动补摘要：
   - 每日抓取论文后自动运行摘要补全；
   - 如果外部接口临时失败，不影响主更新流程。

4. 页面提示优化：
   - 将“摘要暂缺”优化为“摘要待补全”；
   - 论文卡片增加“摘要已收录 / 摘要待补全”状态徽章；
   - 首页不增加摘要覆盖率，避免页面信息过重。

5. 图标质感优化：
   - 首页功能入口使用统一渐变图标；
   - 日期、期刊、专题、导出入口更加产品化。

## 替换文件

```text
app.py                                → 项目根目录
src/database.py                       → src 文件夹
src/main.py                           → src 文件夹
src/enrich_pubmed.py                  → src 文件夹
.github/workflows/daily_update.yml    → .github/workflows 文件夹
scripts/run_enrich_abstracts.bat      → scripts 文件夹
docs/UPDATE_V4_6_ABSTRACT_ENRICHMENT.md → docs 文件夹
```

## 本地测试

```powershell
python -m src.main init-db
python -m src.main enrich-abstracts --limit 30
streamlit run app.py --server.port 8506
```

## 推送线上

```powershell
git add .
git commit -m "add abstract enrichment"
git push
```

## 说明

自动补摘要不能保证 100% 成功。部分 Editorial、Letter、Correction、News、Book review、会议摘要或出版社未开放元数据的记录仍可能显示“摘要待补全”。
