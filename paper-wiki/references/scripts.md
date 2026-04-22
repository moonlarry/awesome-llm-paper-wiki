# Scripts Reference

Scripts are in `scripts/` and use Python standard library only.

| Script | Purpose | Usage |
|--------|---------|-------|
| `scan_sources.py` | Scan paper sources | `python scripts/scan_sources.py` |
| `organize_by_journal.py` | Journal-based file organization | `python scripts/organize_by_journal.py --all --dry-run` |
| `rebuild_indexes.py` | Rebuild indexes and journal aggregate indexes | `python scripts/rebuild_indexes.py` |
| `html_table_to_md.py` | Convert HTML tables | `python scripts/html_table_to_md.py <file>` |
| `resolve_journal.py` | Inspect journal resolution for one source file | `python scripts/resolve_journal.py paper/ExampleDirection/PUB/example.md` |
| `ingest_batch.py` | Batch-generate canonical pages and apply keyword-rule tags | `python scripts/ingest_batch.py --direction ExampleDirection --apply-tags` |
| `scan_tags.py` | Scan canonical tag coverage and keyword-rule hits | `python scripts/scan_tags.py --direction ExampleDirection --rules` |
| `export_summaries.py` | Export titles, metadata, abstracts, and keywords | `python scripts/export_summaries.py --direction ExampleDirection --format json` |
| `detect_duplicates.py` | Detect duplicate paper files | `python scripts/detect_duplicates.py --all` |
| `report_family.py` | Generate deterministic reports from canonical pages | `python scripts/report_family.py --mode journal --journal JOURNAL` |
| `status_report.py` | Summarize current vault status | `python scripts/status_report.py --direction ExampleDirection` |
| `lint_vault.py` | Run non-destructive vault health checks | `python scripts/lint_vault.py --direction ExampleDirection` |
| `web_search.py` | Search OpenAlex/Semantic Scholar/arXiv | `python scripts/web_search.py find --direction ExampleDirection --query "topic"` |
| `arxiv_fulltext.py` | Fetch arXiv HTML/TEX/PDF/API full text | Imported by `web_search.py` |
| `web_import_clipper.py` | Import Obsidian Web Clipper Markdown | `python scripts/web_import_clipper.py --direction ExampleDirection` |
| `common.py` | Shared utilities | Imported by other scripts |
| `report_support.py` | Shared report helpers | Imported by `report_family.py`, `status_report.py`, `lint_vault.py` |

All scripts use the vault root as project root (auto-detected from script location via `Path(__file__).resolve().parents[1]`).