# Evidence Validation Protocol

> Part of paper-wiki skill. Required for `journal-report` and `direction-report` workflows. Load this file together with the corresponding workflow reference file.

For `journal-report` and `direction-report`, the evidence pipeline is required before the report is considered complete. Prompt checkpoints guide the Agent, but `report_family.py --complete` is the authoritative completion gate.

Bundle preparation initializes all required evidence files under `evidence_dir`. The workflow then fills them in stages; `verification.json` starts with checks set to `"pending"` and must only be changed to `"passed"` after count equality is verified.

## Stage 1: Evidence Pipeline (REQUIRED BEFORE ANY REPORT WRITING)

1. Create `screening.jsonl` under `evidence_dir` with one entry per record:
   ```jsonl
   {"ref_id": "R001", "decision": "confirmed_included", "reason": "..."}
   {"ref_id": "R032", "decision": "uncertain_needs_review", "reason": "DOI pattern anomaly"}
   {"ref_id": "R050", "decision": "metadata_only_duplicate", "reason": "same DOI as R047"}
   ```

2. Create `paper_notes.jsonl` with one brief evidence note per confirmed paper.

3. Create `coverage_ledger.json` using the validator-compatible top-level schema:
   ```json
   {
     "candidate_count": 51,
     "confirmed_included": ["R001", "R002", "..."],
     "metadata_only": ["R050"],
     "excluded_wrong_scope": [],
     "skipped_unreadable": [],
     "uncertain_needs_review": ["R032"]
   }
   ```

4. Output partition counts before report writing:
   ```
   Evidence pipeline complete:
   - candidate_count: 51
   - confirmed_included: 49
   - metadata_only: 1
   - excluded_wrong_scope: 0
   - skipped_unreadable: 0
   - uncertain_needs_review: 1
   ```

Leave `verification.json` checks as `"pending"` during Stage 1.

## Stage 2: Report Writing

After Stage 1 completes:

5. Create `Paper Coverage Matrix` table listing every `confirmed_included` paper with citation marker
6. Write report body citing each confirmed paper at least once
7. Fill `synthesis_notes.md` with key findings from the confirmed evidence set

## Stage 3: Pre-Finalize Verification (REQUIRED BEFORE OUTPUT)

Verify the following equalities and OUTPUT the check result:

```
Verification check:
- coverage_ledger.confirmed_count: 49
- unique_cited_paper_count (count distinct [N] markers in body): 49
- reference_entry_count (count Reference List entries): 49
- All 49 confirmed papers appear in Coverage Matrix: YES

Status: PASS / FAIL
```

After these checks pass, update `verification.json` with validator-compatible pass keys:

```json
{
  "citation_check": "passed",
  "coverage_check": "passed",
  "evidence_consistency_check": "passed",
  "candidate_count": 51,
  "confirmed_included_count": 49,
  "metadata_only_count": 1,
  "uncertain_needs_review_count": 1,
  "unique_cited_paper_count": 49,
  "coverage_matrix_entry_count": 49,
  "reference_entry_count": 49
}
```

If any check fails, **STOP** and fix before finalizing.

## Stage 4: Hard Completion Gate

After the report Markdown exists and all evidence files are filled, run:

```bash
python scripts/report_family.py --mode journal --journal Energy --complete
```

or the equivalent `direction` command. The report is not complete until this command passes.

## Allowed Exception

User explicitly requests `--metadata-only` or "brief/selective report" → skip full coverage requirements, document boundary in `Coverage / Source Set`.
