from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from common import ROOT, load_config, write_json
from report_support import (
    TAG_FIELDS,
    ensure_output_path,
    load_canonical_records,
    load_source_records,
    read_recent_lines,
    today_stamp,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize current vault status.")
    parser.add_argument("--direction")
    return parser.parse_args()


def markdown_path(config: dict[str, Any], direction: str | None) -> Path:
    base = ROOT / config["paths"]["reports"] / "vault"
    date = today_stamp()
    name = f"status-{direction}-{date}.md" if direction else f"status-{date}.md"
    return base / name


def json_path(config: dict[str, Any]) -> Path:
    return ROOT / config["paths"]["manifests"] / "status_report.json"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    config = load_config()
    sources = load_source_records(config, direction=args.direction)
    canonicals = load_canonical_records(config, direction=args.direction)

    by_direction = Counter(str(record.get("direction") or "") for record in sources)
    by_journal = Counter(str(record.get("journal_abbr") or "") for record in sources)
    canonical_by_direction = Counter(str(record.get("direction") or "") for record in canonicals)
    tag_coverage = {}
    for field in TAG_FIELDS:
        tagged = sum(1 for record in canonicals if record.get(field))
        total = len(canonicals)
        tag_coverage[field] = {
            "tagged": tagged,
            "total": total,
            "pct": round(tagged * 100 / total, 1) if total else 0.0,
        }

    web_recent = read_recent_lines(ROOT / config["paths"]["logs"] / "web_search.md", limit=5)
    report_recent = read_recent_lines(ROOT / config["paths"]["logs"] / "report_generation.md", limit=5)
    registry = config.get("templates", {}).get("registry") or {}

    payload: dict[str, Any] = {
        "generated_at": today_stamp(),
        "direction_filter": args.direction,
        "source_count": len(sources),
        "canonical_count": len(canonicals),
        "canonical_coverage_pct": round(len(canonicals) * 100 / len(sources), 1) if sources else 0.0,
        "by_direction": dict(sorted(by_direction.items())),
        "canonical_by_direction": dict(sorted(canonical_by_direction.items())),
        "top_journals": dict(by_journal.most_common(10)),
        "tag_coverage": tag_coverage,
        "recent_activity": {
            "web_search": web_recent,
            "report_generation": report_recent,
        },
        "template_registry": {
            "count": len(registry),
            "domains": registry,
        },
    }

    lines = [
        "# Vault Status Report",
        "",
        f"> Generated: {today_stamp()}",
        "",
        "## Summary",
        "",
        f"- Source files: {len(sources)}",
        f"- Canonical pages: {len(canonicals)}",
        f"- Canonical coverage: {payload['canonical_coverage_pct']}%",
        "",
        "## Direction Distribution",
        "",
    ]
    if by_direction:
        for direction, count in by_direction.items():
            lines.append(f"- {direction}: {count} source / {canonical_by_direction.get(direction, 0)} canonical")
    else:
        lines.append("- None")
    lines.extend(["", "## Journal Distribution", ""])
    if by_journal:
        for journal, count in by_journal.most_common(10):
            lines.append(f"- {journal}: {count}")
    else:
        lines.append("- None")
    lines.extend(["", "## Tag Coverage", ""])
    for field, info in tag_coverage.items():
        lines.append(f"- {field}: {info['tagged']}/{info['total']} ({info['pct']}%)")
    lines.extend(["", "## Recent Activity", ""])
    lines.append("### Web Search")
    lines.append("")
    if web_recent:
        lines.extend(f"- {line}" for line in web_recent)
    else:
        lines.append("- None")
    lines.extend(["", "### Report Generation", ""])
    if report_recent:
        lines.extend(f"- {line}" for line in report_recent)
    else:
        lines.append("- None")
    lines.extend(["", "## Template Registry", ""])
    if registry:
        for domain, info in registry.items():
            lines.append(f"- {domain}: {info}")
    else:
        lines.append("- No domain templates registered.")
    lines.append("")

    md_path = markdown_path(config, args.direction)
    ensure_output_path(md_path)
    md_path.write_text("\n".join(lines), encoding="utf-8")
    write_json(json_path(config), payload)
    print(f"Wrote {md_path.relative_to(ROOT).as_posix()}")
    print(f"Wrote {json_path(config).relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
