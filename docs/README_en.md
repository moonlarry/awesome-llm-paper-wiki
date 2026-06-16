# awesome-llm-paper-wiki

[🇨🇳 简体中文](../README.md) | [English](README_en.md)

![awesome-llm-paper-wiki](awesome-llm-paper-wiki.png)

> A structured, continuously evolving literature survey system powered by LLM agents. It works on local Markdown paper files to organize, tag, analyze, and generate survey reports for academic writing and submission decisions.

## 🎯 What the Repository Can Do

awesome-llm-paper-wiki manages a local Markdown literature vault and lets your LLM agent handle repetitive literature work:

| Capability | Description |
|------|------|
| **Journal Organization** | Automatically sort papers into `paper/{direction}/{journal}/` |
| **Multi-Dimensional Tagging** | Analyze complex tags across research task, core method, dataset, evaluation metric, and more |
| **Automated Survey Reports** | Generate journal reports, direction reports, statistical reports, and literature reviews from existing papers |
| **Single-Paper Reading** | Read one paper with an MIT-style 10-phase framework covering the problem, failed paradigms, key insight, method derivation, evidence, and follow-up questions |
| **Web Search Integration** | Connect to OpenAlex / Semantic Scholar / arXiv, search papers online, and try to store them into the local source library (API keys configured in `config.json`) |
| **Submission Guidance** | Score target journals from six dimensions based on the local knowledge network and generate targeted revision suggestions |
| **Research Idea Discovery** | Discover information gaps from the literature and produce evidence-backed research ideas with per-claim novelty verification |

## 💡 Why This Project

This project suits the following common research scenarios:

1. **Using LLMs like Gemini, ChatGPT, Qwen, or DeepSeek for literature research, but the results are not consistent enough.**
   General-purpose deep research is often limited by access scope, crawl depth, and context constraints. This project uses a **local Markdown literature vault** as the stable information source and "web search" as the supplementary source, letting the Agent continuously generate reports from a controlled corpus.

2. **Want to quickly see what a direction or journal has been focusing on in recent years.**
   The mainstream tasks, common methods, frequently used datasets, evaluation metrics, and hot-spot evolution in a direction, or what problem settings and experimental styles a particular journal prefers — all suitable for initial topic exploration, pivot decisions, and submission scouting.

3. **Have many papers but lack a knowledge layer that can continuously accumulate.**
   Traditional tools lean toward archiving and retrieval. This project continuously generates canonical pages, tags, indexes, and reports on top of the raw Markdown papers, so the same collection of papers can be reused for surveys, topic selection, and submission analysis.

4. **Not only want to "collect papers" but also want the LLM to help you screen and compare them.**
   When the number of papers is large, the real bottleneck is deciding which ones are worth deep reading, which ones only need skimming, and what the methodological differences between them are. The project supports single-paper deep reading, tag-based statistics, and direction-level reviews, helping you first see the big picture and then focus on what matters.

5. **Struggling to come up with paper ideas, or have a new idea but are not sure if it has already been published.**
   When entering or opening up a new direction, you may have read many papers but still lack a good idea — let the LLM help you think of a few innovation points. When you have a research direction or concrete technical idea, the hardest question is "has someone already done this?" The project provides the full pipeline of idea-survey → idea-evidence → idea-create → idea-claim-novelty-check. Based on the local literature and web search, it scores each technical claim for novelty and provides evidence provenance, helping you decide whether an idea is worth pursuing.

6. **Want evidence-supported submission guidance rather than experience-based guessing.**
   If the vault covers the candidate journals, this project can generate journal reports, submission recommendations, and targeted revision suggestions based on the local paper network, turning "where to submit" and "how to revise" into an evidence-supported analysis process.

7. **Have accumulated many papers but don't know how to write a literature review.**
   The project can generate a review draft based on existing papers and web search results, helping you organize scattered reading into a more structured survey framework.

8. **Let LLMs process Markdown and fully leverage their long-context capabilities.**
   Compared to PDF, Markdown is lighter, more structurally clear, and more suitable as LLM input. Long-term maintenance is easy through script processing, tag extraction, and citation reuse, letting the LLM process hundreds of papers at once and fully utilize long-context capability.

At its core, `awesome-llm-paper-wiki` is not about "how to do yet another one-off survey" but about "how to turn the papers you have already collected into a local knowledge system that can continuously evolve, be repeatedly reused, and be understood and invoked by Agents." Papers only need to be ingested once; after that, they can be continuously organized, tagged, cross-referenced, and gradually compiled into increasingly mature surveys, statistical analyses, and submission support reports.

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
- **Conference papers**: Search the paper on arXiv, click `Access Paper`, choose `HTML (experimental)`, then save the full text with `Obsidian Web Clipper`. **If you have a conference paper list (many available on GitHub), hand it directly to the skills for batch downloading!**
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

#### Step 4: Generate Reports or Submission Guidance (when processing many papers, maximize the Agent's reasoning capability)

After papers are ingested, you can run analyses such as:

```text
"Read this paper: {path}"             → single-paper reading note
"Journal report for {journal}"        → journal survey report
"Direction report for {topic}"        → direction survey report
"Write a literature review for {topic}" → literature review writing (regular mode cites about 40-80 papers; deep mode about 80-120)
"Recommend submission"                → journal recommendation (requires a local paper draft)
"Revision suggestions for {journal}"  → revision suggestions for a target journal or special issue
"Resubmit audit for {journal}"        → target-venue transfer audit plus a complete revised draft
"Paper review loop for {journal}"     → venue-evidence-based review, revision, and post-revision audit loop
```

