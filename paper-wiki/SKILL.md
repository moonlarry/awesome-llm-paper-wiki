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
- **Survey reports**: journal reports, direction reports, method/dataset stats, idea novelty surveys
- **Submission guidance**: journal scoring, revision suggestions based on local literature evidence

## Quick Start

- "Initialize vault" → **init**
- "Scan Battery papers" → **scan-organize**
- "Generate RESS journal report" → **journal-report**
- "Recommend submission target for my paper" → **submission-recommend**

---

## Configuration

All config is in `config.json` at project root. Key fields:

```json
{
  "output_lang": "zh",
  "templates": {
    "regeneration_threshold": 0.2,
    "registry": {}
  },
  "web_search": {
    "default_top": 10,
    "min_citations": 5,
    "openalex_email": "",
    "openalex_api_key": "",
    "semantic_scholar_api_key": "",
    "clipper_inbox": "workspace/web-inbox",
    "output_root": "paper/web_search",
    "arxiv_fulltext_default": true,
    "arxiv_output_root": "paper/web_search",
    "arxiv_fulltext_priority": ["html", "tex", "pdf", "api"],
    "domain_profiles": {
      "Battery": {"strict": true, "required_groups": [], "negative_keywords": [], "preferred_venues": []},
      "TimeSeries": {"strict": false, "keywords": []}
    },
    "sources": ["openalex", "semanticscholar", "arxiv"]
  }
}
```

- `output_lang`: `"zh"` (Chinese, default) or `"en"` (English) — controls all user-facing output
- `templates.registry`: tracks domain-specific template generation status
- `templates.regeneration_threshold`: ratio of new papers that triggers template refresh
- `web_search.default_top`: default number of online results to save
- `web_search.min_citations`: OpenAlex citation threshold for default web-find
- `web_search.openalex_api_key`: optional OpenAlex API key for normal quota-based access
- `web_search.openalex_email`: optional OpenAlex contact email / mailto metadata
- `web_search.semantic_scholar_api_key`: optional Semantic Scholar key
- `web_search.clipper_inbox`: Obsidian Web Clipper Markdown import folder
- `web_search.output_root`: research material layer for web search metadata and incomplete arXiv results
- `web_search.arxiv_fulltext_default`: default to arXiv full-text capture for arXiv results
- `web_search.arxiv_output_root`: root folder for web-search-only arXiv Markdown
- `web_search.arxiv_fulltext_priority`: arXiv capture priority, default `html > tex > pdf > api`
- `web_search.domain_profiles`: direction-level keywords, required keyword groups, negative keywords, and preferred venues used by web-find and web-digest domain filtering

---

## Output Language Rules

All internal content (this SKILL.md, schemas, scripts, template structure) is in **English**.

All user-facing output follows `output_lang` from `config.json`:
- `zh` → Chinese reports, console messages, status summaries
- `en` → English equivalents with identical structure

File paths, directory names, variable names, and frontmatter keys remain in English regardless of `output_lang`.

---

## Report Citation Policy

All report-generation workflows must maintain a citation registry while writing the report.

- Add a numeric citation marker at every place where a paper is used as evidence in prose, tables, comparisons, trend claims, journal recommendations, or revision suggestions.
- Use `[1]`, `[2]`, ... numbered by first appearance in the report. Reuse the same number for the same paper throughout the report.
- The final `References` / `Reference List` section must include every paper cited in the report body and only papers cited in the report body.
- Do not list papers that were retrieved or matched but not used as evidence. If a paper is included in the analysis, either cite it where it supports a claim or omit it from the final references.
- Reference entries use: `[N] Title. Journal, Year. DOI: xxx. URL: xxx. Source: local path or [arxiv-web].`
- If DOI is missing, omit the DOI field. If URL is missing, use `source_path`. If journal is missing, use `journal_abbr` or `arXiv`. If year is missing, use `published_date`; if unavailable, use `n.d.`

Before finalizing a report, verify that citation numbers are continuous, every in-text citation has one reference entry, and every reference entry is cited at least once.

---

## Workflow Routing

Route user intent to the appropriate workflow:

| User Intent | Workflow | Standalone? |
|-------------|----------|:-----------:|
| "initialize vault" / "初始化文献库" | → **init** | ✅ |
| "scan papers" / "扫描文献", "organize by journal" / "整理期刊" | → **scan-organize** | ✅ |
| "ingest" / "入库", "process paper" / "处理论文" | → **ingest** | ✅ |
| "tag" / "标签", "assign tags" / "打标" | → **tag** | ✅ |
| "journal report for XX" / "XX期刊报告" | → **journal-report** | ✅ |
| "direction report for XX" / "XX方向报告" | → **direction-report** | ✅ |
| "method stats" / "方法统计", "dataset stats" / "数据集统计" | → **stat-report** | ✅ |
| "idea survey" / "idea调研" | → **idea-survey** | ✅ |
| "read this paper" / "单篇文献精读" / "阅读这篇文献" | → **paper-read** | ✅ |
| "web find" / "联网检索" / "查找论文" / "search papers" | → **web-find** | ✅ |
| "daily digest" / "今日 arxiv" / "最新预印本" | → **web-digest** | ✅ |
| "import web clipper" / "导入 web clipper" | → **web-import-clipper** | ✅ |
| "submission recommendation" / "投稿推荐" | → **submission-recommend** | ✅ |
| "revision suggestions" / "修改建议" | → **revision-suggest** | ✅ |
| "vault status" / "文献库状态" | → **status** | ✅ |
| "health check" / "检查" / "lint" | → **lint** | ✅ |
| "full pipeline" / "完整流程" | → **pipeline** | ✅ |

