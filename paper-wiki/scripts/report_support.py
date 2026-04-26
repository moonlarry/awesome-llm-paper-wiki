from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from common import ROOT, ensure_dir, load_json, normalize_identity, rel, slugify
from rebuild_indexes import collect_canonical_pages, collect_records


TAG_FIELDS = [
    "tags_task",
    "tags_method",
    "tags_dataset",
    "tags_domain",
    "tags_signal",
    "tags_application",
    "tags_metric",
    "tags_custom",
]

REQUIRED_CANONICAL_FIELDS = [
    "id",
    "title",
    "direction",
    "source_path",
    "journal",
    "journal_abbr",
    "published_date",
    "published_year",
    "doi",
    "url",
    "status",
    "reading_priority",
]

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "based",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "state",
    "study",
    "the",
    "to",
    "using",
    "with",
}

DEFAULT_REFERENCE_SECTION_HEADINGS = [
    "references",
    "reference",
    "bibliography",
    "works cited",
    "literature cited",
    "references and notes",
]


def source_reading_policy(config: dict[str, Any], args: Any | None = None) -> dict[str, Any]:
    include = bool(config.get("report_generation", {}).get("include_reference_sections", False))
    if args is not None and getattr(args, "include_references", False):
        include = True
    return {
        "include_reference_sections": include,
        "reference_section_headings": DEFAULT_REFERENCE_SECTION_HEADINGS,
        "default_behavior": "include_reference_sections" if include else "skip_reference_sections",
        "instruction": (
            "When reading records[*].source_path for report writing, read the full Markdown including References."
            if include
            else "When reading records[*].source_path for report writing, ignore References/Bibliography sections from source papers."
        ),
    }


def today_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def source_index_path(config: dict[str, Any]) -> Path:
    return ROOT / config["paths"]["indexes"] / "papers.json"


def canonical_index_path(config: dict[str, Any]) -> Path:
    return ROOT / config["paths"]["indexes"] / "canonical_pages.json"


def load_source_records(config: dict[str, Any], direction: str | None = None) -> list[dict[str, Any]]:
    path = source_index_path(config)
    records = load_json(path) if path.exists() else collect_records(config)
    return filter_by_direction(records, direction)


def load_canonical_records(config: dict[str, Any], direction: str | None = None) -> list[dict[str, Any]]:
    path = canonical_index_path(config)
    records = load_json(path) if path.exists() else collect_canonical_pages(config)
    return filter_by_direction(records, direction)


def filter_by_direction(records: list[dict[str, Any]], direction: str | None) -> list[dict[str, Any]]:
    if not direction:
        return list(records)
    return [record for record in records if str(record.get("direction") or "") == direction]


def filter_by_journal(records: list[dict[str, Any]], journal: str) -> list[dict[str, Any]]:
    target = normalize_identity(journal)
    return [
        record
        for record in records
        if normalize_identity(str(record.get("journal_abbr") or "")) == target
        or normalize_identity(str(record.get("journal") or "")) == target
    ]


def record_year(record: dict[str, Any]) -> str:
    year = str(record.get("year") or record.get("published_year") or "").strip()
    return year or "n.d."


def year_sort_value(record: dict[str, Any]) -> int:
    try:
        return int(record_year(record))
    except ValueError:
        return 0


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[A-Za-z0-9]+", text.lower())
        if len(token) > 1 and token not in STOPWORDS
    ]


def idea_query(idea_text: str) -> str:
    tokens = tokenize(idea_text)
    return " ".join(tokens[:8]) if tokens else idea_text.strip()


def record_search_blob(record: dict[str, Any]) -> str:
    parts = [
        str(record.get("title") or ""),
        str(record.get("abstract") or ""),
        " ".join(record.get("keywords") or []),
        str(record.get("journal") or ""),
        str(record.get("journal_abbr") or ""),
    ]
    for key in TAG_FIELDS:
        parts.extend(record.get(key) or [])
    return " ".join(parts).lower()


def query_score(record: dict[str, Any], query: str) -> int:
    blob = record_search_blob(record)
    score = 0
    norm_query = query.strip().lower()
    if norm_query and norm_query in blob:
        score += 5
    for token in tokenize(query):
        if token in blob:
            score += 2
    for key in ("tags_task", "tags_method", "tags_domain", "tags_application", "tags_signal"):
        for value in record.get(key) or []:
            value_norm = normalize_identity(str(value))
            if value_norm and value_norm in normalize_identity(query):
                score += 3
    return score


