from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import ROOT, direction_paths, load_config, resolve_journal, write_json


def scan_sources(config_path: Path) -> list[dict]:
    config = load_config(config_path)
    records: list[dict] = []
    for direction_path in direction_paths(config):
        for md_path in sorted(direction_path.rglob("*.md")):
            records.append(resolve_journal(md_path, config))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan paper markdown sources.")
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args()

    config_path = ROOT / args.config
    config = load_config(config_path)
    records = scan_sources(config_path)
    manifest_path = ROOT / config["paths"]["manifests"] / "source_manifest.json"
    write_json(manifest_path, records)

    by_direction: dict[str, int] = {}
    root_files = 0
    for record in records:
        by_direction[record["direction"]] = by_direction.get(record["direction"], 0) + 1
        if record["is_direction_root_file"]:
            root_files += 1
    print(f"Scanned {len(records)} markdown files.")
    print(f"Root-level unsorted candidates: {root_files}.")
    for direction, count in sorted(by_direction.items()):
        print(f"- {direction}: {count}")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
