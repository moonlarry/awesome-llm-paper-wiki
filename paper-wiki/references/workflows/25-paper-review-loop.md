# Workflow 25: paper-review-loop

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 25: paper-review-loop

### Purpose
Run a venue-conditioned manuscript review, revision, and post-revision audit loop. Use this workflow when a manuscript should be reviewed against a target venue evidence base, revised, and then checked against the same standard before finalization.

### Input
- Required: paper draft
- Required: target venue report or compatible `resubmit-audit` report
- Optional: max rounds, prior review comments, author constraints, and readiness threshold

### Reviewer Route
- Preferred route: use a Codex-compatible MCP reviewer.
- Claude Code route: explicitly call `codex` as the external reviewer/auditor for the manuscript review loop.
- Fallback route: if the MCP reviewer is unavailable, use a bounded dual-agent split such as reviewer/editor and auditor/adjudicator.
- Degraded route: if neither route is available, run single-agent structured review and label the report as degraded mode.

### Steps
1. Load the venue report or upstream `resubmit-audit` report and resolve the topic-near evidence basis.
2. Review the manuscript against venue expectations, evidence-backed novelty framing, experiment sufficiency, claim quality, and citation coverage.
3. Build an issue ledger with severity, evidence, revision target, and acceptance blocker status.
4. Produce revised manuscript content for the issues selected in the current round.
5. Audit the revised manuscript against the same evidence basis and mark issues as `answered_by_current_text`, `partially_answered`, or `still_unresolved`; reject superficial fixes that do not close the evidence-backed issue.
6. Continue until the paper meets the readiness threshold, the configured round limit is reached, or the user stops at a checkpoint.
7. Save `library/reports/review/{slug}-paper-review-loop-{date}.md` using `templates/generic/paper_review_loop.md`.

### Output
- Reviewer route and round history
- Venue/evidence basis and references
- Issue-resolution ledger
- Final revised manuscript draft
- Readiness verdict and residual risks

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
| `report_family.py` | Full-text journal/direction run-bundle preparation by default; `--complete` closes the run after the final report exists; deterministic reports with `--metadata-only`; stat reports unchanged | `python scripts/report_family.py --mode journal --journal RESS` |
| `prepare_direction_review.py` | Prepare a direction-level literature review bundle with default web supplementation for Agent writing | `python scripts/prepare_direction_review.py --direction Battery --focus "battery SOH"` |
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
