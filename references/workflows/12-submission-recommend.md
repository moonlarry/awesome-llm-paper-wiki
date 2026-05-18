# Workflow 12: submission-recommend

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 12: submission-recommend

### Purpose
Recommend suitable journals for a user's paper based on local literature evidence.

### Input
Path to the user's paper (Markdown file)

### Steps

1. Read and analyze the user's paper:
   - Extract: research topic, methods, datasets, key results, reference list

2. Identify candidate journals from the vault (all journals with ≥ 5 papers)

3. For each candidate journal:
   a. Read the journal report if it exists; otherwise prompt user to generate one first
   b. Score across 6 dimensions:

   | Dimension | Weight | Description |
   |-----------|--------|-------------|
   | topic_fit | 0.25 | Does the paper's topic match the journal's recent hotspots? |
   | method_fit | 0.20 | Does the method type align with the journal's preferences? |
   | novelty_fit | 0.20 | Is the paper differentiated from the journal's recent work? |
   | experiment_fit | 0.15 | Do datasets, metrics, and experiment scale meet journal norms? |
   | citation_fit | 0.10 | Does the reference list cover the journal's key papers? |
   | risk | -0.10 | Scope mismatch, insufficient novelty, experimental gaps |

   c. Compute total score (0–100 scale)

4. Rank top 5 journals by total score

5. **Generate report** → `library/reports/submission/{paper_slug}-recommend-{date}.md`
   - Use template: `templates/generic/submission_report.md`
   - Apply the Report Citation Policy: cite journal reports and underlying papers where they support scoring evidence or recommendations, and list all cited evidence in `References`.

### Output (zh)
```
投稿推荐报告

论文：{title}

推荐期刊 Top 5：
1. {journal_1}（{score_1}/100）— {reason}
2. {journal_2}（{score_2}/100）— {reason}
3. {journal_3}（{score_3}/100）— {reason}
4. {journal_4}（{score_4}/100）— {reason}
5. {journal_5}（{score_5}/100）— {reason}

报告已保存：library/reports/submission/{paper_slug}-recommend-{date}.md
```

