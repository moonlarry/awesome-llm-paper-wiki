# Workflow 17: paper-read

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 17: paper-read

### Purpose
Read one paper deeply and generate a structured reading note for single-paper understanding.

Answer these questions:
- What problem does this paper solve?
- Why is this problem important?
- What method or model does it use?
- Why can this method or model solve the problem?
- What are the core conclusions?
- What can be done next?

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
   - Because this workflow reads one paper, do not apply the multi-paper Report Citation Policy unless additional papers are used.

6. Save output when the user asks for a file or when a durable note is useful:
   - `library/reports/paper/{date}-{paper_id}-reading.md`

### Output (zh)
```
单篇文献精读：{title}

1. 这篇文章解决了什么问题？
{answer}

2. 这个问题为什么重要？
{answer}

3. 本文使用了什么方法或模型？
{answer}

4. 为什么这个方法或模型能解决这个问题？
{answer}

5. 核心结论是什么？
{answer}

6. 下一步可以怎么做？
{answer}

阅读笔记已保存：library/reports/paper/{date}-{paper_id}-reading.md
```

