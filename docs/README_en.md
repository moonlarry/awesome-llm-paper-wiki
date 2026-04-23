# awesome-llm-paper-wiki

[🇨🇳 简体中文](../README.md) | [English](README_en.md)

![awesome-llm-paper-wiki](awesome-llm-paper-wiki.png)

> A structured, continuously evolving literature survey system powered by LLM agents. It works on local Markdown paper files to organize, tag, analyze, and generate survey reports for academic writing and submission decisions.

## 🎯 What It Does

awesome-llm-paper-wiki manages a local Markdown literature vault and lets your LLM agent handle repetitive literature work:

| Capability | Description |
|------|------|
| **Journal Organization** | Automatically sort papers into `paper/{direction}/{journal}/` |
| **Multi-Dimensional Tagging** | Analyze complex tags across research task, core method, dataset, evaluation metric, and more |
| **Automated Survey Reports** | Generate journal reports, direction reports, statistical reports, and literature reviews from existing papers |
| **Single-Paper Reading** | Read one paper with a fixed question template covering its problem, importance, method, mechanism, conclusions, and next steps |
| **Web Search Integration** | Connect to OpenAlex / Semantic Scholar / arXiv, search papers online, and try to store them into the local source library (API keys configured in `config.json`) |
| **Submission Guidance** | Score target journals from six dimensions based on the local knowledge network and generate targeted revision suggestions |

## 💡 Why This Project

When using deep research features from LLMs such as Gemini, ChatGPT, Qwen, or DeepSeek, literature platform access limits often mean too few citable papers and incomplete information, which makes the final survey report less reliable in practice.

Traditional literature management platforms such as Zotero are usually centered around PDFs. PDFs can be used as LLM input, but they are less lightweight and less convenient than Markdown, and double-column PDFs often require multimodal processing. Markdown files are smaller, cleaner, and much better suited for long-term LLM workflows. Saving a paper webpage as Markdown is usually as convenient as downloading a PDF, while making later organization, extraction, and reuse much easier.

For that reason, `awesome-llm-paper-wiki` takes a more autonomous approach: on top of the raw Markdown paper collection, the LLM **gradually extracts, builds, and maintains a dedicated structured knowledge layer**. A paper only needs to be ingested once; after that, it can be tagged, cross-referenced, and continuously compiled into increasingly mature survey and analysis reports as the research evolves.

## 🚀 Recommended Workflow

### 1. Setup and Installation

The recommended way is to run `install.sh` from the repository root:

```bash
bash install.sh --platform claude
bash install.sh --platform codex
```

If you prefer manual installation, you can also copy `paper-wiki/` into the skills directory of the corresponding agent platform.

It is also recommended to install the `Obsidian Web Clipper` extension in Chrome, Edge, or Firefox.

### 2. Common Workflow

Most of the time, you can complete the full process just by telling your agent these actions in natural language:

#### Step 1: Prepare Source Paper Files

Because journals such as IEEE Transactions and Elsevier often have strong anti-crawling protections, the full-text source files usually need to be collected manually.

**How to collect them:**
- **Journal papers**: Open the journal paper webpage and save the full text with `Obsidian Web Clipper`. Keeping the English original is recommended; you can also use tools such as Immersive Translate to save mixed bilingual or Chinese Markdown versions.
- **Conference papers**: Search the paper on arXiv, click `Access Paper`, choose `HTML (experimental)`, then save the full text with `Obsidian Web Clipper`.
- **Notes**: Images and formulas are usually preserved well. Tables are often saved as HTML, and the project scripts will convert them into a Markdown-friendly table format.

**Where to put them:**
- Create a direction folder: `paper/{Direction}/` such as `paper/TimeSeries/`
- Put the corresponding Markdown paper files into that direction folder

#### Step 2: Initialize the Vault

Open the literature folder and tell your agent:

```text
"Initialize a paper vault" or "请初始化文献库"
```

#### Step 3: Organize and Ingest

