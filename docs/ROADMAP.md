# Roadmap｜后续迭代路线

## Phase 1：本地 MVP

- [x] 86 本 JCR Sport Sciences-SCIE 期刊配置表
- [x] SQLite 数据库
- [x] RSS / Crossref / PubMed 抓取接口
- [x] DOI + 标题去重
- [x] 关键词主题分类
- [x] Word / Excel 日报与周报
- [x] Streamlit 本地看板

## Phase 2：元数据完整性增强

- [ ] 从 JCR/MJL 导出表补全 ISSN/eISSN
- [ ] 逐本验证 RSS 地址
- [ ] 建立 `journal_sources.csv`，支持同一本期刊多个数据源
- [ ] 添加抓取失败重试机制
- [ ] 增加 `last_success_at` 与 `source_health` 字段

## Phase 3：AI 科研情报层

- [ ] 中文题名翻译
- [ ] 摘要结构化总结
- [ ] 研究类型识别：RCT、综述、动物实验、横断面、队列等
- [ ] PICO/PECO 提取：对象、干预/暴露、对照、结局
- [ ] 相关性评分升级为语义评分
- [ ] 每周推荐 5–10 篇值得精读论文

## Phase 4：知识库与写作联动

- [ ] Zotero/RIS/BibTeX 导出
- [ ] 开放获取 PDF 自动识别
- [ ] 论文精读卡片生成
- [ ] 主题文献库：低氧、高压氧、恢复、运动营养、代谢组学
- [ ] 与综述/课题申报写作模板联动

## Phase 5：部署与协同

- [ ] GitHub Actions 自动化稳定运行
- [ ] 云端数据库或对象存储
- [ ] Notion/飞书多维表格同步
- [ ] 多用户收藏、阅读状态、标签管理
