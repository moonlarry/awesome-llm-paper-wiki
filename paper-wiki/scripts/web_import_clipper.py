from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from common import (
    ROOT,
    append_log,
    apply_keyword_rules_to_canonical,
    clean_author_name,
    ensure_dir,
    existing_identities,
    extract_doi,
    extract_heading_section,
    extract_year,
    first_author_key,
    generate_canonical,
    journal_abbr_from_name,
    load_config,
    load_keyword_rules,
    normalize_identity,
    parse_frontmatter,
    paper_root,
    rel,
    rebuild_indexes,
    slugify,
    validate_direction,
    write_json,
    yaml_int_or_null,
    yaml_list,
    yaml_quote,
)


def first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def frontmatter_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [clean_author_name(str(item)) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [clean_author_name(part) for part in value.replace(" and ", ";").split(";") if part.strip()]
    return []


def infer_metadata(path: Path, text: str) -> dict[str, Any]:
    fm = parse_frontmatter(text)
    title = str(fm.get("title") or first_heading(text) or path.stem).strip()
    source = str(fm.get("source") or fm.get("url") or "").strip()
    doi = str(fm.get("doi") or extract_doi(text) or "").strip()
    year = fm.get("published_year") or fm.get("year") or extract_year(text) or ""
    journal = str(fm.get("published") or fm.get("journal") or fm.get("site") or "UnknownJournal").strip()
    authors = frontmatter_list(fm.get("authors") or fm.get("author"))
    abstract = extract_heading_section(text, "Abstract")
    return {
        "title": title,
        "authors": authors,
        "source": source,
        "doi": doi,
        "year": year,
        "journal": journal,
        "abstract": abstract,
    }


def identity(meta: dict[str, Any]) -> str:
    if meta["doi"]:
        return f"doi:{str(meta['doi']).lower()}"
    return f"title:{normalize_identity(meta['title'])}:{meta['year']}"


def normalize_clipped_markdown(text: str, meta: dict[str, Any], direction: str, journal_abbr: str) -> str:
    body = text
    if body.startswith("---"):
        parts = body.split("---", 2)
        if len(parts) == 3:
            body = parts[2].lstrip()
    if not body.lstrip().startswith("# "):
        body = f"# {meta['title']}\n\n{body.lstrip()}"
    if "## Abstract" not in body and meta["abstract"]:
        body = body.replace(f"# {meta['title']}", f"# {meta['title']}\n\n## Abstract\n\n{meta['abstract']}", 1)
    header = "\n".join(
        [
            "---",
            f"title: {yaml_quote(meta['title'])}",
            "authors:",
            yaml_list(meta["authors"]),
            f"published: {yaml_quote(meta['journal'])}",
            f"published_year: {yaml_int_or_null(meta['year'])}",
            f"doi: {yaml_quote(meta['doi'])}",
            f"source: {yaml_quote(meta['source'])}",
            'web_source: "clipper"',
            'citation_count: ""',
            f"direction: {yaml_quote(direction)}",
            f"journal_abbr: {yaml_quote(journal_abbr)}",
            'source_type: "clipped"',
            'import_status: "clipper-imported"',
            f"created_at: {yaml_quote(datetime.now().isoformat(timespec='seconds'))}",
            "---",
            "",
        ]
    )
    if "## Full Text / Clipped Content" not in body:
        body += "\n\n## Full Text / Clipped Content\n\nContent above was imported from Obsidian Web Clipper.\n"
    if "## User Notes" not in body:
        body += "\n\n## User Notes\n\n"
    return header + body.rstrip() + "\n"


def import_file(path: Path, direction: str, config: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    meta = infer_metadata(path, text)
    journal_abbr = journal_abbr_from_name(meta["journal"], config)
    filename = f"{meta['year'] or 'unknown'}-{first_author_key(meta['authors'])}-{slugify(meta['title'])}.md"
    target = paper_root(config) / direction / journal_abbr / filename
    record = {"source": rel(path), "target": rel(target), "title": meta["title"], "identity": identity(meta), "status": "dry-run" if dry_run else "created"}
    if target.exists():
        record["status"] = "skipped_existing"
        return record
    if not dry_run:
        ensure_dir(target.parent)
        target.write_text(normalize_clipped_markdown(text, meta, direction, journal_abbr), encoding="utf-8")
        generate_canonical(target, config)
    return record


def archive_imported_file(path: Path, inbox: Path) -> str:
    archive_dir = inbox / "imported"
    ensure_dir(archive_dir)
    target = archive_dir / path.name
    if target.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = archive_dir / f"{path.stem}-{stamp}{path.suffix}"
    shutil.move(str(path), str(target))
    return rel(target)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Obsidian Web Clipper Markdown into the paper vault.")
    parser.add_argument("--direction", required=True)
    parser.add_argument("--inbox")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = load_config()
    try:
        validate_direction(args.direction, config)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    inbox = ROOT / (args.inbox or config.get("web_search", {}).get("clipper_inbox", "workspace/web-inbox"))
    ensure_dir(inbox)
    identities = existing_identities(args.direction, config)
    created: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for md_path in sorted(inbox.glob("*.md")):
        meta = infer_metadata(md_path, md_path.read_text(encoding="utf-8", errors="replace"))
        ident = identity(meta)
        if ident in identities:
            skipped.append({"source": rel(md_path), "title": meta["title"], "identity": ident, "status": "skipped_existing"})
            continue
        record = import_file(md_path, args.direction, config, args.dry_run)
        if record["status"] == "skipped_existing":
            skipped.append(record)
            continue
        if not args.dry_run:
            record["archived_to"] = archive_imported_file(md_path, inbox)
        created.append(record)
    manifest_path = ROOT / config["paths"]["manifests"] / "web_clipper_import.json"
    if not args.dry_run:
        write_json(manifest_path, {"direction": args.direction, "inbox": rel(inbox), "dry_run": args.dry_run, "created": created, "skipped_existing": skipped})
        rules = load_keyword_rules(config)
        tag_updates = 0
        for record in created:
            if record.get("status") == "created":
                target_path = ROOT / record["target"]
                if target_path.exists():
                    updates = apply_keyword_rules_to_canonical(target_path, rules, dry_run=False)
                    tag_updates += len(updates)
        rebuild_indexes()
        append_log(f"- {datetime.now().isoformat(timespec='seconds')} clipper {args.direction}: created={len(created)} skipped={len(skipped)} tags={tag_updates} dry_run={args.dry_run}", config)
        print(f"Tag updates: {tag_updates}")
    print(f"Clipper import: created {len(created)}; skipped {len(skipped)}.")
    if args.dry_run:
        print("Dry run: no files were written.")
    else:
        print(f"Manifest: {rel(manifest_path)}")


if __name__ == "__main__":
    main()