Every time you add new papers, run these three steps:

```text
"Scan papers"         → scan the `paper/` directory and generate the file inventory
"Organize by journal" → sort files by journal abbreviation
"Ingest papers"       → generate canonical pages, extract metadata, and assign tags automatically
```

#### Step 3.5: Domain Template Status

The current version does not provide a standalone `domain-template` workflow or default automatic generation command. Domain templates are template-system resources:

```text
templates/generic/                 → default generic templates
templates/domains/{Direction}/      → optional domain templates when they already exist
status / lint                       → inspect template registry status and staleness hints
```

#### Step 4: Generate Reports or Submission Guidance

After papers are ingested, you can run analyses such as:

```text
"Read this paper: {path}"             → single-paper reading note
"Journal report for {journal}"        → journal survey report
"Direction report for {topic}"        → direction survey report
"Write a literature review for {topic}" → literature review writing (regular mode cites about 40-80 papers; deep mode about 80-120)
"Recommend submission"                → journal recommendation (requires a local paper draft)
"Revision suggestions for {journal}"  → revision suggestions for a target journal or special issue
```

## 🛠️ Full Workflow List

`awesome-llm-paper-wiki` currently includes 18 workflows, and **each one can be triggered independently by instruction.**

| # | Workflow | Example Trigger | Module |
|---|--------|----------|------|
| 1 | **init** | "initialize vault" / "建库" | Initialization |
| 2 | **scan-organize** | "scan papers" / "整理期刊" | Preprocessing |
| 3 | **ingest** | "ingest papers" / "文档入库" | Preprocessing |
| 4 | **tag** | "assign tags" / "分配打分与标签" | Preprocessing |
| 5 | **journal-report** | "XXX journal report" / "XXX 期刊报告" | Journal Survey |
| 6 | **direction-report** | "TSF report" / "time series forecasting 方向报告" | Direction Survey |
| 7 | **stat-report** | "method stats" / "论文使用方法统计" | Statistical Survey |
| 8 | **idea-survey** | "idea survey" / "Idea 新颖性调研" | Idea Review |
| 9 | **web-find** | "web find" / "联网检索论文" | Web Search |
| 10 | **web-digest** | "daily digest" / "近期 arXiv 精选" | Web Recommendation |
| 11 | **web-import-clipper** | "import web clipper" / "导入剪藏文件" | New Paper Processing |
| 12 | **submission-recommend** | "recommend submission" / "投稿推荐" | Submission Guidance |
| 13 | **revision-suggest** | "revision suggestions" / "修改建议" | Revision Guidance |
| 14 | **status** | "vault status" / "查看知识库状态" | Environment Check |
| 15 | **lint** | "health check" / "错误/冲突与安全检查" | Environment Check |
| 16 | **pipeline** | "full pipeline" / "执行一条龙全流程" | Composite Pipeline |
| 17 | **paper-read** | "read this paper" / "单篇文献精读" | Single-Paper Reading |
| 18 | **direction-review** | "direction review" / "方向综述" | Literature Review Writing |

> **Workflow rule**: unless you explicitly ask for `"full pipeline"`, workflows run independently by default and do not automatically chain themselves. If prerequisites are missing, the agent will tell you what to do first.

---

## 🏗️ Vault Architecture Overview