def matched_records(records: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    scored = []
    for record in records:
        score = query_score(record, query)
        if score > 0:
            scored.append((score, record))
    ranked = sorted(
        scored,
        key=lambda item: (-item[0], -year_sort_value(item[1]), item[1]["title"].lower()),
    )
    return [record for _, record in ranked]


def most_common_tags(records: list[dict[str, Any]], key: str, limit: int = 5) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for record in records:
        for value in record.get(key) or []:
            counter[str(value)] += 1
    return counter.most_common(limit)


def year_counts(records: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for record in records:
        counter[record_year(record)] += 1
    return counter


def representative_record(records: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    matches = [record for record in records if value in (record.get(key) or [])]
    if not matches:
        return None
    return sorted(matches, key=paper_rank_key, reverse=True)[0]


def paper_rank_key(record: dict[str, Any]) -> tuple[int, int, int, str]:
    tag_count = sum(len(record.get(key) or []) for key in TAG_FIELDS)
    has_doi = 1 if record.get("doi") else 0
    try:
        year = int(record_year(record))
    except ValueError:
        year = 0
    return (tag_count, has_doi, year, str(record.get("title") or "").lower())


def top_ranked(records: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    return sorted(records, key=paper_rank_key, reverse=True)[:limit]


def ensure_output_path(path: Path) -> None:
    ensure_dir(path.parent)


def report_slug(value: str) -> str:
    return slugify(value, 8)


def report_run_key(mode: str, journal: str | None, direction: str | None, query: str | None) -> str:
    parts = [mode]
    if journal:
        parts.append(report_slug(journal))
    parts.append(report_slug(direction) if direction else "all-directions")
    if query:
        parts.append(report_slug(query))
    return "--".join(parts)


def report_cache_path(
    config: dict[str, Any],
    mode: str,
    journal: str | None,
    direction: str | None,
    query: str | None,
) -> Path:
    del config
    return ROOT / "workspace" / "cache" / "fulltext-report" / f"{report_run_key(mode, journal, direction, query)}.json"


def resolve_record_source_path(record: dict[str, Any]) -> Path | None:
    source_path = str(record.get("source_path") or "").strip()
    if not source_path:
        return None
    path = Path(source_path)
    return path if path.is_absolute() else ROOT / source_path


def compact_skipped_entry(record: dict[str, Any], reason: str, ref_id: str) -> dict[str, Any]:
    return {
        "ref_id": ref_id,
        "source_path": str(record.get("source_path") or ""),
        "reason": reason,
    }


def partition_records_by_source(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    readable: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for idx, record in enumerate(records, start=1):
        ref_id = f"R{idx:03d}"
        source_path = resolve_record_source_path(record)
        if source_path is None:
            skipped.append(compact_skipped_entry(record, "missing_source_path", ref_id))
            continue
        if not source_path.exists():
            skipped.append(compact_skipped_entry(record, "missing_source_file", ref_id))
            continue
        normalized = dict(record)
        normalized["ref_id"] = ref_id
        normalized["source_path"] = rel(source_path)
        readable.append(normalized)
    return readable, skipped


def build_fulltext_run_bundle(
    workflow: str,
    mode: str,
    journal: str | None,
    direction: str | None,
    query: str | None,
    output_path: Path,
    cache_path: Path,
    readable_records: list[dict[str, Any]],
    skipped_records: list[dict[str, Any]],
    source_reading: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "workflow": workflow,
        "mode": mode,
        "journal": journal,
        "direction": direction,
        "query": query,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "output_path": rel(output_path),
        "cache_path": rel(cache_path),
        "source_reading": source_reading or {},
        "selected_count": len(readable_records) + len(skipped_records),
        "readable_count": len(readable_records),
        "skipped_count": len(skipped_records),
        "records": [
            {
                "ref_id": record["ref_id"],
                "title": str(record.get("title") or ""),
                "journal": str(record.get("journal") or record.get("journal_abbr") or ""),
                "published_year": record_year(record),
                "direction": str(record.get("direction") or ""),
                "source_path": str(record.get("source_path") or ""),
                "canonical_path": str(record.get("path") or ""),
                "abstract": str(record.get("abstract") or ""),
                "keywords": list(record.get("keywords") or []),
                "tags_task": list(record.get("tags_task") or []),
                "tags_method": list(record.get("tags_method") or []),
                "tags_dataset": list(record.get("tags_dataset") or []),
                "tags_domain": list(record.get("tags_domain") or []),
                "tags_metric": list(record.get("tags_metric") or []),
                "doi": str(record.get("doi") or ""),
                "url": str(record.get("url") or ""),
            }
            for record in readable_records
        ],
        "skipped": skipped_records,
    }


def build_compact_prep_notes(bundle: dict[str, Any]) -> list[str]:
    return [
        "status=prepared",
        f"selected={bundle['selected_count']}",
        f"readable={bundle['readable_count']}",
        f"skipped={bundle['skipped_count']}",
        f"cache={bundle['cache_path']}",
    ]


def select_journal_fulltext_records(
    config: dict[str, Any],
    journal: str,
    direction: str | None,
    query: str | None,
) -> list[dict[str, Any]]:
    records = load_canonical_records(config)
    records = filter_by_journal(records, journal)
    records = filter_by_direction(records, direction)
    if query:
        records = matched_records(records, query)
    return records


def select_direction_fulltext_records(
    config: dict[str, Any],
    direction: str | None,
    query: str,
) -> list[dict[str, Any]]:
    records = load_canonical_records(config)
    records = filter_by_direction(records, direction)
    return matched_records(records, query)


def read_recent_lines(path: Path, limit: int = 5) -> list[str]:
    if not path.exists():
        return []
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    return lines[-limit:]


def append_report_log(config: dict[str, Any], workflow: str, target: str, output_path: Path, notes: list[str]) -> None:
    log_path = ROOT / config["paths"]["logs"] / "report_generation.md"
    ensure_dir(log_path.parent)
    if not log_path.exists():
        log_path.write_text("# Report Generation Log\n", encoding="utf-8")
    lines = [
        "",
        f"## {today_stamp()} {workflow}",
        "",
        f"- Workflow: `{workflow}`",
        f"- Target: `{target}`",
        f"- Output: `{output_path.as_posix() if output_path.is_absolute() else output_path}`",
    ]
    lines.extend(f"- Notes: {note}" for note in notes)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def append_compact_report_log(
    config: dict[str, Any],
    workflow: str,
    status: str,
    target: str,
    output_path: Path,
    cache_path: Path,
    read_count: int,
    skipped_refs: list[str],
) -> None:
    log_path = ROOT / config["paths"]["logs"] / "report_generation.md"
    ensure_dir(log_path.parent)
    if not log_path.exists():
        log_path.write_text("# Report Generation Log\n", encoding="utf-8")
    skipped_count = len(skipped_refs)
    skipped_label = ", ".join(skipped_refs[:10])
    if skipped_count > 10:
        skipped_label = f"{skipped_label}, +{skipped_count - 10} more" if skipped_label else f"+{skipped_count - 10} more"
    lines = [
        "",
        f"## {today_stamp()} {workflow}",
        "",
        f"- workflow={workflow}",
        f"- status={status}",
        f"- target={target}",
    ]
    if status == "prepared":
        lines.extend(
            [
                f"- selected={read_count + skipped_count}",
                f"- readable={read_count}",
                f"- skipped={skipped_count}",
            ]
        )
    else:
        lines.extend(
            [
                f"- read={read_count}",
                f"- skipped={skipped_count}",
            ]
        )
    lines.extend(
        [
            f"- output={rel(output_path)}",
            f"- cache={rel(cache_path)}",
        ]
    )
    if skipped_label:
        lines.append(f"- skipped_refs={skipped_label}")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


class CitationRegistry:
    def __init__(self) -> None:
        self._numbers: dict[str, int] = {}
        self._records: list[dict[str, Any]] = []

    def cite(self, record: dict[str, Any]) -> str:
        key = str(record.get("path") or record.get("source_path") or record.get("title"))
        if key not in self._numbers:
            self._numbers[key] = len(self._records) + 1
            self._records.append(record)
        return f"[{self._numbers[key]}]"

    def reference_lines(self, heading: str = "## References") -> list[str]:
        lines = [heading, ""]
        if not self._records:
            lines.append("- None")
            lines.append("")
            return lines
        for idx, record in enumerate(self._records, start=1):
            source = str(record.get("source_path") or record.get("path") or "")
            url = str(record.get("url") or "")
            year = record_year(record)
            journal = str(record.get("journal") or record.get("journal_abbr") or "Unknown")
            doi = str(record.get("doi") or "")
            pieces = [f"[{idx}] {record.get('title')}.", f"{journal}, {year}."]
            if doi:
                pieces.append(f"DOI: {doi}.")
            if url:
                pieces.append(f"URL: {url}.")
            pieces.append(f"Source: {source}.")
            lines.append(" ".join(piece for piece in pieces if piece))
            lines.append("")
        return lines
