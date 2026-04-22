# 底层架构与脚本说明 (Architecture & Scripts)

[<- 返回主页](../README.md)

本系统的核心任务逻辑分离调度。打标签、报告生成、智能评分等复杂的语义和推理运算由 **LLM Agent 系统智能体** (`SKILL.md`) 直接驱动。

而涉及到文件读写、纯数据运算（I/O 获取），系统内置了一组零依赖 Python 脚本与辅助模块。用户通常不需要手动干预与执行脚本，智能体会根据任务上下文自动为你调用。

## 内置 Python 脚本列表

| 脚本文件 | 作用说明 |
|------|------|
| `scan_sources.py` | 扫描根目录的 `paper/` 并自动生成 source manifest 记录追踪 |
| `organize_by_journal.py` | 按解析出的期刊缩写整理文献文件夹，支持安全 `dry-run` 预览 |
| `rebuild_indexes.py` | 自动重建所有文献索引，并重写更新前端展示数据板（`paper-library.md`） |
| `html_table_to_md.py` | 提取转化 Markdown 文件内嵌的纯 HTML 复杂表格至标准 Markdown 数据表格式 |
| `resolve_journal.py` | 用于验证与解决单文件期刊字段解析的内部映射测试 |
| `ingest_batch.py` | 批量生成标准入库 `canonical` 知识页面，可附带执行 `keyword rules` 进行快速初筛打标 |
| `scan_tags.py` | 遍历扫描并统计已有的 `canonical` 页面的标签覆盖率及命中词频率报告 |
| `export_summaries.py` | 导出论文集数据的题名、元数据、预处理摘要及所绑定关键词信息，供用户外部检查与筛选 |
| `detect_duplicates.py` | 检查同一方向或全库中的重复论文文件，并输出保留建议 |
| `report_family.py` | 统一生成 `journal / direction / stat` 三类确定性报告 |
| `status_report.py` | 汇总当前 vault 的 source / canonical / tag coverage / recent activity 状态 |
| `lint_vault.py` | 对 vault 做非破坏性健康检查，输出缺失页、孤儿页、标签异常等问题 |
| `web_search.py` | 执行联网学术检索并实时构建 Markdown 文档化。arXiv 提取出 Full-Text 会进入正式文库层，OpenAlex/Semantic Scholar 仅存研究调研层。 |
| `arxiv_fulltext.py` | 专注负责 arXiv 不同类型底层文件（如 `HTML / TeX / PDF / API fallback `）向 Full-Text 抓取并组装 |
| `web_import_clipper.py` | 支持导入 Obsidian Web Clipper 外部手动捕捉剪藏的纯 Markdown 资源归入完整知识库管线 |
| `common.py` | 提供共享的 frontmatter、canonical、direction 校验与日志工具函数 |
| `report_support.py` | 提供报告族共用的加载、过滤、排序与引用辅助逻辑 |

## 框架工作原理解析

### **关于全文本地化生成**

1. 联网检索机制本身**不强制**主动生成渲染复杂的 HTML 框架页面；
2. **arXiv 拦截规则**：该模块会优先读取并提取 arXiv 基于作者提供的 HTML 文本或 TeX 原始文稿进行编译。抓取完整全文后自动将其进入 `paper/{direction}/arxiv/` 序列并生成带标签内容的 canonical 结构化界面。若是纯 PDF/兜底获取的残缺文本记录（未完整提炼），会一直滞留存放于研究资料层 (`paper/web_search/{direction}/arxiv/`) 防止污染主干库文档。
3. **OpenAlex / Semantic Scholar 服务**：这两个平台主要存储**元数据(Metadata)**、摘要 (Abstract)、全球统一识别符 DOI 与直达 URL，自动入库至 `paper/web_search/{direction}/openalex`。随后可以被唤醒输出 web-find 调查报告。
4. **外部全网抓取辅助**：建议利用 `Obsidian Web Clipper` 在出版商官方通过合法获取通道剪藏学术长文全文为 Markdown 格式，然后转移到正式文献库，以解决各种刁钻的学术网关拦截。
5. **方向校验策略**：`web-find` / `web-digest` 现在采用 fail-fast 校验。若 `paper/{direction}/` 不存在，脚本会直接报错并提示先初始化或手动创建方向目录，而不是自动建库。

### 批量处理协同
大批量文件的高承载运行任务，如多线程导入读取、全局扫描打标处理、海量数据字典导出统计分别对应以上表中的 `ingest_batch.py`、`scan_tags.py` 与 `export_summaries.py`，全部提供多维度 CLI 指令供高级开发者配置排期运行。

此外，`detect_duplicates.py`、`report_family.py`、`status_report.py` 与 `lint_vault.py` 已作为正式 CLI 提供给用户或上层 Agent 调度使用。
