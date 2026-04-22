from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from common import (
    ROOT,
    apply_keyword_rules_to_canonical,
    canonical_id,
    direction_paths,
    ensure_dir,
    generate_canonical,
    load_config,
    load_keyword_rules,
    paper_root,
    parse_frontmatter,
    rel,
    rebuild_indexes,
    write_json,
)


def resolve_input_file(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def canonical_target_for_source(source_path: Path, config: dict[str, Any]) -> Path:
    text = source_path.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)
    direction = str(fm.get("direction") or source_path.relative_to(paper_root(config)).parts[0])
    return ROOT / config["paths"]["papers"] / direction / f"{canonical_id(source_path, fm, config)}.md"


def source_paths(args: argparse.Namespace, config: dict[str, Any]) -> list[Path]:
    if args.file:
        path = resolve_input_file(args.file)
        if "web_search" in path.parts:
            raise ValueError("Refusing to ingest web_search research-layer files directly.")
        if not path.exists() or path.suffix.lower() != ".md":
            raise ValueError(f"Markdown source does not exist: {path}")
        return [path]
    paths: list[Path] = []
    for direction_path in direction_paths(config):
        if args.direction and direction_path.name != args.direction:
            continue
        for md_path in sorted(direction_path.rglob("*.md")):
            if "web_search" in md_path.parts:
                continue
            if args.journal:
                rel_parts = md_path.relative_to(direction_path).parts
                if len(rel_parts) < 2 or rel_parts[0] != args.journal:
                    continue
            paths.append(md_path)
    return paths


def ingest_one(source_path: Path, config: dict[str, Any], rules: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    canonical_path = canonical_target_for_source(source_path, config)
    existed = canonical_path.exists()
    record: dict[str, Any] = {
        "source": rel(source_path),
        "canonical": rel(canonical_path),
        "status": "dry-run" if args.dry_run else ("updated" if existed else "created"),
        "tag_updates": [],
    }
    if args.dry_run:
        if args.apply_tags and canonical_path.exists():
            record["tag_updates"] = apply_keyword_rules_to_canonical(canonical_path, rules, dry_run=True)
        return record
    canonical_path = generate_canonical(source_path, config)
    record["canonical"] = rel(canonical_path)
    if args.apply_tags:
        record["tag_updates"] = apply_keyword_rules_to_canonical(canonical_path, rules, dry_run=False)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-generate canonical paper pages and optionally apply keyword-rule tags.")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--file")
    scope.add_argument("--direction")
    scope.add_argument("--all", action="store_true")
    parser.add_argument("--journal")
    parser.add_argument("--apply-tags", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rebuild-indexes", action="store_true")
    args = parser.parse_args()

    config = load_config()
    rules = load_keyword_rules(config) if args.apply_tags else []
    try:
        paths = source_paths(args, config)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    processed: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for source_path in paths:
        try:
            processed.append(ingest_one(source_path, config, rules, args))
        except Exception as exc:
            errors.append({"source": rel(source_path), "error": str(exc)})
    summary = {
        "dry_run": args.dry_run,
        "apply_tags": args.apply_tags,
        "processed": processed,
        "errors": errors,
        "counts": {
            "processed": len(processed),
            "tag_updates": sum(len(item["tag_updates"]) for item in processed),
            "errors": len(errors),
        },
    }
    if not args.dry_run:
        manifest_path = ROOT / config["paths"]["manifests"] / "ingest_batch.json"
        write_json(manifest_path, summary)
        if args.rebuild_indexes:
            rebuild_indexes()
    print(f"Ingest batch: processed {len(processed)}; tag updates {summary['counts']['tag_updates']}; errors {len(errors)}.")
    if args.dry_run:
        print("Dry run: no files were written.")
    elif args.rebuild_indexes:
        print("Indexes rebuilt.")


if __name__ == "__main__":
    main()
