# Report Workflows Reference

## Table of Contents

- [Workflow 5: journal-report](#workflow-5-journal-report)
- [Workflow 6: direction-report](#workflow-6-direction-report)
- [Workflow 7: stat-report](#workflow-7-stat-report)
- [Workflow 8: idea-survey](#workflow-8-idea-survey)
- [Workflow 19: idea-evidence](#workflow-19-idea-evidence)
- [Workflow 20: idea-create](#workflow-20-idea-create)
- [Workflow 21: idea-discover](#workflow-21-idea-discover)
- [Workflow 22: idea-claim-novelty-check](#workflow-22-idea-claim-novelty-check)
- [Workflow 23: auto-review-loop](#workflow-23-auto-review-loop)
- [Workflow 24: resubmit-audit](#workflow-24-resubmit-audit)
- [Workflow 25: paper-review-loop](#workflow-25-paper-review-loop)
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
7. For each readable record, run `records[*].source_read_command` to create an Agent-safe temporary Markdown view, then read that temporary file. Do not read `records[*].source_path` directly. Follow `bundle.source_reading` policy. By default, skip source-paper References/Bibliography sections unless `--include-references` is used. This rule only affects source-paper References/Bibliography sections; the final report must still keep its own References section according to the citation policy.
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
6. For each readable record, run `records[*].source_read_command` to create an Agent-safe temporary Markdown view, then read that temporary file. Do not read `records[*].source_path` directly. Follow `bundle.source_reading` policy. By default, skip source-paper References/Bibliography sections unless `--include-references` is used. This rule only affects source-paper References/Bibliography sections; the final report must still keep its own References section.
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

## Workflow 19: idea-evidence

Prepare the dedicated evidence pack that `idea-create` consumes.

### Input

- Required: research topic text or `workspace/research-briefs/{topic_slug}-research-brief.md`
- Optional: direction, scope constraints, excluded directions, or a related `idea-survey` report

### Steps

1. Read or assemble the durable topic brief.
2. Aggregate local evidence from canonical pages, source Markdown, existing reports, indexes, and related survey output when present.
3. Run the network evidence path through existing `web-find` / `web-digest` capabilities.
4. Deduplicate and screen at least 50 suitable network papers.
5. Deep-read all 50 selected papers beyond abstract skim.
6. Synthesize gap map, contradiction map, transfer opportunities, underexplored design space, and negative space.
7. Generate `library/reports/idea/{topic_slug}-idea-evidence-{date}.md` using `templates/generic/idea_evidence.md`.

This workflow only prepares evidence for `idea-create`; it does not replace `direction-review`.

---

## Workflow 20: idea-create

Generate and rank concrete ideas from a topic brief plus an `idea-evidence` pack.

### Input

- Required: `workspace/research-briefs/{topic_slug}-research-brief.md`
- Required: compatible `library/reports/idea/{topic_slug}-idea-evidence-{date}.md`

### Steps

1. Read the topic brief and evidence pack together.
2. Generate 8-12 concrete ideas.
3. Record concept, hypothesis, minimum validation path, contribution type, feasibility, risk, and evidence support for each idea.
4. Rank by feasibility, novelty promise, expected impact, and evidence support.
5. Run `idea-claim-novelty-check` for finalists whose novelty depends on distinct technical claims.
6. Generate `library/reports/idea/{topic_slug}-idea-report-{date}.md`.

---

## Workflow 21: idea-discover

Orchestrate the full idea-family path.

### Steps

1. Create or incrementally merge updates into `workspace/research-briefs/{topic_slug}-research-brief.md`, preserving prior context and an update log for the same topic.
2. If the user already has a proto-idea, run or refresh `idea-survey`.
3. Run `idea-evidence`.
4. Run `idea-create`.
5. Run `idea-claim-novelty-check` on selected candidate claims or finalist ideas.
6. Summarize the combined outputs in `library/reports/idea/{topic_slug}-idea-discovery-{date}.md`.

---

## Workflow 22: idea-claim-novelty-check

Check novelty at the claim level and return evidence-backed verdicts.

### Steps

1. Extract 3-5 core technical claims.
2. Search the configured evidence layers in `research_workflows.novelty_check_sources`.
3. If `research_workflows.live_web_search` is enabled, reuse `web-find` for a fresh supplementary pass.
4. Build an evidence chain for each claim.
5. Assign `LIKELY NOVEL`, `PARTIALLY KNOWN`, `NOT NOVEL`, or `INSUFFICIENT EVIDENCE`.
6. Generate `library/reports/idea/{idea_slug}-idea-claim-novelty-{date}.md`.

`idea-survey` remains the idea-level similarity workflow; this workflow is the deeper per-claim layer.

---

## Workflow 23: auto-review-loop

Run a general research-review loop for a paper draft, experiment report, method proposal, or related research output.

### Reviewer Route

Prefer a Codex-compatible MCP reviewer. In Claude Code, explicitly call `codex` as the external reviewer/auditor. If unavailable, use a bounded dual-agent split. If that is unavailable, use single-agent degraded mode and label the report.

### Steps

1. Capture review scope, source artifact, reviewer route, evidence basis, and round limit.
2. Build an issue ledger with severity, evidence, affected section, and whether the current text answers the issue.
3. Classify major criticisms as `answered_by_current_text`, `partially_answered`, or `still_unresolved`.
4. Produce revision actions and a final recommended version without overwriting the source by default.
5. Save `library/reports/review/{slug}-auto-review-{date}.md` using `templates/generic/auto_review.md`.

---

## Workflow 24: resubmit-audit

Audit a paper draft for transfer to a target venue and return both prioritized revision advice and a complete revised draft.

### Input

- Paper draft
- Target venue information

### Steps

1. Resolve or generate the target venue report, searching existing workflow outputs such as `library/reports/journal/` first.
2. Identify the manuscript topic, method, dataset, claims, and target-venue fit profile.
3. Retain only topic-near papers from the venue report as the evidence basis.
4. Audit fit, novelty framing, evidence gaps, citation risks, experiments, claims, and presentation.
5. Apply citation soft-only handling when bibliography metadata is frozen: `keep_unchanged`, `keep_metadata_drift_acknowledged`, `soften_citing_sentence`, or `drop_cite_in_body_only`.
6. Maintain an edit discipline checklist for content that should not change during venue transfer.
7. Produce a complete revised draft and audit it through the reviewer route.
8. Save `library/reports/submission/{slug}-resubmit-audit-{date}.md` using `templates/generic/resubmit_audit.md`.

---

## Workflow 25: paper-review-loop

Run a venue-conditioned manuscript review, revision, and post-revision audit loop.

### Input

- Paper draft
- Target venue report or compatible `resubmit-audit` report

### Steps

1. Load the venue report or upstream `resubmit-audit` report and resolve the topic-near evidence basis.
2. Review the manuscript against venue expectations, evidence-backed novelty framing, experiment sufficiency, claim quality, and citation coverage.
3. Build an issue ledger with severity, evidence, revision target, and acceptance blocker status.
4. Produce revised manuscript content for the current round.
5. Audit the revised manuscript against the same evidence basis and mark issues as `answered_by_current_text`, `partially_answered`, or `still_unresolved`.
6. Continue until readiness threshold, round limit, or user stop.
7. Save `library/reports/review/{slug}-paper-review-loop-{date}.md` using `templates/generic/paper_review_loop.md`.

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

Read one paper deeply using the MIT Professor Mode 10-phase framework.

### Input

- Required: one paper path, title, DOI, canonical id, or source path
- Optional: user research context

### Steps

1. Locate the paper
2. Read metadata and content
3. Analyze the paper through 10 phases: problem formulation, why existing solutions fail, key insight, method derivation, mathematical understanding, evidence examination, critical thinking, research mapping, AI for Science reflection, and Socratic questions
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
10. For each readable record in the bundle, run `records[*].source_read_command` to create an Agent-safe temporary Markdown view, then read that temporary file. Do not read `records[*].source_path` directly. Follow `bundle.source_reading` policy. By default, skip source-paper References/Bibliography sections unless `--include-references` is used. This rule only affects source-paper References/Bibliography sections; the final review must still keep its own References section according to the citation policy.
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
