from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from common import (
    ROOT,
    ensure_dir,
    is_missing_journal,
    journal_abbr_from_name,
    load_aliases,
    load_config,
    load_json,
    lookup_crossref_by_title,
    lookup_openalex_by_title,
    normalize_title_for_match,
    parse_frontmatter,
    read_text,
    rel,
    replace_frontmatter_field,
    resolve_journal,
    write_json,
    yaml_int_or_null,
    yaml_quote,
)


CACHE_PATH = ROOT / "workspace" / "cache" / "metadata_lookup_cache.json"
MISSING_JOURNAL_PATH = ROOT / "workspace" / "manifests" / "missing_journal_sources.json"
PLAN_PATH = ROOT / "workspace" / "manifests" / "metadata_enrichment_plan.json"
LOG_PATH = ROOT / "workspace" / "logs" / "metadata_enrichment.md"


def load_cache() -> dict[str, Any]:
    if CACHE_PATH.exists():
        return load_json(CACHE_PATH)
    return {}


def save_cache(cache: dict[str, Any]) -> None:
    ensure_dir(CACHE_PATH.parent)
    write_json(CACHE_PATH, cache)


def detect_missing_journal_sources(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Scan all directions and return records missing journal metadata."""
    missing: list[dict[str, Any]] = []
    manifest_path = ROOT / config["paths"]["manifests"] / "source_manifest.json"

    if not manifest_path.exists():
        return missing

    records = load_json(manifest_path)
    for record in records:
        if is_missing_journal(record):
            missing.append({
                "path": record.get("path"),
                "direction": record.get("direction"),
                "current_journal_folder": record.get("current_journal_folder"),
                "title": record.get("title"),
                "source": record.get("source"),
                "journal": record.get("journal"),
                "journal_abbr": record.get("journal_abbr"),
                "journal_source": record.get("journal_source"),
                "journal_confidence": record.get("journal_confidence"),
                "reason": "missing_journal_metadata",
            })

    write_json(MISSING_JOURNAL_PATH, missing)
    return missing


def plan_matches_manifest(plan: dict[str, Any], manifest: list[dict[str, Any]]) -> bool:
    """Verify plan paths match current missing journal manifest."""
    plan_paths = set()
    for record in plan.get("matched", []):
        path = record.get("path")
        if path:
            plan_paths.add(path)
    for record in plan.get("unresolved", []):
        path = record.get("path")
        if path:
            plan_paths.add(path)

    manifest_paths = set()
    for record in manifest:
        path = record.get("path")
        if path:
            manifest_paths.add(path)

    return plan_paths == manifest_paths


def cache_key(title: str, provider: str) -> str:
    """Generate cache key from normalized title and provider."""
    normalized = normalize_title_for_match(title)
    return f"{provider}:{normalized}"


def query_with_cache(title: str, config: dict[str, Any], cache: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    """Query Crossref/OpenAlex with caching. Returns (metadata, provider)."""
    key_crossref = cache_key(title, "crossref")
    key_openalex = cache_key(title, "openalex")

    if key_crossref in cache:
        cached = cache[key_crossref]
        if cached.get("status") == "matched":
            return cached, "crossref"
        if cached.get("status") == "unresolved":
            pass
    else:
        crossref_result = lookup_crossref_by_title(title, config)
        if crossref_result:
            cache[key_crossref] = {
                "provider": "crossref",
                "queried_at": datetime.now().isoformat(timespec="seconds"),
                "status": "matched",
                "title": crossref_result.get("title"),
                "journal": crossref_result.get("journal"),
                "doi": crossref_result.get("doi"),
                "published_year": crossref_result.get("published_year"),
            }
            save_cache(cache)
            return cache[key_crossref], "crossref"
        else:
            cache[key_crossref] = {
                "provider": "crossref",
                "queried_at": datetime.now().isoformat(timespec="seconds"),
                "status": "unresolved",
            }
            save_cache(cache)

    if key_openalex in cache:
        cached = cache[key_openalex]
        if cached.get("status") == "matched":
            return cached, "openalex"
    else:
        openalex_result = lookup_openalex_by_title(title, config)
        if openalex_result:
            cache[key_openalex] = {
                "provider": "openalex",
                "queried_at": datetime.now().isoformat(timespec="seconds"),
                "status": "matched",
                "title": openalex_result.get("title"),
                "journal": openalex_result.get("journal"),
                "doi": openalex_result.get("doi"),
                "published_year": openalex_result.get("published_year"),
            }
            save_cache(cache)
            return cache[key_openalex], "openalex"
        else:
            cache[key_openalex] = {
                "provider": "openalex",
                "queried_at": datetime.now().isoformat(timespec="seconds"),
                "status": "unresolved",
            }
            save_cache(cache)

    return None, ""


def build_enrichment_plan(missing_records: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """Build enrichment plan from missing journal records."""
    cache = load_cache()
    aliases = load_aliases(config)

    matched: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for record in missing_records:
        path = record.get("path")
        title = record.get("title") or ""
        source_path = ROOT / path if path else None

        if not title or not source_path or not source_path.exists():
            errors.append({
                "path": path,
                "title": title,
                "reason": "file_not_found_or_no_title",
            })
            continue

        try:
            metadata, provider = query_with_cache(title, config, cache)
            if metadata:
                matched_title = metadata.get("title") or ""
                matched_journal = metadata.get("journal") or ""
                matched_doi = metadata.get("doi") or ""
                matched_year = metadata.get("published_year")

                journal_abbr = journal_abbr_from_name(matched_journal, config)

                matched.append({
                    "path": path,
                    "title": title,
                    "current_journal": record.get("journal"),
                    "current_journal_abbr": record.get("journal_abbr"),
                    "matched_provider": provider,
                    "matched_title": matched_title,
                    "journal": matched_journal,
                    "journal_abbr": journal_abbr,
                    "doi": matched_doi,
                    "published_year": matched_year,
                    "confidence": "high",
                    "action": "update",
                    "reason": "exact_title_match",
                })
            else:
                unresolved.append({
                    "path": path,
                    "title": title,
                    "current_journal": record.get("journal"),
                    "current_journal_abbr": record.get("journal_abbr"),
                    "reason": "no_match_found",
                })
        except Exception as exc:
            errors.append({
                "path": path,
                "title": title,
                "reason": f"query_error: {exc}",
            })

    plan = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_missing": len(missing_records),
        "matched_count": len(matched),
        "unresolved_count": len(unresolved),
        "error_count": len(errors),
        "matched": matched,
        "unresolved": unresolved,
        "errors": errors,
    }

    write_json(PLAN_PATH, plan)
    return plan


def is_placeholder_journal(value: str) -> bool:
    """Check if journal value is a placeholder that can be replaced."""
    if not value:
        return True
    value = value.strip()
    if value == "UnknownJournal":
        return True
    if value == "IEEE":
        return True
    return False


def apply_frontmatter_updates(plan: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Apply frontmatter updates for matched records."""
    updated: list[dict[str, Any]] = []
    skipped_full: list[dict[str, Any]] = []
    updated_partial: list[dict[str, Any]] = []

    for record in plan.get("matched", []):
        path_str = record.get("path")
        if not path_str:
            continue

        source_path = ROOT / path_str
        if not source_path.exists():
            continue

        text = read_text(source_path)
        fm = parse_frontmatter(text)

        existing_journal = str(fm.get("journal") or "").strip()
        existing_journal_abbr = str(fm.get("journal_abbr") or "").strip()
        existing_doi = str(fm.get("doi") or "").strip()
        existing_year = fm.get("published_year")

        has_real_journal = existing_journal and not is_placeholder_journal(existing_journal)
        has_real_journal_abbr = existing_journal_abbr and not is_placeholder_journal(existing_journal_abbr)
        has_doi = bool(existing_doi)
        has_year = bool(existing_year)

        if has_real_journal and has_real_journal_abbr and has_doi and has_year:
            skipped_full.append({
                "path": path_str,
                "title": record.get("title"),
                "reason": "all_metadata_present",
            })
            continue

        new_journal = record.get("journal") or ""
        new_journal_abbr = record.get("journal_abbr") or ""
        new_doi = record.get("doi") or ""
        new_year = record.get("published_year")

        updated_text = text
        journal_updated = False
        journal_abbr_updated = False

        if not has_real_journal and new_journal and is_placeholder_journal(existing_journal):
            updated_text = replace_frontmatter_field(
                updated_text, "journal", f"journal: {yaml_quote(new_journal)}"
            )
            journal_updated = True

        if not has_real_journal_abbr and new_journal_abbr and is_placeholder_journal(existing_journal_abbr):
            updated_text = replace_frontmatter_field(
                updated_text, "journal_abbr", f"journal_abbr: {yaml_quote(new_journal_abbr)}"
            )
            journal_abbr_updated = True

        if not has_doi and new_doi:
            updated_text = replace_frontmatter_field(
                updated_text, "doi", f"doi: {yaml_quote(new_doi)}"
            )

        if not has_year and new_year:
            updated_text = replace_frontmatter_field(
                updated_text, "published_year", f"published_year: {yaml_int_or_null(str(new_year))}"
            )
            updated_text = replace_frontmatter_field(
                updated_text, "published_date", f"published_date: {yaml_quote(str(new_year))}"
            )

        source_path.write_text(updated_text, encoding="utf-8")

        final_journal = new_journal if journal_updated else existing_journal
        final_journal_abbr = new_journal_abbr if journal_abbr_updated else existing_journal_abbr
        final_doi = new_doi if not has_doi else existing_doi
        final_year = new_year if not has_year else existing_year

        is_full_update = (journal_updated or journal_abbr_updated) and not has_doi and not has_year
        is_partial_update = (journal_updated or journal_abbr_updated) and (has_doi or has_year)

        if is_full_update:
            updated.append({
                "path": path_str,
                "title": record.get("title"),
                "journal": final_journal,
                "journal_abbr": final_journal_abbr,
                "doi": final_doi,
                "published_year": final_year,
                "action": "full_update",
            })
        elif is_partial_update:
            updated_partial.append({
                "path": path_str,
                "title": record.get("title"),
                "journal": final_journal,
                "journal_abbr": final_journal_abbr,
                "doi": final_doi,
                "published_year": final_year,
                "journal_updated": journal_updated,
                "journal_abbr_updated": journal_abbr_updated,
                "action": "partial_update",
            })
        else:
            skipped_full.append({
                "path": path_str,
                "title": record.get("title"),
                "reason": "no_placeholder_to_replace",
            })

    return updated, skipped_full, updated_partial


def write_log(plan: dict[str, Any], updated: list[dict[str, Any]], skipped: list[dict[str, Any]], journal_only: list[dict[str, Any]], dry_run: bool) -> None:
    """Write human-readable log."""
    ensure_dir(LOG_PATH.parent)
    status = "dry-run" if dry_run else "applied"

    lines = [
        f"# Metadata Enrichment Log ({status})",
        f"",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"",
        f"## Summary",
        f"",
        f"- Total missing journal records: {plan.get('total_missing', 0)}",
        f"- Matched: {plan.get('matched_count', 0)}",
        f"- Unresolved: {plan.get('unresolved_count', 0)}",
        f"- Errors: {plan.get('error_count', 0)}",
        f"- Full updates: {len(updated)}",
        f"- Journal-only updates: {len(journal_only)}",
        f"- Skipped (all metadata present): {len(skipped)}",
        f"",
        f"## Updated Files (Full)",
        f"",
    ]

    for record in updated:
        lines.append(f"- `{record.get('path')}`")
        lines.append(f"  - Title: {record.get('title')}")
        lines.append(f"  - Journal: {record.get('journal')} ({record.get('journal_abbr')})")
        lines.append(f"  - DOI: {record.get('doi')}")
        lines.append(f"  - Year: {record.get('published_year')}")
        lines.append(f"")

    if journal_only:
        lines.append(f"## Updated Files (Journal Only)")
        lines.append(f"")
        for record in journal_only:
            lines.append(f"- `{record.get('path')}`")
            lines.append(f"  - Title: {record.get('title')}")
            lines.append(f"  - Journal: {record.get('journal')} ({record.get('journal_abbr')})")
            lines.append(f"")

    if skipped:
        lines.append(f"## Skipped Files (all metadata present)")
        lines.append(f"")
        for record in skipped:
            lines.append(f"- `{record.get('path')}`: {record.get('reason')}")
        lines.append(f"")

    if plan.get("unresolved"):
        lines.append(f"## Unresolved Files")
        lines.append(f"")
        for record in plan.get("unresolved", []):
            lines.append(f"- `{record.get('path')}`: {record.get('title')}")
        lines.append(f"")

    if plan.get("errors"):
        lines.append(f"## Errors")
        lines.append(f"")
        for record in plan.get("errors", []):
            lines.append(f"- `{record.get('path')}`: {record.get('reason')}")
        lines.append(f"")

    LOG_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Metadata enrichment for papers missing journal info.")
    parser.add_argument("--dry-run", action="store_true", help="Build plan only, do not modify files.")
    parser.add_argument("--apply", action="store_true", help="Apply enrichment plan to Markdown files.")
    parser.add_argument("--force-apply", action="store_true", help="Apply without requiring prior dry-run plan review.")
    args = parser.parse_args()

    if args.dry_run and args.apply:
        print("Error: --dry-run and --apply are mutually exclusive.", file=sys.stderr)
        sys.exit(2)

    if args.dry_run and args.force_apply:
        print("Error: --dry-run and --force-apply are mutually exclusive.", file=sys.stderr)
        sys.exit(2)

    if args.apply and not args.force_apply:
        if not PLAN_PATH.exists():
            print(f"Error: No enrichment plan found at {rel(PLAN_PATH)}.", file=sys.stderr)
            print("Run --dry-run first to generate a reviewable plan, or use --force-apply to skip review.", file=sys.stderr)
            sys.exit(2)
        try:
            existing_plan = load_json(PLAN_PATH)
            if not existing_plan.get("matched"):
                print("Error: Existing plan has no matched records.", file=sys.stderr)
                sys.exit(2)
        except Exception:
            print(f"Error: Cannot read existing plan at {rel(PLAN_PATH)}.", file=sys.stderr)
            sys.exit(2)

    config = load_config()

    missing = detect_missing_journal_sources(config)
    if not missing:
        print("No papers with missing journal metadata found.")
        return

    print(f"Found {len(missing)} papers with missing journal metadata.")

    if args.apply and not args.force_apply:
        plan = load_json(PLAN_PATH)
        if not plan_matches_manifest(plan, missing):
            print(f"Error: Plan does not match current missing journal manifest.", file=sys.stderr)
            print("The library has changed since the plan was generated. Run --dry-run again.", file=sys.stderr)
            sys.exit(2)
        print(f"Using existing plan from {rel(PLAN_PATH)}: matched={plan.get('matched_count')}")
    else:
        plan = build_enrichment_plan(missing, config)
        print(f"Enrichment plan: matched={plan.get('matched_count')}, unresolved={plan.get('unresolved_count')}, errors={plan.get('error_count')}")

    if args.dry_run:
        write_log(plan, [], [], [], dry_run=True)
        print(f"Dry-run complete. Plan written to: {rel(PLAN_PATH)}")
        print(f"Log written to: {rel(LOG_PATH)}")
        return

    if args.apply or args.force_apply:
        updated, skipped, journal_only = apply_frontmatter_updates(plan, config)
        write_log(plan, updated, skipped, journal_only, dry_run=False)
        print(f"Applied enrichment: full={len(updated)}, journal_only={len(journal_only)}, skipped={len(skipped)}")
        print(f"Log written to: {rel(LOG_PATH)}")
        return

    print("No action specified. Run with --dry-run to review plan, or --apply to update files.")


if __name__ == "__main__":
    main()