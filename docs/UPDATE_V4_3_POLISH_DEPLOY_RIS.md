# Journal Tracker v4.3：视觉增强 + 单篇 RIS 下载 + 部署说明

## 主要更新

1. **视觉增强**
   - 新增渐变 Hero 区域。
   - 新增自定义 KPI 卡片。
   - 优化论文卡片、专题徽章、期刊分组标题、侧栏质感。
   - 整体更适合对外演示。

2. **单篇 RIS / BibTeX 下载**
   - 每篇论文展开后，新增“本篇 RIS”和“本篇 BibTeX”下载按钮。
   - 当前筛选结果仍保留批量 CSV / BibTeX / RIS 导出。

3. **继续坚持无 AI 相关性评分**
   - 专题分类仍基于关键词词库命中。
   - 不显示“高相关/中相关/低相关”。

4. **部署建议**
   - 本地演示：继续使用 `streamlit run app.py`。
   - 分享给别人：推荐部署到 Streamlit Community Cloud / Hugging Face Spaces / Render / VPS。
   - 如果要让别人看到每日自动更新，服务器端也要运行每日抓取任务。

## 替换方式

把更新包中的文件复制到项目对应位置：

```text
app.py                                      → 项目根目录
src/database.py                            → src 文件夹
scripts/run_app.bat                        → scripts 文件夹
docs/UPDATE_V4_3_POLISH_DEPLOY_RIS.md      → docs 文件夹
```

## 运行

```powershell
python -m src.main init-db
streamlit run app.py --server.port 8502
```

## RIS 下载说明

- 单篇论文：展开论文卡片 → 点击“本篇 RIS”。
- 当前筛选结果：顶部“导出当前显示结果” → 点击“RIS”。
- RIS 文件可导入 Zotero、EndNote、NoteExpress 等文献管理软件。

## 部署提醒

如果部署到云端，需要注意：

1. SQLite 数据库文件需要随项目上传，或者部署后通过抓取任务生成。
2. 只部署 `app.py` 只能看已有数据，不能自动更新。
3. 要实现自动更新，需要在云端配置定时任务，例如 GitHub Actions、服务器 cron、Render Cron Job 等。
4. 如果多人同时写入阅读状态/备注，SQLite 不是最理想方案；长期多人使用建议升级到 PostgreSQL。
