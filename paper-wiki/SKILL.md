---
name: paper-wiki
description: |
  Academic literature management and survey system. Supports journal organization,
  tag management, literature survey report generation, and submission recommendation.
  Trigger: user mentions "literature", "paper", "survey", "journal", "submission",
  "paper-wiki", or requests scan/report/recommendation on an initialized vault.
---

# paper-wiki — Academic Literature Survey Skill

> Manage a local Markdown literature vault. Scan, organize, tag, survey, and recommend — all from one skill.

## What This Skill Does

paper-wiki turns a folder of paper Markdown files into a structured, indexed literature vault with:

- **Journal organization**: auto-sort papers into `paper/{direction}/{journal_abbr}/`
- **Tag management**: multi-dimensional tagging (task, method, dataset, domain, signal, etc.)
- **Survey reports**: journal reports, direction reports, method/dataset stats, idea novelty surveys, literature reviews
- **Submission guidance**: journal scoring, revision suggestions, resubmit audits, review loops

## Quick Start

- "Initialize vault" → **init**
- "Scan Battery papers" → **scan-organize**
- "Generate RESS journal report" → **journal-report**
- "Recommend submission target for my paper" → **submission-recommend**

---

## Configuration

Configuration is read from `config.json` at project root. Key sections: `output_lang`, `templates`, `research_workflows`, `web_search`. For the full schema, field descriptions, and defaults, see `docs/configuration.md`. Before workflows that depend on vault paths, language settings, or report behavior, inspect `config.json` and apply its active values.

---

## Output Language Rules

All internal content (this SKILL.md, schemas, scripts, templates) is in **English**. User-facing output follows `output_lang` from `config.json`: `zh` → Chinese, `en` → English. File paths, directory names, variable names, and frontmatter keys remain in English regardless of `output_lang`.

---

## Report Citation Policy

All report-generation workflows must maintain a citation registry:

- Mark every evidence-bearing paper with `[N]` in prose, tables, and claims. Number by first appearance; reuse numbers.
- The final References section must include every cited paper and ONLY cited papers.
- Reference format: `[N] Title. Journal, Year. DOI: xxx. URL: xxx. Source: local path or [arxiv-web].`
- Omit missing fields (DOI, URL, year) rather than using placeholders.
- Before finalizing: verify citation numbers are continuous, every in-text citation has one reference entry, and every reference entry is cited at least once.
- Direction-review scope: standard 40-80 refs; deep 80-120 refs. Every reference must be cited in the body.

---

## Full-Coverage Report Policy

For `journal-report` and `direction-report`, the evidence pipeline is mandatory. The protocol enforces screening, coverage ledger, citation traceability, and unsupported-claim risk checks. `report_family.py --complete` is the authoritative completion gate.

**Full protocol**: Load `references/evidence-validation-protocol.md` together with the report workflow reference file before execution.

**Summary**: Stage 1 builds screening/ledger evidence files → Stage 2 writes the report with full-coverage matrix → Stage 3 verifies count equality → Stage 4 runs the hard completion gate. `--metadata-only` overrides to the legacy deterministic path.

---

## How Workflows Execute

**SKILL.md is the dispatch layer, not the operational manual.** When a user request matches a row in the routing table below:

1. Load the referenced workflow file(s) from the skill directory.
2. Execute the steps defined in that file.
3. Do not execute a workflow from the routing table alone — catalog entries provide routing, not procedure.
4. If a workflow references another workflow by name, load that workflow's reference file before using it.

**Required files may include both a workflow reference file and supporting reference files.** Load all listed files before execution.

---

## Workflow Routing

Route user intent to the appropriate workflow and reference file:

