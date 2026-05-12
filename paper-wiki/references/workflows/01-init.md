# Workflow 1: init

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 1: init

### Purpose
Initialize the vault structure. Creates missing directories and seed files.

### Steps

1. Check if `E:\paper` has `config.json` — if not, create default config
2. Create missing directories:
   - `schema/`
   - `library/papers/`, `library/reports/journal/`, `library/reports/direction/`, `library/reports/review/`, `library/reports/idea/`, `library/reports/paper/`, `library/reports/submission/`, `library/reports/vault/`
   - `library/indexes/`
   - `workspace/cache/`, `workspace/cache/fulltext-review/`, `workspace/manifests/`, `workspace/logs/`, `workspace/legacy/`, `workspace/research-briefs/`
   - `templates/generic/`, `templates/domains/`
3. Create `schema/tag_taxonomy.json` if missing (empty initial structure)
4. Create `schema/keyword_rules.json` if missing (empty rules array)
5. Create `schema/paper_frontmatter.schema.md` if missing
6. Skip creating generic templates if they already exist
7. Update `paper-library.md` with skeleton if needed

### Output (zh)
```
文献库初始化完成！路径：E:\paper

已创建目录：{list}
已创建文件：{list}

接下来你可以：
- "扫描文献" — 扫描 paper/ 目录
- "整理期刊" — 按期刊缩写归类文件
- "入库" — 处理论文并生成 canonical 页
```