**Important**: Every workflow can run independently. If preconditions are unmet, output a clear message (e.g., "No source manifest found. Run scan-organize first.") but do NOT auto-chain unless the user explicitly requests "full pipeline".

---

## Precondition Matrix

| Workflow | Requires | Auto-generated by |
|----------|----------|-------------------|
| init | — | — |
| scan-organize | init | — |
| ingest | init | — |
| tag | ingest (≥1 canonical page) | ingest |
| journal-report | ingest (canonical pages for target journal; optional direction/query filters) | ingest |
| direction-report | ingest (canonical pages) + query; optional direction filter | ingest |
| stat-report | ingest + tag | ingest, tag |
| idea-survey | init + source papers; canonical/index preferred; web search optional | ingest (preferred), web-find (optional) |
| paper-read | init + one source or canonical paper | ingest (preferred) |
| web-find | init + query; CLI requires existing direction, Agent may bootstrap a missing one after confirmation | init |
| web-digest | init + query; CLI requires existing direction, Agent may bootstrap a missing one after confirmation | init |
| web-import-clipper | init + existing direction | init |
| submission-recommend | journal-report (for candidate journals) | journal-report |
| revision-suggest | journal-report (for target journal) | journal-report |
| status | init | — |
| lint | init | — |
| pipeline | — | — |

When a workflow's precondition is not met, output:
- `zh`: "前置条件未满足：需要先运行 {workflow_name}。"
- `en`: "Precondition not met: run {workflow_name} first."

---

## Template System

### Generic Templates

Located in `templates/generic/`. Domain-agnostic, ship with the skill.
Used as fallback when no domain-specific template exists.

Templates use `{{variable}}` placeholders as reusable report structure references.
For `report_family.py`, the default formal CLI path for `journal-report` and `direction-report` now prepares a full-text run bundle in `workspace/cache/fulltext-report/`.
Agent or LLM workflows must read `records[*].source_path` from that bundle and write the final report from full-text evidence.
Use `--metadata-only` only when a deterministic canonical-metadata report is explicitly desired.

Available generic templates:
- `paper_canonical.md` — standard literature page
- `journal_report.md` — journal survey report
- `direction_report.md` — research direction report
- `idea_survey_report.md` — idea novelty survey
- `paper_reading.md` — single-paper reading note
- `stat_report.md` — method/dataset/experiment statistics
- `submission_report.md` — submission recommendation
- `revision_report.md` — revision suggestions

### Domain-Specific Templates

Located in `templates/domains/{domain_name}/`.

Current codebase status:
- `config.json` can track template registry metadata
- `status_report.py` and `lint_vault.py` report registry state and staleness signals
- the current formal CLI path does **not** auto-generate new domain templates

Practical rule:
1. Prefer existing generic templates as the stable reference structure
2. If a domain template already exists and the user explicitly wants it, treat it as a manual or Agent-selected reference
3. Do not describe domain-template auto-generation as an implemented default behavior

---

## Workflow 1: init

### Purpose
Initialize the vault structure. Creates missing directories and seed files.

### Steps

1. Check if `E:\paper` has `config.json` — if not, create default config
2. Create missing directories:
   - `schema/`
   - `library/papers/`, `library/reports/journal/`, `library/reports/direction/`, `library/reports/idea/`, `library/reports/paper/`, `library/reports/submission/`, `library/reports/vault/`
   - `library/indexes/`
   - `workspace/cache/`, `workspace/manifests/`, `workspace/logs/`, `workspace/legacy/`
   - `templates/generic/`, `templates/domains/`
3. Create `schema/tag_taxonomy.json` if missing (empty initial structure)
4. Create `schema/keyword_rules.json` if missing (empty rules array)
5. Create `schema/paper_frontmatter.schema.md` if missing
6. Skip creating generic templates if they already exist
7. Update `paper-library.md` with skeleton if needed

### Output (zh)
```
文献库初始化完成！路径：E:\paper

已创建目录：{list}
已创建文件：{list}

接下来你可以：
- "扫描文献" — 扫描 paper/ 目录
- "整理期刊" — 按期刊缩写归类文件
- "入库" — 处理论文并生成 canonical 页
```

---

## Workflow 2: scan-organize

> **Status**: Implemented (main flow) | duplicate detection: Implemented

### Purpose
Scan `paper/` for all Markdown files and optionally organize them into journal folders.

### Sub-triggers
- "scan papers" / "扫描文献" → steps 1–3 only (scan + plan)
- "organize by journal" / "整理期刊" → steps 1–6 (scan + move + index)
- "check duplicates" / "检查重复" → steps 1, 4 only

### Steps

1. Run: `python scripts/scan_sources.py`
   - Output: `workspace/manifests/source_manifest.json`

