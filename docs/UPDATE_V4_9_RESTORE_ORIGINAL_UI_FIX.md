# v4.9 Restore Original UI + Journal Center Rendering Fix

本版本用于修复 v4.8 风格偏离和 v4.7 期刊中心 HTML 片段外露的问题。

## 修复内容

1. 恢复 v4.7 原有清爽卡片式风格，不采用 v4.8 的“专业平台大改版”样式。
2. 修复期刊中心中出现 `</div>`、`class="small-muted"` 等 HTML 片段的问题。
3. 期刊中心继续保留“重点关注期刊”功能。
4. 期刊中心不显示 S/A/B/C 优先级。
5. 修复专题中心潜在的 HTML 缩进渲染问题。
6. 清理 `.gitignore`，确保 `data/journal_tracker.db` 不会被忽略。

## 替换文件

```text
app.py      → 项目根目录
.gitignore  → 项目根目录
docs/UPDATE_V4_9_RESTORE_ORIGINAL_UI_FIX.md → docs 文件夹
```

## 本地测试

```powershell
cd D:\博士论文研究\sport_journal_tracker_v1\sport_journal_tracker
streamlit run app.py --server.port 8509
```

## 推送线上

```powershell
git add .
git commit -m "restore original ui and fix journal center"
git pull --rebase origin main
git push
```