| User Intent | Workflow | Reference File |
|:---|:---|:---|
| "initialize vault" / "初始化文献库" | init | `references/workflows/01-init.md` |
| "scan papers" / "扫描文献", "organize by journal" / "整理期刊" | scan-organize | `references/workflows/02-scan-organize.md` |
| "ingest" / "入库", "process paper" / "处理论文" | ingest | `references/workflows/03-ingest.md` |
| "tag" / "标签", "assign tags" / "打标" | tag | `references/workflows/04-tag.md` |
| "journal report for XX" / "XX期刊报告" | journal-report | `references/workflows/05-journal-report.md` + `references/evidence-validation-protocol.md` |
| "direction report for XX" / "XX方向报告" | direction-report | `references/workflows/06-direction-report.md` + `references/evidence-validation-protocol.md` |
| "review paper" / "literature review" / "综述" | direction-review | `references/workflows/18-direction-review.md` |
| "method stats" / "方法统计", "dataset stats" | stat-report | `references/workflows/07-stat-report.md` |
| "idea survey" / "novelty survey" / "idea调研" | idea-survey | `references/workflows/08-idea-survey.md` |
| "prepare evidence for research ideas" / "idea evidence" | idea-evidence | `references/workflows/19-idea-evidence.md` |
| "generate research ideas" / "找idea" / "brainstorm" | idea-create | `references/workflows/20-idea-create.md` |
| "idea discovery pipeline" / "idea全流程" | idea-discover | `references/workflows/21-idea-discover.md` |
| "check novelty" / "claim novelty" / "claim查新" | idea-claim-novelty-check | `references/workflows/22-idea-claim-novelty-check.md` |
| "review my paper" / "adversarial review" / "多轮审稿" | auto-review-loop | `references/workflows/23-auto-review-loop.md` |
| "review and revise my paper for this venue" / "论文审稿改稿闭环" | paper-review-loop | `references/workflows/25-paper-review-loop.md` |
| "resubmit audit" / "venue transfer audit" / "转投审计" | resubmit-audit | `references/workflows/24-resubmit-audit.md` |
| "read this paper" / "单篇文献精读" | paper-read | `references/workflows/17-paper-read.md` |
| "web find" / "联网检索" / "search papers" | web-find | `references/workflows/09-web-find.md` |
| "daily digest" / "今日 arxiv" / "最新预印本" | web-digest | `references/workflows/10-web-digest.md` |
| "import web clipper" / "导入 web clipper" | web-import-clipper | `references/workflows/11-web-import-clipper.md` |
| "submission recommendation" / "投稿推荐" | submission-recommend | `references/workflows/12-submission-recommend.md` |
| "revision suggestions" / "修改建议" | revision-suggest | `references/workflows/13-revision-suggest.md` |
| "vault status" / "文献库状态" | status | `references/workflows/14-status.md` |
| "health check" / "检查" / "lint" | lint | `references/workflows/15-lint.md` |
| "full pipeline" / "完整流程" | pipeline | `references/workflows/16-pipeline.md` |

**Routing notes:**
- Every workflow runs independently. If preconditions are unmet, output a clear message but do NOT auto-chain unless the user explicitly requests "full pipeline".
- **direction-review** = literature review / survey synthesis. **idea-survey** = novelty/similarity analysis for a specific idea.
- For reviewer-backed workflows (idea-evidence, idea-create, idea-discover, idea-claim-novelty-check): prefer Codex-compatible MCP reviewer, otherwise dual-agent, otherwise degraded single-agent. Label degraded mode.
- For review/audit workflows (auto-review-loop, resubmit-audit, paper-review-loop): prefer Codex-compatible MCP reviewer. In Claude Code, explicitly call `codex`. Fallback to dual-agent then single-agent degraded.
- **Conference Seed Mode**: When idea-create is triggered with an explicit conference paper file path, load `references/workflows/19-idea-evidence.md` and execute its `### Conference Seed Mode` section first. The routing table entry for idea-create includes this path; the activation gate is in `references/workflows/20-idea-create.md`.

---

## Precondition Matrix

| Workflow | Requires | Auto-generated by |
|:---|:---|:---|
| init | — | — |
| scan-organize | init | — |
| ingest | init | — |
| tag | ingest (≥1 canonical page) | ingest |
| journal-report | ingest (canonical pages for target journal) | ingest |
| direction-report | ingest (canonical pages) + query | ingest |
| direction-review | ingest (canonical pages with readable `source_path`) | ingest; web supplementation inside workflow |
| stat-report | ingest + tag | ingest, tag |
| idea-survey | init + source papers; canonical/index preferred | ingest (preferred), web-find (optional) |
| idea-evidence | init + research topic or brief. In Conference Seed Mode a verified conference paper file may serve as the seed. | user input, idea-discover Phase 0, idea-create activation gate |
| idea-create | init + topic research brief + compatible evidence pack. If conference paper file provided, Workflow 19 Conference Seed Mode must run first. | idea-evidence, idea-evidence Conference Seed Mode |
| idea-discover | init + research topic or brief. Does NOT auto-activate Conference Seed Mode. If conference paper is provided, ask user. | Phase 0 creates/updates brief |
| idea-claim-novelty-check | init + method or idea description | — |
| auto-review-loop | init + research output (paper draft, experiment report, or method proposal) | — |
| paper-review-loop | init + paper draft + target venue report or compatible resubmit-audit report | resubmit-audit can provide downstream evidence |
| resubmit-audit | init + paper draft + target venue info | resolves or generates target venue report |
| paper-read | init + one source or canonical paper | ingest (preferred) |
| web-find | init + query | init |
| web-digest | init + config.json domain_profiles | web-find |
| web-import-clipper | init + file list from clipper | init |
| submission-recommend | init + paper draft + canonical pages | journal-report |
| revision-suggest | init + paper draft + journal-report + target-journal canonical pages | journal-report |
| status | init | — |
| lint | init + scan-organize preferred | — |
| pipeline | init | orchestrates: init → scan → ingest → tag → index → status |

