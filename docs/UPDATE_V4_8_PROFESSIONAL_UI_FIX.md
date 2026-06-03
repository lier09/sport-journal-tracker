# Journal Tracker v4.8 Professional UI Fix

本版用于修复 v4.7 期刊中心出现原始 HTML 片段的问题，并按“清爽、专业、科研数据平台”的风格重构首页和主要页面。

## 核心变化

1. 修复期刊中心乱码/HTML 残片
   - 不再用长 HTML 字符串拼接期刊卡片；
   - 改用 Streamlit 原生 columns + 完整卡片容器，避免 `</div>` 等内容被显示出来。

2. UI 风格重构
   - 浅灰蓝背景；
   - 白色/半透明卡片；
   - 深蓝 + 科技蓝主色；
   - 绿色用于正常/增长；
   - 橙色用于热点/提醒；
   - 中等偏高信息密度。

3. 首页结构调整
   - 顶部状态标签“数据监控正常”；
   - 右侧按钮：专题中心、引用导出；
   - 大标题“体育期刊情报平台”；
   - 今日情报摘要卡片；
   - 四个指标卡片：今日新增、监控期刊、热点专题、待读文献；
   - 左侧今日新增文献；
   - 右侧近 14 日趋势、专题热度与提醒卡片。

4. 期刊中心优化
   - 不显示优先级；
   - 保留用户自选重点关注期刊；
   - 重点关注只保存在当前浏览会话，不写入公共数据库。

## 替换文件

```text
app.py → 项目根目录
.gitignore → 项目根目录，修正数据库忽略问题
docs/UPDATE_V4_8_PROFESSIONAL_UI_FIX.md → docs 文件夹
```

## 本地测试

```powershell
streamlit run app.py --server.port 8508
```

## 推送线上

```powershell
git add .
git commit -m "fix professional dashboard ui"
git pull --rebase origin main
git push
```
