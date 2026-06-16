# awesome-llm-paper-wiki

[🇺🇸 English](docs/README_en.md) | [🇨🇳 简体中文](README.md)

![awesome-llm-paper-wiki](docs/awesome-llm-paper-wiki.png)

> 一个由 LLM agent 驱动的结构化、可持续演进的文献综述系统。它可以基于本地 Markdown 文献文件，完成整理、标签、分析，并生成可用于论文写作和投稿决策的综述报告。

## 🎯 仓库能做什么？

awesome-llm-paper-wiki 管理一个本地 Markdown 文献库，并让你的 LLM agent 处理重复性的文献工作：

| 核心能力 | 说明 |
|------|------|
| **学术期刊整理** | 自动将论文按 `paper/{方向}/{期刊名}/` 进行分类归档整理 |
| **全维度标签管理** | 支持研究任务、底层方法、数据集、测试指标等多维复杂标签自动分析 |
| **自动化综述报告** | 基于已有文献，自动生成期刊报告、方向报告、统计报告，并撰写文献综述 |
| **单篇文献精读** | 按 MIT 教授式 10 阶段范式精读单篇论文，分析问题、失败范式、核心洞察、方法推导、证据与后续问题 |
| **联网搜索接入** | 原生对接 OpenAlex / Semantic Scholar / arXiv，自动检索论文并尝试存入本地源文件（需在 config.json 配置 API key），基于arxiv会议论文清单实现批量下载 |
| **学术投稿向导建议** | 基于项目内的本地知识网络库进行 6 维评分，并生成期刊投稿的修改建议 |
| **研究想法发现** | 从本地文献和网络检索中发现信息差，生成经过证据验证和逐条新颖性核查的具体研究想法 |

## 💡 为什么要做这个项目？

这个项目适合下面几类高频科研场景：

1. **用 Gemini、ChatGPT、Qwen、DeepSeek 等 LLM 做文献调研，但结果不够稳定。**  
   通用 deep research 容易受访问范围、抓取深度和上下文限制影响。这个项目把**本地 Markdown 文献库**作为稳定信息源，把“网络搜索”作为补充信息源，让 Agent 在可控语料上持续生成报告。
2. **想快速看清一个方向或期刊近几年关注什么。**  
   某个方向的主流任务、常见方法、常用数据集、评价指标、热点演化，或者某期刊更偏好哪些问题设定与实验写法，都适合用它来做开题调研、换题判断和投稿摸底。
3. **有很多文献，但缺少一个能持续积累的知识层。**  
   传统工具更偏存档和检索；这个项目会在原始 Markdown 文献之上持续生成 canonical 页面、标签、索引和报告，让同一批文献能持续用于综述、选题和投稿分析。
4. **不只想”收集论文”，还想让 LLM 帮你筛选和比较。**  
   当文献很多时，真正耗时的是判断哪些值得精读、哪些只需略读，以及它们的方法差异。项目支持单篇精读、标签统计和方向综述，便于先看全局，再聚焦重点。
5. **想不出来论文Idea，或者有新想法但不确定是否已被发表。**  
   当你接手或者开辟一个新的方向时，读了很多论文但是依然没有任何好的论文Idea，不如让LLM帮你想几个创新点试试看！当你有了一个研究方向或具体的技术想法，最难判断的是”这个 idea 有没有人做过”。项目提供 idea-survey → idea-evidence → idea-create → idea-claim-novelty-check 完整链路，基于本地文献和联网检索，对每个技术声明做逐条新颖性评分，并给出证据来源，帮助你判断一个想法是否值得投入。
6. **希望用证据辅助投稿，而不是只靠经验判断。**  
   如果文献库覆盖了候选期刊，本项目可以基于本地论文网络生成期刊报告、投稿推荐和定向修改建议，把”投哪里””怎么改”变成更有证据支撑的分析流程。
