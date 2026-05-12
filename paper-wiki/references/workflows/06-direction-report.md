# Workflow 6: direction-report

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 6: direction-report

### Purpose
Prepare a full-text direction or topic status report from local canonical pages.

### Formal CLI
```bash
python scripts/report_family.py --mode direction --query "soh"
python scripts/report_family.py --mode direction --direction Battery --query "soh"
python scripts/report_family.py --mode direction --direction Battery --query "soh" --metadata-only
python scripts/report_family.py --mode direction --direction Battery --query "soh" --complete
```

### Steps

1. Load canonical records from the whole vault
2. If `--direction` is set, restrict to that exact direction
3. Apply query matching using title, abstract, keywords, and tag fields
4. Partition selected records into readable vs. skipped by `source_path`
5. Save a single disposable run bundle:
   - `workspace/cache/fulltext-report/{run_key}.json`
6. Agent runs `records[*].source_read_command` for each readable record to create the Agent-safe temporary Markdown view, reads that temporary file, and writes the final report to:
   - `library/reports/direction/{topic_slug}-report-{date}.md`
   - Before writing the final report, fill all required evidence files under `bundle.evidence_dir`: screening.jsonl, paper_notes.jsonl, coverage_ledger.json, synthesis_notes.md, verification.json
7. After the final report exists, run:
   - `python scripts/report_family.py --mode direction ... --complete`
8. Write a compact preparation/completion log entry to `workspace/logs/report_generation.md`

### Notes
- `--mode direction --query "soh"` allows cross-journal local screening from the whole vault
- `--direction` only narrows the query scope when explicitly provided
- Missing source files are skipped silently; detailed reasons stay only in the run-bundle JSON
- Final direction-report conclusions must come from full-text evidence, not from canonical metadata alone
- `--complete` is the formal close-out step after the final Markdown report has been written
- `--metadata-only` keeps the deterministic canonical-metadata report path

