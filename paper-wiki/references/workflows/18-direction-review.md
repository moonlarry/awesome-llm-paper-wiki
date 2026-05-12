# Workflow 18: direction-review

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 18: direction-review

### Purpose
Prepare a review-writing bundle for one direction, combining local full-text evidence, related vault context, and default web supplementation.

### Current execution path
This workflow is **Agent-driven with a lightweight preparation script**, not a `report_family.py` mode.

### Formal preparation command
```bash
python scripts/prepare_direction_review.py --direction Battery
python scripts/prepare_direction_review.py --direction Battery --focus "battery SOH"
python scripts/prepare_direction_review.py --direction Battery --focus "battery SOH" --top 6 --dry-run
```

### Input
- Required: `--direction {existing_direction}`
- Optional: `--focus "topic"`
- Optional: `--top N` for approximate total web supplementation volume
- Optional: `--dry-run`

### Steps

1. Validate that the direction exists and already has canonical pages with usable `source_path`. If canonical pages are missing, prompt the user to run `ingest` first.
2. Load canonical pages for the direction.
3. If `--focus` is set, further restrict the local set using title, abstract, keyword, and tag matching.
4. Partition the selected local set into:
   - readable records with valid `source_path`
   - skipped records with missing/unreadable source files
5. Derive 1-3 web queries from:
   - the direction name
   - the optional focus text
   - top local task / method / application tags when available
6. Run default web supplementation using the existing `web_search.py` logic:
   - reuse current ranking, domain filtering, and arXiv full-text behavior
   - allow both new formal full-text saves and web-layer metadata saves into the review bundle
7. Gather related context paths from `library/reports/journal/`, `library/reports/direction/`, `library/reports/idea/`, and `library/reports/web/`.
8. Build review hints from the local reading set:
   - candidate method categories
   - common datasets
   - common metrics
   - common applications
   - suggested comparison tables
9. Save the preparation outputs:
   - `workspace/cache/fulltext-review/{run_key}.json`
   - `workspace/manifests/direction_review_prepare.json`
10. Agent reads every readable record in the bundle and writes the final review to:
   - `library/reports/review/{direction-or-focus}-review-{date}.md`

### Writing rules
- This workflow borrows the **review-writing mode** from a review-oriented skill, but it must stay domain-agnostic.
- Do not hardcode field-specific method taxonomies or section names from any pre-existing domain template.
- Method categories, datasets, metrics, and application groupings must be inferred from the current direction corpus.
- Every major section should include at least one comparison table.
- Every major method category should end with a limitations paragraph.
- Unless the user explicitly asks for a deep review, a standard `direction-review` should target **40-80** cited references.
- When the user explicitly asks for a deep / comprehensive / full survey review, target **80-120** cited references.
- Related reports in `library/reports/` are secondary context only; all substantive conclusions must still come from the paper text.

### Notes
- `direction-review` is not a replacement for `direction-report`.
- `direction-report` remains the direction/topic status report workflow.
- `direction-review` is the survey-style literature review workflow.
- `--dry-run` still writes the preparation bundle and manifest, but it does not write the final review Markdown and may include preview-only web records that are not yet readable on disk.

### Output (zh)
```
方向综述准备完成

方向：{direction}
聚焦主题：{focus_or_none}

本地可读论文：{local_readable}
本地跳过论文：{local_skipped}
网络补充记录：{web_count}

Bundle：workspace/cache/fulltext-review/{run_key}.json
Manifest：workspace/manifests/direction_review_prepare.json
最终综述目标：library/reports/review/{direction-or-focus}-review-{date}.md
```

