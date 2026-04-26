from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import ROOT, ensure_dir, load_config, load_json, rel


def write_links(path, title: str, groups: dict[str, list[dict]]) -> None:
    lines = [f"# {title}", ""]
    for group, records in sorted(groups.items()):
        lines.append(f"## {group}")
        lines.append("")
        for record in sorted(records, key=lambda r: r["title"].lower()):
            lines.append(f"- [{record['title']}]({rel(ROOT / record['path'])})")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config = load_config()
    index_path = ROOT / config["paths"]["indexes"] / "papers.json"
    if not index_path.exists():
        raise SystemExit("Run scripts/rebuild_indexes.py first.")
    records = load_json(index_path)
    links = ROOT / config["paths"]["links"]
    ensure_dir(links)

    by_direction: dict[str, list[dict]] = defaultdict(list)
    by_journal: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_direction[record["direction"]].append(record)
        by_journal[record["journal_abbr"]].append(record)

    write_links(links / "by-direction.md", "Links by Direction", by_direction)
    write_links(links / "by-journal.md", "Links by Journal", by_journal)
    print(f"Wrote {rel(links / 'by-direction.md')}")
    print(f"Wrote {rel(links / 'by-journal.md')}")


if __name__ == "__main__":
    main()
