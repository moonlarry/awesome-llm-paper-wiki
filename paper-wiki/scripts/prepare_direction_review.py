from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from common import ROOT, ensure_dir, load_config, normalize_identity, rebuild_indexes, rel, validate_direction, write_json
from report_support import (
    append_report_log,
    build_compact_prep_notes,
    load_canonical_records,
    matched_records,
    most_common_tags,
    paper_rank_key,
    partition_records_by_source,
    report_slug,
    today_stamp,
    year_counts,
)
from web_search import collect_results, result_identity, save_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a direction-level literature review bundle from local canonical pages plus web supplementation."
    )
    parser.add_argument("--direction", required=True)
    parser.add_argument("--focus")
    parser.add_argument("--top", type=int)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def review_target(direction: str, focus: str | None) -> str:
    return f"{direction}: {focus}" if focus else direction


def review_slug(direction: str, focus: str | None) -> str:
    parts = [direction]
    if focus:
        parts.append(focus)
    return report_slug(" ".join(parts))


def output_path(config: dict[str, Any], direction: str, focus: str | None) -> Path:
    return ROOT / config["paths"]["reports"] / "review" / f"{review_slug(direction, focus)}-review-{today_stamp()}.md"


def cache_path(direction: str, focus: str | None) -> Path:
    return ROOT / "workspace" / "cache" / "fulltext-review" / f"direction-review--{review_slug(direction, focus)}.json"


def manifest_path(config: dict[str, Any]) -> Path:
    return ROOT / config["paths"]["manifests"] / "direction_review_prepare.json"


def choose_local_records(config: dict[str, Any], direction: str, focus: str | None) -> list[dict[str, Any]]:
    records = load_canonical_records(config, direction=direction)
    if not records:
        raise ValueError(f"No canonical pages found for direction '{direction}'. Run ingest first.")
    if focus:
        records = matched_records(records, focus)
        if not records:
            raise ValueError(
                f"No canonical pages in direction '{direction}' matched focus '{focus}'. Broaden the focus or ingest more papers first."
            )
    return sorted(records, key=paper_rank_key, reverse=True)


def top_tag_values(records: list[dict[str, Any]], key: str, limit: int = 5) -> list[str]:
    return [value for value, _ in most_common_tags(records, key, limit=limit)]


def derive_review_queries(direction: str, focus: str | None, records: list[dict[str, Any]]) -> list[str]:
    queries: list[str] = []
    direction_identity = normalize_identity(direction)

    def add_query(value: str) -> None:
        value = " ".join(value.split()).strip()
        if not value:
            return
        identity = normalize_identity(value)
        if identity and identity not in {normalize_identity(item) for item in queries}:
            queries.append(value)

    if focus:
        focus_identity = normalize_identity(focus)
        add_query(focus if direction_identity and direction_identity in focus_identity else f"{direction} {focus}")
    add_query(direction)

    tasks = top_tag_values(records, "tags_task", limit=2)
    methods = top_tag_values(records, "tags_method", limit=2)
    applications = top_tag_values(records, "tags_application", limit=2)

    if tasks:
        add_query(f"{direction} {tasks[0]}")
    if methods:
        add_query(f"{direction} {methods[0]}")
    elif applications:
        add_query(f"{direction} {applications[0]}")

    return queries[:3]


def report_matches_tokens(path: Path, tokens: list[str]) -> bool:
    target = normalize_identity(path.stem)
    return any(token and token in target for token in tokens)


