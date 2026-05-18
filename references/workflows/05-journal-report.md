# Workflow 5: journal-report

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 5: journal-report

### Purpose
Prepare a full-text literature survey workflow for a specific journal.

### Formal CLI
```bash
python scripts/report_family.py --mode journal --journal RESS
python scripts/report_family.py --mode journal --journal RESS --direction Battery --query "soh"
python scripts/report_family.py --mode journal --journal RESS --metadata-only
python scripts/report_family.py --mode journal --journal RESS --complete
```

### Steps

1. Load canonical records from `library/indexes/canonical_pages.json` (or rebuild in memory if the index is missing)
2. Filter by journal name or abbreviation
3. If `--direction` is set, further restrict to that exact direction
4. If `--query` is set, further restrict the journal subset using canonical query matching
5. Partition selected records into:
   - readable records with valid `source_path`
   - skipped records with missing/unreadable source files
6. Audit journal identity before writing:
   - Do not rely only on the parent folder or canonical `journal_abbr`
   - Confirm journal identity from DOI, URL, source-page journal title, or full-text journal heading
   - For Elsevier journals, treat DOI prefix and ScienceDirect journal page evidence as stronger than folder name
   - Partition records into:
     - `confirmed_included`: journal identity confirmed
     - `metadata_only`: duplicate or metadata-only records (use `metadata_only_duplicate` screening decision, map to `metadata_only` ledger partition)
     - `excluded_wrong_scope`: wrong journal or out of scope
     - `skipped_unreadable`: missing or unreadable source files
     - `uncertain_needs_review`: ambiguous journal identity
7. Save a single disposable run bundle:
   - `workspace/cache/fulltext-report/{run_key}.json`
8. Agent runs `records[*].source_read_command` for each readable record to create the Agent-safe temporary Markdown view, reads that temporary file, applies the journal audit, and writes the final report to:
   - `library/reports/journal/{journal_key}-report-{date}.md`
   - Before writing the final report, fill all required evidence files under `bundle.evidence_dir`: screening.jsonl, paper_notes.jsonl, coverage_ledger.json, synthesis_notes.md, verification.json
9. Include a `Paper Coverage Matrix` in the final report:
   - Every `confirmed_included` paper must appear in the matrix with a numeric citation marker
   - Excluded, skipped, and uncertain records must be summarized separately without reference-list entries
10. After the final report exists, run:
   - `python scripts/report_family.py --mode journal ... --complete`
11. Write a compact preparation/completion log entry to `workspace/logs/report_generation.md`

### Notes
- `--mode journal --journal RESS` means journal-only selection: select all canonical papers from that journal and do not apply extra filtering
- `--direction` and `--query` only narrow the already-selected journal subset when explicitly provided
- Missing source files are skipped silently; detailed reasons stay only in the run-bundle JSON
- Final journal-report conclusions must come from full-text evidence, not from canonical metadata alone
- Journal reports default to full coverage of `confirmed_included` records; write a representative-only report only when explicitly requested
- `--complete` is the formal close-out step after the final Markdown report has been written
- `--metadata-only` keeps the old deterministic canonical-metadata report path