2. Run: `python scripts/organize_by_journal.py --all --dry-run`
   - Output: `workspace/manifests/journal_move_plan.json`

3. Display plan summary to user:
   - Files to move (count by action: move/skip/warn/conflict)
   - Journal distribution

4. **(If "check duplicates")**: Run `python scripts/detect_duplicates.py --all`:
   - Compare file SHA256 checksums (exact) and normalized title+year (probable)
   - Generate `workspace/manifests/duplicate_report.json` and `.md`

5. **(If "organize by journal")**: Ask user to confirm, then:
   - Run: `python scripts/organize_by_journal.py --all --apply`

6. Run: `python scripts/rebuild_indexes.py`
   - Triggers domain profile update (see Template System)

### Output (zh)
```
扫描完成：{N} 个文件

按操作分类：
- 移动：{move_count}
- 跳过：{skip_count}
- 冲突：{conflict_count}
- 警告：{warn_count}

计划已保存：workspace/manifests/journal_move_plan.json
是否执行移动？(y/n)
```

---

## Workflow 3: ingest

### Purpose
Process paper Markdown files: extract metadata, generate canonical pages, convert HTML tables.

### Input
- A specific file path, or "all new papers", or a journal/direction scope

### Steps

1. Identify target files:
   - If path given → process that file
   - If "all" → scan `paper/` for files without corresponding canonical pages in `library/papers/`
   - If journal/direction given → filter accordingly

2. For each target file:

   a. **Read file** and parse frontmatter using the same logic as `scripts/common.py`

   b. **Extract/complete metadata**:
      - `title`: from frontmatter or filename
      - `journal`, `journal_abbr`: from `resolve_journal()` logic
      - `published_date`: parse from frontmatter `published`, `created`, or body text
      - `doi`: extract from frontmatter `source` or body DOI patterns
      - `url`: from frontmatter `source`

   c. **Generate paper ID**: `{direction}-{year}-{journal_abbr}-{slug}`
      - slug = first 5 significant words of title, lowercase, hyphenated

   d. **Identify tag candidates** from title, abstract, keywords, highlights:
      - Match against `schema/keyword_rules.json` patterns
      - Agent or LLM review can optionally suggest extra tags during a manual path
      - Rule-based tagging is the only built-in automatic write-back path

   e. **Convert HTML tables** to Markdown:
      - Run: `python scripts/html_table_to_md.py <file_path>` (if HTML tables found)
      - Or an Agent can convert simple tables inline during a manual path

   f. **Generate canonical page** to `library/papers/{direction}/{paper_id}.md`:
      - Use template: `templates/generic/paper_canonical.md`
      - Fill frontmatter fields, abstract, keywords
      - Set `source_path` to link back to original source file
      - Preserve `## User Notes` section if existing canonical page already exists

3. **Domain profile update**: Count papers by domain tag, update `config.json` template registry

### Batch Command
```bash
python scripts/ingest_batch.py --direction Battery --journal Energy --apply-tags --rebuild-indexes
python scripts/ingest_batch.py --file paper/Battery/arxiv/example.md --apply-tags
python scripts/ingest_batch.py --direction Battery --dry-run
```

### Output (zh)
```
入库完成：处理了 {N} 篇论文

新增 canonical 页：
- {paper_id_1}
- {paper_id_2}

标签候选（需确认）：
- "transfer learning" → method [新标签]
- "CALCE" → dataset [已有标签]

确认添加新标签？(y/n)
```

---

## Workflow 4: tag

> **Status**: Implemented (read-only audit and write-back paths clarified)

### Purpose
Manage the tag system: view, edit, batch-assign, and analyze tags.

### Sub-triggers
- "view tags" / "查看标签" → display tag_taxonomy.json summary
- "batch tag" / "批量打标" → run keyword rules on all canonical pages
- "add tag" / "添加标签" → add a custom tag to taxonomy
- "tag stats" / "标签统计" → show tag frequency distribution

### Scripts

| Script | Purpose | Command |
|--------|---------|---------|
| `scan_tags.py` | **Read-only audit**: scan tag coverage, rule hits | `python scripts/scan_tags.py --direction Battery --rules` |
| `ingest_batch.py --apply-tags` | **Write-back entry**: batch tag canonical pages | `python scripts/ingest_batch.py --direction Battery --apply-tags` |

**Note**: `scan_tags.py` is read-only and never modifies canonical pages. Tag write-back must use `ingest_batch.py --apply-tags`.

### Steps (batch tag)

1. Load `schema/tag_taxonomy.json` and `schema/keyword_rules.json`

2. For each canonical page in `library/papers/`:
   a. Read frontmatter tags
   b. Apply keyword rules to title, abstract, keywords sections
   c. Optional Agent review may suggest additional tags for manual confirmation
   d. Merge rule: preserve user tags; add keyword-rule hits without overwriting existing user edits

3. Apply tag updates through `python scripts/ingest_batch.py --direction Battery --apply-tags`

4. Rebuild indexes when batch tagging changes canonical frontmatter

### Commands
```bash
python scripts/ingest_batch.py --direction Battery --apply-tags --rebuild-indexes
python scripts/scan_tags.py --direction Battery
python scripts/scan_tags.py --direction Battery --rules --include-empty
```

