"""Core analysis and scoring utilities for Web Analyzer CLI."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": "WebAnalyzerCLI/2.0 (+https://github.com/N1ghthill/web-analyzer-cli)",
}

DEFAULT_WEIGHTS = {
    "performance": 25,
    "security": 30,
    "seo": 20,
    "accessibility": 15,
    "best_practices": 10,
}

SECURITY_HEADERS = [
    "strict-transport-security",
    "content-security-policy",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
]

DEPRECATED_TAGS = {"marquee", "center", "font", "blink"}


def normalize_url(url: str) -> str:
    """Ensure URL has a scheme."""
    url = (url or "").strip()
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 2)


def _score_by_threshold(value: float, thresholds: List[tuple]) -> float:
    for limit, score in thresholds:
        if value <= limit:
            return score
    return thresholds[-1][1]


def calculate_overall_score(
    criteria_scores: Dict[str, float],
    weights: Optional[Dict[str, int]] = None,
) -> float:
    """Return weighted score between 0 and 100."""
    used_weights = weights or DEFAULT_WEIGHTS
    total_weight = 0
    weighted_sum = 0.0

    for criterion, weight in used_weights.items():
        if criterion not in criteria_scores:
            continue
        total_weight += weight
        weighted_sum += criteria_scores[criterion] * weight

    if total_weight == 0:
        return 0.0

    return _clamp_score(weighted_sum / total_weight)


def _fetch_url(url: str, timeout: int = 10) -> Dict[str, Any]:
    started_at = time.time()
    response = requests.get(url, timeout=timeout, headers=DEFAULT_HEADERS, allow_redirects=True)
    elapsed = time.time() - started_at

    return {
        "response": response,
        "elapsed": elapsed,
        "final_url": response.url,
        "status": response.status_code,
        "headers": {k.lower(): v for k, v in response.headers.items()},
        "content_size_bytes": len(response.content or b""),
    }


def _extract_basic_html_stats(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else None
    images = soup.find_all("img")
    links = soup.find_all("a")
    viewport = bool(soup.find("meta", attrs={"name": "viewport"}))
    charset_meta = soup.find("meta", attrs={"charset": True})

    return {
        "soup": soup,
        "title": title,
        "images": len(images),
        "links": len(links),
        "mobile_friendly": viewport,
        "meta_charset": charset_meta.get("charset") if charset_meta else None,
    }


def _estimate_request_count(soup: BeautifulSoup) -> int:
    total = 0
    total += len(soup.find_all("script", src=True))
    total += len(soup.find_all("img", src=True))
    total += len(soup.find_all("link", href=True))
    total += len(soup.find_all("iframe", src=True))
    return total


def _image_alt_coverage(soup: BeautifulSoup) -> float:
    images = soup.find_all("img")
    if not images:
        return 1.0
    with_alt = 0
    for img in images:
        alt = (img.get("alt") or "").strip()
        if alt:
            with_alt += 1
    return with_alt / len(images)


def _form_label_coverage(soup: BeautifulSoup) -> float:
    fields = []
    for field in soup.find_all(["input", "select", "textarea"]):
        field_type = (field.get("type") or "").lower()
        if field.name == "input" and field_type in {"hidden", "submit", "button", "reset", "image"}:
            continue
        fields.append(field)

    if not fields:
        return 1.0

    labelled = 0
    for field in fields:
        if (field.get("aria-label") or "").strip():
            labelled += 1
            continue
        if (field.get("title") or "").strip():
            labelled += 1
            continue
        field_id = (field.get("id") or "").strip()
        if field_id and soup.find("label", attrs={"for": field_id}):
            labelled += 1
            continue
        if field.find_parent("label") is not None:
            labelled += 1

    return labelled / len(fields)


def _button_accessibility_coverage(soup: BeautifulSoup) -> float:
    button_candidates = list(soup.find_all("button"))
    button_candidates.extend(
        soup.find_all("input", attrs={"type": lambda x: (x or "").lower() in {"button", "submit"}})
    )

    if not button_candidates:
        return 1.0

    accessible = 0
    for button in button_candidates:
        label = ""
        if button.name == "button":
            label = (button.get_text(" ", strip=True) or "").strip()
        else:
            label = (button.get("value") or "").strip()

        aria = (button.get("aria-label") or "").strip()
        title = (button.get("title") or "").strip()

        if label or aria or title:
            accessible += 1

    return accessible / len(button_candidates)


def _heading_order_score(soup: BeautifulSoup) -> float:
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    if not headings:
        return 0.6

    levels = [int(tag.name[1]) for tag in headings]
    jumps = 0
    previous = levels[0]
    for level in levels[1:]:
        if level > previous + 1:
            jumps += 1
        previous = level

    jump_ratio = jumps / max(1, len(levels) - 1)
    if jump_ratio == 0:
        return 1.0
    if jump_ratio <= 0.25:
        return 0.7
    if jump_ratio <= 0.5:
        return 0.4
    return 0.2


def _has_mixed_content(soup: BeautifulSoup, page_is_https: bool) -> int:
    if not page_is_https:
        return 0

    mixed = 0
    selectors = [
        ("script", "src"),
        ("img", "src"),
        ("iframe", "src"),
        ("link", "href"),
        ("video", "src"),
        ("audio", "src"),
        ("source", "src"),
    ]

    for tag_name, attr in selectors:
        for tag in soup.find_all(tag_name):
            raw = (tag.get(attr) or "").strip()
            if raw.startswith("http://"):
                mixed += 1

    return mixed


def _target_blank_without_rel_count(soup: BeautifulSoup) -> int:
    count = 0
    for anchor in soup.find_all("a", target=True):
        if (anchor.get("target") or "").lower() != "_blank":
            continue
        rel_tokens = " ".join(anchor.get("rel") or []).lower()
        if "noopener" not in rel_tokens and "noreferrer" not in rel_tokens:
            count += 1
    return count


def _score_performance(response_time: float, content_size_bytes: int, request_count: int) -> Dict[str, Any]:
    response_score = _score_by_threshold(response_time, [
        (0.4, 100),
        (0.8, 90),
        (1.2, 80),
        (2.0, 65),
        (3.0, 45),
        (9999.0, 20),
    ])

    content_size_kb = content_size_bytes / 1024 if content_size_bytes else 0
    size_score = _score_by_threshold(content_size_kb, [
        (500, 100),
        (1024, 85),
        (2048, 65),
        (3072, 45),
        (999999, 20),
    ])

    request_score = _score_by_threshold(request_count, [
        (25, 100),
        (50, 80),
        (80, 60),
        (120, 40),
        (99999, 20),
    ])

    final_score = _clamp_score((response_score * 0.55) + (size_score * 0.25) + (request_score * 0.20))
    method = "local"

    notes = []
    if response_time > 2.0:
        notes.append("Slow response time")
    if content_size_kb > 2048:
        notes.append("Large HTML payload")
    if request_count > 80:
        notes.append("High estimated request count")

    return {
        "score": final_score,
        "method": method,
        "details": {
            "response_time_s": round(response_time, 3),
            "content_size_kb": round(content_size_kb, 1),
            "estimated_request_count": request_count,
            "notes": notes,
        },
    }


def _score_security(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    parsed = urlparse(url)
    is_https = parsed.scheme == "https"

    points = 0
    max_points = 100
    missing_headers: List[str] = []

    if is_https:
        points += 20

    for header in SECURITY_HEADERS:
        if header in headers:
            points += 10
        else:
            missing_headers.append(header)

    set_cookie = (headers.get("set-cookie") or "").lower()
    if not set_cookie:
        points += 20
        cookie_state = "no_cookies"
    else:
        secure = "secure" in set_cookie
        httponly = "httponly" in set_cookie
        if secure:
            points += 10
        if httponly:
            points += 10
        cookie_state = "secure+httponly" if secure and httponly else "missing_cookie_flags"

    score = _clamp_score((points / max_points) * 100)

    notes = []
    if not is_https:
        notes.append("Site not served over HTTPS")
    if missing_headers:
        notes.append("Missing security headers: " + ", ".join(missing_headers))
    if cookie_state == "missing_cookie_flags":
        notes.append("Cookies detected without Secure/HttpOnly flags")

    return {
        "score": score,
        "method": "local",
        "details": {
            "https": is_https,
            "missing_headers": missing_headers,
            "cookie_state": cookie_state,
            "notes": notes,
        },
    }


def _score_seo(soup: BeautifulSoup) -> Dict[str, Any]:
    title_text = ""
    if soup.title and soup.title.string:
        title_text = soup.title.string.strip()

    meta_description_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = (meta_description_tag.get("content") or "").strip() if meta_description_tag else ""

    robots_tag = soup.find("meta", attrs={"name": "robots"})
    canonical_tag = soup.find("link", attrs={"rel": lambda v: v and "canonical" in [x.lower() for x in (v if isinstance(v, list) else [v])]})
    lang = (soup.html.get("lang") or "").strip() if soup.html else ""
    h1_count = len(soup.find_all("h1"))
    alt_coverage = _image_alt_coverage(soup)
    has_schema = bool(soup.find("script", attrs={"type": "application/ld+json"}))

    points = 0

    if 10 <= len(title_text) <= 60:
        points += 20
    elif title_text:
        points += 10

    if 50 <= len(meta_description) <= 160:
        points += 20
    elif meta_description:
        points += 10

    if canonical_tag:
        points += 10

    if robots_tag:
        points += 10

    if lang:
        points += 10

    if h1_count == 1:
        points += 15
    elif h1_count > 1:
        points += 8

    if alt_coverage >= 0.9:
        points += 10
    elif alt_coverage >= 0.7:
        points += 6
    elif alt_coverage > 0:
        points += 3

    if has_schema:
        points += 5

    final_score = _clamp_score(points)
    method = "local"

    notes = []
    if not title_text:
        notes.append("Missing title tag")
    if not meta_description:
        notes.append("Missing meta description")
    if h1_count == 0:
        notes.append("Missing H1 heading")

    return {
        "score": final_score,
        "method": method,
        "details": {
            "title_length": len(title_text),
            "meta_description_length": len(meta_description),
            "has_canonical": bool(canonical_tag),
            "has_robots": bool(robots_tag),
            "lang": lang,
            "h1_count": h1_count,
            "image_alt_coverage": round(alt_coverage, 3),
            "has_schema_org": has_schema,
            "notes": notes,
        },
    }


def _score_accessibility(soup: BeautifulSoup) -> Dict[str, Any]:
    lang_ok = bool((soup.html.get("lang") or "").strip()) if soup.html else False
    img_alt_coverage = _image_alt_coverage(soup)
    form_label_coverage = _form_label_coverage(soup)
    button_accessibility = _button_accessibility_coverage(soup)
    heading_structure = _heading_order_score(soup)

    final_score = _clamp_score(
        (20 if lang_ok else 0)
        + (img_alt_coverage * 20)
        + (form_label_coverage * 20)
        + (button_accessibility * 20)
        + (heading_structure * 20)
    )
    method = "local"

    notes = []
    if not lang_ok:
        notes.append("Missing html lang attribute")
    if img_alt_coverage < 0.8:
        notes.append("Low image alt coverage")
    if form_label_coverage < 0.8:
        notes.append("Low form label coverage")

    return {
        "score": final_score,
        "method": method,
        "details": {
            "lang_ok": lang_ok,
            "image_alt_coverage": round(img_alt_coverage, 3),
            "form_label_coverage": round(form_label_coverage, 3),
            "button_accessibility": round(button_accessibility, 3),
            "heading_structure": round(heading_structure, 3),
            "notes": notes,
        },
    }


def _score_best_practices(soup: BeautifulSoup, html: str, final_url: str) -> Dict[str, Any]:
    doctype_ok = html.lstrip().lower().startswith("<!doctype html")
    is_https = urlparse(final_url).scheme == "https"
    mixed_content_items = _has_mixed_content(soup, is_https)
    deprecated_count = sum(len(soup.find_all(tag)) for tag in DEPRECATED_TAGS)
    favicon_ok = bool(
        soup.find(
            "link",
            attrs={
                "rel": lambda v: v and any("icon" in item.lower() for item in (v if isinstance(v, list) else [v]))
            },
        )
    )
    insecure_blank_links = _target_blank_without_rel_count(soup)

    points = 0
    if doctype_ok:
        points += 20
    if mixed_content_items == 0:
        points += 25
    if deprecated_count == 0:
        points += 20
    if favicon_ok:
        points += 15
    if insecure_blank_links == 0:
        points += 20

    final_score = _clamp_score(points)
    method = "local"

    notes = []
    if mixed_content_items > 0:
        notes.append("Mixed content detected")
    if deprecated_count > 0:
        notes.append("Deprecated HTML tags detected")
    if insecure_blank_links > 0:
        notes.append("target=_blank links missing rel=noopener/noreferrer")

    return {
        "score": final_score,
        "method": method,
        "details": {
            "doctype_ok": doctype_ok,
            "mixed_content_items": mixed_content_items,
            "deprecated_tag_count": deprecated_count,
            "has_favicon": favicon_ok,
            "insecure_blank_links": insecure_blank_links,
            "notes": notes,
        },
    }


def run_basic_analysis(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Return basic website checks without full scoring."""
    normalized = normalize_url(url)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    try:
        fetched = _fetch_url(normalized, timeout=timeout)
        response = fetched["response"]
        html = response.text or ""
        parsed = _extract_basic_html_stats(html)

        return {
            "mode": "basic",
            "timestamp": timestamp,
            "url": normalized,
            "final_url": fetched["final_url"],
            "status": fetched["status"],
            "response_time_s": round(fetched["elapsed"], 3),
            "title": parsed["title"],
            "images": parsed["images"],
            "links": parsed["links"],
            "mobile_friendly": parsed["mobile_friendly"],
            "charset": parsed["meta_charset"] or response.encoding,
            "content_size_bytes": fetched["content_size_bytes"],
            "error": None,
        }
    except requests.exceptions.Timeout:
        return {
            "mode": "basic",
            "timestamp": timestamp,
            "url": normalized,
            "error": "timeout",
        }
    except requests.exceptions.ConnectionError:
        return {
            "mode": "basic",
            "timestamp": timestamp,
            "url": normalized,
            "error": "connection_error",
        }
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {
            "mode": "basic",
            "timestamp": timestamp,
            "url": normalized,
            "error": str(exc),
        }


