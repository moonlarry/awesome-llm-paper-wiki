from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from common import ROOT, load_config, load_json, rel, write_json
from report_support import (
    CitationRegistry,
    append_compact_report_log,
    append_report_log,
    build_compact_prep_notes,
    build_fulltext_run_bundle,
    ensure_output_path,
    most_common_tags,
    paper_rank_key,
    record_year,
    report_cache_path,
    report_slug,
    select_direction_fulltext_records,
    select_journal_fulltext_records,
    today_stamp,
    top_ranked,
    year_counts,
    partition_records_by_source,
    load_canonical_records,
)
from web_search import run_find


DIMENSION_FIELDS = {
    "task": "tags_task",
    "method": "tags_method",
    "dataset": "tags_dataset",
    "domain": "tags_domain",
    "signal": "tags_signal",
    "application": "tags_application",
    "metric": "tags_metric",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare or generate literature reports from canonical pages.")
    parser.add_argument("--mode", choices=["journal", "direction", "stat"], required=True)
    parser.add_argument("--journal")
    parser.add_argument("--direction")
    parser.add_argument("--query")
    parser.add_argument("--dimension", choices=sorted(DIMENSION_FIELDS))
    parser.add_argument("--cross-dimension", choices=sorted(DIMENSION_FIELDS))
    parser.add_argument("--web", action="store_true")
    parser.add_argument("--top", type=int)
    parser.add_argument("--out")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()

    if args.mode == "journal" and not args.journal:
        parser.error("--mode journal requires --journal")
    if args.mode == "direction" and not args.query:
        parser.error("--mode direction requires --query")
    if args.mode == "stat":
        if not args.direction or not args.dimension:
            parser.error("--mode stat requires --direction and --dimension")
    if args.mode == "direction" and args.web and not args.metadata_only:
        parser.error("--web is only supported with --metadata-only in --mode direction")
    if args.mode == "direction" and args.web and not args.direction:
        parser.error("--web requires --direction")
    return args


def default_output_path(config: dict[str, Any], args: argparse.Namespace) -> Path:
    date = today_stamp()
    reports_root = ROOT / config["paths"]["reports"]
    if args.out:
        return (ROOT / args.out).resolve()
    if args.mode == "journal":
        journal_key = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in args.journal.strip())
        return reports_root / "journal" / f"{journal_key}-report-{date}.md"
    if args.mode == "direction":
        topic_slug = report_slug(args.query)
        return reports_root / "direction" / f"{topic_slug}-report-{date}.md"
    if args.mode == "stat":
        return reports_root / "direction" / f"{args.dimension}-stats-{date}.md"
    raise SystemExit(f"Unsupported mode: {args.mode}")


def journal_label(record: dict[str, Any]) -> str:
    return str(record.get("journal") or record.get("journal_abbr") or "Unknown")


def representative_for_value(records: list[dict[str, Any]], field: str, value: str) -> dict[str, Any] | None:
    matches = [record for record in records if value in (record.get(field) or [])]
    if not matches:
        return None
    return sorted(matches, key=paper_rank_key, reverse=True)[0]


def range_label(records: list[dict[str, Any]]) -> str:
    years = sorted({year for year in (record_year(record) for record in records) if year != "n.d."})
    if not years:
        return "n.d."
    return years[0] if len(years) == 1 else f"{years[0]}-{years[-1]}"