7. **积累了不少文献，但不知道该怎么写综述。**  
   项目可以基于已有文献和联网搜索文献生成综述草稿，帮助你把零散阅读整理成更有结构的综述框架。
8. **让 LLM 处理 Markdown，充分利用长上下文能力。**  
   相比 PDF，Markdown 更轻量、结构更清晰，更适合作为 LLM 的输入。通过脚本处理、标签提取、引用复用轻松实现长期维护，让 LLM 一次处理上百篇文献，充分利用长上下文。

归根结底，`awesome-llm-paper-wiki` 想解决的不是“怎么再做一次临时调研”，而是“怎么把已经收集到的文献，沉淀成一个可以持续演进、反复复用、能被 Agent 理解和调用的本地知识系统”。文献只需入库一次，随后即可被持续整理、打标签、建立交叉引用，并逐步汇编为更成熟的综述、统计分析与投稿辅助报告。


## 🚀 最佳使用实践

### 1. 环境准备与安装

推荐直接运行仓库根目录下的 `install.sh` 完成安装：

```bash
bash install.sh --platform claude
bash install.sh --platform codex
```

如需手动安装，也可以将 `paper-wiki/` 复制到对应 Agent 平台的 skills 目录下。

需要在 Chrome、Edge 或 Firefox 中安装 `Obsidian Web Clipper` 插件。

### 2. 常用工作流程

大多数时候，你只需要通过自然语言告诉 Agent 下列这几个动作，即可走通一套完整的流程：

#### 第一步：准备文献源文件（能下多少下多少！）

由于 IEEE Trans、Elsevier 等期刊有严格的反爬机制，文献源全文文件需要手动获取。

**获取方式**：

- **期刊论文**：打开期刊论文页面，使用 `Obsidian Web Clipper` 插件保存全文。建议优先保留英文原文；也可以借助“沉浸式翻译”等插件，保存为中英混合或纯中文 Markdown。
- **会议论文**：通过 arXiv 搜索论文，点击论文右侧的 `Access Paper`，选择 `HTML (experimental)`，再使用 `Obsidian Web Clipper` 插件保存全文。**如果你有一份会议论文清单(github上有很多，可以搜一下)，直接丢给skills，能实现批量下载！**
- **相关说明**：图片、公式通常可以完整保存；表格多以 HTML 形式保存，项目脚本会将其转换为更适配 Markdown 的表格格式。

**存放位置**：

- 创建研究方向目录：`paper/{Direction}/`（如 `paper/TimeSeries/`）
- 将对应的文献 Markdown 文件放入对应方向目录下即可

#### 第二步：初始化文献库

打开文献文件夹，对 Agent 发送：
```
“Initialize a paper vault” 或 “请初始化文献库”
```

#### 第三步：整理入库（建库时执行，新文献加入时重复执行）

每次有新文献加入时，执行以下三步：

```
“Scan papers”         → 扫描 `paper/` 目录，生成文件清单
“Organize by journal” → 按期刊缩写对文件归类
“Ingest papers”       → 生成 canonical 页面、提取元数据并打标签（Agent 会自动阅读并提取标签）
```

#### 第三步半：领域模板状态（可选说明）

当前版本没有独立的 `domain-template` 工作流或默认自动生成命令。领域模板作为模板系统资源使用：

```
templates/generic/                 → 默认通用模板
templates/domains/{Direction}/      → 已存在时可作为领域模板参考
status / lint                       → 查看模板 registry 状态和陈旧度提示
```

#### 第四步：生成综述或投稿建议（当涉及多篇文献时，建议把Agent推理能力拉到最大）

文献入库后，可执行以下分析：

