from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from common import (
    ROOT,
    direction_paths,
    ensure_dir,
    extract_heading_section,
    extract_year,
    load_config,
    parse_frontmatter,
    rel,
    resolve_journal,
)


def frontmatter_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip() and value.strip() != "[]":
        return [part.strip() for part in re.split(r";|, and | and ", value) if part.strip()]
    return []


def extract_keywords(text: str, fm: dict[str, Any]) -> str:
    for key in ("keywords", "keyword"):
        value = fm.get(key)
        if isinstance(value, list):
            return "; ".join(str(item) for item in value)
        if isinstance(value, str) and value.strip():
            return value.strip()
    section = extract_heading_section(text, "Keywords")
    if section:
        return re.sub(r"\s+", " ", section).strip()
    match = re.search(r"(?im)^keywords?\s*:?\s*(.+)$", text)
    return match.group(1).strip() if match else ""


def year_value(fm: dict[str, Any], text: str = "") -> int | None:
    raw = fm.get("published_year") or fm.get("year")
    raw_text = str(raw or "").strip()
    if re.fullmatch(r"\d{4}", raw_text):
        return int(raw_text)
    return extract_year(text)


def source_records(config: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for direction_path in direction_paths(config):
        if args.direction and direction_path.name != args.direction:
            continue
        for path in sorted(direction_path.rglob("*.md")):
            if "web_search" in path.parts:
                continue
            journal = resolve_journal(path, config)
            if args.journal and journal["journal_abbr"] != args.journal and journal["published_raw"] != args.journal:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            fm = parse_frontmatter(text)
            year = year_value(fm, text)
            if args.year_from and (year is None or year < args.year_from):
                continue
            if args.year_to and (year is None or year > args.year_to):
                continue
            records.append(
                {
                    "title": str(fm.get("title") or journal["title"] or path.stem),
                    "authors": frontmatter_list(fm.get("authors") or fm.get("author")),
                    "published_year": year,
                    "journal": str(fm.get("published") or journal["journal"] or ""),
                    "journal_abbr": journal["journal_abbr"],
                    "doi": str(fm.get("doi") or ""),
                    "source": str(fm.get("source") or ""),
                    "abstract": extract_heading_section(text, "Abstract"),
                    "keywords": extract_keywords(text, fm),
                    "source_path": rel(path),
                    "canonical_path": "",
                }
            )
    return records


def canonical_records(config: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    root = ROOT / config["paths"]["papers"]
    if args.direction:
        root = root / args.direction
    if not root.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        journal_abbr = str(fm.get("journal_abbr") or "")
        journal = str(fm.get("journal") or "")
        if args.journal and journal_abbr != args.journal and journal != args.journal:
            continue
        year = year_value(fm, text)
        if args.year_from and (year is None or year < args.year_from):
            continue
        if args.year_to and (year is None or year > args.year_to):
            continue
        records.append(
            {
                "title": str(fm.get("title") or path.stem),
                "authors": frontmatter_list(fm.get("authors") or fm.get("author")),
                "published_year": year,
                "journal": journal,
                "journal_abbr": journal_abbr,
                "doi": str(fm.get("doi") or ""),
                "source": str(fm.get("url") or ""),
                "abstract": extract_heading_section(text, "Abstract"),
                "keywords": extract_keywords(text, fm),
                "source_path": str(fm.get("source_path") or ""),
                "canonical_path": rel(path),
            }
        )
    return records


def render_markdown(records: list[dict[str, Any]]) -> str:
    lines = ["# Exported Paper Summaries", "", f"- Count: {len(records)}", ""]
    for item in records:
        lines.extend(
            [
                f"## {item['title']}",
                "",
                f"- Year: {item['published_year'] or ''}",
                f"- Journal: {item['journal'] or item['journal_abbr']}",
                f"- DOI: {item['doi'] or ''}",
                f"- Source: {item['source'] or item['source_path']}",
                f"- Keywords: {item['keywords']}",
                "",
                item["abstract"] or "No abstract.",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Export paper titles, metadata, abstracts, and keywords for review.")
    parser.add_argument("--direction")
    parser.add_argument("--journal")
    parser.add_argument("--year-from", type=int)
    parser.add_argument("--year-to", type=int)
    parser.add_argument("--source", choices=["canonical", "source"], default="source")
    parser.add_argument("--format", choices=["json", "md"], default="json")
    parser.add_argument("--out")
    args = parser.parse_args()
    config = load_config()
    records = canonical_records(config, args) if args.source == "canonical" else source_records(config, args)
    output = json.dumps(records, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown(records)
    if args.out:
        out_path = ROOT / args.out
        ensure_dir(out_path.parent)
        out_path.write_text(output, encoding="utf-8")
        print(f"Exported {len(records)} papers to {rel(out_path)}")
    else:
        print(output)


if __name__ == "__main__":
    main()
