# Workflow 9: web-find

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 9: web-find

> **Status**: Implemented (MCP-first with CLI fallback)

### Purpose

Search academic web sources and save results as Markdown files in the local vault.

### Prerequisites

- **CLI path**: `paper/{direction}/` directory must already exist before running `web_search.py`
- **Agent path**: if direction is missing, the Agent may guide the user to choose one of two direction options and create it after confirmation
- **MCP path**: MCP tools are preferred when available; fallback to CLI when MCP unavailable

### Data Layers

- Formal full-text library: `paper/{direction}/{journal_abbr}/` for clipped journal papers and arXiv papers with extracted full text
- Web-search research layer: `paper/web_search/{direction}/{source}/` for OpenAlex/Semantic Scholar metadata and arXiv non-full-text fallbacks
- Knowledge layer: `library/` for canonical pages, indexes, and reports

### Input

- Required: `--direction {existing_direction}`
- Required: query text, e.g. `web-find --direction Battery --query "battery RUL transformer" --top 10`
- Optional: `--top N`, `--source mixed|openalex|semanticscholar|arxiv|venues`, `--fulltext`, `--no-fulltext`, `--arxiv-id`, `--no-domain-filter`, `--show-filtered`, `--dry-run`

### MCP Integration

This workflow uses a **MCP-first** strategy with CLI fallback:

| Priority | Layer | Provider | Use Case |
|:---:|:---|:---|:---|
| 1 | Discovery | `paper-search-mcp` | Broad multi-source search (OpenAlex, Semantic Scholar, arXiv) |
| 2 | arXiv Deep | `arxiv-mcp-server` | arXiv precise search, full-text extraction, citation graph |
| 3 | Fallback | `web_search.py` CLI | Direct HTTP API when MCP unavailable |

**MCP Tool Reference**:

| MCP Server | Tool Name | Purpose |
|:---|:---|:---|
| `paper-search-mcp` | `mcp__paper-search-mcp__search_papers` | Unified multi-source search with deduplication |
| `paper-search-mcp` | `mcp__paper-search-mcp__search_openalex` | OpenAlex single-source search |
| `paper-search-mcp` | `mcp__paper-search-mcp__search_semantic` | Semantic Scholar single-source search |
| `paper-search-mcp` | `mcp__paper-search-mcp__download_with_fallback` | OA-first download chain for non-arXiv papers |
| `arxiv-mcp-server` | `mcp__arxiv__search_papers` | arXiv search with category/date filters |
| `arxiv-mcp-server` | `mcp__arxiv__get_abstract` | Fast arXiv metadata by ID |
| `arxiv-mcp-server` | `mcp__arxiv__download_paper` | Download arXiv full text (HTML/TeX/PDF) |
| `arxiv-mcp-server` | `mcp__arxiv__read_paper` | Read downloaded arXiv paper content |

### Steps

#### Step 1: Parse inputs and check MCP availability

1. Parse input arguments: `--direction`, `--query`, `--source`, `--top`, `--arxiv-id`
2. Load `config.json` and check `mcp.enabled` setting
3. Check MCP server availability:
   - List available MCP tools via `ListMcpResourcesTool` or runtime check
   - Record which MCP servers are connected: `paper-search-mcp`, `arxiv-mcp-server`
4. If both MCP servers unavailable and `mcp.fallback_to_cli=true`, proceed to CLI fallback path
5. If MCP unavailable and `mcp.fallback_to_cli=false`, report error and suggest MCP installation

#### Step 2: Route by intent

Route the request based on input parameters:

| Input Condition | Route | Primary MCP |
|:---|:---|:---|
| `--arxiv-id` present | arXiv exact route | `arxiv-mcp-server` |
| `--source=arxiv` | arXiv keyword route | `arxiv-mcp-server` |
| `--source=mixed` | Broad discovery route | `paper-search-mcp` |
| `--source=openalex` | Single-source route | `paper-search-mcp` |
| `--source=semantic` | Single-source route | `paper-search-mcp` |
| `--source=semanticscholar` | Single-source route (alias) | `paper-search-mcp` |
| `--source=venues` | Venue-filtered route | `paper-search-mcp` |
| No `--source` specified | Default: `mixed` route | `paper-search-mcp` |