```
“Read this paper: {path}”             → 单篇文献精读
“Journal report for {journal}”        → 期刊调研报告
“Direction report for {topic}”        → 方向调研报告
“Write a literature review for {topic}” → 撰写文献综述（普通模式约引用 40-80 篇，深度模式约引用 80-120 篇）
“Recommend submission”                → 投稿推荐（需有本地论文草稿）
“Revision suggestions for {journal}” → 针对特刊的修改建议
“Resubmit audit for {journal}”        → 面向目标期刊/会议的转投审计和完整修改稿
“Paper review loop for {journal}”     → 基于目标 venue 证据的审稿-改稿-复核闭环
```

## 🛠️ 全量工作流目录

`awesome-llm-paper-wiki` 的系统技能集总共内置了 25 大工作流，**各自都可以受指令独立触发并运行。** 按功能板块分组，组内按推荐执行顺序排列。

### 一、文献处理与管理

| 序号 | Workflow | 触发示例 | 说明 |
|:---:|:---|:---|:---|
| 1 | **init** | “initialize vault” / “建库” | 初始化文献库目录结构与默认配置 |
| 2 | **scan-organize** | “scan papers” / “整理期刊” | 扫描 paper/ 目录，按期刊缩写归类文件 |
| 3 | **web-import-clipper** | “import web clipper” / “导入剪藏文件” | 从 Obsidian Web Clipper 导入新文献并生成 canonical 页 |
| 4 | **ingest** | “ingest papers” / “文档入库” | 提取元数据，生成 canonical 页面，可选自动打标 |
| 5 | **tag** | “assign tags” / “分配标签” | 多维标签（任务/方法/数据集/指标等）自动分析与分配 |
| 6 | **pipeline** | “full pipeline” / “执行一条龙全流程” | 复合链路：init → scan → ingest → tag → 索引 → 状态 |
| 7 | **paper-read** | “read this paper” / “单篇文献精读” | 按 MIT 教授式 10 阶段范式深度阅读单篇论文 |
| 8 | **status** | “vault status” / “查看知识库状态” | 文献库整体状态总览（论文数/分布/canonical/标签/模板） |
| 9 | **lint** | “health check” / “健康检查” | 错误/冲突/陈旧索引/孤立 canonical 页检测 |

### 二、文献报告

| 序号 | Workflow | 触发示例 | 说明 |
|:---:|:---|:---|:---|
| 10 | **journal-report** | “XXX journal report” / “XXX 期刊报告” | 指定期刊的文献调研报告（基于全文证据） |
| 11 | **direction-report** | “TSF report” / “方向报告” | 指定主题的方向调研报告（基于全文证据） |
| 12 | **stat-report** | “method stats” / “方法统计” | 方法/数据集/指标等维度的统计报告 |

### 三、网络检索

| 序号 | Workflow | 触发示例 | 说明 |
|:---:|:---|:---|:---|
| 13 | **web-find** | “web find” / “联网检索论文” | 多源检索（OpenAlex/Semantic Scholar/arXiv）并保存为本地 Markdown |
| 14 | **web-digest** | “daily digest” / “近期 arXiv 精选” | 按方向获取近期 arXiv 预印本并生成精选报告 |

### 四、Idea 研究想法发现

| 序号 | Workflow | 触发示例 | 说明 |
|:---:|:---|:---|:---|
| 15 | **idea-survey** | “idea survey” / “Idea 新颖性调研” | 基于全文阅读评估想法相似性与新颖性 |
| 16 | **idea-evidence** | “prepare idea evidence” / “整理 idea 证据包” | 聚合本地与 ≥50 篇网络文献，构建 idea 生成所需证据包 |
| 17 | **idea-create** | “generate research ideas” / “生成研究想法” | 基于证据包生成、筛选并排序具体研究想法 |
| 18 | **idea-claim-novelty-check** | “check claim novelty” / “核查声明新颖性” | 对每个技术声明做逐条新颖性评分与证据溯源 |
| 19 | **idea-discover** | “idea discovery pipeline” / “idea 发现全流程” | 编排 survey→evidence→create→novelty-check 全链路 |

### 五、论文投稿与改进

