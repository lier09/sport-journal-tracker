# Journal Tracker 快速部署清单

## 1. 复制部署文件

把这些文件复制到项目根目录：

```text
.github/workflows/daily_update.yml
.streamlit/config.toml
```

项目根目录应该直接包含：

```text
app.py
requirements.txt
src/
data/
config/
```

不要把外层 `sport_journal_tracker_v1` 当成部署根目录，应该上传里面真正含有 `app.py` 的 `sport_journal_tracker` 文件夹。

## 2. 确认数据库会上传

检查 `.gitignore`。不能忽略：

```text
data/journal_tracker.db
```

如果 `.gitignore` 中有：

```text
data/
*.db
```

请删除，或在末尾添加：

```text
!data/
!data/journal_tracker.db
```

## 3. 本地测试

```powershell
python -m src.main init-db
streamlit run app.py
```

## 4. 上传 GitHub

```powershell
git init
git add .
git commit -m "Initial journal tracker deployment"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

## 5. 手动测试自动更新

进入 GitHub 仓库：

```text
Actions → Daily Journal Update → Run workflow
```

## 6. 部署 Streamlit

Streamlit Community Cloud：

```text
New app
Repository: 你的仓库
Branch: main
Main file path: app.py
Deploy
```

## 7. 以后每天同步逻辑

```text
GitHub Actions 每天更新 data/journal_tracker.db
→ 自动 commit + push 到 GitHub
→ Streamlit Cloud 读取最新数据库
→ 别人打开链接看到最新更新
```