def related_report_paths(config: dict[str, Any], direction: str, focus: str | None, records: list[dict[str, Any]]) -> dict[str, list[str]]:
    reports_root = ROOT / config["paths"]["reports"]
    focus_token = normalize_identity(focus or "")
    direction_token = normalize_identity(direction)
    tokens = [direction_token]
    if focus_token:
        tokens.append(focus_token)

    journal_tokens = {
        normalize_identity(str(record.get("journal_abbr") or ""))
        for record in records
        if str(record.get("journal_abbr") or "").strip()
    }
    journal_tokens |= {
        normalize_identity(str(record.get("journal") or ""))
        for record in records
        if str(record.get("journal") or "").strip()
    }

    def collect(category: str, extra_tokens: set[str] | None = None, limit: int = 12) -> list[str]:
        category_dir = reports_root / category
        if not category_dir.exists():
            return []
        category_tokens = tokens + sorted(extra_tokens or set())
        matches = [path for path in category_dir.glob("*.md") if report_matches_tokens(path, category_tokens)]
        matches.sort(key=lambda item: item.stat().st_mtime, reverse=True)
        return [rel(path) for path in matches[:limit]]

    return {
        "journal": collect("journal", extra_tokens=journal_tokens),
        "direction": collect("direction"),
        "idea": collect("idea"),
        "web": collect("web"),
    }


def comparison_tables() -> list[dict[str, Any]]:
    return [
        {
            "title": "Scope, Datasets, and Protocols",
            "columns": ["Dataset", "Representative Papers", "Common Tasks", "Common Metrics"],
        },
        {
            "title": "Method Taxonomy Comparison",
            "columns": ["Category", "Representative Methods", "Strengths", "Limitations", "Typical Evidence"],
        },
        {
            "title": "Applications and Deployment Landscape",
            "columns": ["Application", "Representative Papers", "Validation Setting", "Practical Constraints"],
        },
    ]


def review_hints(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "candidate_tasks": top_tag_values(records, "tags_task"),
        "candidate_method_categories": top_tag_values(records, "tags_method"),
        "candidate_datasets": top_tag_values(records, "tags_dataset"),
        "candidate_domains": top_tag_values(records, "tags_domain"),
        "candidate_applications": top_tag_values(records, "tags_application"),
        "candidate_metrics": top_tag_values(records, "tags_metric"),
        "year_distribution": dict(sorted(year_counts(records).items())),
        "suggested_comparison_tables": comparison_tables(),
    }


def local_bundle_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "ref_id": str(record.get("ref_id") or ""),
        "origin": "local",
        "available_for_reading": True,
        "title": str(record.get("title") or ""),
        "journal": str(record.get("journal") or record.get("journal_abbr") or ""),
        "published_year": str(record.get("year") or record.get("published_year") or ""),
        "direction": str(record.get("direction") or ""),
        "source_path": str(record.get("source_path") or ""),
        "canonical_path": str(record.get("path") or ""),
        "abstract": str(record.get("abstract") or ""),
        "keywords": list(record.get("keywords") or []),
        "tags_task": list(record.get("tags_task") or []),
        "tags_method": list(record.get("tags_method") or []),
        "tags_dataset": list(record.get("tags_dataset") or []),
        "tags_domain": list(record.get("tags_domain") or []),
        "tags_application": list(record.get("tags_application") or []),
        "tags_metric": list(record.get("tags_metric") or []),
        "doi": str(record.get("doi") or ""),
        "url": str(record.get("url") or ""),
    }


def web_bundle_record(
    index: int,
    created: dict[str, Any],
    result: Any | None,
    direction: str,
    query: str,
    dry_run: bool,
) -> dict[str, Any]:
    source_path = str(created.get("path") or "")
    absolute_path = ROOT / source_path if source_path else None
    available = False if dry_run else bool(absolute_path and absolute_path.exists())
    title = str(created.get("title") or (result.title if result else ""))
    return {
        "ref_id": f"W{index:03d}",
        "origin": "web",
        "available_for_reading": available,
        "preview_only": dry_run,
        "title": title,
        "journal": str(result.journal if result else ""),
        "published_year": str(result.year if result and result.year else ""),
        "direction": direction,
        "source_path": source_path,
        "canonical_path": "",
        "abstract": str(result.abstract if result else ""),
        "keywords": [],
        "tags_task": [],
        "tags_method": [],
        "tags_dataset": [],
        "tags_domain": [],
        "tags_application": [],
        "tags_metric": [],
        "doi": str(result.doi if result else ""),
        "url": str(result.url if result else ""),
        "web_source": str(created.get("web_source") or (result.web_source if result else "")),
        "storage_layer": str(created.get("storage_layer") or ""),
        "identity": str(created.get("identity") or ""),
        "full_text_status": str(created.get("full_text_status") or ""),
        "search_query": query,
        "status": str(created.get("status") or ""),
    }


