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

SCREENING_TO_LEDGER_PARTITION = {
    "confirmed_included": "confirmed_included",
    "metadata_only_duplicate": "metadata_only",
    "metadata_only": "metadata_only",
    "excluded_wrong_scope": "excluded_wrong_scope",
    "skipped_unreadable": "skipped_unreadable",
    "uncertain_needs_review": "uncertain_needs_review",
}


def normalize_partition_entries(entries: Any, partition: str = "partition") -> list[str]:
    """Normalize ledger partition entries to Ref ID strings.

    Accepts both string entries and legacy object entries with ref_id field.
    Returns list of normalized Ref ID strings.
    """
    if not isinstance(entries, list):
        raise ValueError(f"{partition} must be a list, got {type(entries).__name__}")

    normalized: list[str] = []
    for idx, entry in enumerate(entries):
        if isinstance(entry, str):
            ref_id = entry.strip()
            if not ref_id:
                raise ValueError(f"{partition}[{idx}] is an empty Ref ID string")
            normalized.append(ref_id)
        elif isinstance(entry, dict):
            ref_id = entry.get("ref_id")
            if not isinstance(ref_id, str) or not ref_id.strip():
                raise ValueError(
                    f"{partition}[{idx}] legacy object missing non-empty string ref_id: {entry!r}"
                )
            normalized.append(ref_id.strip())
        else:
            raise ValueError(
                f"{partition}[{idx}] expected string Ref ID or legacy object with ref_id, "
                f"got {type(entry).__name__}: {entry!r}"
            )
    return normalized


def build_coverage_ledger(screening_entries: list[dict[str, Any]]) -> tuple[list[str], dict[str, Any] | None]:
    """Build coverage_ledger.json from screening.jsonl entries.

    Returns tuple of (errors, ledger). Unknown decisions produce errors.
    """
    ledger = {
        "candidate_count": len(screening_entries),
        "confirmed_included": [],
        "metadata_only": [],
        "excluded_wrong_scope": [],
        "skipped_unreadable": [],
        "uncertain_needs_review": [],
    }
    errors: list[str] = []
    for entry in screening_entries:
        decision = entry.get("decision") or entry.get("status") or ""
        ref_id = entry.get("ref_id")

        if not decision:
            errors.append(f"Empty decision for ref_id {ref_id or 'unknown'}")
            continue

        if decision not in SCREENING_TO_LEDGER_PARTITION:
            errors.append(f"Unknown screening decision '{decision}' for ref_id {ref_id or 'unknown'}")
            continue

        partition = SCREENING_TO_LEDGER_PARTITION[decision]
        if ref_id:
            ledger[partition].append(ref_id)

    return errors, ledger if not errors else None


def get_confirmed_ids(ledger: dict[str, Any]) -> set[str]:
    """Extract confirmed_included IDs from ledger (handles string or object arrays)."""
    confirmed = ledger.get("confirmed_included", [])
    return set(normalize_partition_entries(confirmed, "confirmed_included"))


def extract_numeric_citations(report_body: str) -> set[int]:
    """Extract unique numeric citation markers from report body (before References section)."""
    grouped = re.findall(r"\[((?:\d+\s*,\s*)*\d+)\]", report_body)
    markers: list[int] = []
    for group in grouped:
        markers.extend(int(part.strip()) for part in group.split(","))
    return set(markers)


def count_reference_entries(reference_section: str) -> int:
    """Count reference entries starting with numeric markers like [1]."""
    return len(re.findall(r"^\[\d+\]\s+", reference_section, re.MULTILINE))


def extract_reference_section(markdown_text: str) -> str:
    """Extract the References/Reference List section from report Markdown."""
    headings = ["## References", "## Reference List", "# References", "# Reference List"]
    for heading in headings:
        if heading in markdown_text:
            start = markdown_text.find(heading)
            remaining = markdown_text[start + len(heading):]
            next_section_match = re.search(r"\n#{1,3} ", remaining)
            if next_section_match:
                return remaining[:next_section_match.start()]
            return remaining
    return ""


