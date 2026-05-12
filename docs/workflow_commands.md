# 自然语言指令指南

> **强烈建议**：使用本系统前，请先阅读本文档。了解每个自然语言指令的精确含义和预期输出，有助于你更有效地与 Agent 协作。

---

## 核心概念

本系统通过自然语言指令触发工作流。Agent 会解析你的指令，执行相应的 CLI 命令或操作序列，并生成预期输出。

**重要**：所有工作流独立运行，不会自动串联。Agent 会检测前置条件并提示缺失。

---

## 数据初始化类

### init — 初始化文献库

| 自然语言指令 | 说明 |
|--------------|------|
| `"Initialize a paper vault"` | 初始化当前目录为文献库 |
| `"请初始化文献库"` | 同上（中文） |
| `"Initialize vault at ~/Documents/my-papers"` | 在指定路径初始化 |

**执行内容**：
- 创建目录结构：`library/`, `schema/`, `templates/`, `workspace/`
- 生成 `config.json` 默认配置
- 创建 `schema/tag_taxonomy.json`, `schema/keyword_rules.json`

**输出**：
- 目录结构创建确认
- `config.json` 配置文件
- 初始化完成提示

---

## 定向预处理类

### scan-organize — 扫描与整理

| 自然语言指令 | 说明 |
|--------------|------|
| `"Scan papers"` | 扫描 `paper/` 目录，生成文件清单 |
| `"扫描文献"` | 同上（中文） |
| `"Organize by journal"` | 按期刊缩写归类文件 |
| `"整理期刊"` | 同上（中文） |
| `"Check duplicates"` | 检测重复文件 |

**执行内容**：
- 扫描所有 Markdown 文件
- 识别期刊归属
- 生成移动计划（dry-run）
- 执行移动（需确认）

**输出**：
- `workspace/manifests/source_manifest.json` — 文件清单
- `workspace/manifests/journal_move_plan.json` — 移动计划
- 文件按期刊归类到 `paper/{Direction}/{journal_abbr}/`

---

### ingest — 文献入库

| 自然语言指令 | 说明 |
|--------------|------|
| `"Ingest papers"` | 处理所有未入库论文 |
| `"文档入库"` | 同上（中文） |
| `"Ingest papers in Battery direction"` | 处理指定方向的论文 |
| `"Ingest paper: paper/Battery/RESS/example.md"` | 处理单篇论文 |

**执行内容**：
- 解析论文元数据（标题、期刊、年份、DOI）
- 生成 canonical 页面
- 应用关键词规则打标签
- 转换 HTML 表格为 Markdown

**输出**：
- `library/papers/{Direction}/{paper_id}.md` — canonical 页面
- `library/indexes/canonical_pages.json` — 索引更新
- 标签候选列表（需确认新标签）

---

### tag — 标签管理

| 自然语言指令 | 说明 |
|--------------|------|
| `"Assign tags"` | 批量打标签 |
| `"分配打分与标签"` | 同上（中文） |
| `"View tags"` | 查看标签体系概览 |
| `"Tag stats"` | 查看标签分布统计 |
| `"Add tag 'LSTM' to method dimension"` | 添加自定义标签 |

**执行内容**：
- 应用 `schema/keyword_rules.json` 规则
- Claude 补充智能标签建议
- 写回 canonical 页面 frontmatter

**输出**：
- 更新的 canonical 页面
- `workspace/logs/tag_operations.md` — 操作日志
- 标签分布统计表

---

## 模板系统说明（非独立工作流）

### domain templates — 领域模板

领域模板不是当前 skill 中的独立工作流，也没有默认的 `domain-template` CLI。
不要把 `"generate domain template"` 计入全量工作流目录。

当前实现状态：
- `templates/generic/` 提供通用模板，作为默认报告结构。
- `templates/domains/{Direction}/` 可以保存已存在的领域模板。
- `config.json` 的 `templates.registry` 可以记录模板状态和陈旧度信号。
- `status` 与 `lint` 会报告领域模板状态或过期提示。

实践规则：
1. 优先使用 `templates/generic/` 中的通用模板。
2. 只有当领域模板已经存在且用户明确需要时，才把它作为手动或 Agent 选择的参考结构。
3. 不要描述或承诺自动生成领域模板，除非后续实现了对应脚本和 workflow。

---

## 报告生成类

### journal-report — 期刊调研报告