def run_full_audit(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Run a complete quality audit with weighted scoring."""
    normalized = normalize_url(url)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    try:
        fetched = _fetch_url(normalized, timeout=timeout)
        response = fetched["response"]
        html = response.text or ""
        parsed_html = _extract_basic_html_stats(html)
        soup = parsed_html["soup"]

        estimated_request_count = _estimate_request_count(soup)

        criteria = {
            "performance": _score_performance(
                response_time=fetched["elapsed"],
                content_size_bytes=fetched["content_size_bytes"],
                request_count=estimated_request_count,
            ),
            "security": _score_security(fetched["final_url"], fetched["headers"]),
            "seo": _score_seo(soup),
            "accessibility": _score_accessibility(soup),
            "best_practices": _score_best_practices(
                soup=soup,
                html=html,
                final_url=fetched["final_url"],
            ),
        }

        criteria_scores = {name: data["score"] for name, data in criteria.items()}
        overall_score = calculate_overall_score(criteria_scores, DEFAULT_WEIGHTS)

        return {
            "mode": "full",
            "timestamp": timestamp,
            "url": normalized,
            "final_url": fetched["final_url"],
            "status": fetched["status"],
            "response_time_s": round(fetched["elapsed"], 3),
            "title": parsed_html["title"],
            "images": parsed_html["images"],
            "links": parsed_html["links"],
            "mobile_friendly": parsed_html["mobile_friendly"],
            "charset": parsed_html["meta_charset"] or response.encoding,
            "content_size_bytes": fetched["content_size_bytes"],
            "estimated_request_count": estimated_request_count,
            "criteria": criteria,
            "weights": DEFAULT_WEIGHTS,
            "overall_score": overall_score,
            "error": None,
        }
    except requests.exceptions.Timeout:
        return {
            "mode": "full",
            "timestamp": timestamp,
            "url": normalized,
            "error": "timeout",
        }
    except requests.exceptions.ConnectionError:
        return {
            "mode": "full",
            "timestamp": timestamp,
            "url": normalized,
            "error": "connection_error",
        }
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {
            "mode": "full",
            "timestamp": timestamp,
            "url": normalized,
            "error": str(exc),
        }


def _format_basic_report(result: Dict[str, Any]) -> str:
    if result.get("error"):
        return (
            "\n" + "=" * 60 + "\n"
            + "WEB ANALYZER - BASIC CHECK\n"
            + "=" * 60 + "\n"
            + f"URL: {result.get('url')}\n"
            + f"Timestamp: {result.get('timestamp')}\n"
            + f"Error: {result.get('error')}\n"
            + "=" * 60 + "\n"
        )

    return (
        "\n" + "=" * 60 + "\n"
        + "WEB ANALYZER - BASIC CHECK\n"
        + "=" * 60 + "\n"
        + f"URL: {result.get('url')}\n"
        + f"Final URL: {result.get('final_url')}\n"
        + f"Timestamp: {result.get('timestamp')}\n"
        + f"HTTP status: {result.get('status')}\n"
        + f"Response time: {result.get('response_time_s')}s\n"
        + f"Title: {result.get('title') or 'N/A'}\n"
        + f"Images: {result.get('images')}\n"
        + f"Links: {result.get('links')}\n"
        + f"Mobile friendly (viewport): {'yes' if result.get('mobile_friendly') else 'no'}\n"
        + f"Charset: {result.get('charset') or 'N/A'}\n"
        + "=" * 60 + "\n"
    )


def _format_full_report(result: Dict[str, Any]) -> str:
    if result.get("error"):
        return (
            "\n" + "=" * 60 + "\n"
            + "WEB ANALYZER - FULL AUDIT\n"
            + "=" * 60 + "\n"
            + f"URL: {result.get('url')}\n"
            + f"Timestamp: {result.get('timestamp')}\n"
            + f"Error: {result.get('error')}\n"
            + "=" * 60 + "\n"
        )

    lines = [
        "",
        "=" * 60,
        "WEB ANALYZER - FULL AUDIT",
        "=" * 60,
        f"URL: {result.get('url')}",
        f"Final URL: {result.get('final_url')}",
        f"Timestamp: {result.get('timestamp')}",
        f"HTTP status: {result.get('status')}",
        f"Overall score: {result.get('overall_score')}/100",
        "-" * 60,
        "Scores by criterion:",
    ]

    criteria = result.get("criteria", {})
    for name in ["performance", "security", "seo", "accessibility", "best_practices"]:
        score = criteria.get(name, {}).get("score")
        method = criteria.get(name, {}).get("method")
        lines.append(f"  - {name}: {score}/100 ({method})")

    lines.append("=" * 60)
    return "\n".join(lines) + "\n"


def format_report(result: Dict[str, Any], output_format: str = "text") -> str:
    """Render report text or JSON."""
    if output_format == "json":
        return json.dumps(result, indent=2, ensure_ascii=False)

    if result.get("mode") == "full":
        return _format_full_report(result)
    return _format_basic_report(result)


def verificar_url(
    url: str,
    full: bool = False,
    timeout: int = 10,
    output_format: str = "text",
    report_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Compatibility wrapper used by the CLI entry points."""
    if full:
        result = run_full_audit(url, timeout=timeout)
    else:
        result = run_basic_analysis(url, timeout=timeout)

    rendered = format_report(result, output_format=output_format)
    print(rendered)

    if report_file:
        with open(report_file, "w", encoding="utf-8") as handle:
            handle.write(rendered if output_format == "text" else json.dumps(result, indent=2, ensure_ascii=False))

    return result
