# Maintenance Workflows Reference

## Workflow 14: status

Display vault status summary.

### Steps

1. Count papers by direction, journal, year from source manifest or indexes
2. Show tag coverage from canonical pages
3. Show template registry status
4. Show recent log entries (last 5)

### Command

```bash
python scripts/status_report.py --direction ExampleDirection
```

---

## Workflow 15: lint

Health check for the vault.

### Checks

1. Orphan canonical pages: source file missing
2. Missing canonical pages: source file has no canonical
3. Tag inconsistencies: tags not in taxonomy
4. Stale indexes: manifest older than newest paper
5. Missing frontmatter: required fields missing
6. Template staleness: domain templates need regeneration

### Command

```bash
python scripts/lint_vault.py --direction ExampleDirection
```

---

## Workflow 16: pipeline

Execute the full preprocessing pipeline in sequence.

### Steps

Execute in order, stopping on errors:

1. init
2. scan-organize (scan only)
3. ingest (all unprocessed papers)
4. tag (batch tag)
5. rebuild indexes
6. status (show final state)

---

## Utility Scripts

### detect_duplicates.py

Detect duplicate paper files in one direction or across the vault.

```bash
python scripts/detect_duplicates.py --all
```

### rebuild_indexes.py

Rebuild indexes and journal aggregate indexes.

```bash
python scripts/rebuild_indexes.py
```

### export_summaries.py

Export titles, metadata, abstracts, and keywords for review.

```bash
python scripts/export_summaries.py --direction ExampleDirection --format json
```