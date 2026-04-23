from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.json"

STOPWORDS = {"of", "and", "&", "the", "for", "in", "on", "a", "an"}
UNKNOWN_JOURNAL = "UnknownJournal"

_last_arxiv_request_time: float = 0.0


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def http_bytes(url: str, headers: dict[str, str] | None = None, timeout: int = 30) -> bytes:
    headers = headers or {}
    waits = [2, 5, 10]
    for attempt in range(len(waits) + 1):
        request = urllib.request.Request(url, headers={"User-Agent": "paper-llm-wiki/1.0", **headers})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == len(waits):
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = int(retry_after) if retry_after and retry_after.isdigit() else waits[attempt]
            time.sleep(delay)
        except urllib.error.URLError:
            if attempt == len(waits):
                raise
            time.sleep(waits[attempt])
    raise RuntimeError("unreachable")


def http_json(url: str, headers: dict[str, str] | None = None, timeout: int = 30) -> dict[str, Any]:
    data = http_bytes(url, headers=headers, timeout=timeout)
    return json.loads(data.decode("utf-8"))


def http_bytes_arxiv(url: str, timeout: int = 30) -> bytes:
    """Fetch from arXiv API with strict rate limiting (3 seconds between requests)."""
    global _last_arxiv_request_time
    elapsed = time.time() - _last_arxiv_request_time
    if elapsed < 3.0:
        time.sleep(3.0 - elapsed)
    config = load_config()
    email = config.get("web_search", {}).get("openalex_email", "")
    user_agent = "paper-llm-wiki/1.0"
    if email:
        user_agent = f"paper-llm-wiki/1.0 (contact: {email})"
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            _last_arxiv_request_time = time.time()
            return response.read()
    except urllib.error.HTTPError as exc:
        _last_arxiv_request_time = time.time()
        if exc.code == 403:
            raise RuntimeError(f"arXiv API rate limit exceeded (403). Wait before retrying.") from exc
        raise


def read_text(path: Path, limit: int | None = None) -> str:
    data = path.read_text(encoding="utf-8", errors="replace")
    return data if limit is None else data[:limit]


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.S)
    if not match:
        return {}
    fields: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] | None = None
    lines = match.group(1).splitlines()
    i = 0
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.rstrip()
        if not line.strip():
            i += 1
            continue
        if line.lstrip().startswith("- ") and current_key and current_list is not None:
            current_list.append(clean_scalar(line.lstrip()[2:]))
            fields[current_key] = current_list
            i += 1
            continue
        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not key_match:
            i += 1
            continue
        key, value = key_match.group(1), key_match.group(2).strip()
        current_key = key
        if value in {'"', "'"}:
            quote = value
            i += 1
            chunks: list[str] = []
            while i < len(lines):
                part = lines[i].strip()
                if part == quote:
                    break
                if part:
                    chunks.append(part)
                i += 1
            fields[key] = clean_scalar(" ".join(chunks))
            current_list = None
            i += 1
            continue
        if value == "":
            current_list = []
            fields[key] = current_list
        else:
            current_list = None
            fields[key] = clean_scalar(value)
        i += 1
    return fields


def frontmatter_bounds(text: str) -> tuple[int, int] | None:
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.S)
    if not match:
        return None
    return match.start(1), match.end(1)


def strip_frontmatter_block(text: str) -> str:
    match = re.match(r"^---\s*\n.*?\n---\s*(?:\n|$)", text, re.S)
    return text[match.end():] if match else text


def clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def strip_markdown_links(value: str) -> str:
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    return value.strip()


def slugify(value: str, max_words: int = 8) -> str:
    value = strip_markdown_links(value)
    words = re.findall(r"[A-Za-z0-9]+", value.lower())
    words = [word for word in words if word not in STOPWORDS]
    if not words:
        return "paper"
    return "-".join(words[:max_words])


