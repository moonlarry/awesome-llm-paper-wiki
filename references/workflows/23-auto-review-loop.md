# Workflow 23: auto-review-loop

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 23: auto-review-loop

### Purpose
Run a general research-review loop for a paper draft, experiment report, method proposal, or related research output. The workflow returns review findings, revision guidance, and a final recommended version without overwriting the source by default.

### Input
- Required: research output to review
- Optional: target venue, review criteria, related evidence reports, max rounds, and stop criteria

### Reviewer Route
- Preferred route: use a Codex-compatible MCP reviewer.
- Claude Code route: explicitly call `codex` as the external reviewer/auditor for this review stage.
- Fallback route: if the MCP reviewer is unavailable, use a bounded dual-agent split such as reviewer vs. editor/adjudicator.
- Degraded route: if neither route is available, run single-agent structured self-review and label the report as degraded mode.

### Steps
1. Capture the review scope, source artifact, reviewer route, evidence basis, and configured round limit from `research_workflows.max_review_rounds`.
2. Build an issue ledger with severity, evidence, affected section, and whether the current text answers the issue.
3. Classify each major criticism as:
   - `answered_by_current_text`
   - `partially_answered`
   - `still_unresolved`
4. Generate revision actions for unresolved or partially resolved issues.
5. Produce a revised recommended version as a separate artifact or section, without overwriting the original unless the user explicitly asks.
6. Re-run the reviewer route for additional rounds when needed and when checkpoints permit.
7. Save `library/reports/review/{slug}-auto-review-{date}.md` using `templates/generic/auto_review.md`.

### Output
- Review route and degraded-mode label if applicable
- Evidence basis and citation/reference sections
- Issue ledger and round history
- Final recommended version

