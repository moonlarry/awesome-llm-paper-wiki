---
name: paper-wiki
description: |
  Academic literature management and survey system. Supports journal organization,
  tag management, literature survey report generation, review-paper/literature-review
  drafting, and submission recommendation. Trigger: user mentions "literature",
  "paper", "survey", "review paper", "literature review", "journal", "submission",
  "paper-wiki", or requests scan/report/recommendation/review on an initialized vault.
---

# paper-wiki - Academic Literature Survey Skill

Manage a local Markdown literature vault: scan, organize, ingest, tag, generate survey reports,
read individual papers, search academic web sources, and recommend submission targets.

## Quick Start

- "Initialize vault" / "初始化文献库" -> run **init**
- "Scan papers" / "扫描文献" -> run **scan-organize**
- "Ingest papers" / "入库" -> run **ingest**
- "Generate RESS journal report" / "RESS期刊报告" -> run **journal-report**
- "Write a literature review" / "方向综述" -> run **direction-review**
- "Read this paper" / "单篇文献精读" -> run **paper-read**
- "Web find papers" / "联网检索" -> run **web-find**
- "Recommend submission target" / "投稿推荐" -> run **submission-recommend**
- "Vault status" / "文献库状态" -> run **status**

Use this file as the always-loaded entrypoint. Read reference files only when the user's task needs
that detail.

## Reference Map / 按需读取

All detailed references are one level deep under `references/`.

| Need | Read |
|------|------|
| Config fields, default `config.json`, template registry, domain profile options | [configuration.md](references/configuration.md) |
| init, scan-organize, ingest, tag | [workflows-core.md](references/workflows-core.md) |
| journal-report, direction-report, direction-review, stat-report, idea-survey, submission-recommend, revision-suggest, paper-read | [workflows-reports.md](references/workflows-reports.md) |
| web-find, web-digest, web-import-clipper, academic source/data-layer rules | [workflows-web.md](references/workflows-web.md) |
| status, lint, pipeline, maintenance utilities | [workflows-maintenance.md](references/workflows-maintenance.md) |
| Script inventory and formal command surface | [scripts.md](references/scripts.md) |
| Schema details, canonical page format, frontmatter fields | [schema.md](references/schema.md) |
| User-facing Chinese output examples for workflows | [output-formats.md](references/output-formats.md) |

Do not duplicate long details from those references in the answer. Load the narrowest file that
matches the workflow, then execute from that reference plus the core rules below.

## Workflow Routing

Route user intent to the appropriate workflow:

| User intent | Workflow |
|-------------|----------|
| initialize vault / 初始化文献库 | **init** |
| scan papers / 扫描文献 / organize by journal / 整理期刊 | **scan-organize** |
| ingest / 入库 / process paper / 处理论文 | **ingest** |
| tag / 标签 / assign tags / 打标 | **tag** |
| journal report / 期刊报告 | **journal-report** |
| direction report / 方向报告 | **direction-report** |
| review paper / literature review / 综述 / direction review | **direction-review** |
| method stats / dataset stats / 方法统计 / 数据集统计 | **stat-report** |
| idea survey / novelty survey / idea调研 | **idea-survey** |
| read this paper / 单篇文献精读 / 阅读这篇文献 | **paper-read** |
| web find / 联网检索 / 查找论文 / search papers | **web-find** |
| daily digest / 今日 arxiv / 最新预印本 | **web-digest** |
| import web clipper / 导入 web clipper | **web-import-clipper** |
| submission recommendation / 投稿推荐 | **submission-recommend** |
| revision suggestions / 修改建议 | **revision-suggest** |
| vault status / 文献库状态 | **status** |
| health check / 检查 / lint | **lint** |
| full pipeline / 完整流程 | **pipeline** |

Use **direction-review** for survey-style review-paper drafting over a direction or focused topic.
Use **direction-report** for shorter status reports, and **idea-survey** for novelty/similarity
checks on a specific idea.

Every workflow can run independently. If preconditions are unmet, report the missing prerequisite
and stop unless the user explicitly requests the full pipeline or asks you to perform the missing
step.

## Preconditions

