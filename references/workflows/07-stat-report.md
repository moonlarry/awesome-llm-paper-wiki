# Workflow 7: stat-report

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 7: stat-report

### Purpose
Generate deterministic statistics reports for one tag dimension.

### Formal CLI
```bash
python scripts/report_family.py --mode stat --direction Battery --dimension method
python scripts/report_family.py --mode stat --direction Battery --dimension dataset --cross-dimension method
```

### Steps

1. Load canonical records for the direction
2. Aggregate by the requested dimension:
   - count papers per tag value
   - compute yearly trend
   - compute cross-tabulation with another tag dimension
3. Generate deterministic Markdown tables
4. Save to `library/reports/direction/{dimension}-stats-{date}.md`

