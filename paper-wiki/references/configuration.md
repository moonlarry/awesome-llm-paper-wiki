# 配置指南 (Configuration)

文档库的各项行为均可通过根目录下的 `config.json` 进行配置。

```json
{
  "output_lang": "zh",
  "directions": ["ExampleDirection", "AnotherDirection"],
  "templates": {
    "regeneration_threshold": 0.2,
    "registry": {}
  },
  "research_workflows": {
    "external_reviewer": "codex",
    "external_reviewer_model": "",
    "external_reviewer_effort": "xhigh",
    "max_review_rounds": 4,
    "require_human_checkpoints": true,
    "novelty_check_sources": ["canonical_pages", "source_markdown", "web_digest"],
    "live_web_search": false
  },
  "mcp": {
    "enabled": true,
    "fallback_to_cli": true,
    "fallback_on_empty": false,
    "timeout_seconds": 30,
    "paper_search": {
      "enabled": true,
      "broad_sources": ["openalex", "semantic", "arxiv"]
    },
    "arxiv": {
      "enabled": true,
      "content_priority": ["html", "tex", "pdf"],
      "download_fulltext": {
        "exact_id": true,
        "source_arxiv": true,
        "mixed": false,
        "digest": false,
        "max_fulltext_per_run": 5
      }
    }
  },
  "web_digest": {
    "lookback_days": 7,
    "sort_by": "submittedDate",
    "sort_order": "descending",
    "use_alerts": false
  },
  "web_find": {
    "default_top": 10,
    "venues": []
  },
  "web_search": {
    "default_top": 10,
    "min_citations": 5,
    "openalex_email": "",
    "openalex_api_key": "",
    "semantic_scholar_api_key": "",
    "clipper_inbox": "workspace/web-inbox",
    "output_root": "paper/web_search",
    "arxiv_fulltext_default": true,
    "arxiv_output_root": "paper/web_search",
    "arxiv_fulltext_priority": ["html", "tex", "pdf", "api"],
    "domain_profiles": {
      "ExampleDirection": {
        "strict": true,
        "arxiv_categories": ["cs.AI", "cs.LG", "stat.ML"],
        "required_groups": [
          {"name": "core_topic", "terms": ["keyword a", "keyword b"]},
          {"name": "method_family", "terms": ["method x", "method y"]}
        ],
        "negative_keywords": ["unrelated topic"],
        "preferred_venues": ["Example Journal", "Another Journal"]
      },
      "AnotherDirection": {
        "strict": false,
        "arxiv_categories": ["cs.CL", "cs.IR"],
        "keywords": ["keyword c", "keyword d"]
      }
    },
    "sources": ["openalex", "semanticscholar", "arxiv"]
  }
}
```

## 参数说明

### 基础配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `output_lang` | `"zh"` | 输出语言：`"zh"` 中文，`"en"` 英文 |
| `directions` | `[]` | `paper/` 下的研究方向文件夹名称列表 |
| `templates.regeneration_threshold` | `0.2` | 触发模板更新的文献增长比例 |
| `templates.registry` | `{}` | 记录领域模板状态和陈旧度信号 |

### MCP 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `mcp.enabled` | `true` | 是否启用 MCP 工具调用 |
| `mcp.fallback_to_cli` | `true` | MCP 不可用时是否回退到 CLI |
| `mcp.fallback_on_empty` | `false` | MCP 返回空结果时是否触发 fallback |
| `mcp.timeout_seconds` | `30` | MCP 工具调用超时时间 |

### MCP paper-search-mcp 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `mcp.paper_search.enabled` | `true` | 是否启用 paper-search-mcp |
| `mcp.paper_search.broad_sources` | `["openalex", "semantic", "arxiv"]` | 多源聚合搜索的默认源列表 |

