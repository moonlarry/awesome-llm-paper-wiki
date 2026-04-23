from __future__ import annotations

import gzip
import html
import io
import re
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from common import (
    ROOT,
    clean_author_name,
    ensure_dir,
    first_author_key,
    generate_canonical,
    http_bytes_arxiv,
    normalize_identity,
    parse_frontmatter,
    paper_root,
    rel,
    slugify,
    yaml_int_or_null,
    yaml_list,
    yaml_quote,
)


@dataclass
class FullTextPayload:
    source: str
    status: str
    markdown: str
    pdf_path: str = ""
    tex_source_path: str = ""
    error: str = ""


class ArxivHTMLToMarkdown(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0
        self.skip_stack: list[str] = []
        self.link: str | None = None
        self.math_depth = 0
        self.equation_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class") or ""
        if self.math_depth:
            self.math_depth += 1
            return
        if tag == "math":
            tex = (attrs_dict.get("alttext") or "").strip()
            display = attrs_dict.get("display") == "block" or tex.startswith(r"\displaystyle") or self.equation_depth > 0
            if tex:
                self.parts.append(format_math_markdown(tex, display))
            self.math_depth = 1
            return
        if tag in {"script", "style", "noscript", "svg"} or tag in {"header", "nav", "footer"}:
            self.skip_depth += 1
            self.skip_stack.append(tag)
            return
        if "ltx_page_footer" in classes or "ltx_dates" in classes or "ltx_tag" in classes:
            self.skip_depth += 1
            self.skip_stack.append(tag)
            return
        if self.skip_depth:
            return
        if tag == "table" and ("ltx_equation" in classes or "ltx_eqn" in classes):
            self.equation_depth += 1
            self.parts.append("\n\n")
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = min(int(tag[1]) + 1, 6)
            self.parts.append("\n\n" + "#" * level + " ")
        elif tag in {"p", "article", "section", "div", "br"}:
            self.parts.append("\n\n")
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag == "tr":
            self.parts.append("\n")
        elif tag in {"td", "th"} and not self.equation_depth:
            self.parts.append(" | ")
        elif tag == "a":
            href = attrs_dict.get("href")
            self.link = href if href and href.startswith("http") else None

    def handle_endtag(self, tag: str) -> None:
        if self.math_depth:
            self.math_depth -= 1
            return
        if self.skip_stack and self.skip_stack[-1] == tag:
            self.skip_depth -= 1
            self.skip_stack.pop()
            return
        if self.skip_depth:
            return
        if tag == "table" and self.equation_depth:
            self.equation_depth -= 1
            self.parts.append("\n\n")
            return
        if tag == "a":
            self.link = None
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth or self.math_depth:
            return
        text = html.unescape(data)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return
        self.parts.append(text)
        if self.link:
            self.parts.append(f" ({self.link})")
        self.parts.append(" ")

    def markdown(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" +", " ", text)
        return text.strip()


def format_math_markdown(tex: str, display: bool) -> str:
    tex = tex.strip()
    tex = re.sub(r"^\\displaystyle\s*", "", tex).strip()
    if display:
        return f"\n\n$$\n{tex}\n$$\n\n"
    return f"${tex}$"


def arxiv_abs_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/abs/{arxiv_id}"


def arxiv_html_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/html/{arxiv_id}"


def arxiv_eprint_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/e-print/{arxiv_id}"


def arxiv_pdf_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/pdf/{arxiv_id}"


def normalize_arxiv_id(arxiv_id: str) -> str:
    arxiv_id = arxiv_id.strip()
    arxiv_id = arxiv_id.replace("https://arxiv.org/abs/", "")
    arxiv_id = arxiv_id.replace("https://arxiv.org/html/", "")
    arxiv_id = arxiv_id.replace("https://arxiv.org/pdf/", "")
    return arxiv_id.strip().strip("/")


def arxiv_id_slug(arxiv_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", normalize_arxiv_id(arxiv_id)).strip("-").lower()


def arxiv_output_dir(config: dict[str, Any], direction: str) -> Path:
    web_config = config.get("web_search", {})
    root = web_config.get("arxiv_output_root") or web_config.get("output_root", "paper/web_search")
    return ROOT / root / direction / "arxiv"


def formal_arxiv_dir(config: dict[str, Any], direction: str) -> Path:
    return paper_root(config) / direction / "arxiv"


def arxiv_assets_dir(config: dict[str, Any], direction: str) -> Path:
    return arxiv_output_dir(config, direction) / "assets"


def existing_arxiv_identities(direction: str, config: dict[str, Any], include_web: bool = True) -> set[str]:
    identities: set[str] = set()
    roots = [paper_root(config) / direction]
    if include_web:
        roots.append(arxiv_output_dir(config, direction))
    for base in roots:
        if not base.exists():
            continue
        for md_path in base.rglob("*.md"):
            text = md_path.read_text(encoding="utf-8", errors="replace")
            fm = parse_frontmatter(text)
            arxiv_id = str(fm.get("arxiv_id") or "").strip().lower()
            doi = str(fm.get("doi") or "").strip().lower()
            title = str(fm.get("title") or md_path.stem)
            year = str(fm.get("published_year") or fm.get("year") or "")
            if arxiv_id:
                identities.add(f"arxiv:{arxiv_id}")
            if doi:
                identities.add(f"doi:{doi}")
            identities.add(f"title:{normalize_identity(title)}:{year}")
    return identities


def fetch_arxiv_html_markdown(arxiv_id: str) -> str:
    data = http_bytes_arxiv(arxiv_html_url(arxiv_id))
    text = data.decode("utf-8", errors="replace")
    parser = ArxivHTMLToMarkdown()
    parser.feed(text)
    markdown = parser.markdown()
    if len(markdown) < 1500:
        raise ValueError("arXiv HTML body is too short to be treated as full text")
    return normalize_markdown_headings(markdown)


def normalize_markdown_headings(markdown: str) -> str:
    markdown = re.sub(r"(?im)^#+\s*abstract\.?\s*$", "## Abstract", markdown)
    markdown = re.sub(r"(?im)^#+\s*(\d+\.?\s+.+)$", r"## \1", markdown)
    markdown = re.sub(r"(?im)^#+\s*references\s*$", "## References", markdown)
    return markdown.strip()


def download_tex_source(arxiv_id: str, assets_dir: Path) -> tuple[Path, bytes]:
    ensure_dir(assets_dir)
    data = http_bytes_arxiv(arxiv_eprint_url(arxiv_id))
    source_path = assets_dir / f"{arxiv_id_slug(arxiv_id)}-source.tar"
    source_path.write_bytes(data)
    return source_path, data


def extract_tex_text(data: bytes) -> str:
    candidates: list[tuple[str, str]] = []
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
            for member in archive.getmembers():
                if not member.isfile() or not member.name.lower().endswith(".tex"):
                    continue
                extracted = archive.extractfile(member)
                if not extracted:
                    continue
                text = extracted.read().decode("utf-8", errors="replace")
                candidates.append((member.name, text))
    except tarfile.TarError:
        try:
            text = gzip.decompress(data).decode("utf-8", errors="replace")
        except OSError:
            text = data.decode("utf-8", errors="replace")
        candidates.append(("source.tex", text))
    if not candidates:
        return ""
    return max(candidates, key=lambda item: len(item[1]))[1]


def tex_to_markdown(tex: str) -> str:
    tex = re.sub(r"(?s)%.*?$", "", tex, flags=re.M)
    abstract = ""
    abstract_match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if abstract_match:
        abstract = clean_tex_text(abstract_match.group(1))
    body = tex
    body = re.sub(r"\\title\{([^{}]+)\}", r"# \1\n", body)
    body = re.sub(r"\\section\*?\{([^{}]+)\}", r"\n## \1\n", body)
    body = re.sub(r"\\subsection\*?\{([^{}]+)\}", r"\n### \1\n", body)
    body = re.sub(r"\\subsubsection\*?\{([^{}]+)\}", r"\n#### \1\n", body)
    body = re.sub(r"\\begin\{abstract\}.*?\\end\{abstract\}", "", body, flags=re.S)
    body = re.sub(r"\\begin\{(?:figure|table|equation|align|align\*)\}.*?\\end\{(?:figure|table|equation|align|align\*)\}", "\n\n[omitted LaTeX environment]\n\n", body, flags=re.S)
    body = clean_tex_text(body)
    chunks = []
    if abstract:
        chunks.extend(["## Abstract", "", abstract, ""])
    chunks.append(body)
    markdown = "\n".join(chunks)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()
    return markdown


def clean_tex_text(text: str) -> str:
    text = re.sub(r"\\cite[tp]?\{[^{}]*\}", "[citation]", text)
    text = re.sub(r"\\ref\{[^{}]*\}", "[ref]", text)
    text = re.sub(r"\\label\{[^{}]*\}", "", text)
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", "", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_arxiv_tex_markdown(arxiv_id: str, assets_dir: Path) -> FullTextPayload:
    source_path, data = download_tex_source(arxiv_id, assets_dir)
    tex = extract_tex_text(data)
    if not tex:
        return FullTextPayload("tex", "tex_saved", "", tex_source_path=rel(source_path), error="No TeX file found in source archive")
    markdown = tex_to_markdown(tex)
    if len(markdown) < 1000:
        return FullTextPayload("tex", "tex_saved", markdown, tex_source_path=rel(source_path), error="Extracted TeX text is short")
    return FullTextPayload("tex", "full_text_extracted", markdown, tex_source_path=rel(source_path))


def fetch_arxiv_pdf(arxiv_id: str, assets_dir: Path) -> FullTextPayload:
    ensure_dir(assets_dir)
    pdf_path = assets_dir / f"{arxiv_id_slug(arxiv_id)}.pdf"
    if not pdf_path.exists():
        pdf_path.write_bytes(http_bytes_arxiv(arxiv_pdf_url(arxiv_id)))
    return FullTextPayload("pdf", "pdf_saved_only", "", pdf_path=rel(pdf_path))


def fetch_arxiv_fulltext(arxiv_id: str, abstract: str, config: dict[str, Any], direction: str) -> FullTextPayload:
    priority = config.get("web_search", {}).get("arxiv_fulltext_priority") or ["html", "tex", "pdf", "api"]
    errors: list[str] = []
    assets_dir = arxiv_assets_dir(config, direction)
    for source in priority:
        try:
            if source == "html":
                markdown = fetch_arxiv_html_markdown(arxiv_id)
                return FullTextPayload("html", "full_text_extracted", markdown)
            if source == "tex":
                payload = fetch_arxiv_tex_markdown(arxiv_id, assets_dir)
                if payload.status == "full_text_extracted":
                    return payload
                errors.append(f"tex: {payload.error or payload.status}")
            if source == "pdf":
                return fetch_arxiv_pdf(arxiv_id, assets_dir)
            if source == "api":
                return FullTextPayload("api", "abstract_only", abstract or "", error="Full text endpoints unavailable")
        except Exception as exc:
            errors.append(f"{source}: {exc}")
    return FullTextPayload("none", "failed", abstract or "", error="; ".join(errors))


def arxiv_filename(result: Any) -> str:
    year = str(result.year or "unknown")
    return f"{year}-{first_author_key(result.authors)}-{slugify(result.title)}-{arxiv_id_slug(result.source_id)}.md"


def arxiv_identity(result: Any) -> str:
    arxiv_id = normalize_arxiv_id(str(result.source_id or ""))
    if arxiv_id:
        return f"arxiv:{arxiv_id.lower()}"
    if result.doi:
        return f"doi:{result.doi.lower()}"
    return f"title:{normalize_identity(result.title)}:{result.year or ''}"


def markdown_for_arxiv_result(result: Any, direction: str, query: str, payload: FullTextPayload) -> str:
    retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
    arxiv_id = normalize_arxiv_id(str(result.source_id or ""))
    year = "" if result.year is None else str(result.year)
    published_date = str(result.submitted_date or "")[:10]
    body = payload.markdown.strip()
    if payload.status == "pdf_saved_only":
        body = "\n".join(
            [
                "## Abstract",
                "",
                result.abstract or "Abstract not available from the arXiv API.",
                "",
                "## Full Text Status",
                "",
                "PDF was downloaded but not converted to Markdown.",
                "",
                f"- PDF: {payload.pdf_path}",
                f"- arXiv: {arxiv_abs_url(arxiv_id)}",
            ]
        )
    elif payload.status in {"abstract_only", "failed"}:
        body = "\n".join(
            [
                "## Abstract",
                "",
                result.abstract or "Abstract not available from the arXiv API.",
                "",
                "## Full Text Status",
                "",
                "Full text could not be fetched from arXiv HTML, TeX, or PDF endpoints. This file contains metadata and abstract only.",
                "",
                f"- Error: {payload.error or 'N/A'}",
            ]
        )
    elif body and not body.lstrip().startswith("#"):
        body = f"# {result.title}\n\n{body}"
    elif not body:
        body = f"# {result.title}\n\n## Abstract\n\n{result.abstract or 'Abstract not available from the arXiv API.'}"

    return "\n".join(
        [
            "---",
            f"title: {yaml_quote(result.title)}",
            "authors:",
            yaml_list([clean_author_name(author) for author in result.authors]),
            'published: "arXiv"',
            f"published_year: {yaml_int_or_null(year)}",
            f"published_date: {yaml_quote(published_date)}",
            f"doi: {yaml_quote(result.doi)}",
            f"source: {yaml_quote(arxiv_abs_url(arxiv_id))}",
            f"arxiv_id: {yaml_quote(arxiv_id)}",
            'web_source: "arxiv"',
            f"direction: {yaml_quote(direction)}",
            'journal_abbr: "arxiv"',
            'source_type: "preprint"',
            'import_status: "web-search-fulltext"',
            f"full_text_source: {yaml_quote(payload.source)}",
            f"full_text_status: {yaml_quote(payload.status)}",
            f"pdf_path: {yaml_quote(payload.pdf_path)}",
            f"tex_source_path: {yaml_quote(payload.tex_source_path)}",
            f"search_query: {yaml_quote(query)}",
            f"created_at: {yaml_quote(retrieved)}",
            "---",
            "",
            body,
            "",
        ]
    )


def write_arxiv_fulltext_result(result: Any, direction: str, query: str, config: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    preview_target = arxiv_output_dir(config, direction) / arxiv_filename(result)
    identity = arxiv_identity(result)
    record = {
        "title": result.title,
        "path": rel(preview_target),
        "identity": identity,
        "web_source": "arxiv",
        "status": "dry-run" if dry_run else "created",
        "storage_layer": "dry-run" if dry_run else None,
        "full_text_source": None,
        "full_text_status": None,
    }
    if dry_run:
        return record
    payload = fetch_arxiv_fulltext(str(result.source_id), result.abstract, config, direction)
    storage_layer = "formal" if payload.status == "full_text_extracted" else "web_search"
    target_dir = formal_arxiv_dir(config, direction) if storage_layer == "formal" else arxiv_output_dir(config, direction)
    target = target_dir / arxiv_filename(result)
    if target.exists():
        record["path"] = rel(target)
        record["status"] = "skipped_existing"
        record["storage_layer"] = storage_layer
        return record
    record["path"] = rel(target)
    record["storage_layer"] = storage_layer
    record["full_text_source"] = payload.source
    record["full_text_status"] = payload.status
    if payload.status == "failed":
        record["error"] = payload.error
    ensure_dir(target.parent)
    target.write_text(markdown_for_arxiv_result(result, direction, query, payload), encoding="utf-8")
    if storage_layer == "formal":
        generate_canonical(target, config)
    return record