#### Step 3: Broad discovery route (`--source=mixed`)

**Primary**: `mcp__paper-search-mcp__search_papers`

Call parameters:
```json
{
  "query": "<user_query>",
  "max_results_per_source": 5,
  "sources": "openalex,semantic,arxiv"
}
```

Response structure:
```json
{
  "query": "...",
  "sources_used": ["openalex", "semantic", "arxiv"],
  "source_results": { "openalex": 5, "semantic": 3, "arxiv": 4 },
  "papers": [...],
  "total": 12,
  "errors": {}
}
```

Process results:
1. Save OpenAlex metadata to `paper/web_search/{direction}/openalex/`
2. Save Semantic Scholar metadata to `paper/web_search/{direction}/semanticscholar/`
3. Save arXiv metadata to `paper/web_search/{direction}/arxiv/`
4. For arXiv hits, evaluate fulltext decision:
   - If `config.mcp.arxiv.download_fulltext.mixed=true`, download full text for top N papers
   - Cap downloads by `config.mcp.arxiv.download_fulltext.max_fulltext_per_run`

**Fallback**: If `paper-search-mcp` unavailable or returns error:
- Try `arxiv-mcp-server.search_papers` for arXiv portion
- Then fall back to CLI: `python scripts/web_search.py find --source mixed ...`

#### Step 4: Single-source route

**OpenAlex** (`--source=openalex`):
```json
{
  "tool": "mcp__paper-search-mcp__search_openalex",
  "params": {
    "query": "<user_query>",
    "max_results": <top>
  }
}
```

**Semantic Scholar** (`--source=semanticscholar`):
```json
{
  "tool": "mcp__paper-search-mcp__search_semantic",
  "params": {
    "query": "<user_query>",
    "max_results": <top>
  }
}
```

**Venue-filtered** (`--source=venues`):
- Use OpenAlex search with venue filter from `config.web_find.venues`
- Filter results to match `config.domain_profiles.{direction}.preferred_venues`

Save results to respective `paper/web_search/{direction}/{source}/` directories.

#### Step 5: arXiv keyword route (`--source=arxiv`)

**Primary**: `mcp__arxiv__search_papers`

Call parameters:
```json
{
  "query": "<user_query>",
  "max_results": <top>,
  "sort_by": "relevance",
  "categories": ["<from config.domain_profiles.{direction}.arxiv_categories>"]
}
```

Categories are sourced from:
- `config.domain_profiles.{direction}.arxiv_categories` (if defined)
- Common defaults: `["cs.AI", "cs.LG", "cs.CL", "cs.CV", "stat.ML"]`

Process each result:
1. Save metadata to `paper/web_search/{direction}/arxiv/`
2. Evaluate fulltext decision:
   - If `config.mcp.arxiv.download_fulltext.source_arxiv=true`, attempt full text download
   - Use format priority from `config.mcp.arxiv.content_priority`: `["html", "tex", "pdf"]`

#### Step 6: arXiv exact route (`--arxiv-id`)

**Step 6A**: Get metadata via `mcp__arxiv__get_abstract`
```json
{
  "arxiv_id": "<user_provided_id>"
}
```

**Step 6B**: Download full text via `mcp__arxiv__download_paper`
```json
{
  "paper_id": "<arxiv_id>"
}
```

The download tool automatically:
- Tries HTML first (best for modern papers)
- Falls back to TeX source extraction
- Falls back to PDF download

**Step 6C**: If full text needed, read via `mcp__arxiv__read_paper`
```json
{
  "paper_id": "<arxiv_id>"
}
```

Save paths:
- Full text extracted → `paper/{direction}/arxiv/{year}-{first_author}-{title_slug}-{arxiv_id}.md`
- Metadata only → `paper/web_search/{direction}/arxiv/{year}-{first_author}-{title_slug}-{arxiv_id}.md`

#### Step 7: Fulltext decision logic

Evaluate whether to download full text for arXiv results based on `config.mcp.arxiv.download_fulltext`:

| Condition | Download? | Config Key | Default |
|:---|:---:|:---|:---:|
| `--arxiv-id` exact route | Config-controlled | `exact_id` | true |
| `--source=arxiv` keyword | Config-controlled, capped | `source_arxiv` | true |
| `--source=mixed` broad | Config-controlled | `mixed` | false |
| `--fulltext` flag override | Yes | Overrides config | - |
| `--no-fulltext` flag | No | Overrides config | - |

