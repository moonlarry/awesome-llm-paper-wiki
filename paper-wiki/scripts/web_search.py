from __future__ import annotations

import argparse
import math
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from common import (
    ROOT,
    append_log,
    ensure_dir,
    existing_identities,
    first_author_key,
    http_json,
    http_bytes,
    http_bytes_arxiv,
    journal_abbr_from_name,
    load_config,
    normalize_identity,
    rel,
    rebuild_indexes,
    slugify,
    validate_direction,
    write_json,
    yaml_int_or_null,
    yaml_list,
    yaml_quote,
)
from arxiv_fulltext import (
    arxiv_identity,
    existing_arxiv_identities,
    write_arxiv_fulltext_result,
)


@dataclass
class PaperResult:
    title: str
    authors: list[str]
    year: int | None
    journal: str
    doi: str
    url: str
    abstract: str
    web_source: str
    citation_count: int | None
    source_type: str
    source_id: str
    submitted_date: str = ""


@dataclass
class RankedResult:
    result: PaperResult
    api_rank: int
    domain_match: dict[str, Any]
    score: float


def abstract_from_inverted(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, offsets in index.items():
        for offset in offsets:
            positions.append((offset, word))
    return " ".join(word for _, word in sorted(positions))


def fetch_openalex(query: str, top: int, config: dict[str, Any], min_citations: int, sort: str = "cited_by_count:desc") -> list[PaperResult]:
    params = {
        "search": query,
        "select": "id,title,authorships,publication_year,cited_by_count,primary_location,doi,abstract_inverted_index,ids,open_access",
        "per-page": str(max(20, top * 3)),
        "sort": sort,
    }
    if min_citations > 0:
        params["filter"] = f"cited_by_count:>{min_citations}"
    email = config.get("web_search", {}).get("openalex_email")
    api_key = config.get("web_search", {}).get("openalex_api_key")
    if email:
        params["mailto"] = email
    if api_key:
        params["api_key"] = api_key
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    payload = http_json(url)
    results: list[PaperResult] = []
    for item in payload.get("results", []):
        title = item.get("title") or "Untitled"
        authors = []
        for authorship in item.get("authorships") or []:
            name = (authorship.get("author") or {}).get("display_name")
            if name:
                authors.append(name)
        location = item.get("primary_location") or {}
        source = location.get("source") or {}
        journal = source.get("display_name") or "UnknownJournal"
        ids = item.get("ids") or {}
        doi = (item.get("doi") or ids.get("doi") or "").replace("https://doi.org/", "")
        landing = location.get("landing_page_url") or ids.get("doi") or item.get("id") or ""
        results.append(
            PaperResult(
                title=title,
                authors=authors,
                year=item.get("publication_year"),
                journal=journal,
                doi=doi,
                url=landing,
                abstract=abstract_from_inverted(item.get("abstract_inverted_index")),
                web_source="openalex",
                citation_count=item.get("cited_by_count"),
                source_type="journal",
                source_id=item.get("id") or "",
            )
        )
    return results


def fetch_openalex_classic(query: str, top: int, config: dict[str, Any], min_citations: int) -> list[PaperResult]:
    return fetch_openalex(query, top, config, min_citations, sort="cited_by_count:desc")


def fetch_openalex_recent(query: str, top: int, config: dict[str, Any]) -> list[PaperResult]:
    return fetch_openalex(query, top, config, 0, sort="publication_date:desc")


def fetch_semantic_scholar(query: str, top: int, config: dict[str, Any]) -> list[PaperResult]:
    api_key = config.get("web_search", {}).get("semantic_scholar_api_key")
    if not api_key:
        return []
    params = {
        "query": query,
        "fields": "title,authors,year,citationCount,venue,externalIds,abstract,url",
        "limit": str(max(20, top * 2)),
    }
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params)
    payload = http_json(url, headers={"x-api-key": api_key})
    results: list[PaperResult] = []
    for item in payload.get("data", []):
        external = item.get("externalIds") or {}
        doi = external.get("DOI") or ""
        arxiv_id = external.get("ArXiv") or ""
        results.append(
            PaperResult(
                title=item.get("title") or "Untitled",
                authors=[author.get("name") for author in item.get("authors", []) if author.get("name")],
                year=item.get("year"),
                journal=item.get("venue") or ("arXiv" if arxiv_id else "UnknownJournal"),
                doi=doi,
                url=item.get("url") or (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""),
                abstract=item.get("abstract") or "",
                web_source="semanticscholar",
                citation_count=item.get("citationCount"),
                source_type="preprint" if arxiv_id else "journal",
                source_id=item.get("paperId") or arxiv_id,
            )
        )
    return results


