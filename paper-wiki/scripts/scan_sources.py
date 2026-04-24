from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import ROOT, direction_paths, is_missing_journal, load_config, paper_root, resolve_journal, validate_direction, write_json


def scan_sources(config: dict[str, Any], direction: str | None = None) -> list[dict]:
    records: list[dict] = []
    base = paper_root(config)
    if direction:
        validate_direction(direction, config)
        direction_path = base / direction
        for md_path in sorted(direction_path.rglob("*.md")):
            records.append(resolve_journal(md_path, config))
    else:
        for direction_path in direction_paths(config):
            for md_path in sorted(direction_path.rglob("*.md")):
                records.append(resolve_journal(md_path, config))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan paper markdown sources.")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--direction", help="Limit scan to one configured direction.")
    parser.add_argument("--enrich-metadata", action="store_true", help="Enable metadata enrichment after scan.")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run enrichment, do not modify files.")
    parser.add_argument("--apply", action="store_true", help="Apply enrichment plan to Markdown files.")
    args = parser.parse_args()

    if args.dry_run and args.apply:
        print("Error: --dry-run and --apply are mutually exclusive.", file=sys.stderr)
        sys.exit(2)

    if args.dry_run and not args.enrich_metadata:
        print("Error: --dry-run requires --enrich-metadata.", file=sys.stderr)
        sys.exit(2)

    if args.apply and not args.enrich_metadata:
        print("Error: --apply requires --enrich-metadata.", file=sys.stderr)
        sys.exit(2)

    config_path = ROOT / args.config
    config = load_config(config_path)
    records = scan_sources(config, args.direction)
    manifest_path = ROOT / config["paths"]["manifests"] / "source_manifest.json"
    write_json(manifest_path, records)

    by_direction: dict[str, int] = {}
    root_files = 0
    missing_journal = 0
    for record in records:
        by_direction[record["direction"]] = by_direction.get(record["direction"], 0) + 1
        if record["is_direction_root_file"]:
            root_files += 1
        if is_missing_journal(record):
            missing_journal += 1

    print(f"Scanned {len(records)} markdown files.")
    print(f"Root-level unsorted candidates: {root_files}.")
    print(f"Papers missing journal metadata: {missing_journal}.")
    for direction, count in sorted(by_direction.items()):
        print(f"- {direction}: {count}")
    print(f"Wrote {manifest_path}")

    if args.enrich_metadata and missing_journal > 0:
        enrich_script = ROOT / "scripts" / "metadata_enrichment.py"
        cmd = [sys.executable, str(enrich_script)]
        if args.dry_run:
            cmd.append("--dry-run")
        if args.apply:
            cmd.append("--apply")
        subprocess.run(cmd, cwd=ROOT, check=True)
    elif args.enrich_metadata and missing_journal == 0:
        print("No papers with missing journal metadata. Skipping enrichment.")


if __name__ == "__main__":
    main()