def normalize_identity(value: str) -> str:
    value = strip_markdown_links(value)
    value = re.sub(r"[\W_]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip().lower()


def extract_doi(text: str) -> str | None:
    match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", text, re.I)
    if not match:
        return None
    return match.group(0).rstrip(".,;)")


def extract_arxiv_id(text: str) -> str:
    match = re.search(r"arxiv\.org/(?:abs|html|pdf)/([A-Za-z0-9.\-]+v\d+|[A-Za-z0-9.\-]+)", text, re.I)
    if match:
        return match.group(1).rstrip(".,;)")
    match = re.search(r"\barXiv:\s*([A-Za-z0-9.\-]+v\d+|[A-Za-z0-9.\-]+)", text, re.I)
    return match.group(1).rstrip(".,;)") if match else ""


def arxiv_date_from_id(arxiv_id: str) -> str:
    match = re.match(r"^(\d{2})(\d{2})\.\d+", arxiv_id)
    if not match:
        return ""
    year = int(match.group(1))
    month = int(match.group(2))
    if not 1 <= month <= 12:
        return ""
    century = 2000 if year < 90 else 1900
    return f"{century + year:04d}-{month:02d}"


def extract_year(text: str) -> int | None:
    match = re.search(r"\b(19|20)\d{2}\b", text)
    return int(match.group(0)) if match else None


MONTHS = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}


def extract_published_date(fm: dict[str, Any], text: str) -> str:
    for key in ("published_date", "date", "year"):
        value = str(fm.get(key) or "").strip()
        if re.fullmatch(r"(19|20)\d{2}(?:-\d{1,2})?(?:-\d{1,2})?", value):
            return value
    published_year = str(fm.get("published_year") or "").strip()
    if re.fullmatch(r"(19|20)\d{2}", published_year):
        return published_year
    arxiv_date = arxiv_date_from_id(extract_arxiv_id(str(fm.get("source") or "") or text))
    if arxiv_date:
        return arxiv_date
    month_match = re.search(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+((?:19|20)\d{2})\b",
        text,
        re.I,
    )
    if month_match:
        return f"{month_match.group(2)}-{MONTHS[month_match.group(1).lower()]}"
    year = extract_year(text)
    return str(year) if year else ""


