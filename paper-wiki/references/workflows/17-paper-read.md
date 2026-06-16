# Workflow 17: paper-read

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 17: paper-read

### Purpose
Read one paper deeply using an MIT Professor Mode framework. The goal is not to
summarize what the paper says, but to help the user understand why the work was
conceived, what problem structure it reveals, how the method follows from the
problem, whether the experiments prove the claims, and what research questions
come next.

Use the 10-phase reading paradigm:
- Phase 1: Problem Formulation
- Phase 2: Why Existing Solutions Fail
- Phase 3: Key Insight
- Phase 4: Method Derivation
- Phase 5: Mathematical Understanding
- Phase 6: Evidence Examination
- Phase 7: Critical Thinking
- Phase 8: Research Mapping
- Phase 9: AI for Science Reflection
- Phase 10: Socratic Mode

### Input
- Required: one paper path, title, DOI, canonical id, or source path
- Preferred: canonical page under `library/papers/{direction}/`
- Allowed: source Markdown under `paper/{direction}/...`
- Optional: user research context, such as "focus on battery SOH" or "focus on method novelty"

### Steps

1. Locate the paper:
   - If input is a path, read it directly.
   - If input is a title, id, or DOI, search canonical pages first, then source files.
   - If both source and canonical exist, prefer canonical metadata and inspect source/full text when needed.

2. Read metadata:
   - title, authors, journal, year, DOI, source path, tags.

3. Read content:
   - Abstract
   - Introduction / motivation
   - Method / model
   - Experiments / datasets
   - Results
   - Limitations / discussion / conclusion
   - Full text via `source_path` if canonical page provided

4. Generate the reading note using `templates/generic/paper_reading.md`.

5. Evidence discipline:
   - Ground every answer in the paper text.
   - If a point is inferred rather than explicitly stated, label it as inference.
   - If information is missing, write "Not available in the provided paper text" rather than guessing.
   - Do not use external literature unless the user explicitly asks for comparison.
   - For Research Mapping, use only the lineage and positioning that can be supported by the paper's Introduction / Related Work / references unless external comparison is explicitly requested.
   - For Mathematical Understanding, explain why a formula exists and what it means; if the paper has no relevant formula, state that directly.
   - For AI for Science Reflection, only expand the analysis when the paper is about scientific discovery, scientific modeling, or domain knowledge formation; otherwise state why the phase is not applicable.
   - Because this workflow reads one paper, do not apply the multi-paper Report Citation Policy unless additional papers are used.

6. Save output when the user asks for a file or when a durable note is useful:
   - `library/reports/paper/{date}-{paper_id}-reading.md`

### Output (zh)
```
单篇文献精读：{title}

Phase 1：问题定义（Problem Formulation）
- Problem Statement:
- Research Context:
- Why It Matters:

Phase 2：现有方法为什么不行（Why Existing Solutions Fail）
- Existing Paradigm:
- Hidden Assumptions:
- Failure Modes:
- Research Gap:

Phase 3：作者的核心洞察（Key Insight）
- Key Observation:
- Key Insight:
- Intuitive Explanation:

Phase 4：从第一性原理推导方法（Method Derivation）
- Method Motivation:
- Design Logic:
- Component Analysis:
- Necessity Analysis:

Phase 5：数学与理论本质（Mathematical Understanding）
- Mathematical Intuition:
- Physical / Statistical Meaning:
- Alternative Formulations:

Phase 6：实验是否真的证明了作者的观点（Evidence Examination）
- Hypothesis:
- Evidence:
- Missing Evidence:
- Alternative Explanations:

Phase 7：MIT式批判性思考（Critical Thinking）
- Strengths:
- Weaknesses:
- Reviewer Concerns:

Phase 8：研究地图定位（Research Mapping）
- Research Lineage:
- Research Position:
- Future Directions:

Phase 9：AI for Science 深度思考（AI for Science Reflection）
- Scientific Value:
- Knowledge Discovery Value:
- Generalization Potential:

Phase 10：导师提问环节（Socratic Mode）
- 5 个理解性问题:
- 5 个批判性问题:
- 5 个研究拓展问题:

阅读笔记已保存：library/reports/paper/{date}-{paper_id}-reading.md
```

