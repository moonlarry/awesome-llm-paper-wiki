# Paper Frontmatter Schema

This document defines the required and optional frontmatter fields for canonical literature pages in `library/papers/`.

## Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique paper ID: `{direction}-{year}-{journal_abbr}-{slug}` | `exampledirection-2025-journal-bayesian-pinn` |
| `title` | string | Full paper title | `"Bayesian calibrated PINNs for task estimation"` |
| `direction` | string | Research direction (matches `paper/` subdirectory) | `ExampleDirection` |
| `source_path` | string | Relative path to the original paper Markdown | `paper/ExampleDirection/JOURNAL/paper.md` |

## Recommended Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `journal` | string | Full journal name | `"Reliability Engineering & System Safety"` |
| `journal_abbr` | string | Journal abbreviation (directory name) | `RESS` |
| `published_date` | string | Publication date (YYYY-MM-DD, YYYY-MM, or YYYY) | `2025-12` |
| `published_year` | integer | Publication year | `2025` |
| `doi` | string | Digital Object Identifier | `10.1016/j.ress.2025.111432` |
| `url` | string | Paper URL | `https://...` |

## Tag Fields

All tag fields are arrays of strings. Tags should match entries in `schema/tag_taxonomy.json`.

| Field | Type | Description |
|-------|------|-------------|
| `tags_task` | string[] | Research tasks (e.g., task estimation, task prediction) |
| `tags_method` | string[] | Methods or models (e.g., PINN, Transformer) |
| `tags_dataset` | string[] | Datasets (e.g., DatasetA, DatasetB) |
| `tags_domain` | string[] | Research domains (e.g., domain-specific monitoring) |
| `tags_signal` | string[] | Input signals (e.g., voltage, current) |
| `tags_application` | string[] | Applications (e.g., industrial analytics, forecasting) |
| `tags_metric` | string[] | Metrics (e.g., RMSE, MAE) |
| `tags_custom` | string[] | User-defined tags |

## Status Fields

| Field | Type | Values | Default |
|-------|------|--------|---------|
| `status` | string | `unread`, `skimmed`, `read`, `cited` | `unread` |
| `reading_priority` | string | `high`, `medium`, `low` | `medium` |
| `updated_at` | string | ISO 8601 timestamp | `null` |

## Field Precedence Rules

- `title`: frontmatter `title` > filename (without extension)
- `journal_abbr`: follows resolution priority in `scripts/common.py` → `resolve_journal()`
- `published_date`: frontmatter published/date field > body text date extraction > `null`
- Tags: user-set tags are never overwritten by automated tagging