### Output (zh)
```
批量打标完成：更新了 {N} 篇论文的标签

标签分布：
- task: SOH estimation (45), RUL prediction (38), SOC estimation (12), ...
- method: LSTM (28), Transformer (22), GPR (15), PINN (12), ...
- dataset: NASA (35), CALCE (30), Oxford (18), ...

新增标签：{list}
```

---

## Workflow 5: journal-report

### Purpose
Prepare a full-text literature survey workflow for a specific journal.

### Formal CLI
```bash
python scripts/report_family.py --mode journal --journal RESS
python scripts/report_family.py --mode journal --journal RESS --direction Battery --query "soh"
python scripts/report_family.py --mode journal --journal RESS --metadata-only
```

### Steps

1. Load canonical records from `library/indexes/canonical_pages.json` (or rebuild in memory if the index is missing)
2. Filter by journal name or abbreviation
3. If `--direction` is set, further restrict to that exact direction
4. If `--query` is set, further restrict the journal subset using canonical query matching
5. Partition selected records into:
   - readable records with valid `source_path`
   - skipped records with missing/unreadable source files
6. Save a single disposable run bundle:
   - `workspace/cache/fulltext-report/{run_key}.json`
7. Agent reads **all** `records[*].source_path` in the bundle and writes the final report to:
   - `library/reports/journal/{journal_key}-report-{date}.md`
8. Write a compact preparation/completion log entry to `workspace/logs/report_generation.md`

### Notes
- `--mode journal --journal RESS` means journal-only selection: select all canonical papers from that journal and do not apply extra filtering
- `--direction` and `--query` only narrow the already-selected journal subset when explicitly provided
- Missing source files are skipped silently; detailed reasons stay only in the run-bundle JSON
- Final journal-report conclusions must come from full-text evidence, not from canonical metadata alone
- `--metadata-only` keeps the old deterministic canonical-metadata report path

---

## Workflow 6: direction-report

### Purpose
Prepare a full-text direction or topic status report from local canonical pages.

### Formal CLI
```bash
python scripts/report_family.py --mode direction --query "soh"
python scripts/report_family.py --mode direction --direction Battery --query "soh"
python scripts/report_family.py --mode direction --direction Battery --query "soh" --metadata-only
```

### Steps

1. Load canonical records from the whole vault
2. If `--direction` is set, restrict to that exact direction
3. Apply query matching using title, abstract, keywords, and tag fields
4. Partition selected records into readable vs. skipped by `source_path`
5. Save a single disposable run bundle:
   - `workspace/cache/fulltext-report/{run_key}.json`
6. Agent reads **all** `records[*].source_path` in the bundle and writes the final report to:
   - `library/reports/direction/{topic_slug}-report-{date}.md`
7. Write a compact preparation/completion log entry to `workspace/logs/report_generation.md`

### Notes
- `--mode direction --query "soh"` allows cross-journal local screening from the whole vault
- `--direction` only narrows the query scope when explicitly provided
- Missing source files are skipped silently; detailed reasons stay only in the run-bundle JSON
- Final direction-report conclusions must come from full-text evidence, not from canonical metadata alone
- `--metadata-only` keeps the deterministic canonical-metadata report path

---

## Workflow 7: stat-report

### Purpose
Generate deterministic statistics reports for one tag dimension.

### Formal CLI
```bash
python scripts/report_family.py --mode stat --direction Battery --dimension method
python scripts/report_family.py --mode stat --direction Battery --dimension dataset --cross-dimension method
```

### Steps

1. Load canonical records for the direction
2. Aggregate by the requested dimension:
   - count papers per tag value
   - compute yearly trend
   - compute cross-tabulation with another tag dimension
3. Generate deterministic Markdown tables
4. Save to `library/reports/direction/{dimension}-stats-{date}.md`

---

## Workflow 8: idea-survey

### Purpose
Survey literature similarity to a user idea and assess novelty through LLM/full-text reading.

### Current execution path
This workflow is **LLM/Agent-driven**, not implemented as a `report_family.py` screening mode.

### Steps

1. Use canonical pages only as an index to locate source files through `source_path`
2. Let the LLM/Agent read relevant source Markdown files under `paper/`
3. During reading, extract problem, method, dataset, experiment setup, baselines, metrics, results, and limitations
4. Let the LLM/Agent decide which papers are truly similar or dissimilar after reading full evidence
5. If web supplementation is needed, run `web_search.py find` first and then let the LLM/Agent read the resulting source Markdown
6. Generate the final report at `library/reports/idea/{idea_slug}-survey-{date}.md` only after the full-text review pass

### Notes
- Do not use keyword/tag similarity as the final idea candidate filter
- Do not treat metadata-only matches as novelty evidence
- Final novelty judgment must be grounded in source Markdown, not only canonical abstracts or tags

---

## Workflow 9: web-find

> **Status**: Implemented (CLI fail-fast; Agent may bootstrap missing direction)

### Purpose
Search academic web sources and save results as Markdown files in the local vault.

### Prerequisites
- **CLI path**: `paper/{direction}/` directory must already exist before running `web_search.py`
- **Agent path**: if direction is missing, the Agent may guide the user to choose one of two direction options and create it after confirmation

