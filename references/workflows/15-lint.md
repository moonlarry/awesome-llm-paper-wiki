# Workflow 15: lint

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 15: lint

### Purpose
Health check for the vault.

### Formal CLI
```bash
python scripts/lint_vault.py
python scripts/lint_vault.py --direction Battery
```

### Checks

1. **Orphan canonical pages**: canonical page exists but source file is missing
2. **Missing canonical pages**: source file exists but no canonical page
3. **Tag inconsistencies**: tags in canonical pages not in `tag_taxonomy.json`
4. **Stale indexes**: index files older than the latest source/canonical files
5. **Missing frontmatter**: canonical pages missing required fields
6. **Broken source_path**: canonical points to a non-existent source file
7. **Template staleness**: registry entries whose paper counts have outgrown their recorded baseline

### Output files
- `library/reports/vault/lint-{date}.md`
- `workspace/manifests/lint_vault.json`

### Output (zh)
```
文献库健康检查报告

✅ 通过：
- 索引更新状态
- 标签一致性

⚠️ 警告：
- {N} 篇论文未入库（无 canonical 页）
- {N} 个标签未在 taxonomy 中注册
- 领域模板 battery 已过时（新增 {pct}% 论文）

❌ 错误：
- {N} 个 canonical 页找不到源文件

建议操作：
1. 运行 "入库" 处理未入库论文
2. 运行 "标签" 更新标签体系
3. 运行 "重建索引" 刷新索引
```