def extract_coverage_matrix_refs(
    markdown_text: str,
) -> tuple[set[str], dict[str, int], list[str]]:
    """Extract Ref IDs and citation markers from Paper Coverage Matrix table.

    Returns:
        Tuple of (ref_ids, ref_to_citation, errors)
    """
    # Find matrix section, stopping at next heading
    matrix_start = markdown_text.find("## Paper Coverage Matrix")
    if matrix_start == -1:
        return set(), {}, []

    remaining = markdown_text[matrix_start:]
    next_heading = re.search(r"\n## ", remaining[1:])
    if next_heading:
        matrix_section = remaining[: next_heading.start() + 1]
    else:
        matrix_section = remaining

    ref_ids: set[str] = set()
    ref_to_citation: dict[str, int] = {}
    errors: list[str] = []
    seen_refs: set[str] = set()

    for line in matrix_section.split("\n"):
        if not line.startswith("|") or line.startswith("|---"):
            continue

        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 4:  # Need at least: empty, Ref, Year, Paper
            continue

        ref_cell = cells[1]
        paper_cell = cells[3] if len(cells) > 3 else ""

        ref_match = re.match(r"(R\d+)", ref_cell)
        if not ref_match:
            continue

        ref_id = ref_match.group(1)

        # Check for duplicate Ref IDs
        if ref_id in seen_refs:
            errors.append(f"Duplicate Ref ID in Coverage Matrix: {ref_id}")
            continue
        seen_refs.add(ref_id)
        ref_ids.add(ref_id)

        # Extract citation marker from Paper column
        cite_match = re.search(r"\[(\d+)\]", paper_cell)
        if cite_match:
            ref_to_citation[ref_id] = int(cite_match.group(1))
        else:
            errors.append(f"Missing citation marker for {ref_id} in Coverage Matrix Paper column")

    return ref_ids, ref_to_citation, errors