def clean_extracted_text(value: str) -> str:
    value = re.sub(r"\[\[|\]\]", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"^Abstract\s*抽象的", "", value, flags=re.I)
    value = re.sub(r"^\s*Abstract\s*[:：]?\s*", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n,.;")


def extract_frontmatter_abstract(fm: dict[str, Any]) -> str:
    authors = fm.get("author")
    if isinstance(authors, list):
        fragments = [clean_extracted_text(str(item)) for item in authors if str(item).strip()]
        if fragments and any("abstract" in str(item).lower() or "抽象" in str(item) for item in authors[:2]):
            return " ".join(fragment for fragment in fragments if fragment)
    description = str(fm.get("description") or "").strip()
    if description:
        return clean_extracted_text(description)
    return ""


def extract_abstract(text: str, fm: dict[str, Any]) -> str:
    return extract_heading_section(text, "Abstract") or extract_frontmatter_abstract(fm) or "Abstract not available."


def extract_full_text_body(text: str, fm: dict[str, Any]) -> str:
    if str(fm.get("full_text_status") or "") != "full_text_extracted":
        return ""
    body = strip_frontmatter_block(text).strip()
    title = normalize_identity(str(fm.get("title") or ""))
    lines = body.splitlines()
    if lines and lines[0].lstrip().startswith("#"):
        heading = re.sub(r"^#+\s*", "", lines[0]).strip()
        if normalize_identity(heading) == title:
            body = "\n".join(lines[1:]).strip()
    return body


def extract_keywords(text: str) -> list[str]:
    if "## Keywords" not in text:
        return []
    block = text.split("## Keywords", 1)[1]
    block = re.split(r"^##\s+", block, maxsplit=1, flags=re.M)[0]
    keywords: list[str] = []
    for raw_line in block.splitlines():
        line = clean_extracted_text(raw_line.strip(" -•\t"))
        if not line or re.search(r"[\u4e00-\u9fff]", line):
            continue
        if line.lower() in {"keywords", "keyword", "download"}:
            continue
        if len(line) > 90:
            continue
        keywords.append(line)
    deduped: list[str] = []
    seen: set[str] = set()
    for keyword in keywords:
        key = keyword.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(keyword)
    return deduped[:12]


def clean_author_name(value: str) -> str:
    value = strip_markdown_links(value)
    value = re.sub(r"\s+", " ", value).strip(" ,;")
    return value or "Unknown"


def first_author_key(authors: list[str] | str | None) -> str:
    if not authors:
        return "unknown"
    if isinstance(authors, str):
        parts = re.split(r";|, and | and ", authors)
        author = parts[0] if parts else authors
    else:
        author = authors[0] if authors else "unknown"
    author = clean_author_name(author)
    tokens = re.findall(r"[A-Za-z0-9]+", author)
    return (tokens[-1] if tokens else "unknown").lower()


def yaml_quote(value: Any) -> str:
    if value is None:
        return '""'
    text = str(value).replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def yaml_int_or_null(value: Any) -> str:
    text = str(value or "").strip()
    return text if re.fullmatch(r"\d+", text) else "null"


def yaml_list(values: list[str] | None) -> str:
    if not values:
        return "  []"
    return "\n".join(f"  - {yaml_quote(clean_author_name(value))}" for value in values)


def format_yaml_list_field(key: str, values: list[str]) -> str:
    if not values:
        return f"{key}: []"
    lines = [f"{key}:"]
    lines.extend(f"  - {yaml_quote(value)}" for value in values)
    return "\n".join(lines)


def read_frontmatter_list(fm: dict[str, Any], key: str) -> list[str]:
    value = fm.get(key)
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip() and value.strip() != "[]":
        return [value.strip()]
    return []


def replace_frontmatter_field(text: str, key: str, rendered_value: str) -> str:
    bounds = frontmatter_bounds(text)
    if not bounds:
        return text
    start, end = bounds
    fm_text = text[start:end]
    lines = fm_text.splitlines()
    next_lines: list[str] = []
    replaced = False
    i = 0
    while i < len(lines):
        if re.match(rf"^{re.escape(key)}:\s*.*$", lines[i]):
            next_lines.extend(rendered_value.splitlines())
            replaced = True
            i += 1
            while i < len(lines) and re.match(r"^\s+-\s+.*$", lines[i]):
                i += 1
            continue
        next_lines.append(lines[i])
        i += 1
    if not replaced:
        next_lines.append(rendered_value)
    return text[:start] + "\n".join(next_lines).rstrip() + text[end:]


def load_keyword_rules(config: dict[str, Any]) -> list[dict[str, Any]]:
    rules_path = ROOT / config.get("tagging", {}).get("keyword_rules_path", "schema/keyword_rules.json")
    if not rules_path.exists():
        return []
    try:
        raw = json.loads(rules_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    rules = raw.get("rules", [])
    return rules if isinstance(rules, list) else []


def apply_keyword_rules_to_canonical(path: Path, rules: list[dict[str, Any]], dry_run: bool = False) -> list[dict[str, str]]:
    if not rules:
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)
    added: list[dict[str, str]] = []
    updated_text = text
    for rule in rules:
        pattern = str(rule.get("pattern") or "").strip()
        dimension = str(rule.get("dimension") or "").strip()
        tag = str(rule.get("tag") or "").strip()
        if not pattern or not dimension or not tag:
            continue
        try:
            matched = re.search(pattern, text, re.I) is not None
        except re.error:
            continue
        if not matched:
            continue
        key = f"tags_{dimension}"
        values = read_frontmatter_list(fm, key)
        if tag in values:
            continue
        values.append(tag)
        fm[key] = values
        updated_text = replace_frontmatter_field(updated_text, key, format_yaml_list_field(key, values))
        added.append({"dimension": dimension, "tag": tag, "pattern": pattern})
    if added and not dry_run:
        path.write_text(updated_text, encoding="utf-8")
    return added


def extract_heading_section(text: str, heading: str) -> str:
    pattern = rf"^#{{1,6}}\s+{re.escape(heading)}\s*$"
    match = re.search(pattern, text, re.I | re.M)
    if not match:
        return ""
    rest = text[match.end():]
    next_heading = re.search(r"^#{1,6}\s+", rest, re.M)
    section = rest[: next_heading.start()] if next_heading else rest
    return section.strip()


def journal_abbr_from_name(journal: str | None, config: dict[str, Any]) -> str:
    if not journal:
        return config["organize"].get("default_target_for_unknown", UNKNOWN_JOURNAL)
    if journal.lower() == "arxiv":
        return "arxiv"
    aliases = load_aliases(config)
    normalized = normalize_key(journal)
    if normalized in aliases:
        return aliases[normalized]
    return abbr_from_journal_name(journal)


def validate_direction(direction: str, config: dict[str, Any]) -> None:
    """Validate that a direction exists and is configured.

    Raises ValueError with actionable guidance if direction is missing.
    """
    configured = config.get("directions") or []
    if configured and direction not in configured:
        allowed = ", ".join(configured)
        raise ValueError(f"Unknown direction '{direction}'. Allowed directions: {allowed}")
    target = paper_root(config) / direction
    if not target.exists():
        raise ValueError(
            f"Direction folder does not exist: {rel(target)}. "
            f"Create it first: mkdir -p paper/{direction}, or run 'init' workflow."
        )


def existing_identities(direction: str, config: dict[str, Any]) -> set[str]:
    identities: set[str] = set()
    base = paper_root(config) / direction
    if not base.exists():
        return identities
    for md_path in base.rglob("*.md"):
        text = md_path.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        doi = str(fm.get("doi") or "").strip().lower()
        title = str(fm.get("title") or md_path.stem)
        year = str(fm.get("published_year") or fm.get("year") or "")
        if doi:
            identities.add(f"doi:{doi}")
        identities.add(f"title:{normalize_identity(title)}:{year}")
    return identities


def canonical_target_conflicts(candidate: Path, source_path: Path) -> bool:
    if not candidate.exists():
        return False
    text = candidate.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)
    existing_source = str(fm.get("source_path") or "").strip()
    return bool(existing_source and existing_source != rel(source_path))


