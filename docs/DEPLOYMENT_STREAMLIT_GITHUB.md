# Journal Tracker：GitHub + Streamlit Cloud 部署指南

## 推荐架构

```text
GitHub：保存项目代码和 data/journal_tracker.db
GitHub Actions：每天自动抓取并提交数据库更新
Streamlit Community Cloud：读取 GitHub 仓库并展示看板
```

这是“只读展示版”的最佳路线。别人可以查看、筛选、下载 RIS/BibTeX/CSV，但不建议开放多人写备注和收藏。

## 关键原则

1. GitHub 仓库根目录必须直接有 `app.py` 和 `requirements.txt`。
2. `data/journal_tracker.db` 必须上传到 GitHub。
3. `.github/workflows/daily_update.yml` 负责每天自动更新。
4. Streamlit Cloud 部署时入口文件填写 `app.py`。
5. 如果只是你本地电脑自动抓取，但没有 git push，线上页面不会同步。

## 如果 Crossref 不稳定

打开：

```text
.github/workflows/daily_update.yml
```

把：

```bash
python -m src.main run-daily --days-back 3 --sources pubmed crossref --report
```

改成：

```bash
python -m src.main run-daily --days-back 3 --sources pubmed --report
```

## 分享说明建议

对外可以说明：

> 本系统展示的是经 DOI 或题名去重后的入库文献记录，以系统首次发现日期作为每日更新依据。部分文献可能暂缺摘要。RIS/BibTeX/CSV 可用于 Zotero、EndNote、NoteExpress 等文献管理软件。