### Data Layers
- Formal full-text library: `paper/{direction}/{journal_abbr}/` for clipped journal papers and arXiv papers with extracted full text
- Web-search research layer: `paper/web_search/{direction}/{source}/` for OpenAlex/Semantic Scholar metadata and arXiv non-full-text fallbacks
- Knowledge layer: `library/` for canonical pages, indexes, and reports

### Input
- Required: `--direction {existing_direction}`
- Required: query text, e.g. `web-find --direction Battery --query "battery RUL transformer" --top 10`
- Optional: `--top N`, `--source mixed|openalex|semanticscholar|arxiv|venues`, `--fulltext`, `--no-fulltext`, `--arxiv-id`, `--no-domain-filter`, `--show-filtered`, `--dry-run`

### Steps

1. CLI behavior: validate that `paper/{direction}/` already exists. If missing, `web_search.py` fail-fast with guidance to create the direction before running `web-find`.

2. Agent recovery branch for a missing direction:
   - inspect the user query, configured directions, and `web_search.domain_profiles`
   - offer **two direction options**:
     - a best-match existing direction when one is plausible
     - a suggested new direction name; if no existing direction fits, offer two suggested new names
   - wait for user confirmation before making any filesystem or config changes
   - after confirmation, append the chosen direction to `config.json -> directions`, create `paper/{direction}/` and `paper/web_search/{direction}/`, and seed a minimal `web_search.domain_profiles.{direction}` stub
   - rerun the original `web-find` command with the confirmed direction

3. Fetch results:
   - Primary: OpenAlex (`search`, citation-filtered by `web_search.min_citations`; send `openalex_api_key` and optional `openalex_email` when configured)
   - In mixed/openalex mode, query both high-citation classic papers and recent papers, then merge and deduplicate
   - Secondary: Semantic Scholar, only when `semantic_scholar_api_key` is configured
   - `--source venues`: keep only OpenAlex candidates whose venue matches `web_search.domain_profiles.{direction}.preferred_venues`
   - Fallback: arXiv only when `--source arxiv`, or when `--source mixed` returns fewer than `--top`

4. Domain-filter, rank, and deduplicate:
   - Evaluate each candidate against `web_search.domain_profiles.{direction}`
   - Strict profiles require all configured `required_groups` and reject strong negative keyword hits
   - Save only accepted candidates unless `--no-domain-filter` is set
   - arXiv ID is the primary identity for arXiv results
   - DOI is the primary identity
   - normalized title + year is the fallback identity
   - never overwrite existing source Markdown files

5. Save OpenAlex / Semantic Scholar results to:
   - `paper/web_search/{direction}/openalex/{year}-{first_author}-{title_slug}.md`
   - `paper/web_search/{direction}/semanticscholar/{year}-{first_author}-{title_slug}.md`
   - API results include metadata, abstract, DOI/URL, source ID, and a note that formal full text should be supplied via Obsidian Web Clipper when needed

6. Save arXiv results by full-text status:
   - `full_text_extracted` → `paper/{direction}/arxiv/{year}-{first_author}-{title_slug}-{arxiv_id}.md`
   - `pdf_saved_only` / `abstract_only` / `failed` → `paper/web_search/{direction}/arxiv/{year}-{first_author}-{title_slug}-{arxiv_id}.md`
   - Try `html > tex > pdf > api` unless `--no-fulltext` is set

7. Generate canonical pages and rebuild indexes only for formal source saves under `paper/{direction}/`

8. Generate a web-find report:
   - `library/reports/web/{date}-{direction}-find-report.md`
   - Include local duplicates, arXiv full-text downloads, OA/SS metadata findings, skipped and failed records, and filtered-out candidates with reasons

9. Write manifest and log:
   - `workspace/manifests/arxiv_fulltext_results.json` for arXiv full text
   - `workspace/manifests/web_search_results.json` for OA/SS metadata saves
   - Include `filtered_out` so rejected candidates are auditable
   - `workspace/logs/web_search.md`

### Command
```bash
python scripts/web_search.py find --direction Battery --query "battery RUL transformer" --top 10
python scripts/web_search.py find --direction Battery --source arxiv --arxiv-id 2502.18807v7 --fulltext
```

---

## Workflow 10: web-digest

> **Status**: Implemented (CLI fail-fast; Agent may bootstrap missing direction)

### Purpose
Fetch recent arXiv papers for a direction and save them as Markdown sources plus a digest report.

### Input
- Required: `--direction {existing_direction}`
- Required: `--query "topic"`
- Optional: `--top N`, `--no-domain-filter`, `--show-filtered`, `--dry-run`

### Steps

1. CLI behavior: validate that `paper/{direction}/` already exists. If missing, `web_search.py` fail-fast with guidance to create the direction before running `web-digest`.
2. Agent recovery branch for a missing direction:
   - reuse the same bootstrap flow as `web-find`
   - analyze the query and existing direction/profile context
   - offer two direction options and wait for user confirmation
   - after confirmation, create the direction folders and config/profile stub, then rerun `web-digest`