### MCP arxiv-mcp-server 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `mcp.arxiv.enabled` | `true` | 是否启用 arxiv-mcp-server |
| `mcp.arxiv.content_priority` | `["html", "tex", "pdf"]` | arXiv 全文获取格式优先级 |
| `mcp.arxiv.download_fulltext.exact_id` | `true` | arXiv ID 精确搜索时是否下载全文 |
| `mcp.arxiv.download_fulltext.source_arxiv` | `true` | arXiv 关键词搜索时是否下载全文 |
| `mcp.arxiv.download_fulltext.mixed` | `false` | 多源混合搜索时是否下载 arXiv 全文 |
| `mcp.arxiv.download_fulltext.digest` | `false` | digest 模式是否下载全文 |
| `mcp.arxiv.download_fulltext.max_fulltext_per_run` | `5` | 单次运行最大全文下载数量 |

### web_digest 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `web_digest.lookback_days` | `7` | digest 回溯天数 |
| `web_digest.sort_by` | `"submittedDate"` | 排序字段 |
| `web_digest.sort_order` | `"descending"` | 排序方向 |
| `web_digest.use_alerts` | `false` | 是否使用 alert 模式（增量获取） |

### web_find 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `web_find.default_top` | `10` | 默认返回结果数量 |
| `web_find.venues` | `[]` | venue 过滤模式下的目标期刊列表 |

### 研究工作流配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `research_workflows.external_reviewer` | `"codex"` | review/audit 工作流默认优先尝试 Codex-compatible MCP reviewer；在 Claude Code 中 reviewer 名称为 `codex` |
| `research_workflows.external_reviewer_model` | `""` | 外部 reviewer 的可选模型名；为空时使用运行时默认 |
| `research_workflows.external_reviewer_effort` | `"xhigh"` | 外部 reviewer 的推理强度 |
| `research_workflows.max_review_rounds` | `4` | `auto-review-loop` / `paper-review-loop` 最大轮数 |
| `research_workflows.require_human_checkpoints` | `true` | review / revision checkpoint 是否默认需要用户确认 |
| `research_workflows.novelty_check_sources` | `["canonical_pages","source_markdown","web_digest"]` | `idea-claim-novelty-check` 的默认证据层 |
| `research_workflows.live_web_search` | `false` | 是否允许 `idea-claim-novelty-check` 额外触发一次实时 `web-find` |

### 联网检索配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `web_search.default_top` | `10` | 联网检索默认最大保存数量 |
| `web_search.min_citations` | `5` | OpenAlex 默认最低引用量阈值过滤 |
| `web_search.openalex_api_key` | `""` | 可选 OpenAlex API key，用于保障正常额度访问 |
| `web_search.openalex_email` | `""` | 可选 OpenAlex 联系邮箱 / 作为 `mailto` 发送给服务器识别 |
| `web_search.semantic_scholar_api_key` | `""` | 可选 Semantic Scholar API key |
| `web_search.clipper_inbox` | `"workspace/web-inbox"` | Obsidian Web Clipper Markdown 的导入目录 |
| `web_search.output_root` | `"paper/web_search"` | 联网检索调研资料层根目录 |
| `web_search.arxiv_fulltext_default` | `true` | arXiv 检索默认尝试保存全文 |
| `web_search.arxiv_output_root` | `"paper/web_search"` | arXiv 联网检索兜底（非全文）存放目录 |
| `web_search.arxiv_fulltext_priority` | `["html","tex","pdf","api"]` | arXiv 全文获取优先级 |
| `web_search.domain_profiles` | `{}` | 方向级领域匹配规则 |

### domain_profiles 配置

每个研究方向可定义独立的领域匹配规则：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `domain_profiles.{direction}.strict` | `true` | 是否严格匹配所有 required_groups |
| `domain_profiles.{direction}.arxiv_categories` | `[]` | arXiv 类别过滤（如 `["cs.AI", "cs.LG", "stat.ML"]`） |
| `domain_profiles.{direction}.required_groups` | `[]` | 必需的关键词组列表 |
| `domain_profiles.{direction}.negative_keywords` | `[]` | 负向关键词（命中则拒绝） |
| `domain_profiles.{direction}.preferred_venues` | `[]` | 偏好期刊列表（venue 模式过滤） |
| `domain_profiles.{direction}.keywords` | `[]` | 简单关键词列表（非严格模式） |

