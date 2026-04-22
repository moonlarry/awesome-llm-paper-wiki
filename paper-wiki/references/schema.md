# Schema Reference

## tag_taxonomy.json

Defines tag dimensions and known tags.

```json
{
  "dimensions": {
    "task": { "label": "Task", "abbr_map": {} },
    "method": { "label": "Method", "abbr_map": {} },
    "dataset": { "label": "Dataset", "abbr_map": {} },
    "domain": { "label": "Domain", "abbr_map": {} },
    "signal": { "label": "Signal", "abbr_map": {} },
    "application": { "label": "Application", "abbr_map": {} },
    "metric": { "label": "Metric", "abbr_map": {} }
  },
  "tags": {
    "task": ["TaskA estimation", ...],
    "method": ["LSTM", ...],
    "dataset": ["DatasetA", ...]
  }
}
```

---

## keyword_rules.json

Maps text patterns to tags.

```json
{
  "rules": [
    { "pattern": "state of health|TaskA", "tag": "TaskA estimation", "dimension": "task" },
    { "pattern": "neural network|deep learning", "tag": "Neural Network", "dimension": "method" }
  ]
}
```

---

## journal_aliases.json

Maps journal full names to abbreviations.

Example entries:
- `"Reliability Engineering & System Safety"` → `"RESS"`
- `"Journal of Power Sources"` → `"JPS"`
- `"Energy"` → `"Energy"`

---

## paper_frontmatter.schema.md

Documents required and optional frontmatter fields for canonical pages.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Paper identifier: `{direction}-{year}-{journal_abbr}-{slug}` |
| `title` | string | Paper title |
| `direction` | string | Research direction folder name |
| `source_path` | string | Path to source Markdown |
| `journal_abbr` | string | Journal abbreviation |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `journal` | string | Journal full name |
| `published_date` | string | Publication date |
| `published_year` | int | Publication year |
| `doi` | string | DOI |
| `url` | string | URL |
| `tags_*` | list | Tag arrays for each dimension |
| `status` | string | Reading status |
| `reading_priority` | string | Priority level |

---

## Canonical Page Format

Canonical pages in `library/papers/{direction}/{paper_id}.md` serve as index anchors.

```yaml
---
id: example-2025-journal-keyword-method
title: "Paper title"
direction: ExampleDirection
source_path: "paper/ExampleDirection/JOURNAL/paper.md"
source_checksum: sha256...

journal: "Reliability Engineering & System Safety"
journal_abbr: "JOURNAL"
published_date: "2025-12"
published_year: 2025
doi: "10.1016/..."
url: "https://..."

tags_task: []
tags_method: []
tags_dataset: []
tags_domain: []
tags_signal: []
tags_application: []
tags_metric: []
tags_custom: []

status: "unread"
reading_priority: "medium"
updated_at: timestamp
---

# Title

## Source

## Abstract

## Keywords

## User Notes
<!-- User-maintained section. Scripts must never overwrite this. -->
```

Canonical pages contain metadata, tags, abstract, and user notes — not full text. Use `source_path` to access original Markdown in `paper/`.