def web_query_args(direction: str, query: str, top: int, dry_run: bool) -> argparse.Namespace:
    return argparse.Namespace(
        direction=direction,
        query=query,
        top=top,
        source="mixed",
        arxiv_id=None,
        fulltext=False,
        no_fulltext=False,
        no_domain_filter=False,
        show_filtered=False,
        dry_run=dry_run,
    )


def prepare_web_records(
    config: dict[str, Any],
    direction: str,
    queries: list[str],
    top: int,
    dry_run: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str], bool]:
    if not queries or top <= 0:
        return [], [], [], [], [], False

    web_records: list[dict[str, Any]] = []
    query_logs: list[dict[str, Any]] = []
    notices: list[str] = []
    filtered_samples: list[dict[str, Any]] = []
    seen_identities: set[str] = set()
    any_formal_created = False
    used_queries: list[str] = []
    base = top // len(queries)
    remainder = top % len(queries)

    for idx, query in enumerate(queries):
        query_top = base + (1 if idx < remainder else 0)
        if query_top <= 0:
            continue
        used_queries.append(query)
        args = web_query_args(direction, query, query_top, dry_run)
        accepted, filtered_out, query_notices = collect_results(args, config)
        saved = save_results(accepted, args, config)
        by_identity = {result_identity(result): result for result in accepted}
        created_count = 0
        for created in saved["created"]:
            identity = str(created.get("identity") or "")
            if identity in seen_identities:
                continue
            seen_identities.add(identity)
            created_count += 1
            if created.get("storage_layer") == "formal" and not dry_run:
                any_formal_created = True
            web_records.append(
                web_bundle_record(
                    index=len(web_records) + 1,
                    created=created,
                    result=by_identity.get(identity),
                    direction=direction,
                    query=query,
                    dry_run=dry_run,
                )
            )

        notices.extend(query_notices)
        filtered_samples.extend(filtered_out[: min(5, len(filtered_out))])
        query_logs.append(
            {
                "query": query,
                "top": query_top,
                "accepted_count": len(accepted),
                "created_count": created_count,
                "skipped_existing_count": len(saved["skipped_existing"]),
                "failed_count": len(saved["failed"]),
                "filtered_out_count": len(filtered_out),
                "notices": query_notices,
            }
        )

    return web_records, query_logs, filtered_samples[:15], notices, used_queries, any_formal_created