3. Build a profile-aware arXiv query from `web_search.domain_profiles.{direction}`
4. Query arXiv by submitted date
5. Apply the same domain filter and ranking path used by `web-find`
6. Save arXiv full-text successes to `paper/{direction}/arxiv/`
7. Use the same `html > tex > pdf > api` fallback as `web-find`
8. Save PDF-only, abstract-only, and failed fallback records to `paper/web_search/{direction}/arxiv/`
9. Generate canonical pages and rebuild indexes only when a full-text arXiv paper entered the formal library
10. Generate digest report at `library/reports/web/{date}-{direction}-digest.md`, including filtered-out candidates
11. Log the operation

### Command
```bash
python scripts/web_search.py digest --direction Battery --query "battery health prognosis" --top 10
```

---

## Workflow 11: web-import-clipper

### Purpose
Import Obsidian Web Clipper Markdown into the vault as full-text source Markdown.

### Input
- Required: `--direction {existing_direction}`
- Optional: `--inbox path`, default from `web_search.clipper_inbox`
- Optional: `--dry-run`

### Steps

1. Read `.md` files from `workspace/web-inbox/` or the provided inbox path
2. Extract title, authors, year, journal, DOI, URL, and abstract from frontmatter/body
3. Deduplicate by DOI or normalized title + year
4. Save normalized Markdown to `paper/{direction}/{journal_abbr}/`
5. Preserve clipped body content and add missing vault metadata
6. Generate canonical pages, rebuild indexes, and write:
   - `workspace/manifests/web_clipper_import.json`
   - `workspace/logs/web_search.md`

The importer archives successfully imported inbox files to `workspace/web-inbox/imported/`. Dry-run and skipped-existing files are not moved.

### Command
```bash
python scripts/web_import_clipper.py --direction Battery
```

---

## Workflow 12: submission-recommend

### Purpose
Recommend suitable journals for a user's paper based on local literature evidence.

### Input
Path to the user's paper (Markdown file)

### Steps

1. Read and analyze the user's paper:
   - Extract: research topic, methods, datasets, key results, reference list

2. Identify candidate journals from the vault (all journals with ≥ 5 papers)

3. For each candidate journal:
   a. Read the journal report if it exists; otherwise prompt user to generate one first
   b. Score across 6 dimensions:

   | Dimension | Weight | Description |
   |-----------|--------|-------------|
   | topic_fit | 0.25 | Does the paper's topic match the journal's recent hotspots? |
   | method_fit | 0.20 | Does the method type align with the journal's preferences? |
   | novelty_fit | 0.20 | Is the paper differentiated from the journal's recent work? |
   | experiment_fit | 0.15 | Do datasets, metrics, and experiment scale meet journal norms? |
   | citation_fit | 0.10 | Does the reference list cover the journal's key papers? |
   | risk | -0.10 | Scope mismatch, insufficient novelty, experimental gaps |

   c. Compute total score (0–100 scale)

4. Rank top 5 journals by total score

5. **Generate report** → `library/reports/submission/{paper_slug}-recommend-{date}.md`
   - Use template: `templates/generic/submission_report.md`
   - Apply the Report Citation Policy: cite journal reports and underlying papers where they support scoring evidence or recommendations, and list all cited evidence in `References`.

### Output (zh)
```
投稿推荐报告

论文：{title}

推荐期刊 Top 5：
1. {journal_1}（{score_1}/100）— {reason}
2. {journal_2}（{score_2}/100）— {reason}
3. {journal_3}（{score_3}/100）— {reason}
4. {journal_4}（{score_4}/100）— {reason}
5. {journal_5}（{score_5}/100）— {reason}

报告已保存：library/reports/submission/{paper_slug}-recommend-{date}.md
```

---

## Workflow 13: revision-suggest

### Purpose
Generate targeted revision suggestions for a paper aimed at a specific journal.

### Input
- Path to the user's paper (Markdown file)
- Target journal name or abbreviation

### Steps

1. Read the user's paper

2. Read the target journal's literature collection (canonical pages)

3. Read the journal report if available

4. Compare across 5 dimensions:

   **a. Formatting (排版)**:
   - Section structure vs. typical papers in the journal
   - Figure/table style conventions
   - Length norms

   **b. Method Writing Style (方法写作风格)**:
   - How methods are typically presented in this journal
   - Level of mathematical formalism
   - Pseudo-code vs. text description preferences

   **c. Research Method Sufficiency (研究方法充足性)**:
   - Number of baselines typically compared
   - Ablation study expectations
   - Statistical significance testing norms

   **d. Introduction Alignment (引言适配)**:
   - Research motivation framing typical of this journal
   - Literature review scope and depth
   - Problem statement style

   **e. Reference Coverage (参考文献覆盖)**:
   - Key papers from this journal that should be cited
   - Reference count norms
   - Self-citation patterns

5. **Prioritize** suggestions by impact: critical → important → optional

6. **Generate report** → `library/reports/submission/{paper_slug}-revision-for-{journal}-{date}.md`
   - Use template: `templates/generic/revision_report.md`
   - Apply the Report Citation Policy: cite target-journal papers where they support formatting, method, experiment, introduction, reference-coverage, or action-list suggestions, and list all cited evidence in `Evidence Basis`.

