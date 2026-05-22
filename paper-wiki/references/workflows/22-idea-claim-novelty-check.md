# Workflow 22: idea-claim-novelty-check

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 22: idea-claim-novelty-check

### Purpose
Assess novelty at the individual research-claim level and return evidence-backed verdicts that complement, but do not replace, `idea-survey`.

### Input
- Required: a method or idea description with enough detail to extract technical claims
- Optional: related `idea-survey`, `idea-evidence`, or `idea-report` output

### Steps

1. Extract 3-5 core technical claims that require independent novelty checking.
2. Search each claim against sources configured in `research_workflows.novelty_check_sources`:
   - `canonical_pages`
   - `source_markdown`
   - `web_digest`
3. If `research_workflows.live_web_search` is `true`, reuse `web-find` for a fresh supplementary search.
4. Build an evidence chain for each claim using the closest prior work, the overlap, and the remaining differentiator.
5. Run a reviewer-obviousness challenge for each claim: could the closest prior method achieve the same claim by being applied to this problem with only routine task substitution or standard engineering adaptation? If yes, downgrade the claim unless the evidence shows a nontrivial delta in mechanism, objective, function/capability, performance/robustness/efficiency, scenario/domain/constraint, data/benchmark, validation standard, or new scheme.
6. Assign one verdict per claim:
   - `LIKELY NOVEL`
   - `PARTIALLY KNOWN`
   - `NOT NOVEL`
   - `INSUFFICIENT EVIDENCE`
7. Produce a short overall recommendation, such as proceed, proceed with caution, or abandon, with justification grounded in the claim table.
8. Generate `library/reports/idea/{idea_slug}-idea-claim-novelty-{date}.md` using `templates/generic/idea_claim_novelty_check.md`.

### Reviewer Routing
For cross-checking the strongest novelty claims or the nearest-prior-work interpretation, use a Codex-compatible MCP reviewer first, otherwise a fresh independent agent when the runtime supports it, otherwise degraded local analysis. Label degraded local analysis in the output.

### Relationship to `idea-survey`
- `idea-survey` is idea-level similarity assessment through full-text reading.
- `idea-claim-novelty-check` is per-claim structured scoring with evidence chains.
- `idea-survey` may optionally invoke this workflow for deeper analysis when claim-level novelty materially affects the conclusion.

