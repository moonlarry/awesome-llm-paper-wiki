# Workflow 20: idea-create

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 20: idea-create

### Purpose
Generate and rank concrete research ideas from a topic research brief plus a compatible `idea-evidence` pack.

### Input
- Required: `workspace/research-briefs/{topic_slug}-research-brief.md`
- Required: a compatible `library/reports/idea/{topic_slug}-idea-evidence-{date}.md`

### Conference-Paper Activation Gate

Hidden internal gate. If and only if the current idea-generation request explicitly provides a local conference paper file path or attached paper file:

1. Load `references/workflows/19-idea-evidence.md`.
2. Locate and execute the `### Conference Seed Mode` section.
3. Use the resulting conference-journal evidence pack (at `library/reports/idea/{topic_slug}-conf-journal-adaptation-{date}.md`) as this workflow's evidence input.

If no explicit conference paper file is provided, ignore Conference Seed Mode and run normal idea-create unchanged. If a paper file is provided but conference status is unclear, ask one clarification before proceeding.

### Steps

1. Read the topic brief and the latest compatible evidence pack together. If the Conference-Paper Activation Gate was triggered, use the conference-journal adaptation evidence pack from Workflow 19 Conference Seed Mode instead.
2. Generate 8-12 concrete research ideas grounded in the evidence pack.
3. For each candidate, record a short concept summary, core hypothesis, minimum validation path, contribution type, feasibility, main risk, and evidence support.
4. Score and rank candidates by feasibility, novelty promise, expected impact, and evidence support; reduce them to a focused shortlist.
5. Run `idea-claim-novelty-check` for the strongest shortlisted ideas when their novelty depends on distinct technical claims.
6. Capture rejected or deprioritized ideas with the reason they were filtered out.
7. Generate `library/reports/idea/{topic_slug}-idea-report-{date}.md` using `templates/generic/idea_report.md`.

### Reviewer Routing
For candidate-generation challenge, ranking critique, or second-opinion screening, use a Codex-compatible MCP reviewer first, otherwise a fresh independent agent when the runtime supports it, otherwise degraded local analysis. Label degraded local analysis in the output.