### Output (zh)
```
面向 {journal} 的修改建议

评估维度：
- 排版：{score}/5 — {summary}
- 方法写作：{score}/5 — {summary}
- 研究方法：{score}/5 — {summary}
- 引言适配：{score}/5 — {summary}
- 参考文献：{score}/5 — {summary}

关键修改建议（共 {N} 条）：
1. [关键] {suggestion_1}
2. [关键] {suggestion_2}
3. [重要] {suggestion_3}
...

报告已保存：library/reports/submission/{paper_slug}-revision-for-{journal}-{date}.md
```

---

## Workflow 14: status

### Purpose
Display vault status summary.

### Formal CLI
```bash
python scripts/status_report.py
python scripts/status_report.py --direction Battery
```

### Steps

1. Load source records from `library/indexes/papers.json`
2. Load canonical records from `library/indexes/canonical_pages.json`
3. Summarize:
   - source / canonical counts
   - direction and journal distribution
   - tag coverage across `tags_*`
   - recent web/report activity from `workspace/logs/`
   - template registry state from `config.json`
4. Save:
   - `library/reports/vault/status-{date}.md`
   - `workspace/manifests/status_report.json`

### Output (zh)
```
文献库状态

论文总数：{total}
按方向：
- Battery: {count}
- TimeSeries: {count}

按期刊（前 5）：
- Energy: {count}
- JES: {count}
- RESS: {count}
- AppliedEnergy: {count}
- JPS: {count}

Canonical 页：{canonical_count} / {total}（{pct}% 已入库）
标签覆盖率：{tagged_count} / {canonical_count}（{pct}%）

领域模板：
- battery: ✅ 已生成（{date}，{paper_count} 篇时生成）
- timeseries: ❌ 未生成

最近操作：
{last_5_log_entries}
```

---

## Workflow 15: lint

### Purpose
Health check for the vault.

### Formal CLI
```bash
python scripts/lint_vault.py
python scripts/lint_vault.py --direction Battery
```

### Checks

1. **Orphan canonical pages**: canonical page exists but source file is missing
2. **Missing canonical pages**: source file exists but no canonical page
3. **Tag inconsistencies**: tags in canonical pages not in `tag_taxonomy.json`
4. **Stale indexes**: index files older than the latest source/canonical files
5. **Missing frontmatter**: canonical pages missing required fields
6. **Broken source_path**: canonical points to a non-existent source file
7. **Template staleness**: registry entries whose paper counts have outgrown their recorded baseline

### Output files
- `library/reports/vault/lint-{date}.md`
- `workspace/manifests/lint_vault.json`

### Output (zh)
```
文献库健康检查报告

✅ 通过：
- 索引更新状态
- 标签一致性

⚠️ 警告：
- {N} 篇论文未入库（无 canonical 页）
- {N} 个标签未在 taxonomy 中注册
- 领域模板 battery 已过时（新增 {pct}% 论文）

❌ 错误：
- {N} 个 canonical 页找不到源文件

建议操作：
1. 运行 "入库" 处理未入库论文
2. 运行 "标签" 更新标签体系
3. 运行 "重建索引" 刷新索引
```

---

## Workflow 16: pipeline

### Purpose
Execute the full preprocessing pipeline in sequence.

### Steps

Execute in order, stopping on errors:
1. **init**
2. **scan-organize** (scan only, no move unless user confirms)
3. **ingest** (all unprocessed papers)
4. **tag** (batch tag)
5. **rebuild indexes** (via `python scripts/rebuild_indexes.py`)
6. **status** (show final state)

### Output (zh)
```
完整流程执行完成

1. ✅ 初始化
2. ✅ 扫描：{N} 个文件
3. ✅ 入库：{N} 篇新增
4. ✅ 打标：{N} 篇更新
5. ✅ 索引重建
6. 当前状态：{summary}
```

---

## Workflow 17: paper-read

### Purpose
Read one paper deeply and generate a structured reading note for single-paper understanding.

Answer these questions:
- What problem does this paper solve?
- Why is this problem important?
- What method or model does it use?
- Why can this method or model solve the problem?
- What are the core conclusions?
- What can be done next?

### Input
- Required: one paper path, title, DOI, canonical id, or source path
- Preferred: canonical page under `library/papers/{direction}/`
- Allowed: source Markdown under `paper/{direction}/...`
- Optional: user research context, such as "focus on battery SOH" or "focus on method novelty"

### Steps

1. Locate the paper:
   - If input is a path, read it directly.
   - If input is a title, id, or DOI, search canonical pages first, then source files.
   - If both source and canonical exist, prefer canonical metadata and inspect source/full text when needed.

2. Read metadata:
   - title, authors, journal, year, DOI, source path, tags.

3. Read content:
   - Abstract
   - Introduction / motivation
   - Method / model
   - Experiments / datasets
   - Results
   - Limitations / discussion / conclusion
   - Full text via `source_path` if canonical page provided

4. Generate the reading note using `templates/generic/paper_reading.md`.

5. Evidence discipline:
   - Ground every answer in the paper text.
   - If a point is inferred rather than explicitly stated, label it as inference.
   - If information is missing, write "Not available in the provided paper text" rather than guessing.
   - Do not use external literature unless the user explicitly asks for comparison.
   - Because this workflow reads one paper, do not apply the multi-paper Report Citation Policy unless additional papers are used.

