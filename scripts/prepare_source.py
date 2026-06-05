#!/usr/bin/env python3
"""Preflight a URL, HTML file, or PDF before building a NotebookLM publish pack."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


LONG_TEXT_CHARS = 20_000
LONG_IMAGE_COUNT = 10
LONG_HIDDEN_RATIO = 50
SHORT_TEXT_CHARS = 1_000
CONTENT_TYPE_KEYWORDS = {
    "research_report": ("报告", "白皮书", "研究", "调研", "report", "survey", "paper", "index"),
    "news": ("新闻", "速递", "日报", "发布", "announcement", "launch", "breaking"),
    "tutorial": ("教程", "指南", "how to", "guide", "playbook", "实践"),
    "opinion": ("观点", "评论", "专栏", "opinion", "analysis", "essay"),
    "case_study": ("案例", "case", "复盘", "实践", "field study"),
}
TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}
VIDEO_HOST_KEYWORDS = ("youtube.com", "youtu.be", "bilibili.com", "b23.tv", "vimeo.com", "douyin.com", "tiktok.com")
SOCIAL_HOST_KEYWORDS = ("x.com", "twitter.com", "weibo.com", "xiaohongshu.com", "xhslink.com", "threads.net", "linkedin.com")
ARTICLE_HOST_KEYWORDS = ("sohu.com", "medium.com", "substack.com", "mp.weixin.qq.com", "36kr.com", "jiqizhixin.com")
WEB_PREFIX_NOISE = (
    "首页",
    "隐私",
    "登录",
    "注册",
    "搜索",
    "返回",
    "上一页",
    "下一页",
    "全部",
    "评论",
)
WEB_FOOTER_NOISE_PREFIXES = (
    "Copyright",
    "搜狐公司 版权所有",
    "网站地图",
    "热门精选",
    "24小时热文",
    "还没有人评论过",
    "评论 全部",
    "评论 还没有人评论过",
    "推荐阅读",
    "抢首评",
    "阅读原文",
)


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def source_profile(source: str | None, final_url: str | None = None, source_kind: str | None = None) -> dict[str, Any]:
    url = final_url or source or ""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if any(keyword in host for keyword in VIDEO_HOST_KEYWORDS):
        category = "video_page"
        recommended_capture = "Use transcript/subtitles or browser-rendered capture; do not rely on title/thumbnail alone."
    elif any(keyword in host for keyword in SOCIAL_HOST_KEYWORDS):
        category = "social_post"
        recommended_capture = "Use post text, screenshots, and linked source separately; label commentary if no primary source exists."
    elif path.endswith(".pdf") or source_kind == "pdf":
        category = "pdf_report"
        recommended_capture = "Use the original PDF as NotebookLM source; add a source-derived companion only for long reports."
    elif any(keyword in host for keyword in ARTICLE_HOST_KEYWORDS) or source_kind in {"html", "markdown", "text"}:
        category = "article_or_text"
        recommended_capture = "Use source preflight, then archive HTML/TXT/PDF as the source package."
    else:
        category = "unknown_web"
        recommended_capture = "Run preflight; if text is short or navigation-heavy, use browser capture or ask for pasted text/PDF."
    return {
        "host": host,
        "category": category,
        "recommended_capture": recommended_capture,
        "source_kind": source_kind,
    }


def read_source(source: str, timeout: int) -> tuple[bytes, dict[str, Any]]:
    if is_url(source):
        request = urllib.request.Request(
            source,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read(), {
                "input_type": "url",
                "source": source,
                "final_url": response.geturl(),
                "content_type": response.headers.get("content-type", ""),
            }

    path = Path(source).expanduser()
    if not path.exists():
        raise SystemExit(f"Missing source: {source}")
    return path.read_bytes(), {
        "input_type": "file",
        "source": str(path),
        "final_url": None,
        "content_type": "",
        "file_size": path.stat().st_size,
    }


def decode_bytes(raw: bytes) -> str:
    for encoding in ("utf-8", "gb18030", "gbk"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def first_match(patterns: list[str], text: str, flags: int = re.S | re.I) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return clean_text(match.group(1))
    return None


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<script\b.*?</script>", "", value, flags=re.S | re.I)
    value = re.sub(r"<style\b.*?</style>", "", value, flags=re.S | re.I)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def strip_markup(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>", "", value, flags=re.S | re.I)
    value = re.sub(r"<style\b.*?</style>", "", value, flags=re.S | re.I)
    value = re.sub(r"<img\b[^>]*>", " ", value, flags=re.I)
    return clean_text(value)


def extract_article_section(text: str) -> tuple[str, str]:
    candidates = [
        ("sohu_articleContent", r"<section[^>]+id=[\"']articleContent[\"'][^>]*>(.*?)</section>"),
        ("article_tag", r"<article\b[^>]*>(.*?)</article>"),
        ("main_tag", r"<main\b[^>]*>(.*?)</main>"),
        ("content_class", r"<(?:div|section)[^>]+class=[\"'][^\"']*(?:article|post|entry|content|正文)[^\"']*[\"'][^>]*>(.*?)</(?:div|section)>"),
    ]
    best_name = "full_html"
    best_html = text
    best_score = 0
    for name, pattern in candidates:
        for match in re.finditer(pattern, text, re.S | re.I):
            candidate = match.group(1)
            score = len(strip_markup(candidate))
            if score > best_score:
                best_name = name
                best_html = candidate
                best_score = score
    return best_html, best_name


def extract_paragraphs(article_html: str) -> list[str]:
    paragraphs = re.findall(r"<p\b[^>]*>(.*?)</p>", article_html, re.S | re.I)
    if not paragraphs:
        paragraphs = re.findall(r"<div\b[^>]*>(.*?)</div>", article_html, re.S | re.I)
    return [text for text in (strip_markup(paragraph) for paragraph in paragraphs) if text]


def split_text_paragraphs(source_text: str) -> list[str]:
    normalized = source_text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", normalized)
    paragraphs = []
    for block in blocks:
        cleaned = re.sub(r"\s+", " ", block).strip()
        if cleaned:
            paragraphs.append(cleaned)
    if len(paragraphs) <= 1:
        paragraphs = [line.strip() for line in normalized.splitlines() if line.strip()]
    return paragraphs


def clean_rendered_paragraph(paragraph: str) -> str | None:
    value = re.sub(r"\s+", " ", paragraph).strip()
    if not value:
        return None
    for noise in WEB_PREFIX_NOISE:
        if value == noise:
            return None
        prefix = f"{noise} "
        while value.startswith(prefix):
            value = value[len(prefix) :].strip()
            if not value:
                return None
    value = re.sub(r"\s*\+订阅\b.*$", "", value).strip()
    value = re.sub(r"\s*(?:\d{4}[.-]\d{1,2}[.-]\d{1,2}|\d{4}-\d{2}-\d{2})\b.*$", "", value).strip()
    if not value:
        return None
    if any(value.startswith(prefix) for prefix in WEB_FOOTER_NOISE_PREFIXES):
        return None
    if value in {"首页", "隐私", "评论", "全部", "推荐阅读", "热门精选", "网站地图"}:
        return None
    return value


def trim_rendered_paragraphs(paragraphs: list[str]) -> list[str]:
    cleaned: list[str] = []
    started = False
    for paragraph in paragraphs:
        value = clean_rendered_paragraph(paragraph)
        if value is None:
            if started and any(paragraph.startswith(prefix) for prefix in WEB_FOOTER_NOISE_PREFIXES):
                break
            continue
        started = True
        cleaned.append(value)
    return cleaned


def choose_rendered_title(paragraphs: list[str], fallback: str | None = None) -> str | None:
    for paragraph in paragraphs[:12]:
        candidate = clean_rendered_paragraph(paragraph)
        if not candidate:
            continue
        candidate = re.sub(r"\s*[\|｜]\s*", "｜", candidate)
        candidate = re.sub(r"\s+腾讯研究院\s+\d{4}-\d{2}-\d{2}.*$", "", candidate).strip()
        candidate = re.sub(r"\s+\d{4}[.-]\d{1,2}[.-]\d{1,2}.*$", "", candidate).strip()
        candidate = re.sub(r"\s+\+订阅.*$", "", candidate).strip()
        if candidate.endswith(" 腾讯研究院"):
            candidate = candidate[: -len(" 腾讯研究院")].strip()
        candidate = re.sub(r"\s+", " ", candidate).strip()
        if len(candidate) >= 6:
            return candidate[:120]
    return fallback


def extract_frontmatter(source_text: str) -> dict[str, str]:
    match = re.match(r"\s*---\s*\n(.*?)\n---\s*\n", source_text, re.S)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip().lower()] = value.strip().strip("\"'")
    return fields


def remove_frontmatter(source_text: str) -> str:
    return re.sub(r"\s*---\s*\n.*?\n---\s*\n", "", source_text, count=1, flags=re.S)


def markdown_images(source_text: str) -> list[dict[str, Any]]:
    images = []
    for match in re.finditer(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", source_text):
        images.append({"url": match.group(1), "width": None, "height": None, "source": "markdown"})
    return images


def clean_markdown_text(value: str) -> str:
    if re.fullmatch(r"!\[[^\]]*\]\([^)]+\)", value.strip()):
        return ""
    value = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"^\s{0,3}#{1,6}\s+", "", value)
    value = re.sub(r"^\s*[-*+]\s+", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_json_ld(text: str) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for match in re.finditer(r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", text, re.S | re.I):
        raw = html.unescape(match.group(1).strip())
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, list):
            payloads.extend(item for item in parsed if isinstance(item, dict))
        elif isinstance(parsed, dict):
            graph = parsed.get("@graph")
            if isinstance(graph, list):
                payloads.extend(item for item in graph if isinstance(item, dict))
            payloads.append(parsed)
    return payloads


def json_ld_value(payloads: list[dict[str, Any]], keys: tuple[str, ...]) -> str | None:
    for payload in payloads:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return clean_text(value)
            if isinstance(value, dict):
                nested = value.get("name") or value.get("@id")
                if isinstance(nested, str) and nested.strip():
                    return clean_text(nested)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.strip():
                        return clean_text(item)
                    if isinstance(item, dict) and isinstance(item.get("name"), str):
                        return clean_text(item["name"])
    return None


def extract_images(text: str, article_html: str) -> list[dict[str, Any]]:
    images: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None, str | None]] = set()

    for match in re.finditer(
        r'"url"\s*:\s*"([^"]+)"\s*,\s*"width"\s*:\s*"?(?P<width>\d+)"?\s*,\s*"height"\s*:\s*"?(?P<height>\d+)"?',
        text,
        re.S,
    ):
        url = html.unescape(match.group(1))
        width = match.group("width")
        height = match.group("height")
        key = (url, width, height)
        if key not in seen:
            seen.add(key)
            images.append({"url": url, "width": int(width), "height": int(height), "source": "imageList"})

    has_image_list = bool(images)
    for match in re.finditer(r"<img\b([^>]+)>", article_html, re.S | re.I):
        attrs = match.group(1)
        src = first_match([r'\bsrc=["\']([^"\']+)["\']', r'\bdata-src=["\']([^"\']+)["\']'], attrs, re.S | re.I)
        width = first_match([r'\bwidth=["\']?(\d+)'], attrs, re.S | re.I)
        height = first_match([r'\bheight=["\']?(\d+)'], attrs, re.S | re.I)
        if not src:
            continue
        if has_image_list and not src.startswith(("http://", "https://", "//")):
            continue
        key = (src, width, height)
        if key not in seen:
            seen.add(key)
            images.append(
                {
                    "url": src,
                    "width": int(width) if width else None,
                    "height": int(height) if height else None,
                    "source": "articleContent",
                }
            )

    return images


def extract_hidden_ratio(text: str) -> int | None:
    raw = first_match(
        [
            r"hiddenRatio\s*:\s*['\"]?(\d+)['\"]?",
            r'"hiddenRatio"\s*:\s*["\']?(\d+)["\']?',
        ],
        text,
    )
    return int(raw) if raw and raw.isdigit() else None


def parse_html(source_text: str, meta: dict[str, Any]) -> dict[str, Any]:
    article_html, extraction_method = extract_article_section(source_text)
    paragraphs = extract_paragraphs(article_html)
    images = extract_images(source_text, article_html)
    hidden_ratio = extract_hidden_ratio(source_text)
    hidden_content_present = bool(re.search(r'class=["\'][^"\']*hidden-content\b', source_text, re.I))
    article_content_present = bool(re.search(r'id=["\']articleContent["\']', source_text, re.I))
    json_ld = extract_json_ld(source_text)

    title = json_ld_value(json_ld, ("headline", "name")) or first_match(
        [
            r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']',
            r'<meta\s+name=["\']twitter:title["\']\s+content=["\']([^"\']+)["\']',
            r'<meta\s+name=["\']sharecontent["\']\s+content=["\']([^"\']+)["\']',
            r"<h1[^>]*>(.*?)</h1>",
            r"<title[^>]*>(.*?)</title>",
        ],
        source_text,
    )
    author = json_ld_value(json_ld, ("author", "creator", "publisher")) or first_match(
        [
            r'<meta\s+name=["\']mediaid["\']\s+content=["\']([^"\']+)["\']',
            r'<meta\s+name=["\']author["\']\s+content=["\']([^"\']+)["\']',
            r'authorName\s*:\s*[\'"]([^\'"]+)[\'"]',
            r'<span\s+class=["\']name["\'][^>]*>(.*?)</span>',
        ],
        source_text,
    )
    date_published = json_ld_value(json_ld, ("datePublished", "dateCreated", "dateModified")) or first_match(
        [
            r'<meta\s+itemprop=["\']datePublished["\']\s+content=["\']([^"\']+)["\']',
            r'<meta\s+property=["\']og:release_date["\']\s+content=["\']([^"\']+)["\']',
            r'<meta\s+property=["\']article:published_time["\']\s+content=["\']([^"\']+)["\']',
            r'<div\s+class=["\']time["\'][^>]*>(.*?)</div>',
        ],
        source_text,
    )
    canonical = first_match([r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']'], source_text)
    description = json_ld_value(json_ld, ("description",)) or first_match(
        [
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
            r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']',
            r'<meta\s+name=["\']twitter:description["\']\s+content=["\']([^"\']+)["\']',
        ],
        source_text,
    )

    text_chars = sum(len(paragraph) for paragraph in paragraphs)
    long_mode_reasons = []
    if text_chars > LONG_TEXT_CHARS:
        long_mode_reasons.append(f"text_chars>{LONG_TEXT_CHARS}")
    if len(images) > LONG_IMAGE_COUNT:
        long_mode_reasons.append(f"image_count>{LONG_IMAGE_COUNT}")
    if hidden_ratio is not None and hidden_ratio > LONG_HIDDEN_RATIO:
        long_mode_reasons.append(f"hiddenRatio>{LONG_HIDDEN_RATIO}")

    truncation_risks = []
    if extraction_method == "full_html":
        truncation_risks.append("generic_full_html_extraction")
    if not article_content_present and "sohu.com" in (urlparse(meta.get("final_url") or meta.get("source") or "").netloc):
        truncation_risks.append("missing_articleContent")
    if hidden_ratio and hidden_ratio > 0 and not hidden_content_present:
        truncation_risks.append("hiddenRatio_without_hidden_content")
    if text_chars < SHORT_TEXT_CHARS:
        truncation_risks.append(f"text_chars<{SHORT_TEXT_CHARS}")
    if text_chars < SHORT_TEXT_CHARS and hidden_ratio and hidden_ratio > 0:
        truncation_risks.append("short_text_with_hiddenRatio")
    if paragraphs and not any("致谢" in paragraph or "结语" in paragraph for paragraph in paragraphs[-30:]):
        truncation_risks.append("no_obvious_ending_marker")
    network_profile = source_profile(meta.get("source"), meta.get("final_url"), "html")
    if network_profile["category"] in {"video_page", "social_post", "unknown_web"} and text_chars < SHORT_TEXT_CHARS:
        truncation_risks.append(f"{network_profile['category']}_needs_capture_or_transcript")
    profile = content_profile(title, description, paragraphs, text_chars, len(images), long_mode_reasons)

    return {
        **meta,
        "source_kind": "html",
        "title": title,
        "author": author,
        "date_published": date_published,
        "canonical_url": canonical,
        "description": description,
        "extraction": {
            "method": extraction_method,
            "json_ld_count": len(json_ld),
        },
        "network_profile": network_profile,
        "content_profile": profile,
        "sohu": {
            "is_sohu": "sohu.com" in (urlparse(meta.get("final_url") or meta.get("source") or "").netloc),
            "hiddenRatio": hidden_ratio,
            "articleContent_present": article_content_present,
            "hidden_content_present": hidden_content_present,
        },
        "text": {
            "paragraph_count": len(paragraphs),
            "character_count": text_chars,
            "first_paragraphs": paragraphs[:8],
            "last_paragraphs": paragraphs[-8:],
        },
        "images": {
            "count": len(images),
            "items": images,
        },
        "preflight": {
            "long_mode": bool(long_mode_reasons),
            "long_mode_reasons": long_mode_reasons,
            "recommended_notebooklm_sources": 2 if long_mode_reasons else 1,
            "recommended_base_name": recommend_base_name(title, date_published),
            "truncation_risks": truncation_risks,
        },
    }


def parse_plain_text(source_text: str, meta: dict[str, Any], source_kind: str) -> dict[str, Any]:
    frontmatter = extract_frontmatter(source_text)
    body_text = remove_frontmatter(source_text)
    paragraphs = split_text_paragraphs(body_text)
    if source_kind == "markdown":
        paragraphs = [paragraph for paragraph in (clean_markdown_text(paragraph) for paragraph in paragraphs) if paragraph]
    if source_kind in {"text", "markdown"}:
        paragraphs = trim_rendered_paragraphs(paragraphs)
    title = frontmatter.get("title")
    if not title:
        rendered_title = choose_rendered_title(paragraphs)
        if rendered_title:
            title = rendered_title
        else:
            for paragraph in paragraphs[:8]:
                candidate = paragraph.lstrip("#").strip()
                if candidate:
                    title = candidate[:120]
                    break
    author = frontmatter.get("author")
    date_published = frontmatter.get("date") or frontmatter.get("published") or frontmatter.get("date_published")
    description = frontmatter.get("description")
    images = markdown_images(body_text) if source_kind == "markdown" else []
    text_chars = sum(len(paragraph) for paragraph in paragraphs)
    long_mode_reasons = []
    if text_chars > LONG_TEXT_CHARS:
        long_mode_reasons.append(f"text_chars>{LONG_TEXT_CHARS}")
    if len(images) > LONG_IMAGE_COUNT:
        long_mode_reasons.append(f"image_count>{LONG_IMAGE_COUNT}")
    truncation_risks = []
    if text_chars < SHORT_TEXT_CHARS:
        truncation_risks.append(f"text_chars<{SHORT_TEXT_CHARS}")
    if not title:
        truncation_risks.append("missing_title")
    profile = content_profile(title, description, paragraphs, text_chars, len(images), long_mode_reasons)
    network_profile = source_profile(meta.get("source"), meta.get("final_url"), source_kind)
    return {
        **meta,
        "source_kind": source_kind,
        "title": title,
        "author": author,
        "date_published": date_published,
        "canonical_url": None,
        "description": description,
        "extraction": {
            "method": "plain_text_blocks" if source_kind == "text" else "markdown_blocks",
            "frontmatter_keys": sorted(frontmatter.keys()),
        },
        "network_profile": network_profile,
        "content_profile": profile,
        "text": {
            "paragraph_count": len(paragraphs),
            "character_count": text_chars,
            "first_paragraphs": paragraphs[:8],
            "last_paragraphs": paragraphs[-8:],
        },
        "images": {
            "count": len(images),
            "items": images,
        },
        "preflight": {
            "long_mode": bool(long_mode_reasons),
            "long_mode_reasons": long_mode_reasons,
            "recommended_notebooklm_sources": 2 if long_mode_reasons else 1,
            "recommended_base_name": recommend_base_name(title, date_published),
            "truncation_risks": truncation_risks,
        },
    }


def content_profile(
    title: str | None,
    description: str | None,
    paragraphs: list[str],
    text_chars: int,
    image_count: int,
    long_mode_reasons: list[str],
) -> dict[str, Any]:
    blob = " ".join([title or "", description or "", " ".join(paragraphs[:20])]).lower()
    type_scores: dict[str, int] = {}
    for content_type, keywords in CONTENT_TYPE_KEYWORDS.items():
        type_scores[content_type] = sum(1 for keyword in keywords if keyword.lower() in blob)
    content_type = max(type_scores, key=type_scores.get) if any(type_scores.values()) else "general_article"
    if text_chars > 20_000:
        length_band = "long"
    elif text_chars > 5_000:
        length_band = "medium"
    else:
        length_band = "short"
    if image_count >= 10:
        media_density = "image_rich"
    elif image_count > 0:
        media_density = "has_images"
    else:
        media_density = "text_only"
    angle_suggestions = suggest_angles(content_type, length_band, media_density)
    return {
        "content_type": content_type,
        "length_band": length_band,
        "media_density": media_density,
        "angle_suggestions": angle_suggestions,
        "recommended_package_mode": "long_report" if long_mode_reasons else "standard_article",
    }


def suggest_angles(content_type: str, length_band: str, media_density: str) -> list[str]:
    base = {
        "research_report": ["one big finding", "operator checklist", "counterintuitive data", "future scenario"],
        "news": ["what changed", "why now", "who benefits", "what to watch next"],
        "tutorial": ["before/after workflow", "common mistakes", "3-step practical guide", "tool stack"],
        "opinion": ["core argument", "strongest objection", "decision lens", "quote-led hook"],
        "case_study": ["how they did it", "numbers that matter", "replicable pattern", "failure risk"],
        "general_article": ["key tension", "practical takeaway", "surprising detail", "reader checklist"],
    }
    angles = list(base.get(content_type, base["general_article"]))
    if length_band == "long":
        angles.append("executive briefing")
    if media_density == "image_rich":
        angles.append("visual carousel")
    return angles


def inspect_pdf(raw: bytes, meta: dict[str, Any]) -> dict[str, Any]:
    looks_like_pdf = raw.startswith(b"%PDF")
    return {
        **meta,
        "source_kind": "pdf",
        "title": Path(str(meta.get("source") or "source")).stem if meta.get("input_type") == "file" else None,
        "network_profile": source_profile(meta.get("source"), meta.get("final_url"), "pdf"),
        "file": {
            "byte_count": len(raw),
            "looks_like_pdf": looks_like_pdf,
        },
        "preflight": {
            "long_mode": False,
            "long_mode_reasons": [],
            "recommended_notebooklm_sources": 1,
            "recommended_base_name": None,
            "truncation_risks": [] if looks_like_pdf else ["not_pdf_header"],
        },
    }


def recommend_base_name(title: str | None, date_published: str | None) -> str | None:
    if not title:
        return None
    date_part = None
    if date_published:
        match = re.search(r"(\d{4})[-/](\d{2})[-/](\d{2})", date_published)
        if match:
            date_part = "".join(match.groups())
    compact = re.sub(r"\s+", "", title)
    compact = compact.replace("｜", "-").replace("|", "-")
    compact = re.sub(r'[\\/:*?"<>|#%&{}$!@`+=]', "-", compact)
    compact = re.sub(r"-+", "-", compact).strip("-")
    if len(compact) > 36:
        compact = compact[:36].rstrip("-")
    return f"{compact}-{date_part}" if date_part else compact


def preflight_text(result: dict[str, Any]) -> str:
    lines = [
        f"Source: {result.get('source')}",
        f"Final URL: {result.get('final_url') or ''}",
        f"Kind: {result.get('source_kind')}",
        f"Title: {result.get('title') or ''}",
        f"Author: {result.get('author') or ''}",
        f"Date: {result.get('date_published') or ''}",
        f"Canonical: {result.get('canonical_url') or ''}",
        f"Network category: {(result.get('network_profile') or {}).get('category') or ''}",
        f"Recommended capture: {(result.get('network_profile') or {}).get('recommended_capture') or ''}",
    ]
    if result.get("source_kind") in {"html", "text", "markdown"}:
        sohu = result.get("sohu") or {}
        text = result.get("text") or {}
        images = result.get("images") or {}
        lines.extend(
            [
                f"Sohu hiddenRatio: {sohu.get('hiddenRatio')}",
                f"Extraction method: {(result.get('extraction') or {}).get('method')}",
                f"Content type: {(result.get('content_profile') or {}).get('content_type')}",
                f"Package mode: {(result.get('content_profile') or {}).get('recommended_package_mode')}",
                f"Paragraphs: {text.get('paragraph_count')}",
                f"Text characters: {text.get('character_count')}",
                f"Images: {images.get('count')}",
            ]
        )
    preflight = result.get("preflight") or {}
    lines.extend(
        [
            f"Long mode: {preflight.get('long_mode')}",
            f"Long mode reasons: {', '.join(preflight.get('long_mode_reasons') or [])}",
            f"Recommended NotebookLM source count: {preflight.get('recommended_notebooklm_sources')}",
            f"Recommended base name: {preflight.get('recommended_base_name') or ''}",
            f"Truncation risks: {', '.join(preflight.get('truncation_risks') or [])}",
            "Angle suggestions:",
        ]
    )
    for angle in ((result.get("content_profile") or {}).get("angle_suggestions") or []):
        lines.append(f"- {angle}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="URL, HTML file, or PDF file.")
    parser.add_argument("--dry-run", action="store_true", help="Only print the JSON preflight result.")
    parser.add_argument("--output-dir", type=Path, help="Write source manifest and preflight text here.")
    parser.add_argument("--base", help="Output filename base when writing files.")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()

    raw, meta = read_source(args.source, args.timeout)
    source_hint = (meta.get("content_type") or meta.get("source") or "").lower()
    source_suffix = Path(str(meta.get("source") or "")).suffix.lower()
    if raw.startswith(b"%PDF") or source_hint.endswith(".pdf") or "application/pdf" in source_hint:
        result = inspect_pdf(raw, meta)
    elif source_suffix in TEXT_EXTENSIONS or "text/plain" in source_hint or "text/markdown" in source_hint:
        source_kind = "markdown" if source_suffix in {".md", ".markdown"} or "markdown" in source_hint else "text"
        result = parse_plain_text(decode_bytes(raw), meta, source_kind)
    else:
        result = parse_html(decode_bytes(raw), meta)

    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not args.dry_run and args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        base = args.base or (result.get("preflight") or {}).get("recommended_base_name") or "source"
        manifest_path = args.output_dir / f"{base}-source-manifest.json"
        preflight_path = args.output_dir / f"{base}-source-preflight.txt"
        manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        preflight_path.write_text(preflight_text(result), encoding="utf-8")
        print(json.dumps({"written": [str(manifest_path), str(preflight_path)]}, ensure_ascii=False), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
