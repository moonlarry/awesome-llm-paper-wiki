# Workflow 13: revision-suggest

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 13: revision-suggest

### Purpose
Generate targeted revision suggestions for a paper aimed at a specific journal.

### Input
- Path to the user's paper (Markdown file)
- Target journal name or abbreviation

### Steps

1. Read the user's paper

2. Read the target journal's literature collection (canonical pages)

3. Read the journal report if available

4. Compare across 5 dimensions:

   **a. Formatting (排版)**:
   - Section structure vs. typical papers in the journal
   - Figure/table style conventions
   - Length norms

   **b. Method Writing Style (方法写作风格)**:
   - How methods are typically presented in this journal
   - Level of mathematical formalism
   - Pseudo-code vs. text description preferences

   **c. Research Method Sufficiency (研究方法充足性)**:
   - Number of baselines typically compared
   - Ablation study expectations
   - Statistical significance testing norms

   **d. Introduction Alignment (引言适配)**:
   - Research motivation framing typical of this journal
   - Literature review scope and depth
   - Problem statement style

   **e. Reference Coverage (参考文献覆盖)**:
   - Key papers from this journal that should be cited
   - Reference count norms
   - Self-citation patterns

5. **Prioritize** suggestions by impact: critical → important → optional

6. **Generate report** → `library/reports/submission/{paper_slug}-revision-for-{journal}-{date}.md`
   - Use template: `templates/generic/revision_report.md`
   - Apply the Report Citation Policy: cite target-journal papers where they support formatting, method, experiment, introduction, reference-coverage, or action-list suggestions, and list all cited evidence in `Evidence Basis`.

### Output (zh)
```
面向 {journal} 的修改建议

评估维度：
- 排版：{score}/5 — {summary}
- 方法写作：{score}/5 — {summary}
- 研究方法：{score}/5 — {summary}
- 引言适配：{score}/5 — {summary}
- 参考文献：{score}/5 — {summary}

关键修改建议（共 {N} 条）：
1. [关键] {suggestion_1}
2. [关键] {suggestion_2}
3. [重要] {suggestion_3}
...

报告已保存：library/reports/submission/{paper_slug}-revision-for-{journal}-{date}.md
```

