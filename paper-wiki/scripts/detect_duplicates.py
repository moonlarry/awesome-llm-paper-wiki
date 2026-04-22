from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from common import (
    ROOT,
    direction_paths,
    ensure_dir,
    extract_arxiv_id,
    load_config,
    parse_frontmatter,
    rel,
    resolve_journal,
)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_title(title: str) -> str:
    title = re.sub(r"[\W_]+", " ", title, flags=re.UNICODE)
    title = re.sub(r"\s+", " ", title).strip().lower()
    return title


def extract_year(fm: dict[str, Any]) -> str:
    for key in ("published_year", "year", "published_date"):
        value = str(fm.get(key) or "").strip()
        match = re.search(r"\b(19|20)\d{2}\b", value)
        if match:
            return match.group(0)
    return ""


def collect_source_files(direction: str | None, config: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for direction_path in direction_paths(config):
        if direction and direction_path.name != direction:
            continue
        for md_path in sorted(direction_path.rglob("*.md")):
            if "web_search" in md_path.parts:
                continue
            text = md_path.read_text(encoding="utf-8", errors="replace")
            fm = parse_frontmatter(text)
            title = str(fm.get("title") or md_path.stem).strip()
            checksum = file_sha256(md_path)
            doi = str(fm.get("doi") or "").strip().lower()
            year = extract_year(fm)
            source_value = str(fm.get("source") or "").strip()
            arxiv_id = str(fm.get("arxiv_id") or "").strip() or extract_arxiv_id(source_value)
            journal_info = resolve_journal(md_path, config)
            source_path = rel(md_path)
            records.append({
                "path": source_path,
                "source_path": source_path,
                "direction": direction_path.name,
                "title": title,
                "normalized_title": normalize_title(title),
                "year": year,
                "doi": doi,
                "journal": str(journal_info.get("journal") or "").strip(),
                "journal_abbr": str(journal_info.get("journal_abbr") or "").strip(),
                "arxiv_id": arxiv_id,
                "checksum": checksum,
                "size": md_path.stat().st_size,
            })
    return records


def detect_exact_duplicates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checksum_map: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        checksum = record["checksum"]
        if checksum not in checksum_map:
            checksum_map[checksum] = []
        checksum_map[checksum].append(record)

    duplicates: list[dict[str, Any]] = []
    for checksum, group in checksum_map.items():
        if len(group) > 1:
            duplicates.append({
                "type": "exact",
                "checksum": checksum,
                "files": group,
                "count": len(group),
            })
    return duplicates


def detect_probable_duplicates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    title_year_map: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        key = f"{record['normalized_title']}:{record['year']}"
        if key not in title_year_map:
            title_year_map[key] = []
        title_year_map[key].append(record)

    duplicates: list[dict[str, Any]] = []
    for key, group in title_year_map.items():
        if len(group) > 1:
            checksums = set(r["checksum"] for r in group)
            if len(checksums) > 1:
                duplicates.append({
                    "type": "probable",
                    "key": key,
                    "files": group,
                    "count": len(group),
                    "checksum_match": len(checksums) == 1,
                })
    return duplicates


def write_duplicate_report(
    exact: list[dict[str, Any]],
    probable: list[dict[str, Any]],
    output_dir: Path,
) -> tuple[Path, Path]:
    def format_identity(record: dict[str, Any], checksum_note: str | None = None) -> str:
        journal_bits = [record.get("journal") or "", record.get("journal_abbr") or ""]
        journal_display = " / ".join(part for part in journal_bits if part) or "N/A"
        parts = [
            record["direction"],
            f"journal: {journal_display}",
            f"year: {record['year'] or 'N/A'}",
            f"DOI: {record['doi'] or 'N/A'}",
            f"arXiv: {record['arxiv_id'] or 'N/A'}",
        ]
        if checksum_note:
            parts.append(checksum_note)
        return f"- `{record['source_path']}` ({', '.join(parts)})"

    ensure_dir(output_dir)

    json_path = output_dir / "duplicate_report.json"
    md_path = output_dir / "duplicate_report.md"

    data = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "exact_duplicates": exact,
        "probable_duplicates": probable,
        "exact_count": len(exact),
        "probable_count": len(probable),
        "total_exact_files": sum(d["count"] for d in exact),
        "total_probable_files": sum(d["count"] for d in probable),
    }
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Duplicate Detection Report",
        "",
        f"> Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Summary",
        "",
        f"- Exact duplicates (SHA256 match): {len(exact)} groups, {data['total_exact_files']} files",
        f"- Probable duplicates (title+year match): {len(probable)} groups, {data['total_probable_files']} files",
        "",
        "## Exact Duplicates",
        "",
        "Files with identical SHA256 checksum:",
        "",
    ]

    if exact:
        for group in exact:
            lines.append(f"### Group (checksum: {group['checksum'][:16]}...)")
            lines.append("")
            for f in group["files"]:
                lines.append(format_identity(f))
            lines.append("")
    else:
        lines.append("- None")
        lines.append("")

    lines.extend([
        "## Probable Duplicates",
        "",
        "Files with matching normalized title and year (different checksum):",
        "",
    ])

    if probable:
        for group in probable:
            lines.append(f"### Group (title+year: {group['key']})")
            lines.append("")
            for f in group["files"]:
                checksum_note = "same checksum" if group["checksum_match"] else "different checksum"
                lines.append(format_identity(f, checksum_note=f"checksum: {f['checksum'][:16]}... ({checksum_note})"))
            lines.append("")
    else:
        lines.append("- None")
        lines.append("")

    lines.extend([
        "## Action Recommendation",
        "",
        "- **Exact duplicates**: Consider consolidating or removing redundant files.",
        "- **Probable duplicates**: Manual review required before any action.",
        "- **probable duplicates do NOT trigger automatic operations**.",
        "",
    ])

    md_path.write_text("\n".join(lines), encoding="utf-8")

    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect duplicate paper files in the vault.")
    parser.add_argument("--direction", help="Scan specific direction only")
    parser.add_argument("--all", action="store_true", help="Scan all directions")
    args = parser.parse_args()

    if not args.direction and not args.all:
        raise SystemExit("Choose --direction <name> or --all.")

    config = load_config()
    records = collect_source_files(args.direction if not args.all else None, config)

    if not records:
        print("No source files found.")
        return

    print(f"Scanned {len(records)} source files.")

    exact = detect_exact_duplicates(records)
    probable = detect_probable_duplicates(records)

    output_dir = ROOT / "workspace" / "manifests"
    json_path, md_path = write_duplicate_report(exact, probable, output_dir)

    print(f"Exact duplicates: {len(exact)} groups ({sum(d['count'] for d in exact)} files)")
    print(f"Probable duplicates: {len(probable)} groups ({sum(d['count'] for d in probable)} files)")
    print(f"Report: {rel(md_path)}")
    print(f"JSON: {rel(json_path)}")


if __name__ == "__main__":
    main()
