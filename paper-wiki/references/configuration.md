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
        "required_groups": [
          {"name": "core_topic", "terms": ["keyword a", "keyword b"]},
          {"name": "method_family", "terms": ["method x", "method y"]}
        ],
        "negative_keywords": ["unrelated topic"],
        "preferred_venues": ["Example Journal", "Another Journal"]
      },
      "AnotherDirection": {"strict": false, "keywords": ["keyword c", "keyword d"]}
    },
    "sources": ["openalex", "semanticscholar", "arxiv"]
  }
}
```

## 参数说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `output_lang` | `"zh"` | 输出语言：`"zh"` 中文，`"en"` 英文 |
| `directions` | `[]` | `paper/` 下的研究方向文件夹名称列表 |
| `templates.regeneration_threshold` | `0.2` | 触发模板更新的文献增长比例 |
| `templates.registry` | `{}` | 记录领域模板状态和陈旧度信号 |
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
| `web_search.domain_profiles` | `{}` | 方向级领域匹配规则。建议只保留通用字段结构，并按你自己的研究方向填写关键词组、负向词和偏好期刊。 |

## 模板系统 (Template System)

默认提供通用模板（`templates/generic/`），适用于任意研究领域。

可用通用模板：
- `paper_canonical.md`
- `journal_report.md`
- `direction_report.md`
- `direction_review.md`
- `idea_survey_report.md`
- `paper_reading.md`
- `stat_report.md`
- `submission_report.md`
- `revision_report.md`

领域模板位于 `templates/domains/{domain_name}/`。当前代码可以在 `config.json` 中跟踪
模板 registry 状态，`status_report.py` 和 `lint_vault.py` 会报告 registry 状态和陈旧度信号。
正式 CLI 路径不会默认自动生成新的领域模板。

实践规则：
1. 优先使用 `templates/generic/` 中的通用模板。
2. 只有当领域模板已存在且用户明确需要时，才把它作为手动或 Agent 选择的参考结构。
3. 不要把领域模板自动生成描述为当前默认实现。