| 自然语言指令 | 说明 |
|--------------|------|
| `"Journal report for RESS"` | 生成 RESS 期刊报告（全文模式） |
| `"RESS 期刊报告"` | 同上（中文） |
| `"Journal report for RESS, Battery direction"` | 限制为 Battery 方向 |
| `"Journal report for RESS, query 'soh estimation'"` | 筛选包含关键词的论文 |
| `"Journal report for RESS, metadata only"` | 快速元数据概览（不读全文） |

**执行流程**：

1. **默认路径（全文模式）**：
   - CLI 运行 `report_family.py --mode journal --journal RESS`
   - 生成 `workspace/cache/fulltext-report/journal--ress--all-directions.json`
   - Agent 运行每个可读记录的 `records[*].source_read_command` 创建 Agent-safe 临时 Markdown 视图，然后读取该临时文件。不要直接读取 `records[*].source_path`
   - 基于全文证据撰写报告

2. **metadata-only 路径**：
   - 直接从 canonical 元数据生成报告
   - 不读取全文，速度更快但结论深度有限

**输出**：
- `library/reports/journal/RESS-report-{date}.md` — 期刊报告
- 包含：研究热点、方法分布、数据集使用、高价值论文、研究缺口

---

### direction-report — 方向调研报告

| 自然语言指令 | 说明 |
|--------------|------|
| `"Direction report on SOH estimation"` | 全库筛选生成方向报告 |
| `"SOH estimation 方向报告"` | 同上（中文） |
| `"Direction report on SOH estimation, within Battery"` | 限制为 Battery 方向 |
| `"Direction report on transformer, metadata only"` | 快速元数据概览 |

**执行流程**：

1. **默认路径**：
   - CLI 运行 `report_family.py --mode direction --query "soh estimation"`
   - 全库匹配查询（可限制方向）
   - 生成 fulltext bundle
   - Agent 读取全文撰写报告

**输出**：
- `library/reports/direction/{query}-report-{date}.md`
- 包含：研究背景、核心问题、方法分类、数据集、实验设计、趋势、开放问题

---

### direction-review — 方向文献综述

| 自然语言指令 | 说明 |
|--------------|------|
| `"Write a literature review for Battery"` | 为 Battery 方向准备并撰写综述 |
| `"Battery 方向综述"` | 同上（中文） |
| `"Direction review for Battery, focus on SOH"` | 限制为 Battery 方向中的 SOH 主题 |
| `"Deep literature review for Battery"` | 深度综述，目标引用量更高 |

**执行流程**：

1. CLI 运行 `prepare_direction_review.py --direction Battery`
2. 可选 `--focus "topic"` 聚焦子主题
3. 生成 `workspace/cache/fulltext-review/{run_key}.json`
4. Agent 运行每个可读记录的 `records[*].source_read_command` 创建 Agent-safe 临时 Markdown 视图，然后读取该临时文件。不要直接读取 `records[*].source_path`
5. 使用 `templates/generic/direction_review.md` 撰写综述

**输出**：
- `library/reports/review/{direction-or-focus}-review-{date}.md`
- 包含：研究范围、数据集与评价协议、方法分类、应用场景、部署现状、局限与未来方向

---

### stat-report — 统计报告

| 自然语言指令 | 说明 |
|--------------|------|
| `"Method stats"` | 方法维度统计 |
| `"方法统计"` | 同上（中文） |
| `"Dataset stats"` | 数据集维度统计 |
| `"Metric stats for Battery direction"` | Battery 方向的指标统计 |

**执行内容**：
- 统计指定维度的标签分布
- 计算年度趋势
- 生成交叉统计表

**输出**：
- `library/reports/direction/{dimension}-stats-{date}.md`
- Markdown 表格 + 年度趋势图

---

### paper-read — 单篇精读

| 自然语言指令 | 说明 |
|--------------|------|
| `"Read this paper: library/papers/Battery/example.md"` | 精读指定论文 |
| `"单篇文献精读：paper/Battery/RESS/example.md"` | 同上（中文） |
| `"Read paper about SOH estimation, focus on method novelty"` | 带聚焦视角精读 |

**执行内容**：
- 读取 canonical 页面 + 源文件全文
- 回答 6 个固定问题：
  1. 这篇文章解决了什么问题？
  2. 这个问题为什么重要？
  3. 使用了什么方法或模型？
  4. 为什么这个方法能解决问题？
  5. 核心结论是什么？
  6. 下一步可以怎么做？

**输出**：
- `library/reports/paper/{date}-{paper_id}-reading.md` — 精读笔记
- 结构化问答记录

---

### idea-survey — Idea 新颖性调研

| 自然语言指令 | 说明 |
|--------------|------|
| `"Idea survey: 使用 Transformer 做 SOH 预测"` | 调研 Idea 新颖性 |
| `"论文 Idea 查重：基于物理信息的锂电池寿命预测"` | 同上（中文） |

