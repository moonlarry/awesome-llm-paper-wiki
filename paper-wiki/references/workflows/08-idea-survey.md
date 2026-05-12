# Workflow 8: idea-survey

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 8: idea-survey

### Purpose
Survey literature similarity to a user idea and assess novelty through LLM/full-text reading.

### Current execution path
This workflow is **LLM/Agent-driven**, not implemented as a `report_family.py` screening mode.

### Steps

1. Use canonical pages only as an index to locate source files through `source_path`
2. Let the LLM/Agent read relevant source Markdown files under `paper/`
3. During reading, extract problem, method, dataset, experiment setup, baselines, metrics, results, and limitations
4. Let the LLM/Agent decide which papers are truly similar or dissimilar after reading full evidence
5. If web supplementation is needed, run `web_search.py find` first and then let the LLM/Agent read the resulting source Markdown
6. Generate the final report at `library/reports/idea/{idea_slug}-survey-{date}.md` only after the full-text review pass
7. When claim-level verification is needed, optionally invoke `idea-claim-novelty-check` after the idea-level survey and reference its output as a deeper evidence layer rather than replacing the survey report

### Notes
- Do not use keyword/tag similarity as the final idea candidate filter
- Do not treat metadata-only matches as novelty evidence
- Final novelty judgment must be grounded in source Markdown, not only canonical abstracts or tags
- Use `idea-claim-novelty-check` only as an optional deeper pass for specific technical claims; `idea-survey` remains the idea-level similarity workflow