| Workflow | Requires |
|----------|----------|
| init | none |
| scan-organize | init |
| ingest | init |
| tag | ingest with at least one canonical page |
| journal-report | canonical pages for the target journal |
| direction-report | canonical pages plus a query or direction |
| direction-review | canonical pages with readable `source_path` for the direction; optional focus |
| stat-report | canonical pages with tags |
| idea-survey | source papers; canonical/index preferred; web search optional |
| paper-read | one source or canonical paper |
| web-find | init plus query; CLI requires existing direction |
| web-digest | init plus query; CLI requires existing direction |
| web-import-clipper | init plus existing direction |
| submission-recommend | candidate journal evidence; journal reports preferred |
| revision-suggest | target journal evidence; journal report preferred |
| status | init |
| lint | init |
| pipeline | none |

When a precondition is not met, output:

- `zh`: `前置条件未满足：需要先运行 {workflow_name}。`
- `en`: `Precondition not met: run {workflow_name} first.`

## Output Language Rules

All internal skill material, schemas, scripts, template structure, paths, variable names, and
frontmatter keys remain in English.

All user-facing output follows `output_lang` in root `config.json`:

- `zh`: Chinese reports, console messages, and status summaries.
- `en`: English equivalents with identical structure.

For concrete Chinese workflow output examples, read [output-formats.md](references/output-formats.md).

## Report Citation Policy

All multi-paper report workflows must maintain a citation registry while writing.

- Add a numeric citation marker wherever a paper supports prose, tables, comparisons, trends,
  recommendations, scoring, or revision advice.
- Use `[1]`, `[2]`, and so on, numbered by first appearance. Reuse the same number for the same paper.
- The final `References` / `Reference List` section must include every cited paper and only cited papers.
- Do not list retrieved or matched papers that are not used as evidence.
- Reference entries use: `[N] Title. Journal, Year. DOI: xxx. URL: xxx. Source: local path or [arxiv-web].`
- If DOI is missing, omit DOI. If URL is missing, use `source_path`. If journal is missing, use
  `journal_abbr` or `arXiv`. If year is missing, use `published_date`; if unavailable, use `n.d.`

Before finalizing a report, verify that citation numbers are continuous, every in-text citation has
one reference entry, and every reference entry is cited at least once.

Direction-review reference-count defaults:

- Standard `direction-review`: target 40-80 references unless the user explicitly asks for a
  shorter note or the corpus is too sparse to support that range.
- Deep `direction-review`: target 80-120 references when the user explicitly asks for a deep,
  comprehensive, full-survey, or journal-style long review.
- Do not inflate the reference list artificially. Every reference must still be cited in the body
  and used as evidence.

## Full-Coverage Report Policy

For `journal-report` and `direction-report`, if the report claims to analyze all selected, readable,
confirmed, or relevant papers, maintain a `coverage_ledger` before writing.

- Confirm the evidence set first. Separate records into `confirmed_included`,
  `excluded_wrong_scope`, `skipped_unreadable`, and `uncertain_needs_review`.
- Cite every `confirmed_included` paper at least once in the report body. Prefer a `Paper Coverage
  Matrix` table for this.
- Do not satisfy coverage by adding uncited papers directly to the reference list.
- Representative-only reports are allowed only when the user explicitly asks for a brief,
  selective, or representative report; state that boundary in `Coverage / Source Set`.

Before finalizing a full-coverage report, verify:

- `confirmed_included_count == coverage_ledger_count`
- `coverage_ledger_count == unique_cited_paper_count`
- `unique_cited_paper_count == reference_entry_count`
- Every excluded, skipped, or uncertain record is reported separately and is not listed in references.

## Evidence Rules

- Use canonical pages as index anchors; use `source_path` to read original Markdown under `paper/`
  when report or reading conclusions require full-text evidence.
- For `paper-read`, ground answers in the selected paper text. Label inference explicitly and write
  "Not available in the provided paper text" when evidence is missing.
- Do not use external literature unless the workflow or user request explicitly calls for web search
  or comparison.

## Safety Rules

1. Never delete files in `paper/`; these are the user's original paper Markdown files.
2. File moves require a dry run first, then user confirmation before applying.
3. Preserve `## User Notes`; never overwrite content under this heading.
4. Log file operations to `workspace/logs/`.
5. Preserve tag priority: user tags > rule tags > manually confirmed extra suggestions.
6. Do not remove user tags during automated or rule-assisted tagging.
7. Do not move files across directions unless the user explicitly requests it.
8. Do not overwrite existing target files; log conflicts instead.
