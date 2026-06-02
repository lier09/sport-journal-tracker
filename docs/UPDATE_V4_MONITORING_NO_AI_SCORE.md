# Journal Tracker v4 监控看板增强版（无 AI 相关性评分）

本版本定位：把第一版的“论文表格”升级为“监控看板 + 阅读管理系统 + 专题词库追踪”。

## 核心原则

- 不使用 AI 相关性评分。
- 不再展示“高相关 / 中相关 / 低相关”。
- 只显示透明、可检查的专题词库命中结果。
- 保留旧数据库，不删除已抓取论文。

## 新增功能

1. 监控首页
   - 当前筛选论文数
   - 专题命中数
   - 收藏数
   - 覆盖期刊数
   - 今日接口错误数
   - 新增趋势图
   - 期刊新增 Top 15
   - 阅读状态分布

2. 论文卡片
   - 点击论文标题展开
   - 显示摘要、作者、期刊、发表日期、首次发现日期
   - 显示 DOI、PubMed、原文/数据库链接
   - 显示专题标签、命中关键词、研究类型

3. 阅读管理
   - 未读
   - 待读
   - 阅读中
   - 已读
   - 精读
   - 已引用
   - 不相关
   - 收藏
   - 个人标签
   - 个人备注

4. 导出功能
   - 当前筛选结果 CSV
   - 当前筛选结果 BibTeX
   - 当前筛选结果 RIS
   - 阅读管理清单 CSV
   - 期刊库状态 CSV

5. 接口稳定性
   - Crossref / PubMed 请求自动重试
   - 未解决失败队列
   - 接口健康概览
   - 最近错误日志
   - 本地 daily_run.log 看板内查看

6. 报告升级
   - 日报和周报不再使用相关性评分
   - 改为专题命中概览、期刊更新概览、收藏/精读池论文、全部新增论文

## 替换方式

将压缩包内文件复制到你的项目根目录，覆盖同名文件。

对应路径：

- app.py → 项目根目录
- src/database.py → src 文件夹
- src/classify.py → src 文件夹
- src/retry_utils.py → src 文件夹
- src/fetch_crossref.py → src 文件夹
- src/fetch_pubmed.py → src 文件夹
- src/main.py → src 文件夹
- src/reports.py → src 文件夹
- scripts/run_app.bat → scripts 文件夹
- scripts/run_auto_daily.bat → scripts 文件夹
- scripts/run_auto_weekly.bat → scripts 文件夹
- docs/UPDATE_V4_MONITORING_NO_AI_SCORE.md → docs 文件夹

## 更新后第一次运行

```powershell
python -m src.main init-db
python -m src.main run-daily --days-back 3 --sources crossref pubmed --report
streamlit run app.py
```

或双击：

```text
scripts\run_app.bat
```

## 注意

1. 旧数据库不用删除。
2. v4 会自动给旧数据库增加 favorite、user_notes、personal_tags、matched_keywords、fulltext_url 等字段。
3. 任务计划程序如果仍然指向 scripts\run_auto_daily.bat，替换后可继续使用。
4. 如果你已经设置过任务计划程序，通常不需要重设，只要 bat 文件路径不变即可。