**执行内容**：
- 从 Idea 描述提取关键概念
- 搜索本地库匹配论文
- 评估相似度（高/中/低）
- 分析方法、应用、数据、组合新颖性

**输出**：
- `library/reports/idea/{idea_slug}-survey-{date}.md`
- 相似论文列表 + 新颖性评估 + 风险提示

---

### idea-evidence — Idea 证据准备

| 自然语言指令 | 说明 |
|--------------|------|
| `"Idea evidence for battery SOH robustness"` | 为后续 idea 生成准备证据包 |
| `"为这个研究方向准备 idea 证据包"` | 同上（中文） |

**执行内容**：
- 读取或创建 `workspace/research-briefs/{topic_slug}-research-brief.md`
- 聚合本地 canonical/source/report 证据
- 复用 `web-find` / `web-digest` 做网络检索
- 筛出不少于 50 篇合适网络论文，并对这 50 篇做深读
- 形成 gap map、contradiction map、transfer opportunities 与 negative space

**输出**：
- `library/reports/idea/{topic_slug}-idea-evidence-{date}.md`
- 供 `idea-create` 消费的 evidence pack

---

### idea-create — 研究想法生成

| 自然语言指令 | 说明 |
|--------------|------|
| `"Generate research ideas from this evidence pack"` | 基于 evidence pack 生成并排序 ideas |
| `"根据这个研究简报和证据包生成研究想法"` | 同上（中文） |

**执行内容**：
- 读取 topic brief + `idea-evidence`
- 生成 8-12 个具体 idea
- 按可行性、新颖性潜力、影响力、证据支撑排序
- 对强候选调用 `idea-claim-novelty-check`

**输出**：
- `library/reports/idea/{topic_slug}-idea-report-{date}.md`

---

### idea-discover — Idea 全流程

| 自然语言指令 | 说明 |
|--------------|------|
| `"Run the full idea discovery pipeline for battery SOH"` | 运行 idea 全流程 |
| `"从研究简报开始跑完整 idea workflow"` | 同上（中文） |

**执行内容**：
- 创建或增量更新主题 research brief；同主题 brief 采用合并式续写，保留既有上下文与更新日志
- 若已有 proto-idea，先补 `idea-survey`
- 运行 `idea-evidence`
- 运行 `idea-create`
- 对 finalist 调用 `idea-claim-novelty-check`

**输出**：
- `workspace/research-briefs/{topic_slug}-research-brief.md`
- `library/reports/idea/{topic_slug}-idea-discovery-{date}.md`

---

### idea-claim-novelty-check — Idea 声明级查新

| 自然语言指令 | 说明 |
|--------------|------|
| `"Check claim novelty for this idea"` | 对核心技术声明逐条查新 |
| `"检查这个 idea 的声明级新颖性"` | 同上（中文） |

**执行内容**：
- 抽取 3-5 条核心技术声明
- 检索 `canonical_pages` / `source_markdown` / `web_digest`
- 可选触发实时 `web-find`
- 形成逐声明证据链与结论

**输出**：
- `library/reports/idea/{idea_slug}-idea-claim-novelty-{date}.md`

---

### auto-review-loop — 多轮研究审计

| 自然语言指令 | 说明 |
|--------------|------|
| `"Review my paper"` | 对论文草稿做多轮审稿 |
| `"Adversarial review this method proposal"` | 对研究输出做对抗性审计 |
| `"多轮审稿：drafts/my-paper.md"` | 同上（中文） |

**执行内容**：
- 输入可以是论文草稿、实验报告、方法提案或其他研究输出
- 默认优先调用 Codex-compatible MCP reviewer；在 Claude Code 中明确调用 `codex` 作为 external reviewer/auditor
- MCP 不可用时使用 dual-agent review split；仍不可用时进入 single-agent degraded mode 并在报告中标注
- 默认不覆盖原文稿，但必须给出 final recommended version
- 维护 issue ledger、round history、evidence basis 与 residual risks

**输出**：
- `library/reports/review/{slug}-auto-review-{date}.md`

---

### paper-review-loop — 论文审稿改稿闭环

| 自然语言指令 | 说明 |
|--------------|------|
| `"Paper review loop for RESS"` | 基于目标期刊证据审稿、改稿、复核 |
| `"Review and revise my paper for this venue"` | 基于 target venue report 形成修改稿并审计 |
| `"论文审稿改稿闭环：目标期刊 RESS"` | 同上（中文） |

