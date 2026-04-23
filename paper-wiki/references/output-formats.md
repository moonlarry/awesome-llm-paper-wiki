# Output Formats Reference

Chinese user-facing workflow output examples. Use these examples when `config.json` sets
`output_lang` to `zh` or when the user asks for Chinese output.

## Table of Contents

- [Workflow 1: init](#workflow-1-init)
- [Workflow 2: scan-organize](#workflow-2-scan-organize)
- [Workflow 3: ingest](#workflow-3-ingest)
- [Workflow 4: tag](#workflow-4-tag)
- [Workflow 12: submission-recommend](#workflow-12-submission-recommend)
- [Workflow 13: revision-suggest](#workflow-13-revision-suggest)
- [Workflow 14: status](#workflow-14-status)
- [Workflow 15: lint](#workflow-15-lint)
- [Workflow 16: pipeline](#workflow-16-pipeline)
- [Workflow 17: paper-read](#workflow-17-paper-read)
- [Workflow 18: direction-review](#workflow-18-direction-review)

## Workflow 1: init

### Output (zh)

```text
文献库初始化完成！路径：E:\paper

已创建目录：{list}
已创建文件：{list}

接下来你可以：
- "扫描文献" — 扫描 paper/ 目录
- "整理期刊" — 按期刊缩写归类文件
- "入库" — 处理论文并生成 canonical 页
```

## Workflow 2: scan-organize

### Output (zh)

```text
扫描完成：{N} 个文件

按操作分类：
- 移动：{move_count}
- 跳过：{skip_count}
- 冲突：{conflict_count}
- 警告：{warn_count}

计划已保存：workspace/manifests/journal_move_plan.json
是否执行移动？(y/n)
```

## Workflow 3: ingest

### Output (zh)

```text
入库完成：处理了 {N} 篇论文

新增 canonical 页：
- {paper_id_1}
- {paper_id_2}

标签候选（需确认）：
- "transfer learning" → method [新标签]
- "CALCE" → dataset [已有标签]

确认添加新标签？(y/n)
```

## Workflow 4: tag

### Output (zh)

```text
批量打标完成：更新了 {N} 篇论文的标签

标签分布：
- task: SOH estimation (45), RUL prediction (38), SOC estimation (12), ...
- method: LSTM (28), Transformer (22), GPR (15), PINN (12), ...
- dataset: NASA (35), CALCE (30), Oxford (18), ...

新增标签：{list}
```

## Workflow 12: submission-recommend

### Output (zh)

```text
投稿推荐报告

论文：{title}

推荐期刊 Top 5：
1. {journal_1}（{score_1}/100）— {reason}
2. {journal_2}（{score_2}/100）— {reason}
3. {journal_3}（{score_3}/100）— {reason}
4. {journal_4}（{score_4}/100）— {reason}
5. {journal_5}（{score_5}/100）— {reason}

报告已保存：library/reports/submission/{paper_slug}-recommend-{date}.md
```

## Workflow 13: revision-suggest

### Output (zh)

```text
面向 {journal} 的修改建议

评估维度：
- 排版：{score}/5 — {summary}
- 方法写作：{score}/5 — {summary}
- 研究方法：{score}/5 — {summary}
- 引言适配：{score}/5 — {summary}
- 参考文献：{score}/5 — {summary}

关键修改建议（共 {N} 条）：
1. [关键] {suggestion_1}
2. [关键] {suggestion_2}
3. [重要] {suggestion_3}
...

报告已保存：library/reports/submission/{paper_slug}-revision-for-{journal}-{date}.md
```

## Workflow 14: status

### Output (zh)

```text
文献库状态

论文总数：{total}
按方向：
- Battery: {count}
- TimeSeries: {count}

按期刊（前 5）：
- Energy: {count}
- JES: {count}
- RESS: {count}
- AppliedEnergy: {count}
- JPS: {count}

Canonical 页：{canonical_count} / {total}（{pct}% 已入库）
标签覆盖率：{tagged_count} / {canonical_count}（{pct}%）

领域模板：
- battery: ✅ 已生成（{date}，{paper_count} 篇时生成）
- timeseries: ❌ 未生成

最近操作：
{last_5_log_entries}
```

## Workflow 15: lint

### Output (zh)

```text
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

## Workflow 16: pipeline

### Output (zh)

```text
完整流程执行完成

1. ✅ 初始化
2. ✅ 扫描：{N} 个文件
3. ✅ 入库：{N} 篇新增
4. ✅ 打标：{N} 篇更新
5. ✅ 索引重建
6. 当前状态：{summary}
```

## Workflow 17: paper-read

### Output (zh)

```text
单篇文献精读：{title}

1. 这篇文章解决了什么问题？
{answer}

2. 这个问题为什么重要？
{answer}

3. 本文使用了什么方法或模型？
{answer}

4. 为什么这个方法或模型能解决这个问题？
{answer}

5. 核心结论是什么？
{answer}

6. 下一步可以怎么做？
{answer}

阅读笔记已保存：library/reports/paper/{date}-{paper_id}-reading.md
```

## Workflow 18: direction-review

### Output (zh)

```text
方向综述准备完成

方向：{direction}
聚焦主题：{focus_or_none}

本地可读论文：{local_readable}
本地跳过论文：{local_skipped}
网络补充记录：{web_count}

Bundle：workspace/cache/fulltext-review/{run_key}.json
Manifest：workspace/manifests/direction_review_prepare.json
最终综述目标：library/reports/review/{direction-or-focus}-review-{date}.md
```