| 序号 | Workflow | 触发示例 | 说明 |
|:---:|:---|:---|:---|
| 20 | **submission-recommend** | “recommend submission” / “投稿推荐” | 基于本地文献网络做 6 维评分推荐投稿期刊 |
| 21 | **revision-suggest** | “revision suggestions” / “修改建议” | 面向目标期刊的 5 维定向修改建议 |
| 22 | **resubmit-audit** | “resubmit audit” / “转投审计” | 目标期刊转投诊断，产出修改建议与完整修改稿 |
| 23 | **auto-review-loop** | “review my paper” / “多轮审稿” | 通用多轮对抗式研究审计，产出最终建议版 |
| 24 | **paper-review-loop** | “paper review loop” / “论文审稿改稿闭环” | 基于目标 venue 证据的审稿→改稿→复核闭环 |

### 六、文献综述写作

| 序号 | Workflow | 触发示例 | 说明 |
|:---:|:---|:---|:---|
| 25 | **direction-review** | “direction review” / “方向综述” | 撰写方向级文献综述（普通 40-80 篇 / 深度 80-120 篇） |

> **工作流调用原则**：除非你明确要求执行 `”full pipeline”`，否则各工作流默认独立运行，不会自动串联。若前置条件缺失，Agent 会主动提示你先补齐必要步骤。

> **审稿与改稿关系**：`auto-review-loop` 是通用研究审计，不默认覆盖原文稿，但会给出最终建议版；`resubmit-audit` 面向目标期刊/会议做转投审计，并输出完整修改稿；`paper-review-loop` 则基于目标 venue 报告或 `resubmit-audit` 报告执行”审稿 → 改稿 → 修改后复核”的闭环。三者默认优先调用 Codex-compatible MCP reviewer；在 Claude Code 中 reviewer 名称为 `codex`。

---

## 🏗️ 文献目录架构总览

```text
Your Vault/
├── paper/                     ← 原始 Markdown 文献，这是本项目的 source of truth
│   ├── Direction 1/           ← 研究的大方向 (如 Time Series)
│   │   ├── Journal 1/         ← 期刊分类下存放真实的 Markdown 源文本
│   │   └── arxiv/             ← arXiv 独立层
│   └── web_search/            ← 联网检索调研资料存放层 (不会污染正式检索树)
│
├── library/                   ← LLM Agent 为你运算生成的第二大脑【知识层】
│   ├── papers/                ← (重要) Canonical 规范化抽象标签页
│   ├── reports/               ← 自动生成的综述型报告都在该目录下
│   │   ├── paper/             ← 单篇文献精读笔记
│   │   ├── journal/           ← 期刊调研报告
│   │   ├── direction/         ← 方向调研报告
│   │   ├── idea/              ← Idea 新颖性调研等报告
│   │   ├── submission/        ← 投稿推荐与修改建议
│   │   └── web/               ← 联网检索生成的报告
│   └── indexes/               ← 自动生成的索引与统计产物
├── templates/                 ← 强定制化的 Prompt 与报告骨架输出模板
│   ├── generic/               ← 通用报告模板
│   └── domains/               ← 面向具体方向生成的领域模板
├── schema/                    ← 定义了整个系统的标签结构基石、体系映射和术语规则
├── workspace/                 ← 程序缓存、清单、日志与导入暂存目录
│   ├── cache/
│   ├── manifests/
│   ├── logs/
│   └── web-inbox/
│       └── imported/
├── scripts/                   ← 初始化到 Vault 后可直接调用的本地脚本
├── config.json                ← 文献库自定义全局配置（初始化时由示例配置生成）
└── paper-library.md           ← 全局统计数据总控看板
```

本项目秉承了结构分层的思想：
1. **正式全文库** (`paper/`)：严格人工把控进入或提取全量完整学术文本的信息基地。
2. **知识层** (`library/`)：由 Agent 基于源文本提取、压缩并构建出的结构化知识层。
3. **隔离观察层** (`paper/web_search/`)：用于存放联网检索得到的调研材料，避免污染正式文献树。

