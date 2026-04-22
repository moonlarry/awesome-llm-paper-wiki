# Core Workflows Reference

## Workflow 1: init

Initialize the vault structure. Creates missing directories and seed files.

### Steps

1. Check if project root has `config.json` — if not, create default config
2. Create missing directories:
   - `schema/`
   - `library/papers/`, `library/reports/journal/`, `library/reports/direction/`, `library/reports/idea/`, `library/reports/paper/`, `library/reports/submission/`
   - `library/indexes/`, `library/indexes/journals/`
   - `workspace/cache/`, `workspace/manifests/`, `workspace/logs/`
   - `templates/generic/`, `templates/domains/`
3. Create `schema/tag_taxonomy.json` if missing
4. Create `schema/keyword_rules.json` if missing
5. Create `schema/paper_frontmatter.schema.md` if missing
6. Skip creating generic templates if they already exist
7. Update `paper-library.md` with skeleton if needed

---

## Workflow 2: scan-organize

Scan `paper/` for all Markdown files and optionally organize them into journal folders.

### Sub-triggers

- "scan papers" → steps 1–3 only (scan + plan)
- "organize by journal" → steps 1–6 (scan + move + index)
- "check duplicates" → steps 1, 4 only

### Steps

1. Run: `python scripts/scan_sources.py`
   - Output: `workspace/manifests/source_manifest.json`

2. Run: `python scripts/organize_by_journal.py --all --dry-run`
   - Output: `workspace/manifests/journal_move_plan.json`

3. Display plan summary to user

4. **(If "check duplicates")**: Scan for duplicate files by SHA256 checksums

5. **(If "organize by journal")**: Ask user to confirm, then:
   - Run: `python scripts/organize_by_journal.py --all --apply`

6. Run: `python scripts/rebuild_indexes.py`

---

## Workflow 3: ingest

Process paper Markdown files: extract metadata, generate canonical pages, convert HTML tables.

### Input

- A specific file path, or "all new papers", or a journal/direction scope

### Steps

1. Identify target files

2. For each target file:
   a. Read file and parse frontmatter
   b. Extract/complete metadata
   c. Generate paper ID: `{direction}-{year}-{journal_abbr}-{slug}`
   d. Identify tag candidates from keyword rules
   e. Convert HTML tables to Markdown
   f. Generate canonical page

3. Domain profile update

### Batch Command

```bash
python scripts/ingest_batch.py --direction ExampleDirection --journal PUB --apply-tags --rebuild-indexes
python scripts/ingest_batch.py --file paper/ExampleDirection/arxiv/example.md --apply-tags
python scripts/ingest_batch.py --direction ExampleDirection --dry-run
```

---

## Workflow 4: tag

Manage the tag system: view, edit, batch-assign, and analyze tags.

### Sub-triggers

- "view tags" → display tag_taxonomy.json summary
- "batch tag" → run keyword rules on all canonical pages
- "add tag" → add a custom tag to taxonomy
- "tag stats" → show tag frequency distribution

### Steps (batch tag)

1. Load `schema/tag_taxonomy.json` and `schema/keyword_rules.json`

2. For each canonical page:
   a. Read frontmatter tags
   b. Apply keyword rules
   c. Merge: user tags > rule tags > Claude tags

3. Write updated tags back to canonical page frontmatter

4. Log changes to `workspace/logs/tag_operations.md`

### Commands

```bash
python scripts/ingest_batch.py --direction ExampleDirection --apply-tags --rebuild-indexes
python scripts/scan_tags.py --direction ExampleDirection
python scripts/scan_tags.py --direction ExampleDirection --rules --include-empty
```