## MCP 服务器安装建议

当 MCP 服务器未安装时，web-find 和 web-digest 工作流将通过 CLI fallback 执行。工作流结束时将提示：

> 建议安装 MCP 服务器以增强网络搜索功能：arxiv-mcp-server 和 paper-search-mcp。

### arxiv-mcp-server 安装

官方仓库：https://github.com/blazickjp/arxiv-mcp-server

安装方式：
```bash
uv tool install arxiv-mcp-server
```

MCP 配置（添加到 Claude Code MCP 配置文件）：
```json
{
  "mcpServers": {
    "arxiv": {
      "command": "uvx",
      "args": ["arxiv-mcp-server"]
    }
  }
}
```

**重要**：server alias 必须为 `"arxiv"` 才能匹配工作流文档中的工具名 `mcp__arxiv__*`。如果使用其他 alias（如 `"arxiv-mcp-server"`），工具名前缀会变为 `mcp__arxiv-mcp-server__*`，需要相应调整工作流。

### paper-search-mcp 安装

官方仓库：https://github.com/openags/paper-search-mcp

安装方式：
```bash
uv tool install paper-search-mcp
```

MCP 配置：
```json
{
  "mcpServers": {
    "paper-search-mcp": {
      "command": "uvx",
      "args": ["paper-search-mcp"]
    }
  }
}
```

**工具名映射**：
- 统一多源搜索：`mcp__paper-search-mcp__search_papers`（推荐）
- 单源搜索：`mcp__paper-search-mcp__search_openalex`, `mcp__paper-search-mcp__search_semantic`, `mcp__paper-search-mcp__search_arxiv` 等

### MCP 服务器能力对比

| 能力 | arxiv-mcp-server | paper-search-mcp |
|:---|:---|:---|
| arXiv 精确搜索 | ✓ primary | ✓ fallback |
| arXiv 全文提取 (HTML/TeX/PDF) | ✓ | - |
| 本地论文缓存管理 | ✓ | - |
| 引用图谱 (Semantic Scholar) | ✓ | - |
| 研究 alert (watch_topic) | ✓ | - |
| 多源聚合搜索 (OA/SS/arXiv 等) | - | ✓ primary |
| OA-first 下载链 | - | ✓ |
| 去重聚合 | - | ✓ |

## 报告生成 (Report Generation)

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `report_generation.include_reference_sections` | `false` | 控制 Agent 读取源论文时是否包含 References/Bibliography 段。Agent 应运行 `records[*].source_read_command` 创建临时视图后读取，不要直接读取 `records[*].source_path`。默认跳过；可通过 `--include-references` CLI 参数临时启用。 |

## 模板系统 (Template System)

默认提供通用模板（`templates/generic/`），适用于任意研究领域。

可用通用模板：
- `paper_canonical.md`
- `journal_report.md`
- `direction_report.md`
- `direction_review.md`
- `idea_survey_report.md`
- `idea_evidence.md`
- `idea_report.md`
- `idea_claim_novelty_check.md`
- `auto_review.md`
- `resubmit_audit.md`
- `paper_review_loop.md`
- `paper_reading.md`
- `stat_report.md`
- `submission_report.md`
- `revision_report.md`

领域模板位于 `templates/domains/{domain_name}/`。当前代码可以在 `config.json` 中跟踪模板 registry 状态，`status_report.py` 和 `lint_vault.py` 会报告 registry 状态和陈旧度信号。正式 CLI 路径不会默认自动生成新的领域模板。

实践规则：
1. 优先使用 `templates/generic/` 中的通用模板。
2. 只有当领域模板已存在且用户明确需要时，才把它作为手动或 Agent 选择的参考结构。
3. 不要把领域模板自动生成描述为当前默认实现。