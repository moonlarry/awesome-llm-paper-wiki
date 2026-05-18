# Workflow 2: scan-organize

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 2: scan-organize

> **Status**: Implemented (main flow) | duplicate detection: Implemented

### Purpose
Scan `paper/` for all Markdown files and optionally organize them into journal folders.

### Sub-triggers
- "scan papers" / "扫描文献" → steps 1–3 only (scan + plan)
- "organize by journal" / "整理期刊" → steps 1–6 (scan + move + index)
- "check duplicates" / "检查重复" → steps 1, 4 only

### Steps

1. Run: `python scripts/scan_sources.py`
   - Output: `workspace/manifests/source_manifest.json`

2. Run: `python scripts/organize_by_journal.py --all --dry-run`
   - Output: `workspace/manifests/journal_move_plan.json`

3. Display plan summary to user:
   - Files to move (count by action: move/skip/warn/conflict)
   - Journal distribution

4. **(If "check duplicates")**: Run `python scripts/detect_duplicates.py --all`:
   - Compare file SHA256 checksums (exact) and normalized title+year (probable)
   - Generate `workspace/manifests/duplicate_report.json` and `.md`

5. **(If "organize by journal")**: Ask user to confirm, then:
   - Run: `python scripts/organize_by_journal.py --all --apply`

6. Run: `python scripts/rebuild_indexes.py`
   - Triggers domain profile update (see Template System)

### Output (zh)
```
扫描完成：{N} 个文件

按操作分类：
- 移动：{move_count}
- 跳过：{skip_count}
- 冲突：{conflict_count}
- 警告：{warn_count}

计划已保存：workspace/manifests/journal_move_plan.json
是否执行移动？(y/n)
```