**前置条件**：
- 需有本地论文草稿
- 需有 target venue report，或已有兼容的 `resubmit-audit` report

**执行内容**：
- 读取 target venue report 或 `resubmit-audit` report
- 只用与论文草稿主题相近的 target-venue papers 作为主要证据
- 审稿维度包括 venue expectations、novelty framing、experiment sufficiency、claim quality、citation coverage
- 生成 revised manuscript content
- 使用同一 evidence basis 对修改稿做 post-revision audit
- issue 状态可使用 `answered_by_current_text / partially_answered / still_unresolved` 分类

**输出**：
- `library/reports/review/{slug}-paper-review-loop-{date}.md`

---

## 网络检索类

### web-find — 联网检索

| 自然语言指令 | 说明 |
|--------------|------|
| `"Web find: SOH estimation in Battery"` | 检索并保存论文 |
| `"联网检索：battery health prognosis"` | 同上（中文） |
| `"Search arXiv for transformer-based SOH methods"` | 仅检索 arXiv |

**执行内容**：
- 查询 OpenAlex / Semantic Scholar / arXiv
- 应用领域过滤规则
- 尝试获取 arXiv 全文
- 保存到 `paper/web_search/` 或 `paper/{Direction}/arxiv/`

**输出**：
- `paper/web_search/{Direction}/{source}/{paper}.md` — 检索结果
- `library/reports/web/{date}-{Direction}-find-report.md` — 检索报告
- arXiv 全文（如果成功）

---

### web-digest — 每日 arXiv 精选

| 自然语言指令 | 说明 |
|--------------|------|
| `"Daily digest"` | 获取近期 arXiv 论文 |
| `"今日 arXiv"` | 同上（中文） |
| `"Recent arXiv on SOH estimation"` | 指定主题精选 |

**执行内容**：
- 查询 arXiv 最新提交
- 应用领域过滤
- 生成摘要报告

**输出**：
- `library/reports/web/{date}-{Direction}-digest.md` — 每日精选报告

---

### web-import-clipper — 导入 Web Clipper

| 自然语言指令 | 说明 |
|--------------|------|
| `"Import web clipper"` | 导入剪藏文件 |
| `"导入 Obsidian Web Clipper"` | 同上（中文） |

**执行内容**：
- 读取 `workspace/web-inbox/` 目录
- 提取元数据并规范化
- 移动到 `paper/{Direction}/{journal_abbr}/`

**输出**：
- 规范化 Markdown 文件
- 归档到 `workspace/web-inbox/imported/`

---

## 投稿建议类

### submission-recommend — 投稿推荐

| 自然语言指令 | 说明 |
|--------------|------|
| `"Recommend submission for my paper"` | 推荐投稿期刊 |
| `"我要投稿该投哪"` | 同上（中文） |
| `"Which journal fits my paper on SOH estimation"` | 指定主题推荐 |

**前置条件**：
- 需有本地论文草稿
- 需有候选期刊的文献证据（journal-report）

**执行内容**：
- 分析论文主题、方法、数据集
- 对候选期刊评分（6 维）
- 推荐 Top 5 期刊

**输出**：
- `library/reports/submission/{paper_slug}-recommend-{date}.md`
- 期刊评分表 + 推荐理由

---

### revision-suggest — 修改建议

| 自然语言指令 | 说明 |
|--------------|------|
| `"Revision suggestions for RESS"` | 针对 RESS 的修改建议 |
| `"给我针对 RESS 期刊的改稿建议"` | 同上（中文） |

**前置条件**：
- 需有本地论文草稿
- 需有目标期刊的文献证据

**执行内容**：
- 比较 5 维度：排版、方法写作、实验、引言、参考文献
- 生成关键/重要/可选建议列表

**输出**：
- `library/reports/submission/{paper_slug}-revision-for-{journal}-{date}.md`
- 修改建议清单

---

### resubmit-audit — 转投审计

| 自然语言指令 | 说明 |
|--------------|------|
| `"Resubmit audit for RESS"` | 基于目标期刊做转投审计 |
| `"Venue transfer audit for my paper"` | 生成转投报告和完整修改稿 |
| `"转投审计：目标期刊 RESS"` | 同上（中文） |

**前置条件**：
- 需有本地论文草稿
- 只需提供目标期刊/会议信息；若目标 venue report 不存在，Agent 应先生成或提示生成

