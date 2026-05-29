# Workflow 10: web-digest

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 10: web-digest

> **Status**: Implemented (MCP-first with CLI fallback)

### Purpose

Fetch recent arXiv papers for a direction and save them as Markdown sources plus a digest report.

### Input

- Required: `--direction {existing_direction}`
- Required: `--query "topic"`
- Optional: `--top N`, `--no-domain-filter`, `--show-filtered`, `--dry-run`

### MCP Integration

This workflow uses a **MCP-first** strategy with CLI fallback:

| Priority | Layer | Provider | Use Case |
|:---:|:---|:---|:---|
| 1 | arXiv Deep | `arxiv-mcp-server` | Recent arXiv search, full-text extraction, alerts |
| 2 | Discovery Fallback | `paper-search-mcp` | arXiv search when arxiv-mcp-server unavailable |
| 3 | CLI Fallback | `web_search.py` CLI | Direct HTTP API when MCP unavailable |

**MCP Tool Reference**:

| MCP Server | Tool Name | Purpose |
|:---|:---|:---|
| `arxiv-mcp-server` | `mcp__arxiv__search_papers` | arXiv search with date sorting |
| `arxiv-mcp-server` | `mcp__arxiv__watch_topic` | Register topic for alert monitoring |
| `arxiv-mcp-server` | `mcp__arxiv__check_alerts` | Check new papers since last check |
| `arxiv-mcp-server` | `mcp__arxiv__download_paper` | Download arXiv full text |
| `paper-search-mcp` | `mcp__paper-search-mcp__search_arxiv` | arXiv search fallback |

### Steps

#### Step 1: Parse inputs and check MCP availability

1. Parse input arguments: `--direction`, `--query`, `--top`
2. Load `config.json` and check `mcp.enabled` setting
3. Check MCP server availability:
   - `arxiv-mcp-server` (primary for digest)
   - `paper-search-mcp` (fallback)
4. If both MCP servers unavailable and `mcp.fallback_to_cli=true`, proceed to CLI fallback path

#### Step 2: CLI direction validation

CLI behavior: validate that `paper/{direction}/` already exists. If missing, `web_search.py` fail-fast with guidance to create the direction before running `web-digest`.

Agent recovery branch for a missing direction:
- reuse the same bootstrap flow as `web-find`
- analyze the query and existing direction/profile context
- offer two direction options and wait for user confirmation
- after confirmation, create the direction folders and config/profile stub, then rerun `web-digest`

#### Step 3: Build arXiv query

Build a profile-aware arXiv query from:
- `config.web_search.domain_profiles.{direction}` keywords
- `config.web_digest.lookback_days` for date range
- `config.web_search.domain_profiles.{direction}.arxiv_categories` for category filter

Query components:
- Base query: `--query` argument
- Category filter: from `arxiv_categories` (if defined)
- Date filter: `date_from = today - lookback_days`

#### Step 4: Query recent arXiv papers via MCP

**Primary**: `mcp__arxiv__search_papers`

Call parameters:
```json
{
  "query": "<constructed_query>",
  "max_results": <top>,
  "sort_by": "date",
  "date_from": "<lookback_date>",
  "categories": ["<from arxiv_categories>"]
}
```

Sort configuration:
- MCP parameter `sort_by="date"` corresponds to config `web_digest.sort_by="submittedDate"`
- Sort by date ensures newest papers first

#### Step 5: Optional alert mode

If `config.web_digest.use_alerts=true`:

**Step 5A**: Register topic watch via `mcp__arxiv__watch_topic`
```json
{
  "topic": "<query>",
  "categories": ["<arxiv_categories>"],
  "max_results": <top>
}
```

**Step 5B**: Check for new papers via `mcp__arxiv__check_alerts`
```json
{}
```

Alert mode returns only papers published since last check, enabling incremental digest without re-querying all recent papers.

Default behavior: stateless search (matches current web-digest functionality).

#### Step 6: Fulltext decision

Evaluate whether to download full text:

| Condition | Download? | Config Key |
|:---|:---:|:---|
| Default digest | No (abstract only) | `mcp.arxiv.download_fulltext.digest` (default: false) |
| `--fulltext` flag | Yes | Overrides config |

