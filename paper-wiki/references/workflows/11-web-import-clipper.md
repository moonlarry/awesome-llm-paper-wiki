# Workflow 11: web-import-clipper

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

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

