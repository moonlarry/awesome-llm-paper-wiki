# Report Workflows Reference

## Workflow 5: journal-report

Generate a literature survey report for a specific journal.

### Input

Journal name or abbreviation (e.g., "JOURNAL", "PUB", "JPS")

### Steps

1. Resolve journal abbreviation via `schema/journal_aliases.json`
2. Read all canonical pages where `journal_abbr` matches
3. Select template (domain-specific or generic)
4. Analyze: topic distribution, method landscape, dataset usage, temporal trends, high-value papers, research gaps
5. Generate report → `library/reports/journal/{journal_abbr}-report-{date}.md`
6. Apply Report Citation Policy

---

## Workflow 6: direction-report

Generate a research status report for a specific research direction or topic.

### Input

- Research direction or topic
- Optional: `--web` flag for supplementary web search

### Steps

1. Search local vault by tags for matching papers
2. Read all matching canonical pages
3. **(If --web)**: Use web_search.py for arXiv full-text
4. Select template
5. Analyze: core problem, method classification, datasets, performance, trends, open problems
6. Generate report → `library/reports/direction/{topic_slug}-report-{date}.md`

---

## Workflow 7: stat-report

Generate fine-grained statistical reports on methods, datasets, experiments, or custom dimensions.

### Input

Stat dimension: "method" / "dataset" / "metric" / "signal" / custom

### Steps

1. Load all canonical pages
2. Aggregate by requested dimension
3. Generate tables and charts
4. Generate report → `library/reports/direction/{dimension}-stats-{date}.md`

---

## Workflow 8: idea-survey

Survey existing literature for similarity to a user's research idea and assess novelty.

### Input

- User's idea description
- Optional: existing local sources, canonical pages, web-search records

### Steps

1. Extract key concepts from idea text
2. Search local vault by tags and keywords
3. Assess similarity for each matched paper
4. Assess overall novelty
5. Generate report → `library/reports/idea/{idea_slug}-survey-{date}.md`

---

## Workflow 12: submission-recommend

Recommend suitable journals for a user's paper.

### Input

Path to the user's paper

### Steps

1. Read and analyze the user's paper
2. Identify candidate journals (≥ 5 papers)
3. Score across 6 dimensions: topic_fit, method_fit, novelty_fit, experiment_fit, citation_fit, risk
4. Rank top 5 journals
5. Generate report → `library/reports/submission/{paper_slug}-recommend-{date}.md`

---

## Workflow 13: revision-suggest

Generate targeted revision suggestions for a paper aimed at a specific journal.

### Input

- Path to user's paper
- Target journal name

### Steps

1. Read user's paper
2. Read target journal's literature collection
3. Compare across 5 dimensions: formatting, method writing, research method, introduction, references
4. Prioritize suggestions by impact
5. Generate report → `library/reports/submission/{paper_slug}-revision-for-{journal}-{date}.md`

---

## Workflow 17: paper-read

Read one paper deeply and generate a structured reading note.

### Input

- Required: one paper path, title, DOI, canonical id, or source path
- Optional: user research context

### Steps

1. Locate the paper
2. Read metadata and content
3. Answer: problem, importance, method, why it works, conclusions, next steps
4. Generate reading note using `templates/generic/paper_reading.md`
5. Save to `library/reports/paper/{date}-{paper_id}-reading.md`