Digest typically saves metadata + abstract only for efficiency.

If fulltext enabled:
- Cap downloads by `config.mcp.arxiv.download_fulltext.max_fulltext_per_run` (default: 5)
- Format priority: `config.mcp.arxiv.content_priority` (default: `["html", "tex", "pdf"]`)

Call `mcp__arxiv__download_paper` for selected papers:
```json
{
  "paper_id": "<arxiv_id>"
}
```

#### Step 7: Apply domain filter

Apply the same domain filter used by `web-find`:
- Evaluate each candidate against `config.domain_profiles.{direction}`
- Strict profiles require all configured `required_groups`
- Reject papers with strong `negative_keywords` hits
- Save only accepted candidates unless `--no-domain-filter` is set

#### Step 8: Save results

Save paths:
- Full text extracted → `paper/{direction}/arxiv/{year}-{first_author}-{title_slug}-{arxiv_id}.md`
- Metadata/abstract only → `paper/web_search/{direction}/arxiv/{year}-{first_author}-{title_slug}-{arxiv_id}.md`

Add MCP provenance to frontmatter:
```yaml
---
# ... existing fields ...
mcp_provider: "arxiv-mcp-server"
mcp_tool: "search_papers" | "download_paper"
retrieved_at: <ISO timestamp>
retrieval_path: "mcp" | "cli_fallback"
---
```

Generate canonical pages only when a full-text arXiv paper entered the formal library:
- Call `generate_canonical` for each full-text save
- Rebuild indexes via `rebuild_indexes.py`

#### Step 9: Generate digest report

Generate digest report at:
- `library/reports/web/{date}-{direction}-digest.md`

Report sections:
1. Summary: papers found, date range, categories, MCP status
2. Recent arXiv Papers: table with title, authors, submitted date, arXiv link, abstract summary
3. Full Text Downloads: list of papers with extracted full text
4. Filtered-out candidates: list with rejection reasons
5. MCP status: server used, any fallback events
6. Installation suggestion (if MCP unavailable)

Include `filtered_out` candidates for auditability.

#### Step 10: Log and manifest

Write manifest:
- `workspace/manifests/arxiv_fulltext_results.json` (if any full text downloaded)
- `workspace/manifests/web_search_results.json` (metadata only)

Log operation to `workspace/logs/web_search.md`

#### Step 11: CLI fallback path

If MCP servers unavailable, execute CLI fallback:

```bash
python scripts/web_search.py digest --direction {direction} --query "{query}" --top {top}
```

CLI behavior (unchanged from legacy):
1. Validate `paper/{direction}/` exists
2. Direct HTTP request to arXiv API with date sorting
3. Apply domain filter and save to same directory structure
4. Generate same digest report format

At workflow completion, if CLI was used due to MCP unavailable:
- Output suggestion: "建议安装 MCP 服务器以增强网络搜索功能：arxiv-mcp-server 和 paper-search-mcp。详见 config.json 中的 mcp 配置说明。"

#### Step 12: Fallback chain

**Fallback rule**: CLI fallback is allowed only when `config.mcp.fallback_to_cli=true` AND one of the fallback triggers occurs.

MCP fallback order (trigger conditions):
1. **Primary**: `arxiv-mcp-server.search_papers` (with date sort)
2. **Secondary**: `mcp__paper-search-mcp__search_arxiv` (with `sort_by="submittedDate"`)
3. **CLI**: `web_search.py digest`

**Fallback triggers**:
- MCP server unavailable (not connected)
- MCP tool call timeout or error
- `config.mcp.enabled=false`

**No fallback**:
- Valid empty result (no new papers matching query) - unless `config.mcp.fallback_on_empty=true`
- `config.mcp.fallback_to_cli=false` - do not use CLI fallback

### Command Reference

**MCP path (Agent)**:
```
# MCP tools called per above steps
web-digest --direction Battery --query "battery health prognosis" --top 10
```

**CLI path**:
```bash
python scripts/web_search.py digest --direction Battery --query "battery health prognosis" --top 10
```