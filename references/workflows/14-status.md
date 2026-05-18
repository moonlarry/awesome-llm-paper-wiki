# Workflow 14: status

> Part of paper-wiki skill. Loaded on-demand by the Agent when this workflow is triggered.
> See SKILL.md for the routing table and precondition matrix.

## Workflow 14: status

### Purpose
Display vault status summary.

### Formal CLI
```bash
python scripts/status_report.py
python scripts/status_report.py --direction Battery
```

### Steps

1. Load source records from `library/indexes/papers.json`
2. Load canonical records from `library/indexes/canonical_pages.json`
3. Summarize:
   - source / canonical counts
   - direction and journal distribution
   - tag coverage across `tags_*`
   - recent web/report activity from `workspace/logs/`
   - template registry state from `config.json`
4. Save:
   - `library/reports/vault/status-{date}.md`
   - `workspace/manifests/status_report.json`

### Output (zh)
```
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