def fetch_arxiv(query: str, top: int, search_query: str | None = None) -> list[PaperResult]:
    params = {
        "search_query": search_query or f"all:{query}",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max(10, top * 2)),
    }
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
    root = ET.fromstring(http_bytes_arxiv(url))
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    results: list[PaperResult] = []
    for entry in root.findall("atom:entry", ns):
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ns) or "Untitled").split())
        abstract = " ".join((entry.findtext("atom:summary", default="", namespaces=ns) or "").split())
        published = entry.findtext("atom:published", default="", namespaces=ns) or ""
        year = int(published[:4]) if published[:4].isdigit() else None
        authors = [
            author.findtext("atom:name", default="", namespaces=ns)
            for author in entry.findall("atom:author", ns)
        ]
        authors = [author for author in authors if author]
        doi = entry.findtext("arxiv:doi", default="", namespaces=ns) or ""
        arxiv_id = (entry.findtext("atom:id", default="", namespaces=ns) or "").rsplit("/", 1)[-1]
        url_abs = entry.findtext("atom:id", default="", namespaces=ns) or ""
        results.append(
            PaperResult(
                title=title,
                authors=authors,
                year=year,
                journal="arXiv",
                doi=doi,
                url=url_abs,
                abstract=abstract,
                web_source="arxiv",
                citation_count=None,
                source_type="preprint",
                source_id=arxiv_id,
                submitted_date=published,
            )
        )
    return results


def fetch_arxiv_by_id(arxiv_id: str) -> PaperResult:
    params = {"id_list": arxiv_id}
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
    root = ET.fromstring(http_bytes_arxiv(url))
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    entry = root.find("atom:entry", ns)
    if entry is None:
        raise ValueError(f"No arXiv entry found for {arxiv_id}")
    title = " ".join((entry.findtext("atom:title", default="", namespaces=ns) or "Untitled").split())
    abstract = " ".join((entry.findtext("atom:summary", default="", namespaces=ns) or "").split())
    published = entry.findtext("atom:published", default="", namespaces=ns) or ""
    year = int(published[:4]) if published[:4].isdigit() else None
    authors = [
        author.findtext("atom:name", default="", namespaces=ns)
        for author in entry.findall("atom:author", ns)
    ]
    authors = [author for author in authors if author]
    doi = entry.findtext("arxiv:doi", default="", namespaces=ns) or ""
    entry_id = (entry.findtext("atom:id", default="", namespaces=ns) or "").rsplit("/", 1)[-1] or arxiv_id
    url_abs = entry.findtext("atom:id", default="", namespaces=ns) or f"https://arxiv.org/abs/{arxiv_id}"
    return PaperResult(
        title=title,
        authors=authors,
        year=year,
        journal="arXiv",
        doi=doi,
        url=url_abs,
        abstract=abstract,
        web_source="arxiv",
        citation_count=None,
        source_type="preprint",
        source_id=entry_id,
        submitted_date=published,
    )


def score_results(results: list[PaperResult]) -> list[PaperResult]:
    current_year = datetime.now().year
    scored: list[tuple[float, PaperResult]] = []
    for rank, result in enumerate(results, start=1):
        relevance = 1 / rank
        recency = 0 if not result.year else max(0, 1 - ((current_year - result.year) / 10))
        citations = math.log((result.citation_count or 0) + 1)
        if result.web_source == "arxiv":
            score = 0.5 * relevance + 0.5 * recency
        else:
            score = 0.5 * relevance + 0.3 * citations + 0.2 * recency
        scored.append((score, result))
    return [result for _, result in sorted(scored, key=lambda item: item[0], reverse=True)]


def normalize_match_text(value: str) -> str:
    value = value.lower()
    value = value.replace("state-of-health", "state of health")
    value = value.replace("lithium-ion", "lithium ion").replace("li-ion", "li ion")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def match_terms(text: str, terms: list[str]) -> list[str]:
    matched: list[str] = []
    normalized = normalize_match_text(text)
    for term in terms:
        normalized_term = normalize_match_text(str(term))
        if not normalized_term:
            continue
        pattern = rf"(?<![a-z0-9]){re.escape(normalized_term)}(?![a-z0-9])"
        if re.search(pattern, normalized):
            matched.append(str(term))
    return matched


def domain_profile_for_direction(direction: str, config: dict[str, Any]) -> dict[str, Any]:
    profiles = config.get("web_search", {}).get("domain_profiles", {})
    profile = profiles.get(direction, {}) if isinstance(profiles, dict) else {}
    if profile:
        return profile
    return {"strict": False, "keywords": [], "preferred_venues": []}


