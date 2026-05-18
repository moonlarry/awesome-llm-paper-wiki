# Workflow 24: resubmit-audit

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 24: resubmit-audit

### Purpose
Audit a paper draft for transfer to a target venue. The workflow resolves or generates the venue evidence report, selects topic-near evidence papers, returns prioritized revision advice, and produces a complete revised draft.

### Input
- Required: paper draft
- Required: target venue information
- Optional: existing target venue report, submission constraints, prior reviews, or author non-goals

### Reviewer Route
- Preferred route: use a Codex-compatible MCP reviewer.
- Claude Code route: explicitly call `codex` as the external auditor for the resubmission audit.
- Fallback route: if the MCP reviewer is unavailable, use a bounded dual-agent split such as transfer auditor vs. revision adjudicator.
- Degraded route: if neither route is available, run single-agent structured audit and label the report as degraded mode.

### Steps
1. Read the paper draft and resolve the target venue.
2. Locate the latest compatible target venue report, searching current workflow outputs such as `library/reports/journal/` first and future `library/reports/venue/` outputs when available; if none exists, generate it first via the existing journal or venue report workflow.
3. Identify the draft topic, method, dataset, claims, and target-venue fit profile.
4. Retain only topic-near papers from the venue report as the evidence basis.
5. Produce a venue-transfer audit covering fit, novelty framing, evidence gaps, citation risks, experiments, claims, and presentation.
6. Apply citation soft-only handling where bibliography metadata is frozen: translate citation problems into body-text actions such as `keep_unchanged`, `keep_metadata_drift_acknowledged`, `soften_citing_sentence`, or `drop_cite_in_body_only`.
7. Maintain an edit discipline checklist describing what should not change during transfer, such as core claims that are already evidence-backed, verified numerical results, and author-declared non-goals.
8. Produce a complete revised draft grounded in the audit findings and evidence basis.
9. Run the reviewer route to audit whether the revised draft addresses the findings and remains faithful to evidence.
10. Save `library/reports/submission/{slug}-resubmit-audit-{date}.md` using `templates/generic/resubmit_audit.md`.

### Output
- Target venue report resolution
- Topic-near evidence basis and references
- Transfer audit and prioritized revision plan
- Complete revised draft
- Final audit verdict and residual risks

