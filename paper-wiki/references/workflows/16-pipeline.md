# Workflow 16: pipeline

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 16: pipeline

### Purpose
Execute the full preprocessing pipeline in sequence.

### Steps

Execute in order, stopping on errors:
1. **init**
2. **scan-organize** (scan only, no move unless user confirms)
3. **ingest** (all unprocessed papers)
4. **tag** (batch tag)
5. **rebuild indexes** (via `python scripts/rebuild_indexes.py`)
6. **status** (show final state)

### Output (zh)
```
完整流程执行完成

1. ✅ 初始化
2. ✅ 扫描：{N} 个文件
3. ✅ 入库：{N} 篇新增
4. ✅ 打标：{N} 篇更新
5. ✅ 索引重建
6. 当前状态：{summary}
```