def result_match_text(result: PaperResult) -> str:
    return " ".join([result.title or "", result.abstract or "", result.journal or ""])


def evaluate_domain_match(result: PaperResult, profile: dict[str, Any]) -> dict[str, Any]:
    text = result_match_text(result)
    keywords = [str(item) for item in profile.get("keywords", [])]
    negative_keywords = [str(item) for item in profile.get("negative_keywords", [])]
    required_groups = profile.get("required_groups", [])
    preferred_venues = [str(item) for item in profile.get("preferred_venues", [])]
    matched_keywords = match_terms(text, keywords)
    negative_hits = match_terms(text, negative_keywords)
    matched_groups: list[str] = []
    missing_groups: list[str] = []
    for group in required_groups if isinstance(required_groups, list) else []:
        name = str(group.get("name") or "required")
        terms = [str(item) for item in group.get("terms", [])]
        if match_terms(text, terms):
            matched_groups.append(name)
        else:
            missing_groups.append(name)
    venue_hits = match_terms(result.journal or "", preferred_venues)
    strict = bool(profile.get("strict", False))
    passed = True
    reasons: list[str] = []
    if strict and missing_groups:
        passed = False
        reasons.append("missing " + ", ".join(missing_groups))
    if negative_hits and (strict or not matched_groups):
        passed = False
        reasons.append("negative hit: " + ", ".join(negative_hits))
    if not strict and keywords and not matched_keywords:
        reasons.append("no profile keyword matched")
    score = 0.0
    if required_groups:
        score += 0.65 * (len(matched_groups) / max(1, len(required_groups)))
    elif matched_keywords:
        score += 0.45
    score += min(0.25, 0.04 * len(matched_keywords))
    if venue_hits:
        score += 0.10
    if negative_hits:
        score -= 0.25
    score = max(0.0, min(1.0, score))
    return {
        "passed": passed,
        "score": score,
        "matched_keywords": matched_keywords,
        "matched_groups": matched_groups,
        "negative_hits": negative_hits,
        "venue_hits": venue_hits,
        "reason": "; ".join(reasons) if reasons else "passed",
    }


def result_api_key(result: PaperResult) -> str:
    if result_identity(result).startswith("title:"):
        return result_identity(result)
    return result_identity(result)


def merge_dedup_results(results: list[PaperResult]) -> list[tuple[PaperResult, int]]:
    merged: dict[str, tuple[PaperResult, int]] = {}
    for rank, result in enumerate(results, start=1):
        key = result_api_key(result)
        if key not in merged:
            merged[key] = (result, rank)
    return list(merged.values())


def recency_score(result: PaperResult) -> float:
    if not result.year:
        return 0.0
    return max(0.0, 1 - ((datetime.now().year - result.year) / 10))


def filter_and_score_results(results: list[PaperResult], direction: str, config: dict[str, Any], no_domain_filter: bool = False) -> tuple[list[PaperResult], list[dict[str, Any]]]:
    profile = domain_profile_for_direction(direction, config)
    ranked: list[RankedResult] = []
    filtered_out: list[dict[str, Any]] = []
    merged = merge_dedup_results(results)
    for result, api_rank in merged:
        domain_match = evaluate_domain_match(result, profile)
        if not no_domain_filter and not domain_match["passed"]:
            filtered_out.append(
                {
                    "title": result.title,
                    "web_source": result.web_source,
                    "journal": result.journal,
                    "year": result.year,
                    "identity": result_identity(result),
                    "reason": domain_match["reason"],
                    "matched_keywords": domain_match["matched_keywords"],
                    "negative_hits": domain_match["negative_hits"],
                }
            )
            continue
        api_rank_score = 1 / max(1, api_rank)
        citations = math.log((result.citation_count or 0) + 1)
        if result.web_source == "arxiv":
            score = 0.60 * domain_match["score"] + 0.20 * api_rank_score + 0.20 * recency_score(result)
        else:
            score = 0.50 * domain_match["score"] + 0.20 * api_rank_score + 0.20 * citations + 0.10 * recency_score(result)
        ranked.append(RankedResult(result=result, api_rank=api_rank, domain_match=domain_match, score=score))
    ranked.sort(key=lambda item: item.score, reverse=True)
    return [item.result for item in ranked], filtered_out


def venue_matches_profile(result: PaperResult, profile: dict[str, Any]) -> bool:
    venues = [str(item) for item in profile.get("preferred_venues", [])]
    return not venues or bool(match_terms(result.journal or "", venues))