def canonical_id(source_path: Path, fm: dict[str, Any], config: dict[str, Any]) -> str:
    direction = str(fm.get("direction") or source_path.relative_to(paper_root(config)).parts[0])
    text = source_path.read_text(encoding="utf-8", errors="replace")
    year = str(extract_year(extract_published_date(fm, text)) or fm.get("published_year") or "unknown")
    journal_info = resolve_journal(source_path, config)
    journal_abbr = str(fm.get("journal_abbr") or journal_info.get("journal_abbr") or journal_abbr_from_name(str(fm.get("published") or ""), config))
    title = str(fm.get("title") or source_path.stem)
    base = f"{direction}-{year}-{journal_abbr}"
    papers_dir = ROOT / config["paths"]["papers"] / direction
    slug = slugify(title, 5)
    candidate = papers_dir / f"{base}-{slug}.md"
    if canonical_target_conflicts(candidate, source_path):
        slug = slugify(title, 8)
        candidate = papers_dir / f"{base}-{slug}.md"
    if canonical_target_conflicts(candidate, source_path):
        slug = f"{slug}-{file_sha256(source_path)[:8]}"
    return f"{base}-{slug}"


def preserve_user_notes(existing: str) -> str:
    section = extract_heading_section(existing, "User Notes")
    return section.strip()


def find_canonical_by_source(source_path: Path, direction: str, config: dict[str, Any]) -> Path | None:
    base = ROOT / config["paths"]["papers"] / direction
    if not base.exists():
        return None
    wanted = rel(source_path)
    for candidate in sorted(base.glob("*.md")):
        text = candidate.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        if fm.get("source_path") == wanted:
            return candidate
    return None


