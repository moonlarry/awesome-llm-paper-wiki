from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import ROOT, direction_paths, ensure_dir, load_config, rel, resolve_journal, write_json


def build_plan(config: dict, direction_filter: str | None, fix_misplaced: bool) -> list[dict]:
    plan: list[dict] = []
    for direction_path in direction_paths(config):
        if direction_filter and direction_path.name != direction_filter:
            continue
        for md_path in sorted(direction_path.rglob("*.md")):
            record = resolve_journal(md_path, config)
            source = ROOT / record["path"]
            target = ROOT / record["target_path"]
            action = "skip"
            reason = "already in a journal folder"

            if record["is_direction_root_file"]:
                action = "move"
                reason = "root-level markdown"
            elif fix_misplaced and source.resolve() != target.resolve():
                action = "move"
                reason = "fix misplaced journal folder"
            elif source.resolve() != target.resolve():
                action = "warn"
                reason = "possible misplaced file; use --fix-misplaced to move"

            if action == "move" and target.exists():
                action = "conflict"
                reason = "target already exists"

            plan.append({**record, "action": action, "reason": reason})
    return plan


def apply_plan(plan: list[dict], config: dict) -> tuple[int, int]:
    moved = 0
    skipped = 0
    paper_base = (ROOT / config.get("paper_root", "paper")).resolve()
    for item in plan:
        if item["action"] != "move":
            skipped += 1
            continue
        source = (ROOT / item["path"]).resolve()
        target = (ROOT / item["target_path"]).resolve()
        if not str(source).lower().startswith(str(paper_base).lower()):
            raise RuntimeError(f"Refusing to move outside paper root: {source}")
        if not str(target).lower().startswith(str(paper_base).lower()):
            raise RuntimeError(f"Refusing to move outside paper root: {target}")
        ensure_dir(target.parent)
        shutil.move(str(source), str(target))
        moved += 1
    return moved, skipped


def write_log(plan: list[dict], moved: int | None = None) -> None:
    log_path = ROOT / "workspace" / "logs" / "organize_by_journal.md"
    ensure_dir(log_path.parent)
    timestamp = datetime.now().isoformat(timespec="seconds")
    counts: dict[str, int] = {}
    for item in plan:
        counts[item["action"]] = counts.get(item["action"], 0) + 1
    lines = [f"## [{timestamp}] organize_by_journal", ""]
    if moved is not None:
        lines.append(f"- Applied moves: {moved}")
    for action, count in sorted(counts.items()):
        lines.append(f"- {action}: {count}")
    lines.append("")
    for item in plan:
        if item["action"] in {"move", "conflict", "warn"}:
            lines.append(f"- {item['action']}: `{item['path']}` -> `{item['target_path']}` ({item['reason']})")
    lines.append("")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Organize markdown papers into journal folders.")
    parser.add_argument("--config", default="config.json")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--direction")
    group.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--fix-misplaced", action="store_true")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        raise SystemExit("Choose --dry-run or --apply.")
    if not args.all and not args.direction:
        raise SystemExit("Choose --all or --direction <name>.")

    config = load_config(ROOT / args.config)
    plan = build_plan(config, None if args.all else args.direction, args.fix_misplaced)
    plan_path = ROOT / config["paths"]["manifests"] / "journal_move_plan.json"
    write_json(plan_path, plan)
    write_log(plan)

    counts: dict[str, int] = {}
    for item in plan:
        counts[item["action"]] = counts.get(item["action"], 0) + 1

    if args.apply:
        moved, skipped = apply_plan(plan, config)
        write_log(plan, moved=moved)
        print(f"Applied plan. Moved {moved}; skipped {skipped}.")
        if counts.get("conflict", 0):
            print(f"Skipped {counts['conflict']} conflicts without overwriting existing files.")
    else:
        print("Dry-run complete.")

    for action, count in sorted(counts.items()):
        print(f"- {action}: {count}")
    print(f"Wrote {rel(plan_path)}")


if __name__ == "__main__":
    main()
