#!/usr/bin/env python3
"""Agent-safe source reading entrypoint.

Demotes remote Markdown image syntax to ordinary links, preventing
Claude API multimodal image handling while preserving URLs.

Supports batch output with per-ref files, auto-chunk for large papers,
and manifest generation for structured Agent workflows.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from common import ROOT, ensure_dir, load_json, rel

DEFAULT_TEMP_PATH = ROOT / "workspace" / "cache" / "agent-safe-source" / "current.md"
MAX_REF_COUNT = 10
MAX_OUTPUT_CHARS = 300000
DEFAULT_AUTO_CHUNK_SIZE = 50000
DEFAULT_MANUAL_CHUNK_SIZE = 20000
MANIFEST_SCHEMA_VERSION = 1


def demote_remote_markdown_images(text: str) -> tuple[str, int]:
    """Convert ![alt](https://...) to [alt](https://...).

    Returns (demoted_text, count_of_demotions).
    """
    count = 0
    result = []

    # State machine approach to handle edge cases
    i = 0
    while i < len(text):
        if text[i:i+2] == "![":
            # Try to parse image syntax
            alt_start = i + 2
            alt_end = text.find("]", alt_start)
            if alt_end == -1:
                result.append(text[i])
                i += 1
                continue

            # Check for parentheses after ]
            paren_start = alt_end + 1
            if paren_start >= len(text) or text[paren_start] != "(":
                result.append(text[i])
                i += 1
                continue

            # Find matching closing paren (handle nested parens)
            paren_depth = 1
            paren_end = paren_start + 1
            while paren_end < len(text) and paren_depth > 0:
                if text[paren_end] == "(":
                    paren_depth += 1
                elif text[paren_end] == ")":
                    paren_depth -= 1
                paren_end += 1

            if paren_depth != 0:
                result.append(text[i])
                i += 1
                continue

            # Extract destination
            dest = text[paren_start + 1:paren_end - 1]

            # Check if remote URL
            if dest.startswith(("http://", "https://", "<http://", "<https://")):
                # Demote: drop the ! prefix
                alt_text = text[alt_start:alt_end]
                result.append(f"[{alt_text}]({dest})")
                count += 1
                i = paren_end
            else:
                # Keep local image syntax unchanged
                result.append(text[i:paren_end])
                i = paren_end
        else:
            result.append(text[i])
            i += 1

    return "".join(result), count


def list_remote_markdown_images(text: str) -> list[dict[str, Any]]:
    """List all remote Markdown images in text."""
    images = []
    lines = text.split("\n")

    for line_num, line in enumerate(lines, start=1):
        i = 0
        while i < len(line):
            if line[i:i+2] == "![":
                alt_start = i + 2
                alt_end = line.find("]", alt_start)
                if alt_end == -1:
                    i += 1
                    continue

                paren_start = alt_end + 1
                if paren_start >= len(line) or line[paren_start] != "(":
                    i += 1
                    continue

                paren_depth = 1
                paren_end = paren_start + 1
                while paren_end < len(line) and paren_depth > 0:
                    if line[paren_end] == "(":
                        paren_depth += 1
                    elif line[paren_end] == ")":
                        paren_depth -= 1
                    paren_end += 1

                if paren_depth != 0:
                    i += 1
                    continue

                paren_content = line[paren_start + 1:paren_end - 1]
                # Parse destination and optional title
                # Format: url or url "title" or url 'title' or <url>
                dest = paren_content
                title = ""

                # Check for quoted title after URL
                if '"' in paren_content:
                    parts = paren_content.split('"', 1)
                    dest = parts[0].strip()
                    if len(parts) > 1:
                        title = parts[1].rstrip('"').strip()
                elif "'" in paren_content:
                    parts = paren_content.split("'", 1)
                    dest = parts[0].strip()
                    if len(parts) > 1:
                        title = parts[1].rstrip("'").strip()

                if dest.startswith(("http://", "https://", "<http://", "<https://")):
                    alt_text = line[alt_start:alt_end]
                    clean_dest = dest.lstrip("<").rstrip(">")
                    images.append({
                        "index": len(images) + 1,
                        "alt": alt_text,
                        "url": clean_dest,
                        "title": title,
                        "line": line_num,
                    })
                i = paren_end
            else:
                i += 1

    return images


def source_mtime_iso(path: Path) -> str:
    """Return source file mtime as UTC ISO string."""
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def source_read_command(bundle_path: Path, ref_id: str) -> str:
    return f"python scripts/read_source_for_agent.py --bundle {rel(bundle_path)} --ref-id {ref_id}"


def image_list_command(bundle_path: Path, ref_id: str) -> str:
    return f"python scripts/read_source_for_agent.py --bundle {rel(bundle_path)} --ref-id {ref_id} --list-images"


def evidence_dir_for_bundle(bundle_path: Path) -> Path:
    run_key = bundle_path.stem
    return ROOT / "workspace" / "cache" / "report-evidence" / run_key


def run_key_from_bundle(bundle_path: Path) -> str:
    return bundle_path.stem


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agent-safe source reading entrypoint")
    parser.add_argument("--source", help="Direct source Markdown path")
    parser.add_argument("--bundle", help="Bundle JSON path")
    parser.add_argument("--ref-id", help="Single record ref_id in bundle")
    parser.add_argument("--refs", help="Comma-separated ref_ids (max 10 without --output-dir)")
    parser.add_argument("--out", help="Output path for safe Markdown (single file mode)")
    parser.add_argument("--output-dir", help="Write one safe Markdown file per ref into this directory")
    parser.add_argument("--batch-size", type=int, default=10, help="Default refs per batch (info only)")
    parser.add_argument("--batch-index", type=int, default=0, help="Batch index for manifest metadata")
    parser.add_argument("--auto-chunk", action="store_true", help="Split per-ref output that exceeds MAX_OUTPUT_CHARS")
    parser.add_argument("--auto-chunk-size", type=int, default=DEFAULT_AUTO_CHUNK_SIZE, help="Chars per auto chunk")
    parser.add_argument("--chunk", type=int, help="Manual chunk number (1-indexed)")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_MANUAL_CHUNK_SIZE, help="Chars per manual chunk")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of file")
    parser.add_argument("--list", action="store_true", help="List bundle records metadata")
    parser.add_argument("--list-images", action="store_true", help="List remote images for ref-id")
    parser.add_argument("--clean-temp", action="store_true", help="Remove temporary safe view")
    parser.add_argument("--quiet", action="store_true", help="Suppress normal status output; print errors only")
    parser.add_argument("--force", action="store_true", help="Bypass limits")
    return parser.parse_args()


def load_bundle_records(bundle_path: Path) -> list[dict[str, Any]]:
    if not bundle_path.exists():
        raise SystemExit(f"Bundle not found: {rel(bundle_path)}")
    bundle = load_json(bundle_path)
    return bundle.get("records", []) or bundle.get("local_records", []) or []


def resolve_source_path(record: dict[str, Any]) -> Path | None:
    sp = record.get("source_path") or record.get("original_source_path")
    if not sp:
        return None
    path = Path(sp)
    return path if path.is_absolute() else ROOT / sp


def read_source_text(source_path: Path) -> str:
    if not source_path.exists():
        raise SystemExit(f"Source not found: {rel(source_path)}")
    return source_path.read_text(encoding="utf-8", errors="replace")


def format_source_header(ref_id: str, title: str) -> str:
    return f"\n<!-- BEGIN_SOURCE {ref_id} title=\"{title}\" -->\n"


def format_source_footer(ref_id: str) -> str:
    return f"\n<!-- END_SOURCE {ref_id} -->\n"


def format_temp_header() -> str:
    return """<!--
Agent-safe temporary source view.
Generated from original Markdown.
Remote images are demoted to ordinary Markdown links.
This file may be overwritten by the next read batch.
-->
"""


def write_batch_manifest(
    output_dir: Path,
    bundle_path: Path | None,
    batch_index: int,
    batch_id: str,
    records_info: list[dict[str, Any]],
    total_chars: int,
    quiet: bool = False,
) -> Path:
    """Write manifest.json for a batch output directory."""
    manifest_path = output_dir / "manifest.json"
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "script": "read_source_for_agent.py",
        "status": "ok",
        "mode": "batch",
        "bundle": rel(bundle_path) if bundle_path else "",
        "batch_index": batch_index,
        "batch_id": batch_id,
        "record_count": len(records_info),
        "total_chars": total_chars,
        "records": records_info,
    }
    ensure_dir(output_dir)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if not quiet:
        print(f"Wrote batch {batch_id}")
        print(f"records={len(records_info)} files={sum(len(r['files']) for r in records_info)} chars={total_chars} manifest={rel(manifest_path)}")
    return manifest_path


def write_single_auto_chunk_manifest(
    output_dir: Path,
    bundle_path: Path | None,
    ref_id: str,
    title: str,
    source_path: Path,
    chars: int,
    chunk_size: int,
    files: list[str],
    quiet: bool = False,
) -> Path:
    """Write manifest.json for single auto-chunk output."""
    manifest_path = output_dir / "manifest.json"
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "script": "read_source_for_agent.py",
        "status": "ok",
        "mode": "single_auto_chunk",
        "bundle": rel(bundle_path) if bundle_path else "",
        "ref_id": ref_id,
        "title": title,
        "source_path": rel(source_path),
        "source_size": chars,
        "source_mtime": source_mtime_iso(source_path),
        "chars": chars,
        "chunk_size": chunk_size,
        "files": files,
    }
    ensure_dir(output_dir)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if not quiet:
        print(f"Auto-chunked {ref_id}")
        print(f"chunks={len(files)} chars={chars} manifest={rel(manifest_path)}")
    return manifest_path


def split_into_chunks(text: str, chunk_size: int) -> list[str]:
    """Split text into chunks of specified size."""
    chunks = []
    for start in range(0, len(text), chunk_size):
        chunks.append(text[start:start + chunk_size])
    return chunks


def atomic_write_batch(
    output_dir: Path,
    source_texts: list[tuple[str, str, str, Path, int]],  # (ref_id, title, safe_text, source_path, demoted_count)
    auto_chunk: bool,
    auto_chunk_size: int,
    bundle_path: Path | None,
    batch_index: int,
    batch_id: str,
    quiet: bool,
) -> list[dict[str, Any]]:
    """Write per-ref files using atomic tmp directory pattern.

    Returns records_info for manifest.
    Raises on any write failure; caller handles cleanup.
    """
    pid = os.getpid()
    tmp_dir = Path(str(output_dir) + f".tmp.{pid}")

    # Clean up any old tmp directories for this target
    for old_tmp in output_dir.parent.glob(output_dir.name + ".tmp.*"):
        try:
            if old_tmp.exists():
                shutil.rmtree(old_tmp)
        except Exception:
            pass  # Ignore cleanup failures; they don't block new writes

    ensure_dir(tmp_dir)
    records_info = []

    try:
        for ref_id, title, safe_text, source_path, demoted_count in source_texts:
            chars = len(safe_text)
            files = []

            if auto_chunk and chars > MAX_OUTPUT_CHARS:
                # Auto-chunk this paper
                chunks = split_into_chunks(safe_text, auto_chunk_size)
                for idx, chunk in enumerate(chunks, start=1):
                    part_path = tmp_dir / f"{ref_id}.part{idx:03d}.md"
                    part_path.write_text(chunk, encoding="utf-8")
                    files.append(rel(output_dir / f"{ref_id}.part{idx:03d}.md"))
            else:
                # Single file
                file_path = tmp_dir / f"{ref_id}.md"
                file_path.write_text(safe_text, encoding="utf-8")
                files.append(rel(output_dir / f"{ref_id}.md"))

            records_info.append({
                "ref_id": ref_id,
                "title": title,
                "source_path": rel(source_path),
                "source_size": chars,
                "source_mtime": source_mtime_iso(source_path),
                "chars": chars,
                "remote_images_demoted": demoted_count,
                "files": files,
            })

        write_batch_manifest(
            output_dir=tmp_dir,
            bundle_path=bundle_path,
            batch_index=batch_index,
            batch_id=batch_id,
            records_info=records_info,
            total_chars=sum(r["chars"] for r in records_info),
            quiet=True,
        )

        # Atomic rename: remove target if exists, then rename tmp
        if output_dir.exists():
            shutil.rmtree(output_dir)
        shutil.move(str(tmp_dir), str(output_dir))

        if not quiet:
            manifest_path = output_dir / "manifest.json"
            print(f"Wrote batch {batch_id}")
            print(f"records={len(records_info)} files={sum(len(r['files']) for r in records_info)} chars={sum(r['chars'] for r in records_info)} manifest={rel(manifest_path)}")

    except Exception as e:
        # Clean up tmp on failure
        if tmp_dir.exists():
            try:
                shutil.rmtree(tmp_dir)
            except Exception:
                pass
        raise e

    return records_info


def process_single_auto_chunk(
    ref_id: str,
    title: str,
    safe_text: str,
    source_path: Path,
    run_key: str,
    auto_chunk_size: int,
    quiet: bool,
    bundle_path: Path | None = None,
) -> None:
    """Handle single paper that exceeds MAX_OUTPUT_CHARS with auto-chunk."""
    chars = len(safe_text)
    output_dir = ROOT / "workspace" / "cache" / "agent-safe-source" / run_key / "single" / ref_id
    pid = os.getpid()
    tmp_dir = Path(str(output_dir) + f".tmp.{pid}")

    # Clean up old tmp directories
    for old_tmp in output_dir.parent.glob(ref_id + ".tmp.*"):
        try:
            if old_tmp.exists():
                shutil.rmtree(old_tmp)
        except Exception:
            pass

    ensure_dir(tmp_dir)
    chunks = split_into_chunks(safe_text, auto_chunk_size)
    files = []

    try:
        for idx, chunk in enumerate(chunks, start=1):
            part_path = tmp_dir / f"{ref_id}.part{idx:03d}.md"
            part_path.write_text(chunk, encoding="utf-8")
            files.append(rel(output_dir / f"{ref_id}.part{idx:03d}.md"))

        write_single_auto_chunk_manifest(
            output_dir=tmp_dir,
            bundle_path=bundle_path,
            ref_id=ref_id,
            title=title,
            source_path=source_path,
            chars=chars,
            chunk_size=auto_chunk_size,
            files=files,
            quiet=True,
        )

        # Atomic rename
        if output_dir.exists():
            shutil.rmtree(output_dir)
        shutil.move(str(tmp_dir), str(output_dir))

        if not quiet:
            manifest_path = output_dir / "manifest.json"
            print(f"Auto-chunked {ref_id}")
            print(f"chunks={len(files)} chars={chars} manifest={rel(manifest_path)}")

    except Exception as e:
        if tmp_dir.exists():
            try:
                shutil.rmtree(tmp_dir)
            except Exception:
                pass
        raise SystemExit(f"Failed to write auto-chunk files: {e}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()

    # Clean temporary file
    if args.clean_temp:
        temp_path = Path(args.out) if args.out else DEFAULT_TEMP_PATH
        if temp_path.exists():
            temp_path.unlink()
            print(f"Removed {rel(temp_path)}")
        return

    # List bundle records
    if args.list and args.bundle:
        bundle_path = Path(args.bundle)
        records = load_bundle_records(bundle_path)
        metadata = []
        for r in records:
            sp = resolve_source_path(r)
            size = 0
            if sp and sp.exists():
                size = len(read_source_text(sp))
            metadata.append({
                "ref_id": r.get("ref_id", ""),
                "title": r.get("title", ""),
                "journal": r.get("journal", r.get("journal_abbr", "")),
                "published_year": r.get("published_year", ""),
                "source_path": rel(sp) if sp else "",
                "size_chars": size,
            })
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        return

    # List images for ref-id
    if args.list_images and args.bundle and args.ref_id:
        bundle_path = Path(args.bundle)
        records = load_bundle_records(bundle_path)
        record = next((r for r in records if r.get("ref_id") == args.ref_id), None)
        if not record:
            raise SystemExit(f"ref_id {args.ref_id} not found in bundle")
        source_path = resolve_source_path(record)
        if not source_path:
            raise SystemExit(f"No source_path for {args.ref_id}")
        text = read_source_text(source_path)
        images = list_remote_markdown_images(text)
        print(json.dumps(images, indent=2, ensure_ascii=False))
        return

    # Determine source paths to read
    source_texts: list[tuple[str, str, str, Path, int]] = []  # (ref_id, title, safe_text, source_path, demoted_count)
    total_demoted = 0
    bundle_path: Path | None = None

    if args.source:
        source_path = Path(args.source)
        text = read_source_text(source_path)
        safe_text, demoted = demote_remote_markdown_images(text)
        total_demoted += demoted
        source_texts.append(("DIRECT", source_path.stem, safe_text, source_path, demoted))

    elif args.bundle:
        bundle_path = Path(args.bundle)
        records = load_bundle_records(bundle_path)

        if args.ref_id:
            record = next((r for r in records if r.get("ref_id") == args.ref_id), None)
            if not record:
                raise SystemExit(f"ref_id {args.ref_id} not found in bundle")
            source_path = resolve_source_path(record)
            if not source_path:
                raise SystemExit(f"No source_path for {args.ref_id}")
            text = read_source_text(source_path)
            safe_text, demoted = demote_remote_markdown_images(text)
            total_demoted += demoted
            source_texts.append((args.ref_id, record.get("title", ""), safe_text, source_path, demoted))

        elif args.refs:
            ref_ids = [r.strip() for r in args.refs.split(",") if r.strip()]
            unavailable: list[str] = []
            # MAX_REF_COUNT only applies without --output-dir
            if not args.output_dir and len(ref_ids) > MAX_REF_COUNT and not args.force:
                raise SystemExit(f"Too many refs ({len(ref_ids)}). Max {MAX_REF_COUNT} without --output-dir or use --force.")
            for ref_id in ref_ids:
                record = next((r for r in records if r.get("ref_id") == ref_id), None)
                if not record:
                    if args.output_dir:
                        unavailable.append(f"{ref_id}=ref_not_found")
                    continue
                source_path = resolve_source_path(record)
                if not source_path:
                    if args.output_dir:
                        unavailable.append(f"{ref_id}=missing_source_path")
                    continue
                if args.output_dir and not source_path.exists():
                    unavailable.append(f"{ref_id}=missing_source_file")
                    continue
                text = read_source_text(source_path)
                safe_text, demoted = demote_remote_markdown_images(text)
                total_demoted += demoted
                source_texts.append((ref_id, record.get("title", ""), safe_text, source_path, demoted))

            if args.output_dir and unavailable:
                raise SystemExit(f"Batch refs unavailable: {', '.join(unavailable)}")
            if args.output_dir and not source_texts:
                raise SystemExit("Batch refs unavailable: no readable refs")

        else:
            raise SystemExit("Bundle mode requires --ref-id or --refs")

    else:
        raise SystemExit("Requires --source or --bundle")

    # Calculate total chars
    total_chars = sum(len(text) for _, _, text, _, _ in source_texts)

    # Batch output mode
    if args.output_dir:
        output_dir = Path(args.output_dir)
        run_key = run_key_from_bundle(bundle_path) if bundle_path else "direct-source"

        # Determine batch_id from output_dir name
        batch_id = output_dir.name

        try:
            records_info = atomic_write_batch(
                output_dir=output_dir,
                source_texts=source_texts,
                auto_chunk=args.auto_chunk,
                auto_chunk_size=args.auto_chunk_size,
                bundle_path=bundle_path,
                batch_index=args.batch_index,
                batch_id=batch_id,
                quiet=args.quiet,
            )

        except Exception as e:
            raise SystemExit(f"Batch write failed: {e}")

        return

    # Check for output size limits
    if total_chars > MAX_OUTPUT_CHARS and not args.force and not args.chunk:
        if args.stdout:
            raise SystemExit(f"Output too large ({total_chars} chars) for stdout. Use --chunk or omit --stdout for auto chunk files.")

        # Single paper auto-chunk fallback
        if len(source_texts) == 1:
            ref_id, title, safe_text, source_path, _demoted_count = source_texts[0]
            run_key = run_key_from_bundle(bundle_path) if bundle_path else "direct-source"
            process_single_auto_chunk(
                ref_id=ref_id,
                title=title,
                safe_text=safe_text,
                source_path=source_path,
                run_key=run_key,
                auto_chunk_size=args.auto_chunk_size,
                quiet=args.quiet,
                bundle_path=bundle_path,
            )
            return

        raise SystemExit(f"Combined output too large ({total_chars} chars). Use --output-dir --auto-chunk for batch reads.")

    # Single file output (traditional mode)
    output_parts = [format_temp_header()]

    for ref_id, title, safe_text, source_path, _demoted_count in source_texts:
        if args.chunk:
            chunk_start = (args.chunk - 1) * args.chunk_size
            chunk_end = chunk_start + args.chunk_size
            safe_text = safe_text[chunk_start:chunk_end]

        output_parts.append(format_source_header(ref_id, title))
        output_parts.append(safe_text)
        output_parts.append(format_source_footer(ref_id))

    output = "".join(output_parts)

    # Output
    if args.stdout:
        print(output)
    else:
        out_path = Path(args.out) if args.out else DEFAULT_TEMP_PATH
        ensure_dir(out_path.parent)
        out_path.write_text(output, encoding="utf-8")
        if not args.quiet:
            print(f"Wrote {rel(out_path)}")
            print(f"records={len(source_texts)} chars={total_chars} remote_images_demoted={total_demoted}")


if __name__ == "__main__":
    main()