def arxiv_query_for_profile(query: str, profile: dict[str, Any]) -> str:
    required_groups = profile.get("required_groups", [])
    if not required_groups:
        return f"all:{query}"
    group_queries: list[str] = []
    for group in required_groups:
        terms = [str(item) for item in group.get("terms", []) if str(item).strip()]
        if not terms:
            continue
        parts = []
        for term in terms[:8]:
            term = term.strip()
            parts.append(f'all:"{term}"' if " " in term or "-" in term else f"all:{term}")
        group_queries.append("(" + " OR ".join(parts) + ")")
    return " AND ".join(group_queries) if group_queries else f"all:{query}"


def result_identity(result: PaperResult) -> str:
    if result.web_source == "arxiv" and result.source_id:
        return arxiv_identity(result)
    if result.doi:
        return f"doi:{result.doi.lower()}"
    return f"title:{normalize_identity(result.title)}:{result.year or ''}"


def web_output_root(config: dict[str, Any]) -> Path:
    root = config.get("web_search", {}).get("output_root", "paper/web_search")
    return ROOT / root


def web_source_dir(config: dict[str, Any], direction: str, web_source: str) -> Path:
    return web_output_root(config) / direction / web_source


def markdown_for_result(result: PaperResult, direction: str, journal_abbr: str, query: str) -> str:
    retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
    citation = "" if result.citation_count is None else str(result.citation_count)
    year = "" if result.year is None else str(result.year)
    return "\n".join(
        [
            "---",
            f"title: {yaml_quote(result.title)}",
            "authors:",
            yaml_list(result.authors),
            f"published: {yaml_quote(result.journal)}",
            f"published_year: {yaml_int_or_null(year)}",
            f"doi: {yaml_quote(result.doi)}",
            f"source: {yaml_quote(result.url)}",
            f"web_source: {yaml_quote(result.web_source)}",
            f"citation_count: {yaml_int_or_null(citation)}",
            f"direction: {yaml_quote(direction)}",
            f"journal_abbr: {yaml_quote(journal_abbr)}",
            f"source_type: {yaml_quote(result.source_type)}",
            f"import_status: {yaml_quote('web-imported')}",
            f"created_at: {yaml_quote(retrieved)}",
            "---",
            "",
            f"# {result.title}",
            "",
            "## Abstract",
            "",
            result.abstract or "Abstract not available from the selected source.",
            "",
            "## Web Search Metadata",
            "",
            f"- Source: {result.web_source}",
            f"- Citation count: {citation or 'N/A'}",
            f"- DOI: {result.doi or 'N/A'}",
            f"- URL: {result.url or 'N/A'}",
            f"- Search query: {query}",
            f"- Retrieved at: {retrieved}",
            f"- Source ID: {result.source_id or 'N/A'}",
            "",
            "## Full Text / Clipped Content",
            "",
            "Full text was not fetched by API search. Use Obsidian Web Clipper to add clipped Markdown content when available.",
            "",
            "## User Notes",
            "",
        ]
    )


