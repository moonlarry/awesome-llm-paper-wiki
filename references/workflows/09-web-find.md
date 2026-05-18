# Workflow 9: web-find

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

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

