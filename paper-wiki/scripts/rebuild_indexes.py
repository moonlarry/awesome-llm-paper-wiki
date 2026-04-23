from __future__ import annotations

import sys
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import (
    ROOT,
    direction_paths,
    ensure_dir,
    extract_heading_section,
    extract_keywords,
    load_config,
    parse_frontmatter,
    read_frontmatter_list,
    rel,
    resolve_journal,
    write_json,
)


def normalized_year(fm: dict) -> str:
    for key in ("published_year", "year", "published_date"):
        value = str(fm.get(key) or "").strip()
        match = re.search(r"\b(19|20)\d{2}\b", value)
        if match:
            return match.group(0)
    return "n.d."


def collect_records(config: dict) -> list[dict]:
    records: list[dict] = []
    for direction_path in direction_paths(config):
        for md_path in sorted(direction_path.rglob("*.md")):
            records.append(resolve_journal(md_path, config))
    return records


def collect_canonical_pages(config: dict) -> list[dict]:
    pages: list[dict] = []
    papers_root = ROOT / config["paths"]["papers"]
    if not papers_root.exists():
        return pages
    for md_path in sorted(papers_root.rglob("*.md")):
        text = md_path.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        if not fm:
            continue
        keywords = extract_keywords(text)
        direction = str(fm.get("direction") or md_path.parent.name)
        pages.append({
            "path": rel(md_path),
            "id": str(fm.get("id") or md_path.stem),
            "title": str(fm.get("title") or md_path.stem),
            "direction": direction,
            "journal": str(fm.get("journal") or "Unknown"),
            "journal_abbr": str(fm.get("journal_abbr") or "Unknown"),
            "published_date": str(fm.get("published_date") or ""),
            "year": normalized_year(fm),
            "doi": str(fm.get("doi") or ""),
            "url": str(fm.get("url") or ""),
            "source_path": str(fm.get("source_path") or ""),
            "abstract": extract_heading_section(text, "Abstract"),
            "keywords": keywords,
            "tags_task": read_frontmatter_list(fm, "tags_task"),
            "tags_method": read_frontmatter_list(fm, "tags_method"),
            "tags_dataset": read_frontmatter_list(fm, "tags_dataset"),
            "tags_domain": read_frontmatter_list(fm, "tags_domain"),
            "tags_signal": read_frontmatter_list(fm, "tags_signal"),
            "tags_application": read_frontmatter_list(fm, "tags_application"),
            "tags_metric": read_frontmatter_list(fm, "tags_metric"),
            "tags_custom": read_frontmatter_list(fm, "tags_custom"),
            "status": str(fm.get("status") or "unread"),
            "reading_priority": str(fm.get("reading_priority") or "medium"),
            "updated_at": str(fm.get("updated_at") or ""),
        })
    return pages


def write_journal_aggregate_index(journal_abbr: str, pages: list[dict], config: dict) -> None:
    """Write aggregate index for one journal with frontmatter + abstract + tag groupings."""
    journals_dir = ROOT / config["paths"]["indexes"] / "journals"
    ensure_dir(journals_dir)
    index_path = journals_dir / f"{journal_abbr}.md"

    journal_name = pages[0]["journal"] if pages else journal_abbr
    tag_dimensions = ["task", "method", "dataset", "domain", "signal", "application", "metric"]

    lines = [
        f"# Journal Index: {journal_abbr}",
        "",
        f"- **Journal**: {journal_name}",
        f"- **Abbr**: {journal_abbr}",
        f"- **Papers**: {len(pages)}",
        f"- **Last updated**: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Papers Table",
        "",
        "| ID | Title | Year | Tags | DOI |",
        "|----|-------|------|------|-----|",
    ]

    def year_sort_key(p: dict) -> tuple:
        year = str(p.get("year") or "")
        if re.fullmatch(r"(19|20)\d{2}", year):
            return (-int(year), p["title"].lower())
        return (1, p["title"].lower())

    for page in sorted(pages, key=year_sort_key):
        all_tags = []
        for dim in tag_dimensions:
            for tag in page.get(f"tags_{dim}", []):
                all_tags.append(f"{dim}:{tag}")
        tags_str = ", ".join(all_tags[:5]) if all_tags else "-"
        doi_link = f"[DOI]({page['doi']})" if page["doi"] else "-"
        title_link = f"[{page['title']}]({page['path']})"
        lines.append(f"| {page['id'][:30]}... | {title_link} | {page['year']} | {tags_str} | {doi_link} |")

    lines.append("")

    for dim in tag_dimensions:
        tag_pages: dict[str, list[dict]] = defaultdict(list)
        for page in pages:
            for tag in page.get(f"tags_{dim}", []):
                tag_pages[tag].append(page)
        if not tag_pages:
            continue
        lines.append(f"## By {dim.capitalize()}")
        lines.append("")
        for tag, tag_group in sorted(tag_pages.items()):
            lines.append(f"### {tag}")
            lines.append("")
            for page in sorted(tag_group, key=year_sort_key):
                lines.append(f"- [{page['title']}]({page['path']}) ({page['year']})")
            lines.append("")

    index_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {rel(index_path)} ({len(pages)} papers)")