```text
Your Vault/
├── paper/                     ← Raw Markdown papers, the source of truth
│   ├── Direction 1/           ← Research direction such as Time Series
│   │   ├── Journal 1/         ← Real Markdown source files organized by journal
│   │   └── arxiv/             ← Separate layer for arXiv papers
│   └── web_search/            ← Online research materials, isolated from the formal paper tree
│
├── library/                   ← LLM-generated knowledge layer
│   ├── papers/                ← Canonical normalized paper pages
│   ├── reports/               ← Auto-generated survey-style reports
│   │   ├── paper/             ← Single-paper reading notes
│   │   ├── journal/           ← Journal survey reports
│   │   ├── direction/         ← Direction survey reports
│   │   ├── idea/              ← Idea novelty and related reports
│   │   ├── submission/        ← Submission recommendations and revision suggestions
│   │   └── web/               ← Reports generated from web search results
│   └── indexes/               ← Auto-generated indexes and statistics
├── templates/                 ← Prompt and report skeleton templates
│   ├── generic/               ← Generic report templates
│   └── domains/               ← Domain-specific templates generated for a direction
├── schema/                    ← Tag taxonomy, mappings, and terminology rules
├── workspace/                 ← Cache, manifests, logs, and import staging area
│   ├── cache/
│   ├── manifests/
│   ├── logs/
│   └── web-inbox/
│       └── imported/
├── scripts/                   ← Local scripts copied into the vault during initialization
├── config.json                ← Global vault configuration, generated from the example config during initialization
└── paper-library.md           ← Global dashboard
```

This project follows a layered structure:
1. **Formal full-text library** (`paper/`): the strictly curated base of complete academic texts.
2. **Knowledge layer** (`library/`): the structured layer built by the agent through extraction and compression of source papers.
3. **Isolated observation layer** (`paper/web_search/`): online research material kept separate from the formal literature tree.

---

## 📚 Advanced Documentation

If you want to adjust internal behavior, configure advanced options, or troubleshoot network-related issues, see these documents as needed:

- **[📖 Natural-Language Command Guide (recommended first)](workflow_commands.md)** — exact commands, execution behavior, and expected outputs for each workflow
- **[🤖 Core Configuration Reference (`config.json`)](configuration.md)**
- **[🚧 API Rate-Limit Guide for Web Search](api_limits.md)**
- **[💻 Python Script Architecture and Internal Design](architecture.md)**

---

## FAQ

### ❓ How is this different from Zotero / Mendeley?

Zotero and Mendeley are primarily reference managers. With LLM support, `awesome-llm-paper-wiki` is closer to an advanced **literature survey automation assistant and analysis system**. Tedious work such as context linking, concept matching, and cross-paper organization can be handled by the LLM in the background, so the system does more than just organize and tag papers: it continuously produces analysis reports that are useful for research. Since everything is stored in Markdown, it is also much more LLM-friendly for reading and extraction.

### ❓ Does it require a strict paper format? Will messy Markdown copied from random webpages still work?

No strict format is required. The system can handle most free-form Markdown files. To improve extraction accuracy, it first checks whether standard YAML frontmatter exists; if it does not, the model will still try to extract titles, key facts, and basic metadata from the body text. Markdown exported from IEEE Transactions, Elsevier, and arXiv has already been adapted.

In short: **the more standardized the file, the more stable the extraction; the more messy it is, the more it depends on model capability, but basic usability is still preserved.**

### ❓ Can I use it together with local Obsidian?

Yes, and it is strongly recommended. The whole system is fundamentally just a Markdown folder structure, so you can open the same vault in local Obsidian while the agent is running, then use backlinks, graph view, and Dataview to inspect the knowledge network and vault statistics.

### ❓ Many good agents are paid. What if I do not have one?

1. Upload your collected Markdown papers to a GitHub repository and let an LLM read them from the repo to generate the reports you need, using this project as a template.
2. Import the collected Markdown papers into Google NotebookLM and ask questions directly over the literature set.

---

## ❤️ Acknowledgments

Special thanks to the following repositories for their ideas and inspiration in AI-agent-driven academic automation:
- [Andrej Karpathy's llm-wiki / early exploration of the Skills idea](https://github.com/forrestchang/andrej-karpathy-skills)
- [Architectural inspiration from sdyckjq-lab/llm-wiki-skill](https://github.com/sdyckjq-lab/llm-wiki-skill)
- [Academic workflow inspiration from sjqsgg/Paperwise](https://github.com/sjqsgg/Paperwise)
- [Survey writing templates from luwill/research-skills](https://github.com/luwill/research-skills)

## License

MIT
