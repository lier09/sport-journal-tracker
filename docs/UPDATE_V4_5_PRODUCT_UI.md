# Journal Tracker v4.5 Product UI Edition

本次更新重点是产品化界面，而不是增加抓取逻辑。

## 新增与优化

1. 多级菜单结构：
   - 首页总览
   - 今日更新
   - 日期检索
   - 期刊中心
   - 专题中心
   - 导出中心
   - 阅读管理
   - 系统状态

2. 首页增强：
   - 增加四个功能入口卡片；
   - 趋势图、期刊 Top、期刊中心和论文卡片分层展示；
   - 更像正式科研情报平台。

3. 日期切换：
   - 支持“前日 / 今天 / 后日”快速切换；
   - 仍保留日期选择器。

4. 论文卡片升级：
   - 增加摘要预览；
   - 详情页使用 tabs：摘要 / 引用 / 链接 / 备注；
   - 单篇 RIS / BibTeX 下载保留。

5. 期刊中心：
   - 期刊卡片显示今日、近7日、趋势范围更新量；
   - 适合展示“哪些期刊近期活跃”。

6. 专题中心：
   - 专题卡片显示所选日期与趋势范围命中情况；
   - 继续坚持关键词词库，不使用 AI 相关性评分。

## 替换文件

```text
app.py → 项目根目录
docs/UPDATE_V4_5_PRODUCT_UI.md → docs 文件夹
```

## 本地测试

```powershell
python -m src.main init-db
streamlit run app.py --server.port 8505
```

## 推送到线上

```powershell
git add .
git commit -m "update product ui"
git push
```