---

## 📚 进阶深度文档 (Docs)

如果你希望进一步调整底层运行机制、配置高级选项，或遇到网络调用问题，可以按需阅读以下文档：

- **[📖 自然语言指令指南 (强烈建议首先阅读)](docs/workflow_commands.md)** — 每个工作流的精确指令、执行内容、预期输出
- **[🤖 核心系统参数配置项 (config.json 说明)](docs/configuration.md)** 
- **[🚧 论文网络搜索使用 API 请求速率限制机制规避指南](docs/api_limits.md)**
- **[💻 Python 脚本组件底层实现架构逻辑](docs/architecture.md)** 

---

## 常见问题讨论 (FAQ)

### ❓ 这一套系统和传统的 Zotero / Mendeley 有什么本质区别？

Zotero 和 Mendeley 的定位是**“资料架”与文献管理器**；
由于接入了 LLM 支持，`awesome-llm-paper-wiki` 更接近一个进阶的 **“文献综述自动化助手与分析系统”**。繁杂、机械的上下文关联、概念匹配和交叉整理工作可以交给 LLM 在后台完成，因此它不仅能做文献整理与标签分类，还能持续产出有参考价值的分析报告。且文献以 Markdown 形式存储，对 LLM 阅读和信息提取都更友好。

### ❓ 强依赖某种格式约束吗？如果是普通网页随手复制的乱糟糟 Markdown 可以吗？

没有强约束。系统可以兼容大多数自由格式的 Markdown 文件。为了提高识别精度，它会优先检测文本中是否存在标准化的 YAML 元信息（Frontmatter）；如果不存在，大模型也会尝试从正文中提取标题、关键信息和基础元数据。IEEE Trans、Elsevier 以及 arXiv 导出的 Markdown 文献都已做过适配。
结论：**越标准化，识别越稳定；越随性，则越依赖模型能力，但不影响基础可用性。**

### ❓ 我可以通过本地 Obsidian 来一起可视化共生管理吗？

非常推荐。整个系统的底层就是一套纯 Markdown 文件夹结构，因此你完全可以在运行 Agent 的同时，用本地 Obsidian 打开同一个 Vault，通过双向链接、图谱视图和 Dataview 等插件观察知识网络与统计状态。

### ❓ 这套 skills 最简单的使用方式是什么？

目前最便宜、最可行的方式是 **Codex + Claude Code（接入 DeepSeek V4 Pro）**。Codex 提供 MCP reviewer 能力，Claude Code 作为主 Agent 执行 workflows，DeepSeek V4 Pro 作为底层模型提供高性价比推理。三者组合即可覆盖全部 25 个工作流，无需额外付费的 Agent 订阅。

### ❓ 大部分好的Agent都需要付费，我没有Agent怎么办？

1. 把收集好的 Markdown 文献上传到 GitHub 仓库，让 LLM 基于仓库中的文献进行阅读并生成报告，报告形式可参考本项目模板。
2. 将收集好的 Markdown 文献直接导入 Google NotebookLM，然后围绕文献内容进行提问。

---

## ❤️ 致谢 (Acknowledgments)

特别鸣谢以下仓库为 AI Agent 科研自动化领域带来的宝贵指导和实现思路：
- [Andrej Karpathy's llm-wiki / Skills 理念原初探索](https://github.com/forrestchang/andrej-karpathy-skills)
- [sdyckjq-lab/llm-wiki-skill 的体系架构化借鉴](https://github.com/sdyckjq-lab/llm-wiki-skill)
- [sjqsgg/Paperwise 的学术功能洞察与自动化灵感](https://github.com/sjqsgg/Paperwise)
- [luwill/research-skills 的综述写作模板](https://github.com/luwill/research-skills)
- [wanshuiyin/Auto-claude-code-research-in-sleep 的自动化研究思路](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)

## License

MIT