def write_source(result: PaperResult, direction: str, query: str, config: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    journal_abbr = journal_abbr_from_name(result.journal, config)
    year = str(result.year or "unknown")
    filename = f"{year}-{first_author_key(result.authors)}-{slugify(result.title)}.md"
    target = web_source_dir(config, direction, result.web_source) / filename
    record = {
        "title": result.title,
        "path": rel(target),
        "identity": result_identity(result),
        "web_source": result.web_source,
        "storage_layer": "web_search",
        "status": "dry-run" if dry_run else "created",
    }
    if target.exists():
        record["status"] = "skipped_existing"
        return record
    if not dry_run:
        ensure_dir(target.parent)
        target.write_text(markdown_for_result(result, direction, journal_abbr, query), encoding="utf-8")
    return record


def collect_results(args: argparse.Namespace, config: dict[str, Any]) -> tuple[list[PaperResult], list[dict[str, Any]], list[str]]:
    source = getattr(args, "source", "mixed")
    query = args.query
    notices: list[str] = []
    results: list[PaperResult] = []
    profile = domain_profile_for_direction(args.direction, config)
    if source in {"mixed", "openalex"}:
        try:
            results.extend(fetch_openalex_classic(query, args.top, config, config.get("web_search", {}).get("min_citations", 5)))
            results.extend(fetch_openalex_recent(query, args.top, config))
        except Exception as exc:
            notices.append(f"OpenAlex skipped: {exc}")
    if source == "venues":
        try:
            venue_results = fetch_openalex_classic(query, args.top, config, config.get("web_search", {}).get("min_citations", 5))
            venue_results.extend(fetch_openalex_recent(query, args.top, config))
            results.extend([result for result in venue_results if venue_matches_profile(result, profile)])
        except Exception as exc:
            notices.append(f"OpenAlex venues skipped: {exc}")
    if source in {"mixed", "semanticscholar"}:
        try:
            results.extend(fetch_semantic_scholar(query, args.top, config))
        except Exception as exc:
            notices.append(f"Semantic Scholar skipped: {exc}")
    if source == "arxiv":
        try:
            results.extend(fetch_arxiv(query, args.top, arxiv_query_for_profile(query, profile)))
        except Exception as exc:
            notices.append(f"arXiv skipped: {exc}")
    accepted, filtered_out = filter_and_score_results(results, args.direction, config, no_domain_filter=getattr(args, "no_domain_filter", False))
    if source == "mixed" and len(accepted) < args.top:
        try:
            arxiv_results = fetch_arxiv(query, args.top, arxiv_query_for_profile(query, profile))
            results.extend(arxiv_results)
            accepted, filtered_out = filter_and_score_results(results, args.direction, config, no_domain_filter=getattr(args, "no_domain_filter", False))
        except Exception as exc:
            notices.append(f"arXiv skipped: {exc}")
    return accepted, filtered_out, notices


def arxiv_fulltext_enabled(args: argparse.Namespace, config: dict[str, Any]) -> bool:
    if getattr(args, "no_fulltext", False):
        return False
    if getattr(args, "fulltext", False):
        return True
    return bool(config.get("web_search", {}).get("arxiv_fulltext_default", True))


def save_results(results: list[PaperResult], args: argparse.Namespace, config: dict[str, Any]) -> dict[str, Any]:
    use_arxiv_fulltext = arxiv_fulltext_enabled(args, config)
    formal_identities = existing_identities(args.direction, config) | existing_arxiv_identities(args.direction, config, include_web=False)
    all_identities = formal_identities | existing_arxiv_identities(args.direction, config)
    seen: set[str] = set()
    created: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for result in results:
        identity = result_identity(result)
        identities = formal_identities if result.web_source == "arxiv" and use_arxiv_fulltext else all_identities
        if identity in identities or identity in seen:
            skipped.append({"title": result.title, "identity": identity, "status": "skipped_existing"})
            continue
        seen.add(identity)
        if result.web_source == "arxiv" and use_arxiv_fulltext:
            record = write_arxiv_fulltext_result(result, args.direction, args.query or result.source_id, config, args.dry_run)
        else:
            record = write_source(result, args.direction, args.query or result.source_id, config, args.dry_run)
        if record["status"] == "skipped_existing":
            skipped.append(record)
            continue
        if record["status"] == "failed":
            failed.append(record)
            continue
        created.append(record)
        if len(created) >= args.top:
            break
    return {"created": created, "skipped_existing": skipped, "failed": failed}


def write_digest_report(saved: dict[str, Any], args: argparse.Namespace, config: dict[str, Any], filtered_out: list[dict[str, Any]]) -> Path | None:
    if args.dry_run:
        return None
    report_dir = ROOT / config["paths"]["reports"] / "web"
    ensure_dir(report_dir)
    date = datetime.now().strftime("%Y-%m-%d")
    report_path = report_dir / f"{date}-{args.direction}-digest.md"
    lines = [f"# {args.direction} Web Digest - {date}", "", f"Query: `{args.query}`", ""]
    lines.append("## Saved Papers")
    lines.append("")
    for record in saved["created"]:
        lines.append(f"- [{record['title']}]({rel(ROOT / record['path'])}) - {record['web_source']}")
    if not saved["created"]:
        lines.append("- No new papers saved.")
    lines.append("")
    lines.append("## Skipped Existing")
    lines.append("")
    for record in saved["skipped_existing"]:
        lines.append(f"- {record['title']}")
    lines.append("")
    lines.append("## Filtered Out")
    lines.append("")
    visible_filtered = filtered_out if getattr(args, "show_filtered", False) else filtered_out[:10]
    if visible_filtered:
        for record in visible_filtered:
            lines.append(f"- {record.get('title')} [{record.get('web_source')}] - {record.get('reason')}")
        if len(filtered_out) > len(visible_filtered):
            lines.append(f"- ... {len(filtered_out) - len(visible_filtered)} more hidden; rerun with `--show-filtered` for full list")
    else:
        lines.append("- None")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def table_text(value: Any) -> str:
    text = str(value or "").replace("\n", " ")
    return text.replace("|", "\\|").strip()


def link_text(label: str, url: str) -> str:
    if not url:
        return ""
    return f"[{table_text(label)}]({url})"


def result_lookup(results: list[PaperResult]) -> dict[str, PaperResult]:
    return {result_identity(result): result for result in results}


def unique_report_path(report_dir: Path, date: str, direction: str) -> Path:
    report_path = report_dir / f"{date}-{direction}-find-report.md"
    if not report_path.exists():
        return report_path
    stamp = datetime.now().strftime("%H%M%S")
    return report_dir / f"{date}-{direction}-find-report-{stamp}.md"


def write_find_report(saved: dict[str, Any], args: argparse.Namespace, config: dict[str, Any], results: list[PaperResult], filtered_out: list[dict[str, Any]]) -> Path | None:
    if args.dry_run:
        return None
    report_dir = ROOT / config["paths"]["reports"] / "web"
    ensure_dir(report_dir)
    date = datetime.now().strftime("%Y-%m-%d")
    report_path = unique_report_path(report_dir, date, args.direction)
    by_identity = result_lookup(results)
    created = saved["created"]
    skipped = saved["skipped_existing"]
    failed = saved["failed"]
    arxiv_created = [record for record in created if record.get("web_source") == "arxiv"]
    metadata_created = [record for record in created if record.get("web_source") in {"openalex", "semanticscholar"}]
    lines = [
        f"# Web Search Report - {args.direction} - {date}",
        "",
        f"Query: `{args.query}`",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"Accepted candidates: {len(results)}",
        f"Filtered out: {len(filtered_out)}",
        "",
        "## Already in Library",
        "",
        "| Title | Journal | Year | DOI |",
        "|---|---|---:|---|",
    ]
    if skipped:
        for record in skipped:
            result = by_identity.get(record.get("identity", ""))
            doi = link_text(result.doi, f"https://doi.org/{result.doi}") if result and result.doi else ""
            lines.append(f"| {table_text(record.get('title'))} | {table_text(result.journal if result else '')} | {table_text(result.year if result else '')} | {doi} |")
    else:
        lines.append("| None |  |  |  |")
    lines.extend(["", "## New Findings - arXiv Full Text", "", "| Title | Authors | Year | arXiv Link | Full Text Status | Local Path |", "|---|---|---:|---|---|---|"])
    if arxiv_created:
        for record in arxiv_created:
            result = by_identity.get(record["identity"])
            authors = "; ".join((result.authors if result else [])[:3])
            link = link_text("arXiv", result.url if result else "")
            lines.append(f"| {table_text(record['title'])} | {table_text(authors)} | {table_text(result.year if result else '')} | {link} | {table_text(record.get('full_text_status'))} | `{record.get('path', '')}` |")
    else:
        lines.append("| None |  |  |  |  |  |")
    lines.extend(["", "## New Findings - OpenAlex / Semantic Scholar", "", "| Title | Authors | Journal | Year | Citations | DOI/URL | Local Path |", "|---|---|---|---:|---:|---|---|"])
    if metadata_created:
        for record in metadata_created:
            result = by_identity.get(record["identity"])
            authors = "; ".join((result.authors if result else [])[:3])
            doi_or_url = ""
            if result:
                doi_or_url = link_text(result.doi, f"https://doi.org/{result.doi}") if result.doi else link_text("URL", result.url)
            citations = "" if not result or result.citation_count is None else result.citation_count
            lines.append(f"| {table_text(record['title'])} | {table_text(authors)} | {table_text(result.journal if result else '')} | {table_text(result.year if result else '')} | {table_text(citations)} | {doi_or_url} | `{record.get('path', '')}` |")
    else:
        lines.append("| None |  |  |  |  |  |  |")
    lines.extend(["", "## Skipped / Failed", "", "| Title | Identity | Status | Error |", "|---|---|---|---|"])
    skipped_failed = skipped + failed
    if skipped_failed:
        for record in skipped_failed:
            lines.append(f"| {table_text(record.get('title'))} | `{table_text(record.get('identity'))}` | {table_text(record.get('status'))} | {table_text(record.get('error'))} |")
    else:
        lines.append("| None |  |  |  |")
    lines.extend(["", "## Filtered Out", "", "| Title | Source | Journal | Reason |", "|---|---|---|---|"])
    visible_filtered = filtered_out if getattr(args, "show_filtered", False) else filtered_out[:10]
    if visible_filtered:
        for record in visible_filtered:
            lines.append(f"| {table_text(record.get('title'))} | {table_text(record.get('web_source'))} | {table_text(record.get('journal'))} | {table_text(record.get('reason'))} |")
        if len(filtered_out) > len(visible_filtered):
            lines.append(f"| ... {len(filtered_out) - len(visible_filtered)} more hidden; rerun with `--show-filtered` for full list |  |  |  |")
    else:
        lines.append("| None |  |  |  |")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def run_find(args: argparse.Namespace) -> None:
    config = load_config()
    validate_direction(args.direction, config)
    if args.arxiv_id:
        args.source = "arxiv"
        args.query = args.query or args.arxiv_id
        results = [fetch_arxiv_by_id(args.arxiv_id)]
        filtered_out: list[dict[str, Any]] = []
        notices: list[str] = []
    elif not args.query:
        raise ValueError("find requires --query or a positional query")
    else:
        results, filtered_out, notices = collect_results(args, config)
    saved = save_results(results, args, config)
    manifest_name = "arxiv_fulltext_results.json" if any(r.web_source == "arxiv" for r in results) and arxiv_fulltext_enabled(args, config) else "web_search_results.json"
    manifest_path = ROOT / config["paths"]["manifests"] / manifest_name
    report_path = write_find_report(saved, args, config, results, filtered_out)
    if not args.dry_run:
        write_json(manifest_path, {"query": args.query, "direction": args.direction, "dry_run": args.dry_run, "notices": notices, **saved, "filtered_out": filtered_out, "report": rel(report_path) if report_path else None})
        if any(record.get("storage_layer") == "formal" for record in saved["created"]):
            rebuild_indexes()
        append_log(f"- {datetime.now().isoformat(timespec='seconds')} find {args.direction} {args.query}: accepted={len(results)} filtered={len(filtered_out)} created={len(saved['created'])} skipped={len(saved['skipped_existing'])} failed={len(saved['failed'])} dry_run={args.dry_run}", config)
    print(f"Accepted {len(results)} results; filtered {len(filtered_out)}. Created {len(saved['created'])}; skipped {len(saved['skipped_existing'])}; failed {len(saved['failed'])}.")
    for notice in notices:
        print(f"Notice: {notice}")
    if args.dry_run:
        print("Dry run: no files were written.")
        if filtered_out:
            shown = filtered_out if getattr(args, "show_filtered", False) else filtered_out[:10]
            print("Filtered out:")
            for record in shown:
                print(f"- {record.get('title')} [{record.get('web_source')}] - {record.get('reason')}")
            if len(filtered_out) > len(shown):
                print(f"- ... {len(filtered_out) - len(shown)} more hidden; rerun with --show-filtered for full list")
        print(f"Find report would be written to: {config['paths']['reports']}/web/{datetime.now().strftime('%Y-%m-%d')}-{args.direction}-find-report.md")
        if any(r.web_source == "arxiv" for r in results) and arxiv_fulltext_enabled(args, config):
            root = config.get("web_search", {}).get("arxiv_output_root") or config.get("web_search", {}).get("output_root", "paper/web_search")
            print(f"arXiv dry-run preview: {root}/{args.direction}/arxiv/ (non-dry-run will move full_text_extracted papers into paper/{args.direction}/arxiv/)")
        if any(r.web_source in {"openalex", "semanticscholar"} for r in results):
            root = config.get("web_search", {}).get("output_root", "paper/web_search")
            print(f"Metadata web-search output: {root}/{args.direction}/openalex|semanticscholar/")
    else:
        print(f"Manifest: {rel(manifest_path)}")
        if report_path:
            print(f"Report: {rel(report_path)}")


def run_digest(args: argparse.Namespace) -> None:
    config = load_config()
    validate_direction(args.direction, config)
    args.source = "arxiv"
    notices: list[str] = []
    filtered_out: list[dict[str, Any]] = []
    try:
        profile = domain_profile_for_direction(args.direction, config)
        candidates = fetch_arxiv(args.query, args.top, arxiv_query_for_profile(args.query, profile))
        results, filtered_out = filter_and_score_results(candidates, args.direction, config, no_domain_filter=getattr(args, "no_domain_filter", False))
    except Exception as exc:
        results = []
        notices.append(f"arXiv skipped: {exc}")
    saved = save_results(results, args, config)
    report_path = write_digest_report(saved, args, config, filtered_out)
    manifest_path = ROOT / config["paths"]["manifests"] / "web_digest_results.json"
    if not args.dry_run:
        write_json(manifest_path, {"query": args.query, "direction": args.direction, "dry_run": args.dry_run, "notices": notices, **saved, "filtered_out": filtered_out, "report": rel(report_path) if report_path else None})
        if any(record.get("storage_layer") == "formal" for record in saved["created"]):
            rebuild_indexes()
        append_log(f"- {datetime.now().isoformat(timespec='seconds')} digest {args.direction} {args.query}: accepted={len(results)} filtered={len(filtered_out)} created={len(saved['created'])} skipped={len(saved['skipped_existing'])} dry_run={args.dry_run}", config)
    print(f"Digest results: accepted {len(results)}; filtered {len(filtered_out)}. Created {len(saved['created'])}; skipped {len(saved['skipped_existing'])}.")
    for notice in notices:
        print(f"Notice: {notice}")
    if report_path:
        print(f"Report: {rel(report_path)}")
    if args.dry_run:
        print("Dry run: no files were written.")
        if filtered_out:
            shown = filtered_out if getattr(args, "show_filtered", False) else filtered_out[:10]
            print("Filtered out:")
            for record in shown:
                print(f"- {record.get('title')} [{record.get('web_source')}] - {record.get('reason')}")
            if len(filtered_out) > len(shown):
                print(f"- ... {len(filtered_out) - len(shown)} more hidden; rerun with --show-filtered for full list")
    else:
        print(f"Manifest: {rel(manifest_path)}")


def validate_s2_key(config: dict[str, Any]) -> bool | None:
    """Validate Semantic Scholar API key. Returns True if valid, False if invalid, None if not configured."""
    api_key = config.get("web_search", {}).get("semantic_scholar_api_key")
    if not api_key:
        return None
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1"
        http_json(url, headers={"x-api-key": api_key})
        return True
    except Exception:
        return False


def check_config_status(config: dict[str, Any]) -> list[str]:
    """Check web search configuration and return status messages."""
    messages: list[str] = []
    ws = config.get("web_search", {})
    s2_key_status = validate_s2_key(config)
    oa_email = ws.get("openalex_email", "")
    oa_key = ws.get("openalex_api_key", "")

    if s2_key_status is True:
        messages.append("Semantic Scholar: API key valid (1 rps)")
    elif s2_key_status is False:
        messages.append("Semantic Scholar: API key invalid (falling back to 100 req/5min)")
        messages.append("  - Check/update semantic_scholar_api_key in config.json")
    else:
        messages.append("Semantic Scholar: No API key (100 req/5min shared pool)")
        messages.append("  - Add semantic_scholar_api_key for 1 rps")

    if oa_key:
        messages.append("OpenAlex: API key configured")
    else:
        messages.append("OpenAlex: No API key configured")
        messages.append("  - Add openalex_api_key for normal quota-based access")
    if oa_email:
        messages.append(f"OpenAlex: contact email configured ({oa_email})")
    else:
        messages.append("OpenAlex: No contact email configured")
        messages.append("  - Add openalex_email as optional contact metadata")

    return messages


def main() -> None:
    parser = argparse.ArgumentParser(description="Search academic web sources and save Markdown papers.")
    sub = parser.add_subparsers(dest="command", required=True)
    find = sub.add_parser("find")
    find.add_argument("positional_query", nargs="?")
    find.add_argument("--query")
    find.add_argument("--direction", required=True)
    find.add_argument("--top", type=int, default=None)
    find.add_argument("--source", choices=["mixed", "openalex", "semanticscholar", "arxiv", "venues"], default="mixed")
    find.add_argument("--arxiv-id")
    find.add_argument("--fulltext", action="store_true")
    find.add_argument("--no-fulltext", action="store_true")
    find.add_argument("--no-domain-filter", action="store_true")
    find.add_argument("--show-filtered", action="store_true")
    find.add_argument("--dry-run", action="store_true")
    find.set_defaults(func=run_find)
    digest = sub.add_parser("digest")
    digest.add_argument("--query", required=True)
    digest.add_argument("--direction", required=True)
    digest.add_argument("--top", type=int, default=None)
    digest.add_argument("--no-domain-filter", action="store_true")
    digest.add_argument("--show-filtered", action="store_true")
    digest.add_argument("--dry-run", action="store_true")
    digest.set_defaults(func=run_digest)
    args = parser.parse_args()
    if getattr(args, "command", None) == "find" and not args.query:
        args.query = args.positional_query
    config = load_config()
    if args.top is None:
        args.top = int(config.get("web_search", {}).get("default_top", 10))
    status_messages = check_config_status(config)
    if status_messages:
        print("=== Web Search Configuration ===")
        for msg in status_messages:
            print(msg)
        print()
    try:
        args.func(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