def generate_canonical(source_path: Path, config: dict[str, Any]) -> Path:
    """Generate a canonical index page for a paper.

    Canonical pages serve as index anchors linking to source files via `source_path`.
    They contain metadata, tags, abstract, keywords, and user notes — not full text.

    Design principles:
    - Only `## User Notes` is preserved across regenerations.
    - All other content is regenerated from the source file.
    - Full text reading should use `source_path` to access the original file.
    """
    text = source_path.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)
    direction = str(fm.get("direction") or source_path.relative_to(paper_root(config)).parts[0])
    paper_id = canonical_id(source_path, fm, config)
    target = ROOT / config["paths"]["papers"] / direction / f"{paper_id}.md"
    existing_source = target if target.exists() else find_canonical_by_source(source_path, direction, config)
    existing_text = existing_source.read_text(encoding="utf-8", errors="replace") if existing_source else ""
    existing_fm = parse_frontmatter(existing_text)
    existing_notes = preserve_user_notes(existing_text) if existing_text else ""
    ensure_dir(target.parent)
    title = str(fm.get("title") or source_path.stem)
    journal_info = resolve_journal(source_path, config)
    journal = str(fm.get("journal") or journal_info.get("journal") or fm.get("published") or "UnknownJournal")
    journal_abbr = str(fm.get("journal_abbr") or journal_info.get("journal_abbr") or journal_abbr_from_name(journal, config))
    published_date = extract_published_date(fm, text)
    published_year = str(extract_year(published_date) or "")
    doi = str(fm.get("doi") or "")
    if not doi and journal_abbr.lower() != "arxiv":
        doi = str(extract_doi(text) or "")
    url = str(fm.get("source") or "")
    abstract = extract_abstract(text, fm)
    keywords = extract_keywords(text)
    user_notes = existing_notes or "<!-- User-maintained section. Scripts and workflows must NEVER overwrite this section. -->"
    tag_fields = [
        "tags_task",
        "tags_method",
        "tags_dataset",
        "tags_domain",
        "tags_signal",
        "tags_application",
        "tags_metric",
        "tags_custom",
    ]
    rendered_tags = [format_yaml_list_field(field, read_frontmatter_list(existing_fm, field)) for field in tag_fields]
    status = str(existing_fm.get("status") or "unread")
    reading_priority = str(existing_fm.get("reading_priority") or "medium")
    lines = [
        "---",
        f"id: {paper_id}",
        f"title: {yaml_quote(title)}",
        f"direction: {direction}",
        f"source_path: {yaml_quote(rel(source_path))}",
        f"source_checksum: {file_sha256(source_path)}",
        "",
        f"journal: {yaml_quote(journal)}",
        f"journal_abbr: {yaml_quote(journal_abbr)}",
        f"published_date: {yaml_quote(published_date)}",
        f"published_year: {yaml_int_or_null(published_year)}",
        f"doi: {yaml_quote(doi)}",
        f"url: {yaml_quote(url)}",
        "",
        *rendered_tags,
        "",
        f"status: {yaml_quote(status)}",
        f"reading_priority: {yaml_quote(reading_priority)}",
        f"updated_at: {datetime.now().isoformat(timespec='seconds')}",
        "---",
        "",
        f"# {title}",
        "",
        "## Source",
        "",
        f"- **Journal**: {journal} ({journal_abbr})",
        f"- **Year**: {published_year}",
        f"- **DOI**: {'[' + doi + '](https://doi.org/' + doi + ')' if doi else 'N/A'}",
        f"- **URL**: {'[Link](' + url + ')' if url else 'N/A'}",
        "",
        "## Abstract",
        "",
        abstract,
        "",
        "## Keywords",
        "",
        "\n".join(f"- {keyword}" for keyword in keywords) if keywords else "<!-- Keywords not extracted -->",
        "",
        "## User Notes",
        "",
        user_notes,
        "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def rebuild_indexes() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "rebuild_indexes.py")], cwd=ROOT, check=True)


def append_log(message: str, config: dict[str, Any]) -> None:
    log_path = ROOT / config["paths"]["logs"] / "web_search.md"
    ensure_dir(log_path.parent)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(message.rstrip() + "\n")


def is_abbr_like(value: str | None) -> bool:
    if not value:
        return False
    value = value.strip()
    if len(value) > 32 or any(ch.isspace() for ch in value):
        return False
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", value))


def sanitize_dir_name(value: str) -> str:
    value = value.strip()
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or UNKNOWN_JOURNAL


def normalize_key(value: str) -> str:
    value = re.sub(r"[\u4e00-\u9fff]+", " ", value)
    value = value.replace("&", " and ")
    value = re.sub(r"[^A-Za-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def load_aliases(config: dict[str, Any]) -> dict[str, str]:
    alias_path = ROOT / config["journal"]["aliases_path"]
    if not alias_path.exists():
        return {}
    raw = json.loads(alias_path.read_text(encoding="utf-8"))
    aliases: dict[str, str] = {}
    for name, abbr in raw.items():
        aliases[normalize_key(name)] = sanitize_dir_name(str(abbr))
    return aliases


def journal_alias_tokens(name: str) -> list[str]:
    normalized = normalize_key(name)
    stopwords = STOPWORDS | {"journal", "the"}
    return [token for token in normalized.split() if token and token not in stopwords]


def journal_alias_initials(name: str) -> str:
    return "".join(token[0] for token in journal_alias_tokens(name) if token).lower()


def edit_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            current.append(
                min(
                    previous[right_index] + 1,
                    current[right_index - 1] + 1,
                    previous[right_index - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def journal_alias_names_compatible(left: str, right: str) -> bool:
    left_norm = normalize_key(left)
    right_norm = normalize_key(right)
    if left_norm == right_norm:
        return True
    left_tokens = journal_alias_tokens(left)
    right_tokens = journal_alias_tokens(right)
    if left_tokens and right_tokens and set(left_tokens) == set(right_tokens):
        return True
    if left_norm == journal_alias_initials(right) or right_norm == journal_alias_initials(left):
        return True
    if len(left_tokens) == len(right_tokens) == 1 and edit_distance(left_tokens[0], right_tokens[0]) <= 2:
        return True
    return False


def validate_journal_aliases(config: dict[str, Any]) -> list[dict[str, Any]]:
    alias_path = ROOT / config["journal"]["aliases_path"]
    if not alias_path.exists():
        return []
    raw = json.loads(alias_path.read_text(encoding="utf-8"))
    by_abbr: dict[str, list[str]] = {}
    for name, abbr in raw.items():
        clean_abbr = sanitize_dir_name(str(abbr))
        by_abbr.setdefault(clean_abbr, []).append(str(name))

    issues: list[dict[str, Any]] = []
    for abbr, names in sorted(by_abbr.items()):
        unique_names = list(dict.fromkeys(names))
        if len(unique_names) <= 1:
            continue
        base = unique_names[0]
        incompatible = [name for name in unique_names[1:] if not journal_alias_names_compatible(base, name)]
        if not incompatible:
            continue
        issues.append(
            {
                "severity": "error",
                "type": "possible_alias_collision",
                "abbr": abbr,
                "aliases": unique_names,
                "base_alias": base,
                "conflicting_aliases": incompatible,
                "suggested_fix": "Keep the existing journal abbreviation for the first real journal; assign a semantic suffix to later distinct journals.",
            }
        )
    return issues


def known_journal_dirs(direction_path: Path) -> set[str]:
    if not direction_path.exists():
        return set()
    return {p.name for p in direction_path.iterdir() if p.is_dir() and not p.name.startswith(".")}


def abbr_from_journal_name(name: str) -> str:
    cleaned = re.sub(r"[\u4e00-\u9fff]+", " ", name)
    cleaned = cleaned.replace("&", " and ")
    words = re.findall(r"[A-Za-z0-9]+", cleaned)
    words = [w for w in words if w.lower() not in STOPWORDS]
    if not words:
        return UNKNOWN_JOURNAL
    if len(words) == 1:
        return sanitize_dir_name(words[0] if words[0].istitle() else words[0].upper())
    return sanitize_dir_name("".join(w[0].upper() for w in words))


def find_alias_in_text(text: str, aliases: dict[str, str]) -> tuple[str | None, str | None]:
    norm_text = normalize_key(text)
    for alias_key, abbr in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
        if alias_key and alias_key in norm_text:
            return alias_key, abbr
    return None, None


def extract_probable_journal_heading(text: str) -> str | None:
    for raw_line in text.splitlines()[:80]:
        line = raw_line.strip()
        if not line.startswith("## "):
            continue
        heading = line[3:].strip()
        heading = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)
        heading = re.sub(r"[\u4e00-\u9fff].*$", "", heading).strip()
        if not heading:
            continue
        lowered = heading.lower()
        if any(token in lowered for token in ("journal", "transactions", "energy", "reliability", "applied", "arxiv")):
            return heading
    return None


def paper_root(config: dict[str, Any]) -> Path:
    return ROOT / config.get("paper_root", "paper")


def direction_paths(config: dict[str, Any]) -> list[Path]:
    base = paper_root(config)
    web_root = (ROOT / config.get("web_search", {}).get("output_root", "paper/web_search")).resolve()
    configured = config.get("directions") or []
    if configured:
        return [base / name for name in configured if (base / name).exists()]
    if not base.exists():
        return []
    return [p for p in base.iterdir() if p.is_dir() and p.resolve() != web_root]


def resolve_journal(md_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    base = paper_root(config).resolve()
    path = md_path.resolve()
    rel_parts = path.relative_to(base).parts
    direction = rel_parts[0]
    direction_path = base / direction
    parent_folder = rel_parts[1] if len(rel_parts) > 2 else None
    text = read_text(path, limit=160_000)
    fm = parse_frontmatter(text)
    aliases = load_aliases(config)
    known_dirs = known_journal_dirs(direction_path)

    published_raw = str(fm.get("published", "") or "").strip()
    explicit_journal = str(fm.get("journal", "") or "").strip()
    explicit_journal_abbr = str(fm.get("journal_abbr", "") or "").strip()
    title = str(fm.get("title", "") or path.stem).strip()
    source = str(fm.get("source", "") or "").strip()
    source_arxiv_id = extract_arxiv_id(source)

    journal = None
    abbr = None
    source_field = None
    confidence = "low"

    if explicit_journal_abbr:
        abbr = sanitize_dir_name(explicit_journal_abbr)
        journal = explicit_journal or explicit_journal_abbr
        source_field = "frontmatter.journal_abbr"
        confidence = "high"

    if not abbr and explicit_journal:
        journal = explicit_journal
        abbr = journal_abbr_from_name(explicit_journal, config)
        source_field = "frontmatter.journal"
        confidence = "high"

    if not abbr and source_arxiv_id:
        journal = "arXiv"
        abbr = "arxiv"
        source_field = "frontmatter.source.arxiv"
        confidence = "high"

    if not abbr and published_raw:
        candidate = normalize_key(published_raw)
        matching_known_dir = next((name for name in known_dirs if name.lower() == published_raw.lower()), None)
        if candidate in aliases:
            journal = published_raw
            abbr = aliases[candidate]
            source_field = "frontmatter.published.alias"
            confidence = "high"
        elif is_abbr_like(published_raw):
            abbr = sanitize_dir_name(matching_known_dir or published_raw)
            journal = published_raw
            source_field = "frontmatter.published"
            confidence = "high"
        else:
            journal = published_raw
            abbr = abbr_from_journal_name(published_raw)
            source_field = "frontmatter.published.initials"
            confidence = "medium"

    if not abbr and parent_folder and parent_folder in known_dirs:
        abbr = parent_folder
        journal = parent_folder
        source_field = "parent_folder"
        confidence = "medium"

    if not abbr:
        alias_name, alias_abbr = find_alias_in_text(text[:80_000], aliases)
        if alias_abbr:
            abbr = alias_abbr
            journal = alias_name
            source_field = "body.alias"
            confidence = "high"

    if not abbr:
        alias_name, alias_abbr = find_alias_in_text(source, aliases)
        if alias_abbr:
            abbr = alias_abbr
            journal = alias_name
            source_field = "frontmatter.source"
            confidence = "medium"

    if not abbr:
        heading = extract_probable_journal_heading(text)
        if heading:
            journal = heading
            abbr = abbr_from_journal_name(heading)
            source_field = "body.heading.initials"
            confidence = "medium"

    if not abbr:
        abbr = config["organize"].get("default_target_for_unknown", UNKNOWN_JOURNAL)
        journal = None
        source_field = "unknown"
        confidence = "low"

    abbr = sanitize_dir_name(abbr)
    target_path = direction_path / abbr / path.name
    return {
        "direction": direction,
        "path": rel(path),
        "current_journal_folder": parent_folder,
        "title": title,
        "published_raw": published_raw or None,
        "source": source or None,
        "journal": journal,
        "journal_abbr": abbr,
        "journal_source": source_field,
        "journal_confidence": confidence,
        "target_path": rel(target_path),
        "is_direction_root_file": parent_folder is None,
        "checksum": file_sha256(path),
        "size_bytes": path.stat().st_size,
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
    }


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
