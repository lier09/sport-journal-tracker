# Journal Tracker v4.7 Focus Journals Update

本次更新针对「期刊中心」与用户自定义重点关注期刊进行优化。

## 更新内容

1. 期刊中心去除「优先级」展示
   - 不再在期刊卡片中显示 S/A/B/C 优先级。
   - 期刊中心只保留：今日、近7日、趋势范围、重点关注标记。

2. 用户自定义重点关注期刊
   - 左侧新增「重点关注期刊」多选框。
   - 用户可输入期刊名搜索并选择自己关注的期刊。
   - 可勾选「仅显示重点关注期刊」。

3. 新增「重点关注」页面
   - 显示用户已选择的重点关注期刊。
   - 展示这些期刊在所选日期与趋势范围内的更新。

4. 不写入公共数据库
   - 重点关注选择只保存在当前浏览会话中。
   - 不会影响其他访问者，也不会污染公共数据库。

## 替换文件

```text
app.py → 项目根目录
docs/UPDATE_V4_7_FOCUS_JOURNALS.md → docs 文件夹
```

## 本地测试

```powershell
streamlit run app.py --server.port 8507
```

## 推送线上

```powershell
git add .
git commit -m "add focus journals"
git pull --rebase origin main
git push
```

如果 pull 时 data/journal_tracker.db 出现冲突，优先保留远程数据库版本。