def report_target(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.mode == "journal" and args.journal:
        parts.append(f"journal={args.journal}")
    if args.direction:
        parts.append(f"direction={args.direction}")
    if args.query:
        parts.append(f"query={args.query}")
    if args.mode == "stat" and args.dimension:
        parts.append(f"dimension={args.dimension}")
    return ", ".join(parts) or args.mode


def direction_scope_label(direction: str | None) -> str:
    return direction or "All Directions"


def render_common_tag_table(
    records: list[dict[str, Any]],
    field: str,
    heading: str,
    registry: CitationRegistry,
    limit: int = 5,
) -> list[str]:
    rows = most_common_tags(records, field, limit=limit)
    lines = [heading, "", "| Value | Paper Count | Representative |", "|---|---:|---|"]
    if not rows:
        lines.append("| None | 0 | - |")
        lines.append("")
        return lines
    for value, count in rows:
        rep = representative_for_value(records, field, value)
        cite = registry.cite(rep) if rep else ""
        rep_text = f"{rep['title']} {cite}".strip() if rep else "-"
        lines.append(f"| {value} | {count} | {rep_text} |")
    lines.append("")
    return lines


def render_high_value_table(records: list[dict[str, Any]], registry: CitationRegistry) -> list[str]:
    lines = [
        "## High-Value Papers",
        "",
        "| Paper | Year | Journal | Why Read |",
        "|---|---:|---|---|",
    ]
    chosen = top_ranked(records, limit=5)
    if not chosen:
        lines.append("| None |  |  |  |")
        lines.append("")
        return lines
    for record in chosen:
        cite = registry.cite(record)
        reasons: list[str] = []
        for field, label in (
            ("tags_method", "method coverage"),
            ("tags_dataset", "dataset evidence"),
            ("tags_task", "task anchor"),
        ):
            if record.get(field):
                reasons.append(label)
        reason = ", ".join(reasons[:2]) or "strong canonical metadata coverage"
        lines.append(
            f"| {record['title']} {cite} | {record_year(record)} | {journal_label(record)} | {reason} |"
        )
    lines.append("")
    return lines


def render_gap_lines(records: list[dict[str, Any]]) -> list[str]:
    lines = ["## Research Gaps and Opportunities", ""]
    total = len(records) or 1
    for field, label in (
        ("tags_dataset", "dataset evidence"),
        ("tags_metric", "metric coverage"),
        ("tags_domain", "domain-specific labeling"),
    ):
        missing = sum(1 for record in records if not record.get(field))
        if missing:
            pct = round(missing * 100 / total, 1)
            lines.append(f"- {label} is sparse: {missing}/{len(records)} pages ({pct}%) have no `{field}` values.")
    dominant_methods = most_common_tags(records, "tags_method", limit=1)
    if dominant_methods and dominant_methods[0][1] >= max(3, len(records) // 2):
        lines.append(
            f"- Method concentration is high: `{dominant_methods[0][0]}` appears in {dominant_methods[0][1]} papers, so cross-method comparison is still thin."
        )
    if len(lines) == 2:
        lines.append("- No major structural gaps surfaced from current canonical metadata.")
    lines.append("")
    return lines


def run_web_supplement(config: dict[str, Any], direction: str, query: str, top: int, dry_run: bool) -> dict[str, Any]:
    args = argparse.Namespace(
        command="find",
        positional_query=None,
        query=query,
        direction=direction,
        top=top,
        source="arxiv",
        arxiv_id=None,
        fulltext=True,
        no_fulltext=False,
        no_domain_filter=False,
        show_filtered=False,
        dry_run=dry_run,
    )
    run_find(args)
    if dry_run:
        return {
            "query": query,
            "direction": direction,
            "dry_run": True,
            "created": [],
            "skipped_existing": [],
            "failed": [],
            "filtered_out": [],
            "report": None,
        }
    manifest_path = ROOT / config["paths"]["manifests"] / "arxiv_fulltext_results.json"
    if manifest_path.exists():
        return load_json(manifest_path)
    return {
        "query": query,
        "direction": direction,
        "dry_run": False,
        "created": [],
        "skipped_existing": [],
        "failed": [],
        "filtered_out": [],
        "report": None,
    }


def render_web_section(manifest: dict[str, Any]) -> list[str]:
    created = manifest.get("created") or []
    skipped = manifest.get("skipped_existing") or []
    failed = manifest.get("failed") or []
    filtered = manifest.get("filtered_out") or []
    lines = [
        "## Supplementary Web Evidence",
        "",
        f"- Query: `{manifest.get('query') or ''}`",
        f"- Created: {len(created)}",
        f"- Skipped existing: {len(skipped)}",
        f"- Failed: {len(failed)}",
        f"- Filtered out: {len(filtered)}",
    ]
    if manifest.get("dry_run"):
        lines.append("- Dry run only: no web files were written.")
    if manifest.get("report"):
        lines.append(f"- Web search report: `{manifest['report']}`")
    if created:
        lines.extend(["", "### Newly Saved Web Records", ""])
        for record in created[:5]:
            title = record.get("title") or "Untitled"
            path = record.get("path") or ""
            status = record.get("full_text_status") or record.get("storage_layer") or ""
            lines.append(f"- {title} ({status}) `{path}`")
    lines.append("")
    return lines


def build_journal_metadata_report(config: dict[str, Any], args: argparse.Namespace) -> tuple[list[str], list[str]]:
    records = select_journal_fulltext_records(config, args.journal, args.direction, args.query)
    if not records:
        raise SystemExit(f"No canonical pages matched journal report filters: {report_target(args)}.")
    journal_name = journal_label(records[0])
    registry = CitationRegistry()
    lines = [
        f"# {journal_name} Literature Survey Report",
        "",
        f"> Based on {len(records)} canonical pages | Generated: {today_stamp()}",
        "",
        "## Journal Overview",
        "",
        f"- Journal: {journal_name}",
        f"- Coverage: {range_label(records)}",
        f"- Directions: {', '.join(sorted({str(record.get('direction') or '') for record in records}))}",
    ]
    if args.direction:
        lines.append(f"- Direction filter: {args.direction}")
    if args.query:
        lines.append(f"- Query filter: `{args.query}`")
    lines.append("")
    lines.extend(render_common_tag_table(records, "tags_task", "## Research Hotspot Analysis", registry))
    lines.extend(render_common_tag_table(records, "tags_method", "## Method Landscape", registry))
    lines.extend(render_common_tag_table(records, "tags_dataset", "## Dataset Usage", registry))
    lines.extend(["## Temporal Trends", ""])
    for year, count in sorted(year_counts(records).items()):
        lines.append(f"- {year}: {count} papers")
    lines.append("")
    lines.extend(render_high_value_table(records, registry))
    lines.extend(render_gap_lines(records))
    lines.extend(registry.reference_lines())
    notes = [
        f"target={report_target(args)}",
        f"records={len(records)}",
        "metadata-only deterministic report",
    ]
    return lines, notes


def build_direction_metadata_report(config: dict[str, Any], args: argparse.Namespace) -> tuple[list[str], list[str]]:
    scope_records = load_canonical_records(config, direction=args.direction)
    if not scope_records:
        if args.direction:
            raise SystemExit(f"No canonical pages found for direction '{args.direction}'.")
        raise SystemExit("No canonical pages found for direction report generation.")
    focus = select_direction_fulltext_records(config, args.direction, args.query)
    if not focus:
        raise SystemExit(f"No canonical pages matched query '{args.query}' for {direction_scope_label(args.direction)}.")
    registry = CitationRegistry()
    web_manifest: dict[str, Any] | None = None
    if args.web:
        top = args.top or int(config.get("web_search", {}).get("default_top", 10))
        web_manifest = run_web_supplement(config, args.direction, args.query, top, args.dry_run)
    lines = [
        f"# {direction_scope_label(args.direction)} Research Status Report",
        "",
        f"> Local: {len(focus)} matched | Generated: {today_stamp()}",
        "",
        "## Research Background",
        "",
        f"- Query focus: `{args.query}`",
        f"- Direction scope: {direction_scope_label(args.direction)}",
        f"- Coverage: {range_label(scope_records)}",
        f"- Matched canonical pages: {len(focus)}",
        "",
        "## Core Problem Definition",
        "",
    ]
    for record in focus[:3]:
        cite = registry.cite(record)
        lines.append(f"- {record['title']} {cite} anchors the current local evidence for `{args.query}`.")
    lines.append("")
    lines.extend(render_common_tag_table(focus, "tags_method", "## Method Classification", registry))
    lines.extend(render_common_tag_table(focus, "tags_dataset", "## Datasets and Experimental Design", registry))
    lines.extend(render_high_value_table(focus, registry))
    lines.extend(["## Research Trends", ""])
    hot_methods = most_common_tags(focus, "tags_method", limit=3)
    if hot_methods:
        lines.append("- Hot methods: " + ", ".join(f"{value} ({count})" for value, count in hot_methods))
    hot_tasks = most_common_tags(focus, "tags_task", limit=3)
    if hot_tasks:
        lines.append("- Hot tasks: " + ", ".join(f"{value} ({count})" for value, count in hot_tasks))
    for year, count in sorted(year_counts(focus).items()):
        lines.append(f"- {year}: {count} matched pages")
    lines.append("")
    lines.extend(render_gap_lines(focus))
    if web_manifest is not None:
        lines.extend(render_web_section(web_manifest))
    lines.extend(registry.reference_lines())
    notes = [
        f"target={report_target(args)}",
        f"matched={len(focus)}",
        "metadata-only deterministic report",
    ]
    if web_manifest is not None:
        notes.append(f"web_created={len(web_manifest.get('created') or [])}")
        notes.append("web_search.py find reused as supplementary evidence path")
    return lines, notes


def prepare_journal_fulltext_run(config: dict[str, Any], args: argparse.Namespace, output_path: Path) -> tuple[dict[str, Any], list[str]]:
    records = select_journal_fulltext_records(config, args.journal, args.direction, args.query)
    if not records:
        raise SystemExit(f"No canonical pages matched journal report filters: {report_target(args)}.")
    cache_path = report_cache_path(config, args.mode, args.journal, args.direction, args.query)
    readable_records, skipped_records = partition_records_by_source(records)
    bundle = build_fulltext_run_bundle(
        workflow="journal-report",
        mode=args.mode,
        journal=args.journal,
        direction=args.direction,
        query=args.query,
        output_path=output_path,
        cache_path=cache_path,
        readable_records=readable_records,
        skipped_records=skipped_records,
    )
    return bundle, build_compact_prep_notes(bundle)


def prepare_direction_fulltext_run(config: dict[str, Any], args: argparse.Namespace, output_path: Path) -> tuple[dict[str, Any], list[str]]:
    records = select_direction_fulltext_records(config, args.direction, args.query)
    if not records:
        raise SystemExit(f"No canonical pages matched query '{args.query}' for {direction_scope_label(args.direction)}.")
    cache_path = report_cache_path(config, args.mode, args.journal, args.direction, args.query)
    readable_records, skipped_records = partition_records_by_source(records)
    bundle = build_fulltext_run_bundle(
        workflow="direction-report",
        mode=args.mode,
        journal=args.journal,
        direction=args.direction,
        query=args.query,
        output_path=output_path,
        cache_path=cache_path,
        readable_records=readable_records,
        skipped_records=skipped_records,
    )
    return bundle, build_compact_prep_notes(bundle)


def print_fulltext_dry_run(bundle: dict[str, Any]) -> None:
    print("Dry run: full-text report bundle would be prepared.")
    print(f"selected={bundle['selected_count']}")
    print(f"readable={bundle['readable_count']}")
    print(f"skipped={bundle['skipped_count']}")
    print(f"output={bundle['output_path']}")
    print(f"cache={bundle['cache_path']}")


def build_stat_report(config: dict[str, Any], args: argparse.Namespace) -> tuple[list[str], list[str]]:
    records = load_canonical_records(config, direction=args.direction)
    if not records:
        raise SystemExit(f"No canonical pages found for direction '{args.direction}'.")
    field = DIMENSION_FIELDS[args.dimension]
    cross_dimension = args.cross_dimension or ("method" if args.dimension == "dataset" else "dataset")
    cross_field = DIMENSION_FIELDS[cross_dimension]
    tagged = [record for record in records if record.get(field)]
    registry = CitationRegistry()
    counter = Counter()
    cross_counter: dict[str, Counter[str]] = defaultdict(Counter)
    yearly: dict[str, Counter[str]] = defaultdict(Counter)
    for record in tagged:
        year = record_year(record)
        values = record.get(field) or []
        cross_values = record.get(cross_field) or []
        for value in values:
            counter[value] += 1
            yearly[value][year] += 1
            for cross_value in cross_values:
                cross_counter[value][cross_value] += 1
    top_values = [value for value, _ in counter.most_common(8)]
    lines = [
        f"# {args.dimension.title()} Statistics Report",
        "",
        f"> Based on {len(records)} canonical pages in {args.direction} | Generated: {today_stamp()}",
        "",
        "## Overview",
        "",
        f"- Total papers analyzed: {len(records)}",
        f"- Papers with `{field}` tagged: {len(tagged)}",
        f"- Unique {args.dimension} values: {len(counter)}",
        "",
        "## Frequency Ranking",
        "",
        "| Rank | Value | Paper Count | Proportion | Representative |",
        "|---:|---|---:|---:|---|",
    ]
    if not counter:
        lines.append("| 1 | None | 0 | 0% | - |")
    else:
        total_tagged = max(len(tagged), 1)
        for idx, (value, count) in enumerate(counter.most_common(10), start=1):
            rep = representative_for_value(tagged, field, value)
            cite = registry.cite(rep) if rep else ""
            pct = round(count * 100 / total_tagged, 1)
            lines.append(f"| {idx} | {value} | {count} | {pct}% | {rep['title']} {cite} |")
    lines.extend(["", "## Yearly Trend", ""])
    year_order = sorted({year for year_map in yearly.values() for year in year_map.keys()})
    if year_order and top_values:
        lines.append("| Value | " + " | ".join(year_order) + " | Total |")
        lines.append("|---|" + "|".join("---:" for _ in year_order) + "|---:|")
        for value in top_values[:5]:
            counts = [yearly[value].get(year, 0) for year in year_order]
            lines.append("| " + value + " | " + " | ".join(str(count) for count in counts) + f" | {counter[value]} |")
    else:
        lines.append("- No yearly trend available.")
    lines.extend(["", f"## Cross-Tabulation: {args.dimension} x {cross_dimension}", ""])
    if top_values:
        top_cross_values = Counter()
        for value in top_values[:5]:
            top_cross_values.update(cross_counter[value])
        cross_headers = [value for value, _ in top_cross_values.most_common(5)]
        if cross_headers:
            lines.append("| Value | " + " | ".join(cross_headers) + " | Total |")
            lines.append("|---|" + "|".join("---:" for _ in cross_headers) + "|---:|")
            for value in top_values[:5]:
                counts = [cross_counter[value].get(header, 0) for header in cross_headers]
                lines.append("| " + value + " | " + " | ".join(str(count) for count in counts) + f" | {counter[value]} |")
        else:
            lines.append(f"- No `{cross_field}` values available for cross-tabulation.")
    else:
        lines.append(f"- No `{field}` values available for cross-tabulation.")
    lines.extend(["", "## Key Findings", ""])
    if counter:
        top_value, top_count = counter.most_common(1)[0]
        lines.append(f"- `{top_value}` is the most frequent {args.dimension} value with {top_count} tagged papers.")
        if len(counter) > 1:
            second_value, second_count = counter.most_common(2)[1]
            lines.append(f"- The gap to the next value is {top_count - second_count} papers (`{second_value}` is second).")
    else:
        lines.append("- No usable tags found for this dimension.")
    lines.append("")
    lines.extend(registry.reference_lines())
    notes = [
        f"direction={args.direction}",
        f"dimension={args.dimension}",
        f"tagged={len(tagged)}",
    ]
    return lines, notes


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    config = load_config()
    output_path = default_output_path(config, args)

    if args.mode == "journal" and not args.metadata_only:
        bundle, _ = prepare_journal_fulltext_run(config, args, output_path)
        cache_path = ROOT / bundle["cache_path"]
        if args.dry_run:
            print_fulltext_dry_run(bundle)
            return
        write_json(cache_path, bundle)
        append_compact_report_log(
            config,
            "journal-report",
            "prepared",
            report_target(args),
            output_path,
            cache_path,
            bundle["readable_count"],
            [entry["ref_id"] for entry in bundle["skipped"]],
        )
        print(f"Prepared {rel(cache_path)}")
        return

    if args.mode == "direction" and not args.metadata_only:
        bundle, _ = prepare_direction_fulltext_run(config, args, output_path)
        cache_path = ROOT / bundle["cache_path"]
        if args.dry_run:
            print_fulltext_dry_run(bundle)
            return
        write_json(cache_path, bundle)
        append_compact_report_log(
            config,
            "direction-report",
            "prepared",
            report_target(args),
            output_path,
            cache_path,
            bundle["readable_count"],
            [entry["ref_id"] for entry in bundle["skipped"]],
        )
        print(f"Prepared {rel(cache_path)}")
        return

    if args.mode == "journal":
        lines, notes = build_journal_metadata_report(config, args)
    elif args.mode == "direction":
        lines, notes = build_direction_metadata_report(config, args)
    elif args.mode == "stat":
        lines, notes = build_stat_report(config, args)
    else:
        raise SystemExit(f"Unsupported mode: {args.mode}")

    content = "\n".join(lines).rstrip() + "\n"
    if args.dry_run:
        print(f"Dry run: report would be written to {rel(output_path)}")
        print(content[:1500])
        if len(content) > 1500:
            print("... [truncated preview]")
        return

    ensure_output_path(output_path)
    output_path.write_text(content, encoding="utf-8")
    append_report_log(config, f"{args.mode}-report", report_target(args), output_path, notes)
    print(f"Wrote {rel(output_path)}")


if __name__ == "__main__":
    main()