## 🛠️ Full Workflow List

`awesome-llm-paper-wiki` currently includes 25 workflows, and **each one can be triggered independently by instruction.** Grouped by function, ordered by recommended execution sequence within each group.

### 1. Paper Processing & Vault Management

| # | Workflow | Example Trigger | Description |
|:---:|:---|:---|:---|
| 1 | **init** | "initialize vault" / "建库" | Initialize vault directory structure and default configuration |
| 2 | **scan-organize** | "scan papers" / "整理期刊" | Scan paper/ directory and sort files by journal abbreviation |
| 3 | **web-import-clipper** | "import web clipper" / "导入剪藏文件" | Import new papers from Obsidian Web Clipper and generate canonical pages |
| 4 | **ingest** | "ingest papers" / "文档入库" | Extract metadata, generate canonical pages, optionally apply auto-tagging |
| 5 | **tag** | "assign tags" / "分配标签" | Multi-dimensional tag analysis and assignment (task/method/dataset/metric/etc.) |
| 6 | **pipeline** | "full pipeline" / "执行一条龙全流程" | Composite chain: init → scan → ingest → tag → index → status |
| 7 | **paper-read** | "read this paper" / "单篇文献精读" | MIT-style 10-phase deep single-paper reading |
| 8 | **status** | "vault status" / "查看知识库状态" | Vault-wide status overview (counts, distribution, coverage, templates) |
| 9 | **lint** | "health check" / "健康检查" | Error/conflict/stale-index/orphan-canonical-page detection |

### 2. Literature Reports

| # | Workflow | Example Trigger | Description |
|:---:|:---|:---|:---|
| 10 | **journal-report** | "XXX journal report" / "XXX 期刊报告" | Journal survey report grounded in full-text evidence |
| 11 | **direction-report** | "TSF report" / "方向报告" | Topic-focused direction survey report grounded in full-text evidence |
| 12 | **stat-report** | "method stats" / "方法统计" | Statistical reports by method, dataset, metric, and other dimensions |

### 3. Web Search

| # | Workflow | Example Trigger | Description |
|:---:|:---|:---|:---|
| 13 | **web-find** | "web find" / "联网检索论文" | Multi-source search (OpenAlex/Semantic Scholar/arXiv) and save as local Markdown |
| 14 | **web-digest** | "daily digest" / "近期 arXiv 精选" | Fetch recent arXiv preprints for a direction and generate a digest report |

### 4. Idea Discovery

| # | Workflow | Example Trigger | Description |
|:---:|:---|:---|:---|
| 15 | **idea-survey** | "idea survey" / "Idea 新颖性调研" | Assess idea similarity and novelty through full-text reading |
| 16 | **idea-evidence** | "prepare idea evidence" / "整理 idea 证据包" | Aggregate local and ≥50 web papers into an evidence pack for idea generation |
| 17 | **idea-create** | "generate research ideas" / "生成研究想法" | Generate, filter, and rank concrete research ideas from the evidence pack |
| 18 | **idea-claim-novelty-check** | "check claim novelty" / "核查声明新颖性" | Per-claim novelty scoring with evidence chains and risk assessment |
| 19 | **idea-discover** | "idea discovery pipeline" / "idea 发现全流程" | Orchestrate survey→evidence→create→novelty-check pipeline |

### 5. Paper Submission & Improvement

| # | Workflow | Example Trigger | Description |
|:---:|:---|:---|:---|
| 20 | **submission-recommend** | "recommend submission" / "投稿推荐" | 6-dimension journal scoring and recommendation based on the local literature network |
| 21 | **revision-suggest** | "revision suggestions" / "修改建议" | 5-dimension targeted revision suggestions for a specific journal |
| 22 | **resubmit-audit** | "resubmit audit" / "转投审计" | Target-venue transfer audit with revision advice and a complete revised draft |
| 23 | **auto-review-loop** | "review my paper" / "多轮审稿" | General multi-round adversarial research audit with a final recommended version |
| 24 | **paper-review-loop** | "paper review loop" / "论文审稿改稿闭环" | Venue-evidence-grounded review → revision → post-revision audit loop |

### 6. Literature Review Writing

| # | Workflow | Example Trigger | Description |
|:---:|:---|:---|:---|
| 25 | **direction-review** | "direction review" / "方向综述" | Write a direction-level literature review (regular 40-80 refs / deep 80-120 refs) |

> **Workflow rule**: unless you explicitly ask for `"full pipeline"`, workflows run independently by default and do not automatically chain themselves. If prerequisites are missing, the agent will tell you what to do first.

> **Review and revision relationship**: `auto-review-loop` is the general research audit workflow and does not overwrite the source by default, but it returns a final recommended version. `resubmit-audit` is target-venue transfer audit and returns a complete revised draft. `paper-review-loop` runs venue-report-grounded review → revision → post-revision audit. All three prefer a Codex-compatible MCP reviewer; in Claude Code the reviewer name is `codex`.

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

### ❓ What is the simplest way to use these skills?

Currently the cheapest and most feasible approach is **Codex + Claude Code (with DeepSeek V4 Pro)**. Codex provides MCP reviewer capabilities, Claude Code serves as the main Agent executing the workflows, and DeepSeek V4 Pro serves as the backend model for cost-effective reasoning. This combination covers all 25 workflows without requiring additional paid Agent subscriptions.

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
- [Automated research ideas from wanshuiyin/Auto-claude-code-research-in-sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)

## License

MIT
