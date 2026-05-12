# Workflow 21: idea-discover

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 21: idea-discover

### Purpose
Orchestrate the idea-family path from research brief creation through optional proto-idea surveying, evidence construction, idea generation, and claim-level novelty checking.

### Phase 0: Topic Brief Lifecycle

1. Resolve `topic_slug` from the current request or an explicit brief path.
2. Load `workspace/research-briefs/{topic_slug}-research-brief.md` when it exists.
3. If the brief is missing, create it; if it exists, merge new user input into the existing brief rather than replacing prior context.
4. Keep the brief durable with: problem statement, context, constraints, prior attempts, non-goals, current working direction, and an update log.

### Pipeline

1. If the user already has a proto-idea or prior idea note, run or refresh `idea-survey` to establish the idea-level similarity context before evidence construction.
2. Run `idea-evidence` to build the dedicated evidence pack for idea generation.
3. Run `idea-create` to produce and rank candidate ideas.
4. Run `idea-claim-novelty-check` on selected candidate claims or finalist ideas.
5. Summarize the combined outputs in `library/reports/idea/{topic_slug}-idea-discovery-{date}.md` using `templates/generic/idea_report.md` as the report scaffold.

### Outputs
- Topic brief: `workspace/research-briefs/{topic_slug}-research-brief.md`
- Discovery report: `library/reports/idea/{topic_slug}-idea-discovery-{date}.md`

### Reviewer Routing
At any second-opinion checkpoint in the orchestration, use a Codex-compatible MCP reviewer first, otherwise a fresh independent agent when the runtime supports it, otherwise degraded local analysis. Label degraded local analysis in the discovery report.