def write_all_journal_aggregate_indexes(pages: list[dict], config: dict) -> None:
    """Write aggregate indexes for all journals."""
    by_journal: dict[str, list[dict]] = defaultdict(list)
    for page in pages:
        by_journal[page["journal_abbr"]].append(page)
    for journal_abbr, journal_pages in sorted(by_journal.items()):
        write_journal_aggregate_index(journal_abbr, journal_pages, config)


def update_library(records: list[dict]) -> None:
    library_path = ROOT / "paper-library.md"
    text = library_path.read_text(encoding="utf-8") if library_path.exists() else "# Paper Library\n"
    by_direction = defaultdict(int)
    by_journal = defaultdict(int)
    root_files = 0
    unknown = 0
    for record in records:
        by_direction[record["direction"]] += 1
        by_journal[record["journal_abbr"]] += 1
        if record["is_direction_root_file"]:
            root_files += 1
        if record["journal_abbr"] == "UnknownJournal":
            unknown += 1

    org = [
        "<!-- AUTO:journal-organization:start -->",
        f"- Last rebuild: {datetime.now().isoformat(timespec='seconds')}",
        f"- Unsorted root-level files: {root_files}",
        f"- Unknown journal files: {unknown}",
        "- Known journal folders:",
    ]
    for journal, count in sorted(by_journal.items()):
        org.append(f"  - {journal}: {count}")
    org.append("<!-- AUTO:journal-organization:end -->")

    dash = [
        "<!-- AUTO:dashboard:start -->",
        f"- Total papers: {len(records)}",
        "- Papers by direction:",
    ]
    for direction, count in sorted(by_direction.items()):
        dash.append(f"  - {direction}: {count}")
    dash.append("- Papers by journal:")
    for journal, count in sorted(by_journal.items()):
        dash.append(f"  - {journal}: {count}")
    dash.append("<!-- AUTO:dashboard:end -->")

    text = replace_block(text, "journal-organization", "\n".join(org))
    text = replace_block(text, "dashboard", "\n".join(dash))
    library_path.write_text(text, encoding="utf-8")


def replace_block(text: str, name: str, replacement: str) -> str:
    start = f"<!-- AUTO:{name}:start -->"
    end = f"<!-- AUTO:{name}:end -->"
    if start in text and end in text:
        before = text.split(start, 1)[0]
        after = text.split(end, 1)[1]
        return before + replacement + after
    return text.rstrip() + "\n\n" + replacement + "\n"


def main() -> None:
    config = load_config()
    records = collect_records(config)
    indexes = ROOT / config["paths"]["indexes"]
    ensure_dir(indexes)
    source_index_path = indexes / "papers.json"
    canonical_index_path = indexes / "canonical_pages.json"
    write_json(source_index_path, records)

    canonical_pages = collect_canonical_pages(config)
    write_json(canonical_index_path, canonical_pages)
    write_all_journal_aggregate_indexes(canonical_pages, config)

    update_library(records)
    print(f"Indexed {len(records)} source files.")
    print(f"Indexed {len(canonical_pages)} canonical pages.")
    print(f"Wrote {rel(source_index_path)}")
    print(f"Wrote {rel(canonical_index_path)}")


if __name__ == "__main__":
    main()
