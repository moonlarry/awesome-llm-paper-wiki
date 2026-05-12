# Workflow 4: tag

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 4: tag

> **Status**: Implemented (read-only audit and write-back paths clarified)

### Purpose
Manage the tag system: view, edit, batch-assign, and analyze tags.

### Sub-triggers
- "view tags" / "查看标签" → display tag_taxonomy.json summary
- "batch tag" / "批量打标" → run keyword rules on all canonical pages
- "add tag" / "添加标签" → add a custom tag to taxonomy
- "tag stats" / "标签统计" → show tag frequency distribution

### Scripts

| Script | Purpose | Command |
|--------|---------|---------|
| `scan_tags.py` | **Read-only audit**: scan tag coverage, rule hits | `python scripts/scan_tags.py --direction Battery --rules` |
| `ingest_batch.py --apply-tags` | **Write-back entry**: batch tag canonical pages | `python scripts/ingest_batch.py --direction Battery --apply-tags` |

**Note**: `scan_tags.py` is read-only and never modifies canonical pages. Tag write-back must use `ingest_batch.py --apply-tags`.

### Steps (batch tag)

1. Load `schema/tag_taxonomy.json` and `schema/keyword_rules.json`

2. For each canonical page in `library/papers/`:
   a. Read frontmatter tags
   b. Apply keyword rules to title, abstract, keywords sections
   c. Optional Agent review may suggest additional tags for manual confirmation
   d. Merge rule: preserve user tags; add keyword-rule hits without overwriting existing user edits

3. Apply tag updates through `python scripts/ingest_batch.py --direction Battery --apply-tags`

4. Rebuild indexes when batch tagging changes canonical frontmatter

### Commands
```bash
python scripts/ingest_batch.py --direction Battery --apply-tags --rebuild-indexes
python scripts/scan_tags.py --direction Battery
python scripts/scan_tags.py --direction Battery --rules --include-empty
```

### Output (zh)
```
批量打标完成：更新了 {N} 篇论文的标签

标签分布：
- task: SOH estimation (45), RUL prediction (38), SOC estimation (12), ...
- method: LSTM (28), Transformer (22), GPR (15), PINN (12), ...
- dataset: NASA (35), CALCE (30), Oxford (18), ...

新增标签：{list}
```