def build_bundle(
    direction: str,
    focus: str | None,
    output: Path,
    cache: Path,
    local_records: list[dict[str, Any]],
    web_records: list[dict[str, Any]],
    skipped_records: list[dict[str, Any]],
    context_paths: dict[str, list[str]],
    hints: dict[str, Any],
    query_logs: list[dict[str, Any]],
    notices: list[str],
    dry_run: bool,
) -> dict[str, Any]:
    readable_web = [record for record in web_records if record.get("available_for_reading")]
    return {
        "workflow": "direction-review",
        "mode": "agent-prep",
        "direction": direction,
        "focus": focus,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dry_run": dry_run,
        "output_path": rel(output),
        "cache_path": rel(cache),
        "selected_count": len(local_records) + len(web_records) + len(skipped_records),
        "readable_count": len(local_records) + len(readable_web),
        "skipped_count": len(skipped_records) + (len(web_records) - len(readable_web)),
        "local_count": len(local_records),
        "web_count": len(web_records),
        "records": local_records + readable_web,
        "local_records": local_records,
        "web_records": web_records,
        "skipped": skipped_records,
        "context_reports": context_paths,
        "review_hints": hints,
        "web_search": {
            "queries": [item["query"] for item in query_logs],
            "runs": query_logs,
            "notices": notices,
        },
        "writing_rules": {
            "fulltext_first": True,
            "local_reports_are_secondary_context": True,
            "dynamic_taxonomy_required": True,
            "forbid_preset_domain_subsections": True,
            "require_limitations_per_method_category": True,
            "require_comparison_table_per_major_section": True,
            "default_review_depth": "standard",
            "standard_reference_target_range": "40-80",
            "deep_review_reference_target_range": "80-120",
        },
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    config = load_config()
    validate_direction(args.direction, config)

    local_selected = choose_local_records(config, args.direction, args.focus)
    readable_local, skipped_local = partition_records_by_source(local_selected)
    if not readable_local:
        raise SystemExit(
            f"No readable source markdown files found for direction '{args.direction}'. Check source_path values or run ingest again."
        )

    top = args.top or int(config.get("web_search", {}).get("default_top", 10))
    queries = derive_review_queries(args.direction, args.focus, readable_local)
    web_records, query_logs, filtered_samples, notices, used_queries, any_formal_created = prepare_web_records(
        config=config,
        direction=args.direction,
        queries=queries,
        top=top,
        dry_run=args.dry_run,
    )

    if any_formal_created and not args.dry_run:
        rebuild_indexes()

    output = output_path(config, args.direction, args.focus)
    cache = cache_path(args.direction, args.focus)
    manifest = manifest_path(config)
    ensure_dir(output.parent)
    ensure_dir(cache.parent)
    ensure_dir(manifest.parent)

    bundle = build_bundle(
        direction=args.direction,
        focus=args.focus,
        output=output,
        cache=cache,
        local_records=[local_bundle_record(record) for record in readable_local],
        web_records=web_records,
        skipped_records=skipped_local,
        context_paths=related_report_paths(config, args.direction, args.focus, readable_local),
        hints=review_hints(readable_local),
        query_logs=query_logs,
        notices=notices,
        dry_run=args.dry_run,
    )
    write_json(cache, bundle)

    summary = {
        "workflow": "direction-review",
        "direction": args.direction,
        "focus": args.focus,
        "dry_run": args.dry_run,
        "output_path": rel(output),
        "cache_path": rel(cache),
        "counts": {
            "local_readable": len(readable_local),
            "local_skipped": len(skipped_local),
            "web_records": len(web_records),
            "web_readable": sum(1 for record in web_records if record.get("available_for_reading")),
            "web_preview_only": sum(1 for record in web_records if not record.get("available_for_reading")),
        },
        "queries": used_queries,
        "filtered_samples": filtered_samples,
        "context_reports": bundle["context_reports"],
        "review_hints": bundle["review_hints"],
        "notices": notices,
    }
    write_json(manifest, summary)

    notes = build_compact_prep_notes(bundle)
    notes.append(f"local_readable={len(readable_local)}")
    notes.append(f"web_records={len(web_records)}")
    if used_queries:
        notes.append("queries=" + " | ".join(used_queries))
    append_report_log(
        config=config,
        workflow="direction-review",
        target=review_target(args.direction, args.focus),
        output_path=output,
        notes=notes,
    )

    print(
        f"Prepared direction-review bundle: local readable {len(readable_local)}, "
        f"local skipped {len(skipped_local)}, web records {len(web_records)}."
    )
    print(f"Bundle: {rel(cache)}")
    print(f"Manifest: {rel(manifest)}")
    print(f"Final report target: {rel(output)}")
    if args.dry_run:
        print("Dry run: final review markdown was not written; web preview records may not yet exist on disk.")


if __name__ == "__main__":
    main()
