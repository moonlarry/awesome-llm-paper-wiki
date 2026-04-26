# Report Workflows Reference

## Table of Contents

- [Workflow 5: journal-report](#workflow-5-journal-report)
- [Workflow 6: direction-report](#workflow-6-direction-report)
- [Workflow 7: stat-report](#workflow-7-stat-report)
- [Workflow 8: idea-survey](#workflow-8-idea-survey)
- [Workflow 12: submission-recommend](#workflow-12-submission-recommend)
- [Workflow 13: revision-suggest](#workflow-13-revision-suggest)
- [Workflow 17: paper-read](#workflow-17-paper-read)
- [Workflow 18: direction-review](#workflow-18-direction-review)

## Workflow 5: journal-report

Prepare a full-text literature survey report for a specific journal.

### Formal CLI

```bash
python scripts/report_family.py --mode journal --journal JOURNAL
python scripts/report_family.py --mode journal --journal JOURNAL --direction ExampleDirection --query "topic"
python scripts/report_family.py --mode journal --journal JOURNAL --metadata-only
```

### Steps

1. Load canonical records from `library/indexes/canonical_pages.json`, or rebuild in memory if missing.
2. Resolve and filter by journal name or abbreviation.
3. Narrow by `--direction` or `--query` only when explicitly provided.
4. Partition records into readable records with valid `source_path` and skipped records.
5. Audit journal identity from DOI, URL, source-page journal title, or full-text journal heading; do not rely only on folder name or canonical `journal_abbr`.
6. Save one disposable run bundle under `workspace/cache/fulltext-report/{run_key}.json`.
7. Read all `records[*].source_path`. Follow `bundle.source_reading` policy. By default, skip source-paper References/Bibliography sections unless `--include-references` is used. This rule only affects source-paper References/Bibliography sections; the final report must still keep its own References section according to the citation policy.
8. Write the final report to `library/reports/journal/{journal_key}-report-{date}.md`, and apply the Report Citation Policy.
8. Include a `Paper Coverage Matrix` when the report claims full coverage.
9. Log preparation/completion to `workspace/logs/report_generation.md`.

Use `--metadata-only` only when a deterministic canonical-metadata report is explicitly desired.

---

## Workflow 6: direction-report

Prepare a full-text direction or topic status report from local canonical pages.

### Formal CLI

```bash
python scripts/report_family.py --mode direction --query "topic"
python scripts/report_family.py --mode direction --direction ExampleDirection --query "topic"
python scripts/report_family.py --mode direction --direction ExampleDirection --query "topic" --metadata-only
```

### Steps

1. Load canonical records from the whole vault.
2. If `--direction` is set, restrict to that exact direction.
3. Apply query matching using title, abstract, keywords, and tag fields.
4. Partition selected records into readable records with valid `source_path` and skipped records.
5. Save one disposable run bundle under `workspace/cache/fulltext-report/{run_key}.json`.
6. Read all `records[*].source_path`. Follow `bundle.source_reading` policy. By default, skip source-paper References/Bibliography sections unless `--include-references` is used. This rule only affects source-paper References/Bibliography sections; the final report must still keep its own References section.
7. Write the final report to `library/reports/direction/{topic_slug}-report-{date}.md`.
7. Log preparation/completion to `workspace/logs/report_generation.md`.

Final direction-report conclusions must come from full-text evidence, not canonical metadata alone.
Use `--metadata-only` only when explicitly requested.

---

## Workflow 7: stat-report

Generate fine-grained statistical reports on methods, datasets, experiments, or custom dimensions.

### Input

Stat dimension: "method" / "dataset" / "metric" / "signal" / custom

### Steps

1. Load all canonical pages
2. Aggregate by requested dimension
3. Generate tables and charts
4. Generate report → `library/reports/direction/{dimension}-stats-{date}.md`

---

## Workflow 8: idea-survey

Survey existing literature for similarity to a user's research idea and assess novelty.

### Input

- User's idea description
- Optional: existing local sources, canonical pages, web-search records

### Steps

1. Extract key concepts from idea text
2. Use canonical pages as an index to locate source files through `source_path`
3. Read relevant source Markdown files under `paper/`
4. Assess similarity for each matched paper after reading full evidence
5. If web supplementation is needed, run `web_search.py find` first and read the resulting source Markdown
6. Generate report → `library/reports/idea/{idea_slug}-survey-{date}.md`

Do not treat keyword/tag similarity or metadata-only matches as final novelty evidence.

---

## Workflow 12: submission-recommend

Recommend suitable journals for a user's paper.

### Input

Path to the user's paper

### Steps

1. Read and analyze the user's paper
2. Identify candidate journals (≥ 5 papers)
3. Score across 6 dimensions: topic_fit, method_fit, novelty_fit, experiment_fit, citation_fit, risk
4. Rank top 5 journals
5. Generate report → `library/reports/submission/{paper_slug}-recommend-{date}.md`

---

## Workflow 13: revision-suggest

Generate targeted revision suggestions for a paper aimed at a specific journal.

### Input

- Path to user's paper
- Target journal name

### Steps

1. Read user's paper
2. Read target journal's literature collection
3. Compare across 5 dimensions: formatting, method writing, research method, introduction, references
4. Prioritize suggestions by impact
5. Generate report → `library/reports/submission/{paper_slug}-revision-for-{journal}-{date}.md`

---

## Workflow 17: paper-read

Read one paper deeply and generate a structured reading note.

### Input

- Required: one paper path, title, DOI, canonical id, or source path
- Optional: user research context

### Steps

1. Locate the paper
2. Read metadata and content
3. Answer: problem, importance, method, why it works, conclusions, next steps
4. Generate reading note using `templates/generic/paper_reading.md`
5. Save to `library/reports/paper/{date}-{paper_id}-reading.md`

Ground every answer in the selected paper text. Label inference explicitly and write "Not available
in the provided paper text" when evidence is missing.

---

## Workflow 18: direction-review

Prepare a review-writing bundle for one direction, combining local full-text evidence, related vault context, and default web supplementation.

This workflow is Agent-driven with a lightweight preparation script, not a `report_family.py` mode.

### Formal preparation command

```bash
python scripts/prepare_direction_review.py --direction ExampleDirection
python scripts/prepare_direction_review.py --direction ExampleDirection --focus "topic"
python scripts/prepare_direction_review.py --direction ExampleDirection --focus "topic" --top 6 --dry-run
```

### Input

- Required: `--direction {existing_direction}`
- Optional: `--focus "topic"`
- Optional: `--top N` for approximate total web supplementation volume
- Optional: `--dry-run`

### Steps

1. Validate that the direction exists and already has canonical pages with usable `source_path`; otherwise prompt the user to run `ingest` first.
2. Load canonical pages for the direction.
3. If `--focus` is set, restrict the local set using title, abstract, keyword, and tag matching.
4. Partition selected local records into:
   - readable records with valid `source_path`
   - skipped records with missing or unreadable source files
5. Derive 1-3 web queries from:
   - the direction name
   - the optional focus text
   - top local task, method, and application tags when available
6. Run default web supplementation using the existing `web_search.py` logic:
   - reuse current ranking, domain filtering, and arXiv full-text behavior
   - allow both new formal full-text saves and web-layer metadata saves into the review bundle
7. Gather related context from `library/reports/journal/`, `library/reports/direction/`, `library/reports/idea/`, and `library/reports/web/`.
8. Build review hints: candidate method categories, common datasets, common metrics, common applications, and suggested comparison tables.
9. Save preparation outputs:
   - `workspace/cache/fulltext-review/{run_key}.json`
   - `workspace/manifests/direction_review_prepare.json`
10. Read every readable record in the bundle. Follow `bundle.source_reading` policy. By default, skip source-paper References/Bibliography sections unless `--include-references` is used. This rule only affects source-paper References/Bibliography sections; the final review must still keep its own References section according to the citation policy.
11. Write the final review to `library/reports/review/{direction-or-focus}-review-{date}.md`.

### Writing rules

- Use `templates/generic/direction_review.md` as the scaffold.
- Keep the review domain-agnostic; infer method categories, datasets, metrics, and application groupings from the current corpus.
- Do not hardcode field-specific method taxonomies or section names from any pre-existing domain template.
- Include at least one comparison table in every major section.
- End every major method category with a limitations paragraph.
- Standard reviews target 40-80 cited references; deep or comprehensive reviews target 80-120 cited references.
- Related reports are secondary context only; substantive conclusions must come from paper text.

### Notes

- `direction-review` is not a replacement for `direction-report`.
- `direction-report` remains the direction/topic status-report workflow.
- `direction-review` is the survey-style literature-review workflow.
- `idea-survey` remains the novelty or similarity workflow for a specific idea.
- `--dry-run` still writes the preparation bundle and manifest, but it does not write the final
  review Markdown and may include preview-only web records that are not yet readable on disk.