**执行内容**：
- 查找已有 target venue report，优先使用 `library/reports/journal/` 中兼容报告
- 若无报告，先运行现有 `journal-report`；未来 `venue-report` / `conference-report` 可复用同一契约
- 从目标报告及其支撑文献中筛选与论文草稿主题相近的文献
- 形成 fit、novelty framing、experiment sufficiency、claim risk、citation gap 等转投审计
- 按 citation-audit soft-only 思路，把引用问题转译为正文引用句修改、弱化、保留或删除建议
- 输出 prioritized revision plan 和 complete revised draft
- 默认调用 Codex-compatible MCP reviewer；在 Claude Code 中明确调用 `codex` 作为 external auditor；失败后使用 dual-agent，再失败进入 degraded mode

**输出**：
- `library/reports/submission/{slug}-resubmit-audit-{date}.md`

---

## 维护检查类

### status — 库状态

| 自然语言指令 | 说明 |
|--------------|------|
| `"Vault status"` | 查看文献库状态 |
| `"文献库状态"` | 同上（中文） |

**输出**：
- 论文总数统计
- 方向/期刊分布
- canonical 页覆盖率
- 标签覆盖率
- 最近操作日志

---

### lint — 健康检查

| 自然语言指令 | 说明 |
|--------------|------|
| `"Health check"` | 运行健康检查 |
| `"错误检查"` | 同上（中文） |
| `"Lint vault"` | 同上 |

**检查项**：
- orphan canonical 页（源文件缺失）
- missing canonical 页（源文件无对应）
- 标签不一致
- 索引过期
- frontmatter 缺失字段

**输出**：
- 检查报告（通过/警告/错误）
- 建议修复操作

---

### pipeline — 全流程

| 自然语言指令 | 说明 |
|--------------|------|
| `"Full pipeline"` | 执行完整预处理流程 |
| `"执行一条龙全流程"` | 同上（中文） |

**执行序列**：
1. init
2. scan-organize
3. ingest
4. tag
5. rebuild indexes
6. status

**输出**：
- 各步骤执行状态
- 最终库状态摘要

---

## 指令组合示例

### 新文献入库完整流程

```
用户: "我有 20 篇新论文放在 paper/Battery/ 下，请帮我处理"

Agent 执行:
1. "Scan papers" → 扫描新文件
2. "Organize by journal" → 按期刊归类
3. "Ingest papers in Battery direction" → 生成 canonical 页
4. "Assign tags" → 打标签
```

### 生成期刊报告并投稿推荐

```
用户: "我想投稿 RESS，先帮我了解这个期刊的研究情况，再推荐投稿"

Agent 执行:
1. "Journal report for RESS" → 生成期刊报告
2. (用户阅读报告)
3. "Recommend submission for my paper: drafts/my-paper.md" → 投稿推荐
```

### Idea 新颖性检查

```
用户: "我想研究用 PINN 做 SOH 预测，帮我看看这个 Idea 有没有做过"

Agent 执行:
1. "Idea survey: 使用 PINN 做 SOH 预测" → 新颖性调研
2. (Agent 返回相似论文列表和风险评估)
```

---

## 注意事项

### 前置条件检测

Agent 会自动检测前置条件。如果未满足，会提示：

```
用户: "Journal report for RESS"

Agent: 前置条件未满足：没有 RESS 期刊的 canonical 页面。
请先运行 "Ingest papers" 处理 RESS 相关论文。
```

### 全文报告模式

期刊/方向报告默认使用全文模式：
- CLI 准备 `workspace/cache/fulltext-report/*.json` bundle
- Agent 必须运行每个可读记录的 `records[*].source_read_command` 创建 Agent-safe 临时 Markdown 视图，然后读取该临时文件。不要直接读取 `records[*].source_path`
- 最终结论基于全文证据

使用 `--metadata-only` 可跳过全文阅读，直接生成元数据报告。

### 方向限制

部分指令支持方向过滤：
- `"Journal report for RESS, Battery direction"` — 仅 Battery 方向
- `"Direction report on SOH, within Battery"` — 仅 Battery 方向

### 查询筛选

部分指令支持关键词筛选：
- `"Journal report for RESS, query 'soh estimation'"` — 篮选关键词匹配论文
- `"Direction report on transformer"` — 查询关键词

---

## 常见错误与解决

| 错误提示 | 原因 | 解决 |
|----------|------|------|
| `"No canonical pages found"` | 未入库 | 先运行 `"Ingest papers"` |
| `"Direction not found"` | 方向目录不存在 | 创建 `paper/{Direction}/` 或先运行 `"Initialize vault"` |
| `"Source file missing"` | canonical 页引用的源文件不存在 | 检查 `source_path` 或重新入库 |
| `"No papers matched query"` | 查询无匹配 | 调整查询关键词或放宽方向限制 |