def validate_count_equality(
    bundle_path: Path,
    report_path: Path | None = None,
) -> tuple[bool, list[str]]:
    """Validate count equality between ledger, citations, coverage matrix, and references."""
    import json
    paths = evidence_file_paths(bundle_path)
    errors: list[str] = []

    ledger_path = paths["coverage_ledger"]
    if not ledger_path.exists():
        return False, ["coverage_ledger.json missing"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

    try:
        confirmed_ids = get_confirmed_ids(ledger)
    except ValueError as e:
        return False, [f"coverage_ledger.json confirmed_included error: {e}"]
    confirmed_count = len(confirmed_ids)

    if report_path is None:
        bundle = load_json(bundle_path)
        output_path_str = bundle.get("output_path", "")
        if output_path_str:
            report_path = ROOT / output_path_str

    if report_path is None or not report_path.exists():
        return False, ["Report Markdown file not found"]
    report_text = report_path.read_text(encoding="utf-8")

    body_before_refs = report_text
    for heading in ["## References", "## Reference List"]:
        if heading in report_text:
            body_before_refs = report_text[:report_text.find(heading)]
            break

    cited_markers = extract_numeric_citations(body_before_refs)
    cited_count = len(cited_markers)

    ref_section = extract_reference_section(report_text)
    ref_count = count_reference_entries(ref_section)

    matrix_refs, matrix_citations, matrix_errors = extract_coverage_matrix_refs(report_text)
    matrix_count = len(matrix_refs)

    # Add matrix parsing errors
    errors.extend(matrix_errors)

    if confirmed_count != cited_count:
        errors.append(f"confirmed_included_count ({confirmed_count}) != unique_cited_paper_count ({cited_count})")
    if confirmed_count != ref_count:
        errors.append(f"confirmed_included_count ({confirmed_count}) != reference_entry_count ({ref_count})")
    if confirmed_count != matrix_count:
        errors.append(f"confirmed_included_count ({confirmed_count}) != coverage_matrix_entry_count ({matrix_count})")

    # Check for missing confirmed papers in matrix
    missing_in_matrix = confirmed_ids - matrix_refs
    if missing_in_matrix:
        errors.append(f"Coverage Matrix missing confirmed refs: {sorted(missing_in_matrix)[:5]}")

    # Check for extra refs in matrix not in confirmed
    extra_in_matrix = matrix_refs - confirmed_ids
    if extra_in_matrix:
        errors.append(f"Coverage Matrix has extra refs not in confirmed: {sorted(extra_in_matrix)[:5]}")

    # Check that all confirmed papers have citation markers
    missing_citations = confirmed_ids - set(matrix_citations.keys())
    if missing_citations:
        errors.append(f"Coverage Matrix missing citation markers for: {sorted(missing_citations)[:5]}")

    return len(errors) == 0, errors


def source_read_command(bundle_path: Path, ref_id: str) -> str:
    """Generate the Agent-safe reading command for a bundle record."""
    return f"python scripts/read_source_for_agent.py --bundle {rel(bundle_path)} --ref-id {ref_id}"


def source_read_quiet_command(bundle_path: Path, ref_id: str) -> str:
    """Generate the quiet Agent-safe reading command (no status output)."""
    return f"python scripts/read_source_for_agent.py --bundle {rel(bundle_path)} --ref-id {ref_id} --quiet"


def image_list_command(bundle_path: Path, ref_id: str) -> str:
    """Generate the image listing command for a bundle record."""
    return f"python scripts/read_source_for_agent.py --bundle {rel(bundle_path)} --ref-id {ref_id} --list-images"


def source_read_batch_size(config: dict[str, Any]) -> int:
    """Get batch size from config with validation and bounds."""
    value = config.get("report_generation", {}).get("source_read_batch_size", 10)
    try:
        size = int(value)
    except (TypeError, ValueError):
        return 10
    return min(max(size, 1), 50)


def source_read_batch_id(ref_ids: list[str]) -> str:
    """Generate batch ID from ref_id range."""
    if not ref_ids:
        return "batch_empty"
    return f"batch_{ref_ids[0]}-{ref_ids[-1]}"


def source_read_batch_command(bundle_path: Path, ref_ids: list[str], batch_index: int) -> str:
    """Generate batch reading command with quiet output."""
    run_key = bundle_path.stem
    refs = ",".join(ref_ids)
    batch_id = source_read_batch_id(ref_ids)
    output_dir = ROOT / "workspace" / "cache" / "agent-safe-source" / run_key / batch_id
    return (
        "python scripts/read_source_for_agent.py "
        f"--bundle {rel(bundle_path)} "
        f"--refs {refs} "
        f"--output-dir {rel(output_dir)} "
        f"--batch-index {batch_index} "
        "--auto-chunk "
        "--auto-chunk-size 50000 "
        "--quiet"
    )


def generate_source_read_batches(
    bundle_path: Path,
    readable_records: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate source_read_batches structure for bundle."""
    batch_size = source_read_batch_size(config)
    ref_ids = [r.get("ref_id", "") for r in readable_records]
    batches = []

    for batch_start in range(0, len(ref_ids), batch_size):
        batch_ref_ids = ref_ids[batch_start:batch_start + batch_size]
        if not batch_ref_ids:
            continue
        batch_index = batch_start // batch_size
        batch_id = source_read_batch_id(batch_ref_ids)
        output_dir = ROOT / "workspace" / "cache" / "agent-safe-source" / bundle_path.stem / batch_id
        batches.append({
            "batch_index": batch_index,
            "batch_id": batch_id,
            "ref_ids": batch_ref_ids,
            "output_dir": rel(output_dir),
            "manifest_path": rel(output_dir / "manifest.json"),
            "source_read_batch_command": source_read_batch_command(bundle_path, batch_ref_ids, batch_index),
        })

    return batches


def evidence_dir_for_bundle(bundle_path: Path) -> Path:
    """Return the evidence directory path for a bundle run."""
    run_key = bundle_path.stem
    return ROOT / "workspace" / "cache" / "report-evidence" / run_key


def evidence_file_paths(bundle_path: Path) -> dict[str, Path]:
    """Return paths to all required evidence files."""
    evidence_dir = evidence_dir_for_bundle(bundle_path)
    return {
        "screening": evidence_dir / "screening.jsonl",
        "paper_notes": evidence_dir / "paper_notes.jsonl",
        "coverage_ledger": evidence_dir / "coverage_ledger.json",
        "synthesis_notes": evidence_dir / "synthesis_notes.md",
        "verification": evidence_dir / "verification.json",
    }


def initialize_evidence_files(bundle_path: Path) -> None:
    """Create evidence directory and initialize empty evidence files."""
    evidence_dir = evidence_dir_for_bundle(bundle_path)
    ensure_dir(evidence_dir)
    paths = evidence_file_paths(bundle_path)

    if not paths["screening"].exists():
        paths["screening"].write_text("# Screening decisions\n# Format: JSON lines\n", encoding="utf-8")
    if not paths["paper_notes"].exists():
        paths["paper_notes"].write_text("# Paper notes\n# Format: JSON lines\n", encoding="utf-8")
    if not paths["coverage_ledger"].exists():
        default_ledger = {
            "candidate_count": 0,
            "confirmed_included": [],
            "metadata_only": [],
            "excluded_wrong_scope": [],
            "skipped_unreadable": [],
            "uncertain_needs_review": [],
        }
        import json
        paths["coverage_ledger"].write_text(json.dumps(default_ledger, indent=2), encoding="utf-8")
    if not paths["synthesis_notes"].exists():
        paths["synthesis_notes"].write_text(
            "# Synthesis Notes\n\n## Method Taxonomy\n\n## Dataset Patterns\n\n## Metric Usage\n\n## Temporal Trends\n\n## Conflicting Findings\n\n## Limitations and Gaps\n",
            encoding="utf-8",
        )
    if not paths["verification"].exists():
        default_verification = {
            "citation_check": "pending",
            "coverage_check": "pending",
            "evidence_consistency_check": "pending",
            "notes": [],
        }
        paths["verification"].write_text(json.dumps(default_verification, indent=2), encoding="utf-8")


def validate_evidence_files(
    bundle_path: Path,
    report_path: Path | None = None,
) -> tuple[bool, list[str]]:
    """Validate evidence files with count equality checks."""
    import json
    paths = evidence_file_paths(bundle_path)
    errors: list[str] = []

    for name, path in paths.items():
        if not path.exists():
            errors.append(f"Missing evidence file: {rel(path)}")
            continue

        content = path.read_text(encoding="utf-8").strip()
        if not content:
            errors.append(f"Empty evidence file: {rel(path)}")
            continue

        if name == "screening":
            entries = []
            parse_errors = []
            file_lines = content.split("\n")
            for line_number, line in enumerate(file_lines, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                try:
                    entry = json.loads(stripped)
                    entries.append(entry)
                except json.JSONDecodeError as e:
                    parse_errors.append(f"screening.jsonl malformed JSON at line {line_number}: {e}")

            if parse_errors:
                errors.extend(parse_errors)
                continue

            if not entries:
                errors.append(f"{name}.jsonl has no data entries")
                continue

            ledger_errors, expected_ledger = build_coverage_ledger(entries)
            errors.extend(ledger_errors)

            ledger_path = paths["coverage_ledger"]
            if ledger_path.exists() and expected_ledger:
                try:
                    actual_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as e:
                    errors.append(f"coverage_ledger.json invalid JSON: {e}")
                    continue

                for partition in [
                    "confirmed_included",
                    "metadata_only",
                    "excluded_wrong_scope",
                    "skipped_unreadable",
                    "uncertain_needs_review",
                ]:
                    try:
                        expected_set = set(
                            normalize_partition_entries(expected_ledger.get(partition, []), partition)
                        )
                    except ValueError as e:
                        errors.append(f"generated coverage ledger {e}")
                        continue

                    try:
                        actual_set = set(
                            normalize_partition_entries(actual_ledger.get(partition, []), partition)
                        )
                    except ValueError:
                        # The coverage_ledger branch reports malformed ledger entries with
                        # file/partition/index context; avoid duplicating that error here.
                        continue

                    if expected_set != actual_set:
                        missing = expected_set - actual_set
                        extra = actual_set - expected_set
                        if missing:
                            errors.append(f"screening-to-ledger mismatch in {partition}: missing {sorted(missing)[:3]}")
                        if extra:
                            errors.append(f"screening-to-ledger mismatch in {partition}: extra {sorted(extra)[:3]}")

                if expected_ledger.get("candidate_count", 0) != actual_ledger.get("candidate_count", 0):
                    errors.append(f"screening-to-ledger mismatch: candidate_count screening ({expected_ledger.get('candidate_count', 0)}) != ledger ({actual_ledger.get('candidate_count', 0)})")

        elif name == "paper_notes":
            lines = [l for l in content.split("\n") if l.strip() and not l.strip().startswith("#")]
            if not lines:
                errors.append(f"{name}.jsonl has no data entries")

        elif name == "coverage_ledger":
            try:
                data = json.loads(content)
                if "candidate_count" not in data:
                    errors.append("coverage_ledger.json missing candidate_count")
                elif not isinstance(data.get("candidate_count"), int) or data["candidate_count"] <= 0:
                    errors.append("coverage_ledger.json candidate_count must be > 0")

                required_lists = [
                    "confirmed_included",
                    "metadata_only",
                    "excluded_wrong_scope",
                    "skipped_unreadable",
                    "uncertain_needs_review",
                ]
                for field in required_lists:
                    if field not in data:
                        errors.append(f"coverage_ledger.json missing {field}")
                    elif not isinstance(data[field], list):
                        errors.append(f"coverage_ledger.json {field} must be a list")
                    else:
                        try:
                            normalize_partition_entries(data[field], field)
                        except ValueError as e:
                            errors.append(f"coverage_ledger.json {e}")

                try:
                    confirmed_ids = get_confirmed_ids(data)
                except ValueError as e:
                    errors.append(f"coverage_ledger.json confirmed_included error: {e}")
                    confirmed_ids = set()

                total_partitioned = sum(
                    len(data.get(field, []))
                    for field in required_lists
                    if isinstance(data.get(field, []), list)
                )
                if total_partitioned != data.get("candidate_count", 0):
                    errors.append(f"coverage_ledger.json partition sum ({total_partitioned}) != candidate_count ({data.get('candidate_count', 0)})")
            except json.JSONDecodeError as e:
                errors.append(f"coverage_ledger.json invalid JSON: {e}")

        elif name == "synthesis_notes":
            lines = [l for l in content.split("\n") if l.strip() and not l.strip().startswith("#")]
            if len(lines) < 3:
                errors.append("synthesis_notes.md has insufficient content")

        elif name == "verification":
            try:
                data = json.loads(content)
                for check in ["citation_check", "coverage_check", "evidence_consistency_check"]:
                    status = data.get(check)
                    if status != "passed":
                        errors.append(f"verification.json {check} not passed (status: {status})")

                confirmed_count = data.get("confirmed_included_count", 0)
                cited_count = data.get("unique_cited_paper_count", 0)
                ref_count = data.get("reference_entry_count", 0)
                matrix_count = data.get("coverage_matrix_entry_count", 0)

                if confirmed_count != cited_count:
                    errors.append(f"verification.json count mismatch: confirmed ({confirmed_count}) != cited ({cited_count})")
                if confirmed_count != ref_count:
                    errors.append(f"verification.json count mismatch: confirmed ({confirmed_count}) != refs ({ref_count})")
                if confirmed_count != matrix_count:
                    errors.append(f"verification.json count mismatch: confirmed ({confirmed_count}) != matrix ({matrix_count})")
            except json.JSONDecodeError as e:
                errors.append(f"verification.json invalid JSON: {e}")

    count_ok, count_errors = validate_count_equality(bundle_path, report_path=report_path)
    if not count_ok:
        errors.extend(count_errors)

    return len(errors) == 0, errors


def source_reading_policy(config: dict[str, Any], args: Any | None = None) -> dict[str, Any]:
    include = bool(config.get("report_generation", {}).get("include_reference_sections", False))
    if args is not None and getattr(args, "include_references", False):
        include = True
    batch_size = source_read_batch_size(config)
    return {
        "include_reference_sections": include,
        "reference_section_headings": DEFAULT_REFERENCE_SECTION_HEADINGS,
        "default_behavior": "include_reference_sections" if include else "skip_reference_sections",
        "agent_safe_reading": True,
        "evidence_pipeline_required": True,
        "preferred_entrypoint": "source_read_batches",
        "fallback_entrypoint": "records[*].source_read_quiet_command",
        "manual_debug_entrypoint": "records[*].source_read_command",
        "batch_size": batch_size,
        "batch_id_style": "ref_range",
        "batch_atomic_write": True,
        "instruction": (
            "**SEQUENTIAL EVIDENCE PIPELINE**\n\n"
            "Stage 1: Execute source_read_batches to create Agent-safe Markdown views.\n\n"
            "Stage 2: For each read paper, append audit decisions to screening.jsonl and evidence notes to paper_notes.jsonl. "
            "Example: {\"ref_id\": \"R001\", \"decision\": \"confirmed_included\", \"doi_prefix\": \"10.1016/j.energy\", \"summary\": \"...\"}\n\n"
            "Stage 3: After all papers read, create validator-compatible coverage_ledger.json with candidate_count, confirmed_included, metadata_only, excluded_wrong_scope, skipped_unreadable, and uncertain_needs_review. "
            "Screening decision metadata_only_duplicate maps into ledger partition metadata_only.\n\n"
            "Checkpoint: Output partition counts before report writing.\n\n"
            "Stage 4: After Stage 3 completes, write report Markdown and synthesis_notes.md.\n\n"
            "Stage 5: Before finalizing, verify count equality and update verification.json with citation_check, coverage_check, and evidence_consistency_check set to passed.\n\n"
            "Stage 6: Run report_family.py --complete. The report is not complete until this passes.\n\n"
            "Required files: screening.jsonl, paper_notes.jsonl, coverage_ledger.json, synthesis_notes.md, verification.json"
            if include
            else "**SEQUENTIAL EVIDENCE PIPELINE**\n\n"
            "Stage 1: Execute source_read_batches to create Agent-safe Markdown views.\n\n"
            "Stage 2: For each read paper, append audit decisions to screening.jsonl and evidence notes to paper_notes.jsonl. "
            "Example: {\"ref_id\": \"R001\", \"decision\": \"confirmed_included\", \"doi_prefix\": \"10.1016/j.energy\", \"summary\": \"...\"}\n\n"
            "Stage 3: After all papers read, create validator-compatible coverage_ledger.json with candidate_count, confirmed_included, metadata_only, excluded_wrong_scope, skipped_unreadable, and uncertain_needs_review. "
            "Screening decision metadata_only_duplicate maps into ledger partition metadata_only.\n\n"
            "Checkpoint: Output partition counts before report writing.\n\n"
            "Stage 4: After Stage 3 completes, write report Markdown and synthesis_notes.md.\n\n"
            "Stage 5: Before finalizing, verify count equality and update verification.json with citation_check, coverage_check, and evidence_consistency_check set to passed.\n\n"
            "Stage 6: Run report_family.py --complete. The report is not complete until this passes.\n\n"
            "Required files: screening.jsonl, paper_notes.jsonl, coverage_ledger.json, synthesis_notes.md, verification.json"
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


def partition_records_by_source(
    records: list[dict[str, Any]],
    bundle_path: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Partition records into readable and skipped, adding safe reading commands.

    This function no longer creates sanitized copies. Instead, it keeps
    original source_path and adds source_read_command for Agent workflows.
    """
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
        normalized["original_source_path"] = rel(source_path)
        if bundle_path:
            normalized["source_read_command"] = source_read_command(bundle_path, ref_id)
            normalized["source_read_quiet_command"] = source_read_quiet_command(bundle_path, ref_id)
            normalized["image_list_command"] = image_list_command(bundle_path, ref_id)
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
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evidence_dir = evidence_dir_for_bundle(cache_path)
    evidence_paths = evidence_file_paths(cache_path)

    source_read_batches = []
    if config and readable_records:
        source_read_batches = generate_source_read_batches(cache_path, readable_records, config)

    return {
        "workflow": workflow,
        "mode": mode,
        "journal": journal,
        "direction": direction,
        "query": query,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "output_path": rel(output_path),
        "cache_path": rel(cache_path),
        "evidence_dir": rel(evidence_dir),
        "evidence_files": {k: rel(v) for k, v in evidence_paths.items()},
        "source_reading": source_reading or {},
        "source_read_batches": source_read_batches,
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
                "original_source_path": str(record.get("original_source_path") or ""),
                "source_read_command": str(record.get("source_read_command") or ""),
                "source_read_quiet_command": str(record.get("source_read_quiet_command") or ""),
                "image_list_command": str(record.get("image_list_command") or ""),
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