6. Save output when the user asks for a file or when a durable note is useful:
   - `library/reports/paper/{date}-{paper_id}-reading.md`

### Output (zh)
```
单篇文献精读：{title}

1. 这篇文章解决了什么问题？
{answer}

2. 这个问题为什么重要？
{answer}

3. 本文使用了什么方法或模型？
{answer}

4. 为什么这个方法或模型能解决这个问题？
{answer}

5. 核心结论是什么？
{answer}

6. 下一步可以怎么做？
{answer}

阅读笔记已保存：library/reports/paper/{date}-{paper_id}-reading.md
```

---

## Script Reference

Scripts are in `scripts/` and use Python standard library only.

| Script | Purpose | Usage |
|--------|---------|-------|
| `scan_sources.py` | Scan paper sources | `python scripts/scan_sources.py` |
| `organize_by_journal.py` | Journal-based file organization | `python scripts/organize_by_journal.py --all --dry-run` |
| `detect_duplicates.py` | Exact/probable duplicate detection | `python scripts/detect_duplicates.py --direction Battery` |
| `rebuild_indexes.py` | Rebuild indexes | `python scripts/rebuild_indexes.py` |
| `html_table_to_md.py` | Convert HTML tables | `python scripts/html_table_to_md.py <file>` |
| `resolve_journal.py` | Inspect journal resolution for one source file | `python scripts/resolve_journal.py paper/Battery/Energy/example.md` |
| `ingest_batch.py` | Batch-generate canonical pages and optionally apply keyword-rule tags | `python scripts/ingest_batch.py --direction Battery --apply-tags` |
| `scan_tags.py` | Scan canonical tag coverage and keyword-rule hits | `python scripts/scan_tags.py --direction Battery --rules` |
| `export_summaries.py` | Export titles, metadata, abstracts, and keywords for review | `python scripts/export_summaries.py --direction Battery --format json` |
| `report_family.py` | Full-text journal/direction run-bundle preparation by default; deterministic reports with `--metadata-only`; stat reports unchanged | `python scripts/report_family.py --mode journal --journal RESS` |
| `status_report.py` | Vault status summary (Markdown + JSON) | `python scripts/status_report.py` |
| `lint_vault.py` | Vault health check (Markdown + JSON) | `python scripts/lint_vault.py` |
| `web_search.py` | Search OpenAlex/Semantic Scholar/arXiv and save Markdown papers | `python scripts/web_search.py find --direction Battery --query "topic"` |
| `arxiv_fulltext.py` | Fetch arXiv HTML/TeX/PDF/API fallback full text | Imported by `web_search.py` |
| `web_import_clipper.py` | Import Obsidian Web Clipper Markdown | `python scripts/web_import_clipper.py --direction Battery` |
| `common.py` | Shared utilities | Imported by other scripts |

All scripts use the vault root as project root (auto-detected from script location via `Path(__file__).resolve().parents[1]`).

Historical draft scripts and one-off migration tools now live under `workspace/legacy/` and are not part of the formal workflow surface.

---

## Schema Reference

### tag_taxonomy.json

Defines tag dimensions and known tags:

```json
{
  "dimensions": {
    "task": { "label": "Task", "abbr_map": {} },
    "method": { "label": "Method", "abbr_map": {} },
    ...
  },
  "tags": {
    "task": ["SOH estimation", ...],
    "method": ["LSTM", ...],
    ...
  }
}
```

### keyword_rules.json

Maps text patterns to tags:

```json
{
  "rules": [
    { "pattern": "state of health|SOH", "tag": "SOH estimation", "dimension": "task" },
    ...
  ]
}
```

### journal_aliases.json

Maps journal full names to abbreviations. Already exists with 27+ entries.

### paper_frontmatter.schema.md

Documents required and optional frontmatter fields for canonical pages.

---

## Canonical Page Format

Canonical pages in `library/papers/{direction}/{paper_id}.md` serve as **index anchors** linking to source files. They contain metadata, tags, abstract, and user notes — not full text.

Full text reading and evidence retrieval should use `source_path` to access the original Markdown in `paper/`.

```yaml
---
id: battery-2025-ress-bayesian-calibrated-pinn
title: "Paper title"
direction: Battery
source_path: "paper/Battery/RESS/paper.md"
source_checksum: sha256...

journal: "Reliability Engineering & System Safety"
journal_abbr: "RESS"
published_date: "2025-12"
published_year: 2025
doi: "10.1016/..."
url: "https://..."

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

---

## Safety Rules

1. **Never delete** files in `paper/` — these are the user's original paper Markdown files
2. **File moves** require `--dry-run` first, then user confirmation before `--apply`
3. **Preserve `## User Notes`** — never overwrite content under this heading in any file
4. **Log everything** — all file operations go to `workspace/logs/`
5. **Tag priority** — user tags > rule tags > manually confirmed extra suggestions (never remove user tags)
6. **No cross-direction moves** — files stay within their research direction unless user explicitly requests
7. **No overwrites** — if target file exists during organize, log as conflict, do not overwrite
