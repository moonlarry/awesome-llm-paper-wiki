# Web Workflows Reference

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
2. Fetch results from OpenAlex, Semantic Scholar, arXiv
3. Domain-filter, rank, and deduplicate
4. Save results to appropriate paths
5. Generate canonical pages for formal library saves
6. Generate web-find report at `library/reports/web/`
7. Write manifest and log

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
2. Build profile-aware arXiv query
3. Query arXiv by submitted date
4. Apply domain filter and ranking
5. Save arXiv full-text successes to `paper/{direction}/arxiv/`
6. Save fallback records to `paper/web_search/{direction}/arxiv/`
7. Generate canonical pages for formal library entries
8. Generate digest report at `library/reports/web/`

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