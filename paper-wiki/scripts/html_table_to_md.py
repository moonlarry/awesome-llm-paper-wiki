"""Convert HTML tables in Markdown files to GitHub Flavored Markdown tables.

Usage:
    python scripts/html_table_to_md.py <file_or_directory> [--write-source] [--backup]

By default, prints converted content to stdout. Use --write-source to overwrite the file.
Use --backup to save original HTML tables to workspace/cache/tables/ before conversion.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TABLE_PATTERN = re.compile(
    r"<table[^>]*>(.*?)</table>",
    re.DOTALL | re.IGNORECASE,
)

ROW_PATTERN = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
CELL_PATTERN = re.compile(
    r"<(th|td)[^>]*>(.*?)</\1>", re.DOTALL | re.IGNORECASE
)


def strip_tags(text: str) -> str:
    """Remove HTML tags but preserve Markdown links."""
    text = re.sub(r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", r"[\2](\1)", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def has_complex_structure(table_html: str) -> bool:
    """Check if the table has rowspan or colspan that cannot be losslessly converted."""
    return bool(re.search(r"(rowspan|colspan)\s*=\s*[\"']?\d+", table_html, re.IGNORECASE))


def html_table_to_md(table_html: str) -> str | None:
    """Convert a single HTML table to a Markdown table. Returns None if too complex."""
    if has_complex_structure(table_html):
        return None

    rows = ROW_PATTERN.findall(table_html)
    if not rows:
        return None

    md_rows: list[list[str]] = []
    for row_html in rows:
        cells = CELL_PATTERN.findall(row_html)
        md_rows.append([strip_tags(cell_content) for _, cell_content in cells])

    if not md_rows:
        return None

    max_cols = max(len(row) for row in md_rows)
    for row in md_rows:
        while len(row) < max_cols:
            row.append("")

    col_widths = [
        max(len(md_rows[r][c]) for r in range(len(md_rows)))
        for c in range(max_cols)
    ]
    col_widths = [max(w, 3) for w in col_widths]

    lines: list[str] = []
    for i, row in enumerate(md_rows):
        cells = [cell.ljust(col_widths[j]) for j, cell in enumerate(row)]
        lines.append("| " + " | ".join(cells) + " |")
        if i == 0:
            sep = ["-" * col_widths[j] for j in range(max_cols)]
            lines.append("| " + " | ".join(sep) + " |")

    return "\n".join(lines)


def convert_file(file_path: Path, write_source: bool, backup: bool) -> tuple[int, int]:
    """Convert all HTML tables in a file. Returns (converted, skipped) counts."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    tables = TABLE_PATTERN.findall(text)
    if not tables:
        return 0, 0

    converted = 0
    skipped = 0

    def replace_table(match: re.Match) -> str:
        nonlocal converted, skipped
        full_html = match.group(0)
        md = html_table_to_md(full_html)
        if md is None:
            skipped += 1
            if backup:
                save_backup(file_path, full_html, converted + skipped)
            return f"<!-- Complex HTML table preserved (rowspan/colspan) -->\n{full_html}"
        converted += 1
        if backup:
            save_backup(file_path, full_html, converted + skipped)
        return md

    new_text = TABLE_PATTERN.sub(replace_table, text)

    if write_source:
        file_path.write_text(new_text, encoding="utf-8")
    else:
        sys.stdout.write(new_text)

    return converted, skipped


def save_backup(file_path: Path, html_content: str, index: int) -> None:
    """Save original HTML table to backup directory."""
    backup_dir = ROOT / "workspace" / "cache" / "tables"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_table{index}_{timestamp}.html"
    (backup_dir / backup_name).write_text(html_content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert HTML tables to Markdown tables.")
    parser.add_argument("path", help="File or directory to process")
    parser.add_argument("--write-source", action="store_true",
                        help="Overwrite the source file with converted content")
    parser.add_argument("--backup", action="store_true",
                        help="Save original HTML tables to workspace/cache/tables/")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        target = ROOT / args.path
    if not target.exists():
        raise SystemExit(f"Path not found: {args.path}")

    files = list(target.rglob("*.md")) if target.is_dir() else [target]
    total_converted = 0
    total_skipped = 0

    for f in files:
        c, s = convert_file(f, args.write_source, args.backup)
        if c or s:
            print(f"{f.name}: converted {c}, skipped {s} (complex)", file=sys.stderr)
        total_converted += c
        total_skipped += s

    print(f"\nTotal: converted {total_converted} tables, skipped {total_skipped} complex tables",
          file=sys.stderr)


if __name__ == "__main__":
    main()
