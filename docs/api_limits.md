# 联网检索 API 限制说明 (Web Search API Limits)

[<- 返回主页](../README.md)

所有联网检索 API 都有严格的速率限制，违反限制可能导致 IP 被封禁。底层脚本在执行时会自动检测并提示限制状态。

## arXiv API

- **频率限制**：每 3 秒最多 1 次请求（严格执行）
- **并发限制**：仅允许单连接，禁止多线程并发
- **User-Agent**：建议在 header 中包含联系邮箱
- **封禁风险**：违反限制返回 403 Forbidden；持续违规可能导致永久被封禁
- **实现方式**：脚本自动使用底层封装发请求，并强制 3 秒延迟重试，**切勿强行绕过**。

## Semantic Scholar API

- **无 API Key**：限制极其严苛，每 5 分钟大约只能 100 次请求（约等于全站用户 3 秒/次共享资源池）
- **免费 API Key**：**每秒 1 次请求**（1 rps）—— **强烈推荐配置此选项**
- **合作伙伴计划**：通过 [官方申请](https://www.semanticscholar.org/product/api) 最高可达 100 rps
- **批量接口**：`/paper/batch` 单次最多处理 **500 个 Paper ID**（计为 1 次请求）
- **搜索限制**：普通搜索最多返回 **1,000 条结果**；超过需使用 `/search/bulk`
- **响应大小**：单个响应上限 **10 MB**
- **大数据集**：对于海量需求，请直接使用并解析 [S2AG 数据集](https://www.semanticscholar.org/product/api) 进行本地筛选

## OpenAlex API

- **API Key**：建议在 `config.json` 中配置 `openalex_api_key`；底层的检索 Python 脚本会作为 `api_key` 参数发送以保障调用稳定性
- **联系邮箱**：可选配置 `openalex_email`；脚本会作为 `mailto` 标记在请求头中表明身份（即所谓的 "Polite Pool"）
- **额度与速率**：以当前账户注册额度与 OpenAlex 返回的响应头限制为准。批量请求检索时脚本仍保留了 backoff 回避策略，请不要贴紧接口的上限运行
- **分页**：所有 API 请求均带有 `per-page` 来限制翻页返回数量

## 限制机制对比速查

| 数据来源 | 基础速率限制 | 并发请求支持 | 批量 ID 查询(Batch) | 认证推荐 |
|----------|------------|--------------|-------------------|----------|
| arXiv | 3 秒/请求 | 不支持 | 不支持 | 无需 |
| Semantic Scholar | 1 秒/请求 (基于配置Key) | 支持 | 支持（最多500 IDs）| 推荐 |
| OpenAlex | 账户额度配额制 | 支持 | 不支持 | 推荐配置 API key |

## 极简配置建议

1. 去申请并配置 `semantic_scholar_api_key`，获得稳定的 1 rps 爬取速率；
2. 配置您的 `openalex_api_key` 以及 `openalex_email`，以合法并稳定地获取其数据；
3. 本系统全部 Python 执行脚本自带访问冷却和重试回退机制——**请相信脚本设定的请求速率，不要随意移除延迟设置以求快**。
