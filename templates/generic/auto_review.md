# Auto Review Loop Report

## Metadata
- Source artifact: {{source_artifact}}
- Review scope: {{review_scope}}
- Date: {{date}}
- Max review rounds: {{max_review_rounds}}
- Human checkpoints required: {{require_human_checkpoints}}

## Reviewer Route
- Selected route: {{reviewer_route}}
- External reviewer: {{external_reviewer}}
- Claude Code instruction when applicable: call `codex` as the external reviewer/auditor.
- Degraded mode: {{degraded_mode}}
- Route notes: {{reviewer_route_notes}}

## Evidence Basis
- Source draft/version reviewed: {{source_version}}
- Supporting reports or papers: {{supporting_evidence}}
- Evidence limits: {{evidence_limits}}

## Round History
| Round | Reviewer | Main decision | Checkpoint result | Notes |
|---:|---|---|---|---|
| 1 | {{round_1_reviewer}} | {{round_1_decision}} | {{round_1_checkpoint}} | {{round_1_notes}} |

## Issue Ledger
| ID | Severity | Location | Issue | Evidence | Status | Revision action |
|---|---|---|---|---|---|---|
| R1 | {{severity}} | {{location}} | {{issue}} | {{evidence}} | {{status}} | {{revision_action}} |

Allowed status labels for major criticisms:
- `answered_by_current_text`
- `partially_answered`
- `still_unresolved`

## Revision Plan
{{revision_plan}}

## Final Recommended Version
{{final_recommended_version}}

## Final Recommendation
{{final_recommendation}}

## Residual Risks
{{residual_risks}}

## Citation Notes
{{citation_notes}}

## References
{{references}}
