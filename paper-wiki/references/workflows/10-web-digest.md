# Workflow 10: web-digest

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

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