---

## Workflow Catalog

| # | Workflow | Reference File | Purpose |
|:---:|:---|:---|:---|
| 1 | init | `references/workflows/01-init.md` | Initialize vault directory structure and default configuration |
| 2 | scan-organize | `references/workflows/02-scan-organize.md` | Scan paper/ directory, optionally organize by journal |
| 3 | ingest | `references/workflows/03-ingest.md` | Extract metadata, generate canonical pages, convert HTML tables |
| 4 | tag | `references/workflows/04-tag.md` | Multi-dimensional tag analysis and assignment |
| 5 | journal-report | `references/workflows/05-journal-report.md` | Journal-specific full-text literature survey |
| 6 | direction-report | `references/workflows/06-direction-report.md` | Topic-focused full-text direction survey |
| 7 | stat-report | `references/workflows/07-stat-report.md` | Deterministic tag-dimension statistics |
| 8 | idea-survey | `references/workflows/08-idea-survey.md` | LLM/full-text idea similarity and novelty survey |
| 9 | web-find | `references/workflows/09-web-find.md` | Multi-source web search (OpenAlex, Semantic Scholar, arXiv) |
| 10 | web-digest | `references/workflows/10-web-digest.md` | Recent arXiv preprint digest by direction |
| 11 | web-import-clipper | `references/workflows/11-web-import-clipper.md` | Import Obsidian Web Clipper files and generate canonical pages |
| 12 | submission-recommend | `references/workflows/12-submission-recommend.md` | 6-dimension journal scoring and recommendation |
| 13 | revision-suggest | `references/workflows/13-revision-suggest.md` | 5-dimension targeted revision suggestions |
| 14 | status | `references/workflows/14-status.md` | Vault-wide status overview |
| 15 | lint | `references/workflows/15-lint.md` | Health check: errors, conflicts, stale indexes |
| 16 | pipeline | `references/workflows/16-pipeline.md` | Composite chain: init → scan → ingest → tag → index → status |
| 17 | paper-read | `references/workflows/17-paper-read.md` | Deep single-paper reading with fixed question template |
| 18 | direction-review | `references/workflows/18-direction-review.md` | Direction-level literature review (40-80 / 80-120 refs) |
| 19 | idea-evidence | `references/workflows/19-idea-evidence.md` | Build evidence pack for idea generation (local + ≥50 web) |
| 20 | idea-create | `references/workflows/20-idea-create.md` | Generate and rank 8-12 research ideas from evidence pack |
| 21 | idea-discover | `references/workflows/21-idea-discover.md` | Orchestrate survey→evidence→create→novelty-check pipeline |
| 22 | idea-claim-novelty-check | `references/workflows/22-idea-claim-novelty-check.md` | Per-claim novelty scoring with evidence provenance |
| 23 | auto-review-loop | `references/workflows/23-auto-review-loop.md` | Multi-round adversarial research audit |
| 24 | resubmit-audit | `references/workflows/24-resubmit-audit.md` | Target-venue transfer audit with revised draft |
| 25 | paper-review-loop | `references/workflows/25-paper-review-loop.md` | Venue-conditioned review→revision→post-revision audit loop |

---

## Template System

Templates live in `templates/generic/`. Domain-specific templates in `templates/domains/{Direction}/`. The template registry is tracked in `config.json` → `templates.registry`.

**Status check** (`status` workflow): reports template coverage and staleness.
**Lint** (`lint` workflow): detects missing or stale domain templates.
**Regeneration** threshold is set in `config.json` → `templates.regeneration_threshold`.

---

## Safety Rules

1. **Never delete** files in `paper/` — these are the user's original paper Markdown files
2. **File moves** require `--dry-run` first, then user confirmation before `--apply`
3. **Preserve `## User Notes`** — never overwrite content under this heading in any file
4. **Log everything** — all file operations go to `workspace/logs/`
5. **Tag priority** — user tags > rule tags > manually confirmed extra suggestions (never remove user tags)
6. **No cross-direction moves** — files stay within their research direction unless user explicitly requests
7. **No overwrites** — if target file exists during organize, log as conflict, do not overwrite

---

## Frontmatter Template

```yaml
---
title: ""
authors: []
journal: ""
journal_abbr: ""
published_date: null
doi: ""
url: ""
source_path: ""
direction: ""
canonical_type: "research" | "survey" | "review"

tags_task: []
tags_method: []
tags_dataset: []
tags_domain: []
tags_signal: []
tags_application: []
tags_metric: []
tags_custom: []

status: "unread"
reading_priority: "medium"
updated_at: timestamp
---

# Title

## Source

## Abstract

## Keywords

## User Notes
<!-- User-maintained section. Scripts must never overwrite this. -->
```
