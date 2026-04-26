# 配置指南 (Configuration)

[<- 返回主页](../README.md)

文档库的各项行为均可通过根目录下的 `config.json` 进行配置。

```json
{
  "output_lang": "zh",
  "directions": ["ExampleDirection", "AnotherDirection"],
  "templates": {
    "regeneration_threshold": 0.2,
    "domain_min_papers": 10
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
| `templates.domain_min_papers` | `10` | 触发领域模板生成的最少文献数量 |
| `templates.regeneration_threshold` | `0.2` | 触发模板更新的文献增长比例 |
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

## 报告生成 (Report Generation)

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `report_generation.include_reference_sections` | `false` | 控制 Agent 读取 `records[*].source_path` 时是否包含源论文 References/Bibliography 段。默认跳过；可通过 `--include-references` CLI 参数临时启用。 |

## 模板系统 (Template System)

默认提供通用模板（`templates/generic/`），适用于任意研究领域。

当某个领域的论文积累达到阈值（由 `domain_min_papers` 配置，默认为不少于 10 篇文献时），系统会**自动生成领域特定模板**。

例如，针对某个具体研究方向生成的模板可能会预先提取出如下子结构供 LLM 参考：
- **方法子类**：Model-based、Data-driven、Physics-informed
- **常见数据集**：NASA、CALCE、Oxford
- **常见指标**：RMSE、MAE、MAPE

Agent 会在 `ingest` (入库阶段) 自动检测领域文献组成，如果满足阈值条件即会提示用户是否需要生成定制领域模板。
