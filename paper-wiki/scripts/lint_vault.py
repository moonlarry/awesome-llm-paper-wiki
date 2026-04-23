from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from common import ROOT, load_config, parse_frontmatter, validate_journal_aliases, write_json
from detect_duplicates import collect_source_files, detect_exact_duplicates, detect_probable_duplicates
from report_support import (
    REQUIRED_CANONICAL_FIELDS,
    TAG_FIELDS,
    canonical_index_path,
    ensure_output_path,
    load_canonical_records,
    load_source_records,
    source_index_path,
    today_stamp,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run non-destructive health checks on the vault.")
    parser.add_argument("--direction")
    return parser.parse_args()


def markdown_path(config: dict[str, Any], direction: str | None) -> Path:
    base = ROOT / config["paths"]["reports"] / "vault"
    date = today_stamp()
    name = f"lint-{direction}-{date}.md" if direction else f"lint-{date}.md"
    return base / name


def json_path(config: dict[str, Any]) -> Path:
    return ROOT / config["paths"]["manifests"] / "lint_vault.json"


def load_taxonomy(config: dict[str, Any]) -> dict[str, set[str]]:
    path = ROOT / config["tagging"]["taxonomy_path"]
    if not path.exists():
        return {}
    data = __import__("json").loads(path.read_text(encoding="utf-8"))
    dimensions = data.get("dimensions") or {}
    allowed: dict[str, set[str]] = {}
    for dimension, info in dimensions.items():
        abbr_map = info.get("abbr_map") or {}
        values = set(str(key) for key in abbr_map.keys())
        values.update(str(value) for value in abbr_map.values())
        allowed[f"tags_{dimension}"] = values
    return allowed


def stale_index_records(index_path: Path, files: list[Path]) -> dict[str, Any] | None:
    if not index_path.exists():
        return {"path": index_path.as_posix(), "reason": "missing"}
    if not files:
        return None
    newest = max(path.stat().st_mtime for path in files if path.exists())
    if index_path.stat().st_mtime + 1 < newest:
        return {"path": index_path.as_posix(), "reason": "older_than_latest_file"}
    return None


def canonical_frontmatter_issues(config: dict[str, Any], direction: str | None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    root = ROOT / config["paths"]["papers"]
    if direction:
        root = root / direction
    if not root.exists():
        return issues
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        missing = [field for field in REQUIRED_CANONICAL_FIELDS if not str(fm.get(field) or "").strip()]
        if missing:
            issues.append({"path": path.relative_to(ROOT).as_posix(), "missing_fields": missing})
    return issues


def template_registry_issues(config: dict[str, Any], canonical_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    registry = config.get("templates", {}).get("registry") or {}
    threshold = float(config.get("templates", {}).get("regeneration_threshold", 0.2))
    domain_counts = Counter()
    for record in canonical_records:
        for domain in record.get("tags_domain") or []:
            domain_counts[domain] += 1
    for domain, info in registry.items():
        count_at_generation = int(info.get("count_at_generation") or 0)
        current = domain_counts.get(domain, 0)
        if count_at_generation and current > count_at_generation:
            growth = (current - count_at_generation) / count_at_generation
            if growth >= threshold:
                issues.append(
                    {
                        "domain": domain,
                        "reason": "stale",
                        "count_at_generation": count_at_generation,
                        "current_count": current,
                    }
                )
    return issues


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    config = load_config()
    sources = load_source_records(config, direction=args.direction)
    canonicals = load_canonical_records(config, direction=args.direction)

    source_paths = {str(record.get("path") or "") for record in sources}
    canonical_source_paths = {str(record.get("source_path") or "") for record in canonicals if record.get("source_path")}
    orphan_canonical = []
    broken_source_path = []
    for record in canonicals:
        source_path = str(record.get("source_path") or "")
        path = str(record.get("path") or "")
        if not source_path:
            broken_source_path.append({"path": path, "reason": "missing_source_path"})
            orphan_canonical.append({"path": path, "source_path": source_path})
            continue
        source_file = ROOT / source_path
        if not source_file.exists():
            broken_source_path.append({"path": path, "source_path": source_path, "reason": "source_missing"})
            orphan_canonical.append({"path": path, "source_path": source_path})
    missing_canonical = sorted(source_paths - canonical_source_paths)

    duplicate_records = collect_source_files(args.direction, config)
    exact_duplicates = detect_exact_duplicates(duplicate_records)
    probable_duplicates = detect_probable_duplicates(duplicate_records)

    allowed = load_taxonomy(config)
    taxonomy_issues = []
    for record in canonicals:
        for field in TAG_FIELDS:
            valid = allowed.get(field)
            if not valid:
                continue
            unknown = [value for value in record.get(field) or [] if str(value) not in valid]
            if unknown:
                taxonomy_issues.append(
                    {
                        "path": str(record.get("path") or ""),
                        "field": field,
                        "unknown_values": unknown,
                    }
                )

    canonical_files = list((ROOT / config["paths"]["papers"]).rglob("*.md"))
    if args.direction:
        canonical_files = list((ROOT / config["paths"]["papers"] / args.direction).rglob("*.md"))
    source_files = []
    paper_root = ROOT / config["paper_root"]
    if args.direction:
        source_files = list((paper_root / args.direction).rglob("*.md"))
    else:
        for direction in config.get("directions") or []:
            source_files.extend((paper_root / direction).rglob("*.md"))
    stale_indexes = []
    for issue in (
        stale_index_records(source_index_path(config), source_files),
        stale_index_records(canonical_index_path(config), canonical_files),
    ):
        if issue:
            stale_indexes.append(issue)

    frontmatter_issues = canonical_frontmatter_issues(config, args.direction)
    template_issues = template_registry_issues(config, canonicals)
    journal_alias_issues = validate_journal_aliases(config)

    findings = {
        "journal_alias_issues": journal_alias_issues,
        "orphan_canonical": orphan_canonical,
        "missing_canonical": missing_canonical,
        "duplicate_exact": exact_duplicates,
        "duplicate_probable": probable_duplicates,
        "taxonomy_inconsistency": taxonomy_issues,
        "stale_indexes": stale_indexes,
        "missing_required_frontmatter": frontmatter_issues,
        "broken_source_path": broken_source_path,
        "template_registry_staleness": template_issues,
    }

    summary = {
        "error": len(journal_alias_issues) + len(orphan_canonical) + len(broken_source_path) + len(frontmatter_issues),
        "warning": len(missing_canonical) + len(exact_duplicates) + len(probable_duplicates) + len(taxonomy_issues) + len(stale_indexes) + len(template_issues),
        "info": 1,
    }

    payload = {
        "generated_at": today_stamp(),
        "direction_filter": args.direction,
        "summary": summary,
        "findings": findings,
    }

    lines = [
        "# Vault Lint Report",
        "",
        f"> Generated: {today_stamp()}",
        "",
        "## Summary",
        "",
        f"- Error: {summary['error']}",
        f"- Warning: {summary['warning']}",
        f"- Info: {summary['info']}",
        "",
        "## Recommended Actions",
        "",
        "1. Run `python scripts/ingest_batch.py ...` for missing canonical pages.",
        "2. Run `python scripts/rebuild_indexes.py` if indexes are stale.",
        "3. Review duplicate and taxonomy warnings manually before any cleanup.",
        "",
    ]

    section_order = [
        ("Journal Alias Issues", journal_alias_issues, "error"),
        ("Orphan Canonical", orphan_canonical, "error"),
        ("Missing Canonical", missing_canonical, "warning"),
        ("Exact Duplicates", exact_duplicates, "warning"),
        ("Probable Duplicates", probable_duplicates, "warning"),
        ("Taxonomy Inconsistency", taxonomy_issues, "warning"),
        ("Stale Indexes", stale_indexes, "warning"),
        ("Missing Required Frontmatter", frontmatter_issues, "error"),
        ("Broken source_path", broken_source_path, "error"),
        ("Template Registry Staleness", template_issues, "warning"),
    ]
    for title, items, severity in section_order:
        lines.extend([f"## {title}", "", f"- Severity: {severity}", ""])
        if not items:
            lines.append("- None")
            lines.append("")
            continue
        for item in items[:20]:
            lines.append(f"- {item}")
        if len(items) > 20:
            lines.append(f"- ... {len(items) - 20} more")
        lines.append("")

    md_path = markdown_path(config, args.direction)
    ensure_output_path(md_path)
    md_path.write_text("\n".join(lines), encoding="utf-8")
    write_json(json_path(config), payload)
    print(f"Wrote {md_path.relative_to(ROOT).as_posix()}")
    print(f"Wrote {json_path(config).relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