Download cap: `config.mcp.arxiv.download_fulltext.max_fulltext_per_run` (default: 5)

Content format priority: `config.mcp.arxiv.content_priority` (default: `["html", "tex", "pdf"]`)

#### Step 8: Domain filter and deduplicate

Apply domain filtering to all results:
1. Load `config.domain_profiles.{direction}`
2. Evaluate each candidate against profile:
   - `strict` mode: require all `required_groups` keyword groups
   - Reject papers with strong `negative_keywords` hits
3. Filter out non-matching papers unless `--no-domain-filter` is set

Deduplicate by identity:
1. Primary identity: DOI (`doi:<lowercase_doi>`)
2. arXiv identity: arXiv ID (`arxiv:<lowercase_id>`)
3. Fallback identity: normalized title + year + first author

Never overwrite existing source Markdown files.

#### Step 9: Normalize and write results

For each saved paper, add MCP provenance to frontmatter:
```yaml
---
# ... existing fields ...
mcp_provider: "paper-search-mcp" | "arxiv-mcp-server"
mcp_tool: "search_papers" | "download_paper" | "get_abstract"
retrieved_at: <ISO timestamp>
retrieval_path: "mcp" | "cli_fallback"
---
```

Generate canonical pages only for formal source saves under `paper/{direction}/`:
- Call `generate_canonical` for each full-text arXiv paper
- Rebuild indexes via `rebuild_indexes.py`

#### Step 10: Generate report and manifest

Generate web-find report at:
- `library/reports/web/{date}-{direction}-find-report.md`

Report sections:
1. Summary: total found, per-source counts, MCP vs CLI usage
2. New Findings - OpenAlex/Semantic Scholar: table with title, authors, year, DOI, URL
3. New Findings - arXiv Full Text: table with title, authors, year, arXiv link, fulltext status
4. Filtered-out candidates: list with rejection reasons
5. MCP status: which servers used, any fallback events
6. Installation suggestion (if MCP unavailable)

Write manifests:
- `workspace/manifests/arxiv_fulltext_results.json` for arXiv full text
- `workspace/manifests/web_search_results.json` for OA/SS metadata

Log operation to `workspace/logs/web_search.md`

#### Step 11: CLI fallback path

**Fallback rule**: CLI fallback is allowed only when `config.mcp.fallback_to_cli=true` AND one of the fallback triggers occurs.

**Fallback triggers**:
- Both MCP servers (`paper-search-mcp`, `arxiv-mcp-server`) unavailable
- MCP tool call timeout or error
- `config.mcp.enabled=false`

**No fallback**:
- Valid empty result (no papers matching query) - unless `config.mcp.fallback_on_empty=true`
- `config.mcp.fallback_to_cli=false` - report error instead of using CLI

If fallback triggered, execute CLI:

```bash
python scripts/web_search.py find --direction {direction} --query "{query}" --top {top} --source {source}
```

CLI behavior (unchanged from legacy):
1. Validate `paper/{direction}/` exists (fail-fast if missing)
2. Direct HTTP requests to OpenAlex, Semantic Scholar, arXiv APIs
3. Apply domain filter and save to same directory structure
4. Generate same report format

At workflow completion, if CLI was used due to MCP unavailable:
- Output suggestion: "建议安装 MCP 服务器以增强网络搜索功能：arxiv-mcp-server 和 paper-search-mcp。详见 config.json 中的 mcp 配置说明。"
- Do NOT auto-install MCP servers
- If user agrees to install, follow official docs from each MCP repository

### Command Reference

**MCP path (Agent)**:
```
# Intent routing handled by Agent per above steps
web-find --direction Battery --query "battery RUL transformer" --top 10
web-find --direction Battery --source arxiv --arxiv-id 2502.18807v7 --fulltext
```

**CLI path**:
```bash
python scripts/web_search.py find --direction Battery --query "battery RUL transformer" --top 10
python scripts/web_search.py find --direction Battery --source arxiv --arxiv-id 2502.18807v7 --fulltext
```