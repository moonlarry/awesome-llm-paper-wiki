# Workflow 3: ingest

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 3: ingest

### Purpose
Process paper Markdown files: extract metadata, generate canonical pages, convert HTML tables.

### Input
- A specific file path, or "all new papers", or a journal/direction scope

### Steps

1. Identify target files:
   - If path given → process that file
   - If "all" → scan `paper/` for files without corresponding canonical pages in `library/papers/`
   - If journal/direction given → filter accordingly

2. For each target file:

   a. **Read file** and parse frontmatter using the same logic as `scripts/common.py`

   b. **Extract/complete metadata**:
      - `title`: from frontmatter or filename
      - `journal`, `journal_abbr`: from `resolve_journal()` logic
      - `published_date`: parse from frontmatter `published`, `created`, or body text
      - `doi`: extract from frontmatter `source` or body DOI patterns
      - `url`: from frontmatter `source`

   c. **Generate paper ID**: `{direction}-{year}-{journal_abbr}-{slug}`
      - slug = first 5 significant words of title, lowercase, hyphenated

   d. **Identify tag candidates** from title, abstract, keywords, highlights:
      - Match against `schema/keyword_rules.json` patterns
      - Agent or LLM review can optionally suggest extra tags during a manual path
      - Rule-based tagging is the only built-in automatic write-back path

   e. **Convert HTML tables** to Markdown:
      - Run: `python scripts/html_table_to_md.py <file_path>` (if HTML tables found)
      - Or an Agent can convert simple tables inline during a manual path

   f. **Generate canonical page** to `library/papers/{direction}/{paper_id}.md`:
      - Use template: `templates/generic/paper_canonical.md`
      - Fill frontmatter fields, abstract, keywords
      - Set `source_path` to link back to original source file
      - Preserve `## User Notes` section if existing canonical page already exists

3. **Domain profile update**: Count papers by domain tag, update `config.json` template registry

### Batch Command
```bash
python scripts/ingest_batch.py --direction Battery --journal Energy --apply-tags --rebuild-indexes
python scripts/ingest_batch.py --file paper/Battery/arxiv/example.md --apply-tags
python scripts/ingest_batch.py --direction Battery --dry-run
```

### Output (zh)
```
入库完成：处理了 {N} 篇论文

新增 canonical 页：
- {paper_id_1}
- {paper_id_2}

标签候选（需确认）：
- "transfer learning" → method [新标签]
- "CALCE" → dataset [已有标签]

确认添加新标签？(y/n)
```

