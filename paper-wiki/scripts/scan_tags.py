from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from common import ROOT, ensure_dir, load_config, load_keyword_rules, parse_frontmatter, read_frontmatter_list, rel


DEFAULT_DIMENSIONS = ["task", "method", "dataset", "domain", "signal", "application", "metric", "custom"]


def canonical_paths(config: dict[str, Any], direction: str | None) -> list[Path]:
    root = ROOT / config["paths"]["papers"]
    if direction:
        root = root / direction
    if not root.exists():
        return []
    return sorted(root.rglob("*.md"))


def taxonomy_dimensions(config: dict[str, Any]) -> list[str]:
    path = ROOT / config.get("tagging", {}).get("taxonomy_path", "schema/tag_taxonomy.json")
    if not path.exists():
        return DEFAULT_DIMENSIONS
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return DEFAULT_DIMENSIONS
    tags = raw.get("tags", {})
    if isinstance(tags, dict) and tags:
        return [key for key in tags.keys() if key != "journal"]
    return DEFAULT_DIMENSIONS


def scan(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    dimensions = [args.dimension] if args.dimension else taxonomy_dimensions(config)
    tag_counts = {dimension: Counter() for dimension in dimensions}
    empty_counts = {dimension: 0 for dimension in dimensions}
    pages = canonical_paths(config, args.direction)
    rules = load_keyword_rules(config) if args.rules else []
    rule_counts = Counter()
    empty_pages: dict[str, list[str]] = {dimension: [] for dimension in dimensions}
    for path in pages:
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        for dimension in dimensions:
            values = read_frontmatter_list(fm, f"tags_{dimension}")
            if values:
                tag_counts[dimension].update(values)
            else:
                empty_counts[dimension] += 1
                if args.include_empty:
                    empty_pages[dimension].append(rel(path))
        if args.rules:
            for index, rule in enumerate(rules):
                pattern = str(rule.get("pattern") or "").strip()
                if not pattern:
                    continue
                try:
                    if re.search(pattern, text, re.I):
                        rule_counts[str(index)] += 1
                except re.error:
                    continue
    return {
        "direction": args.direction or "all",
        "paper_count": len(pages),
        "dimensions": {
            dimension: {
                "tags": dict(tag_counts[dimension].most_common()),
                "empty_count": empty_counts[dimension],
                "empty_pages": empty_pages[dimension] if args.include_empty else [],
            }
            for dimension in dimensions
        },
        "rule_hits": [
            {
                "index": int(index),
                "tag": rules[int(index)].get("tag"),
                "dimension": rules[int(index)].get("dimension"),
                "pattern": rules[int(index)].get("pattern"),
                "count": count,
            }
            for index, count in rule_counts.most_common()
        ],
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [f"# Tag Scan - {result['direction']}", "", f"- Papers: {result['paper_count']}", ""]
    for dimension, payload in result["dimensions"].items():
        lines.extend([f"## tags_{dimension}", "", f"- Empty pages: {payload['empty_count']}", ""])
        tags = payload["tags"]
        if tags:
            for tag, count in tags.items():
                lines.append(f"- {tag}: {count}")
        else:
            lines.append("- No tags found.")
        if payload["empty_pages"]:
            lines.extend(["", "### Empty Pages", ""])
            for page in payload["empty_pages"]:
                lines.append(f"- `{page}`")
        lines.append("")
    if result["rule_hits"]:
        lines.extend(["## Keyword Rule Hits", ""])
        for item in result["rule_hits"]:
            lines.append(f"- [{item['index']}] {item['dimension']} / {item['tag']}: {item['count']} matches")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan canonical paper tag coverage and optional keyword-rule hits.")
    parser.add_argument("--direction")
    parser.add_argument("--dimension", choices=DEFAULT_DIMENSIONS)
    parser.add_argument("--rules", action="store_true")
    parser.add_argument("--include-empty", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args()
    config = load_config()
    result = scan(config, args)
    output = json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_markdown(result)
    if args.out:
        out_path = ROOT / args.out
        ensure_dir(out_path.parent)
        out_path.write_text(output, encoding="utf-8")
        print(f"Wrote {rel(out_path)}")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
