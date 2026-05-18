# Web Workflows Reference

## Table of Contents

- [Workflow 9: web-find](#workflow-9-web-find)
- [Workflow 10: web-digest](#workflow-10-web-digest)
- [Workflow 11: web-import-clipper](#workflow-11-web-import-clipper)

## Workflow 9: web-find

Search academic web sources and save results as Markdown files.

### Input

- Required: `--direction {existing_direction}`
- Required: query text
- Optional: `--top N`, `--source mixed|openalex|semanticscholar|arxiv|venues`, `--fulltext`, `--no-fulltext`, `--arxiv-id`, `--no-domain-filter`, `--show-filtered`, `--dry-run`

### Data Layers

- Formal full-text library: `paper/{direction}/{journal_abbr}/`
- Web-search layer: `paper/web_search/{direction}/{source}/`
- Knowledge layer: `library/`

### Steps

1. **Fail-fast direction check**: `--direction` must exist under `paper/`
2. Agent recovery branch for a missing direction:
   - inspect the user query, configured directions, and `web_search.domain_profiles`
   - offer two direction options: a plausible existing direction and a suggested new direction name
   - wait for user confirmation before changing config or folders
   - after confirmation, append the direction to `config.json -> directions`, create `paper/{direction}/` and `paper/web_search/{direction}/`, seed a minimal domain profile, then rerun the command
3. Fetch results from OpenAlex, Semantic Scholar, and arXiv:
   - OpenAlex is primary; send optional API key and mailto metadata when configured
   - Semantic Scholar is used only when its API key is configured
   - `--source venues` keeps candidates whose venue matches preferred venues
   - arXiv is used for explicit arXiv source or as mixed-source fallback
4. Domain-filter, rank, and deduplicate:
   - strict profiles require all configured keyword groups and reject strong negative keyword hits
   - arXiv ID is the primary arXiv identity; DOI is the primary general identity
   - normalized title plus year is the fallback identity
   - never overwrite existing source Markdown files
5. Save results to appropriate paths:
   - OpenAlex/Semantic Scholar metadata -> `paper/web_search/{direction}/{source}/`
   - extracted arXiv full text -> `paper/{direction}/arxiv/`
   - PDF-only, abstract-only, or failed arXiv records -> `paper/web_search/{direction}/arxiv/`
6. Generate canonical pages and rebuild indexes only for formal source saves under `paper/{direction}/`
7. Generate web-find report at `library/reports/web/`
8. Write manifest and log, including filtered-out candidates for auditability

### Command

```bash
python scripts/web_search.py find --direction ExampleDirection --query "topic TaskB transformer" --top 10
python scripts/web_search.py find --direction ExampleDirection --source arxiv --arxiv-id 2502.18807v7 --fulltext
```

---

## Workflow 10: web-digest

Fetch recent arXiv papers for a direction and save as Markdown plus digest report.

### Input

- Required: `--direction {existing_direction}`
- Required: `--query "topic"`
- Optional: `--top N`, `--no-domain-filter`, `--show-filtered`, `--dry-run`

### Steps

1. Fail-fast direction check (same as web-find)
2. Use the same Agent recovery branch as `web-find` when the direction is missing
3. Build profile-aware arXiv query
4. Query arXiv by submitted date
5. Apply domain filter and ranking
6. Save arXiv full-text successes to `paper/{direction}/arxiv/`
7. Save fallback records to `paper/web_search/{direction}/arxiv/`
8. Generate canonical pages and rebuild indexes only for formal library entries
9. Generate digest report at `library/reports/web/`, including filtered-out candidates
10. Log the operation

### Command

```bash
python scripts/web_search.py digest --direction ExampleDirection --query "topic health prognosis" --top 10
```

---

## Workflow 11: web-import-clipper

Import Obsidian Web Clipper Markdown into the vault.

### Input

- Required: `--direction {existing_direction}`
- Optional: `--inbox path`, default from `web_search.clipper_inbox`
- Optional: `--dry-run`

### Steps

1. Read `.md` files from inbox
2. Extract metadata from frontmatter/body
3. Deduplicate by DOI or normalized title + year
4. Save normalized Markdown to `paper/{direction}/{journal_abbr}/`
5. Generate canonical pages and rebuild indexes
6. Archive imported files to `workspace/web-inbox/imported/`

### Command

```bash
python scripts/web_import_clipper.py --direction ExampleDirection
```
