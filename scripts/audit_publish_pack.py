#!/usr/bin/env python3
"""Audit a NotebookLM/self-media publish package folder."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:  # pragma: no cover - environment dependent
    Image = None


TEXT_SUFFIXES = {".txt", ".md", ".html", ".json"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v"}
SOURCE_SUFFIXES = {".pdf", ".html", ".txt", ".md"}
PUBLISH_MARKERS = (
    "publish",
    "发布",
    "视频号",
    "bilibili",
    "tiktok",
    "youtube",
    "shorts",
    "xiaohongshu",
    "小红书",
    "linkedin",
)
ENGLISH_MARKERS = ("english", "-en", "_en", "英文")
SOURCE_MARKERS = (
    "source",
    "原文",
    "正文",
    "article",
    "html",
    "pdf",
    "manifest",
    "preflight",
    "briefing-companion",
)
SUMMARY_MARKERS = ("summary", "script", "摘要", "文案", "briefing-companion", "prompt")
EXECUTION_MARKERS = ("execution-note", "execution", "执行说明", "preflight")
OFFICIAL_NOTEBOOKLM_ASSETS = ("video_zh", "video_en", "infographic")


OFFICIAL_NOTEBOOKLM_MARKERS = {
    "video_zh": (
        "chinese notebooklm mp4",
        "chinese notebooklm video",
        "zh notebooklm mp4",
        "zh notebooklm video",
        "中文 notebooklm mp4",
        "中文 notebooklm 视频",
        "notebooklm 中文视频",
    ),
    "video_en": (
        "english notebooklm mp4",
        "english notebooklm video",
        "en notebooklm mp4",
        "en notebooklm video",
        "英文 notebooklm mp4",
        "英文 notebooklm 视频",
        "notebooklm 英文视频",
    ),
    "infographic": (
        "notebooklm infographic",
        "notebooklm image",
        "notebooklm png",
        "notebooklm 信息图",
        "notebooklm 图片",
    ),
}


FALLBACK_NOTEBOOKLM_MARKERS = {
    "video_zh": (
        "chinese mp4 is still the locally generated fallback",
        "chinese notebooklm mp4 is still pending",
        "zh mp4 is still the locally generated fallback",
        "中文视频仍为本地",
        "中文 notebooklm 视频待生成",
    ),
    "video_en": (
        "english mp4 is still the locally generated fallback",
        "english notebooklm mp4 is still pending",
        "en mp4 is still the locally generated fallback",
        "英文视频仍为本地",
        "英文 notebooklm 视频待生成",
    ),
    "infographic": (
        "infographic is still the locally generated fallback",
        "notebooklm infographic is still pending",
        "信息图仍为本地",
        "notebooklm 信息图待生成",
    ),
}


def ffprobe(path: Path) -> dict[str, Any] | None:
    if not shutil.which("ffprobe"):
        return None
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,duration",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return {"error": completed.stderr.strip() or "ffprobe failed"}
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"error": "ffprobe returned invalid JSON"}
    streams = payload.get("streams") or []
    return streams[0] if streams else {"error": "no video stream"}


def image_info(path: Path) -> dict[str, Any] | None:
    if Image is None:
        return None
    try:
        with Image.open(path) as image:
            width, height = image.size
    except Exception as exc:  # pragma: no cover - file dependent
        return {"error": str(exc)}
    return {
        "width": width,
        "height": height,
        "aspect_ratio": round(width / height, 4) if height else None,
    }


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:200_000]
    except OSError:
        return ""


def load_manifest_roles(files: list[Path]) -> dict[str, str]:
    roles: dict[str, str] = {}
    for path in files:
        lower = path.name.lower()
        if path.suffix.lower() != ".json" or "manifest" not in lower:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        declared_files = payload.get("files") if isinstance(payload, dict) else None
        if isinstance(declared_files, list):
            for item in declared_files:
                if isinstance(item, dict) and item.get("path") and item.get("role"):
                    roles[Path(str(item["path"])).name] = str(item["role"])
        if lower.endswith("-source-manifest.json"):
            roles[path.name] = "source_manifest"
    return roles


def has_marker(name: str, markers: tuple[str, ...]) -> bool:
    return any(marker in name for marker in markers)


def classify_file(path: Path, manifest_roles: dict[str, str]) -> list[str]:
    role = manifest_roles.get(path.name, "").lower()
    lower = path.name.lower()
    suffix = path.suffix.lower()
    labels: list[str] = []

    if suffix in VIDEO_SUFFIXES:
        labels.append("videos")
        if has_marker(lower, ENGLISH_MARKERS):
            labels.append("english_videos")
    if suffix in IMAGE_SUFFIXES:
        labels.append("images")
    if "publish" in role or (suffix in TEXT_SUFFIXES and has_marker(lower, PUBLISH_MARKERS)):
        labels.append("publish_files")
    if "execution" in role or (suffix in TEXT_SUFFIXES and has_marker(lower, EXECUTION_MARKERS)):
        labels.append("execution_notes")
    if "summary" in role or "script" in role or (suffix in TEXT_SUFFIXES and has_marker(lower, SUMMARY_MARKERS)):
        labels.append("summaries_or_scripts")
    if (
        "source" in role
        or suffix == ".pdf"
        or lower.endswith("-source-manifest.json")
        or lower.endswith("-source-preflight.txt")
        or (suffix in SOURCE_SUFFIXES and has_marker(lower, SOURCE_MARKERS) and "publish_files" not in labels)
    ):
        labels.append("sources")
    return labels


def classify(files: list[Path]) -> dict[str, list[str]]:
    categories: dict[str, list[str]] = {
        "sources": [],
        "videos": [],
        "english_videos": [],
        "images": [],
        "publish_files": [],
        "summaries_or_scripts": [],
        "execution_notes": [],
    }
    manifest_roles = load_manifest_roles(files)
    for path in files:
        for label in classify_file(path, manifest_roles):
            categories[label].append(path.name)
    return categories


def parse_expected_role(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("--expect-file-role must look like role=filename-pattern")
    role, pattern = raw.split("=", 1)
    role = role.strip()
    pattern = pattern.strip()
    if not role or not pattern:
        raise argparse.ArgumentTypeError("--expect-file-role must look like role=filename-pattern")
    return role, pattern


def matches_pattern(filename: str, pattern: str) -> bool:
    if pattern in filename:
        return True
    try:
        return bool(re.search(pattern, filename))
    except re.error:
        return False


def notebooklm_candidates(asset: str, files: list[Path]) -> list[str]:
    names = [path.name for path in files]
    if asset == "video_zh":
        return [
            name
            for name in names
            if Path(name).suffix.lower() in VIDEO_SUFFIXES
            and "notebooklm" in name.lower()
            and ("video-zh" in name.lower() or "-zh" in name.lower() or "中文" in name)
        ]
    if asset == "video_en":
        return [
            name
            for name in names
            if Path(name).suffix.lower() in VIDEO_SUFFIXES
            and "notebooklm" in name.lower()
            and ("video-en" in name.lower() or "-en" in name.lower() or "english" in name.lower() or "英文" in name)
        ]
    if asset == "infographic":
        return [
            name
            for name in names
            if Path(name).suffix.lower() in IMAGE_SUFFIXES
            and ("notebooklm" in name.lower() or "notebooklm" in Path(name).stem.lower())
        ]
    raise ValueError(f"Unknown NotebookLM asset: {asset}")


def has_any_text_marker(text_blob: str, markers: tuple[str, ...]) -> bool:
    lower = text_blob.lower()
    return any(marker.lower() in lower for marker in markers)


def official_notebooklm_status(asset: str, files: list[Path], text_blob: str) -> dict[str, Any]:
    candidates = notebooklm_candidates(asset, files)
    has_positive_note = has_any_text_marker(text_blob, OFFICIAL_NOTEBOOKLM_MARKERS[asset])
    has_fallback_note = has_any_text_marker(text_blob, FALLBACK_NOTEBOOKLM_MARKERS[asset])

    if candidates and has_positive_note and not has_fallback_note:
        status = "verified"
    elif not candidates:
        status = "missing"
    elif has_fallback_note:
        status = "fallback_or_pending"
    else:
        status = "unverified"

    return {
        "status": status,
        "candidates": candidates,
        "note_evidence": {
            "positive_marker_found": has_positive_note,
            "fallback_marker_found": has_fallback_note,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--expect-term", action="append", default=[], help="Term that should appear in text-like package files.")
    parser.add_argument("--expect-source-count", type=int, default=None, help="Expected number of source files.")
    parser.add_argument(
        "--expect-file-role",
        action="append",
        type=parse_expected_role,
        default=[],
        help="Require at least one file in a category, e.g. sources=source-manifest or publish_files=tiktok.",
    )
    parser.add_argument(
        "--expect-official-notebooklm",
        action="append",
        choices=OFFICIAL_NOTEBOOKLM_ASSETS,
        default=[],
        help="Require a verified NotebookLM-origin asset: video_zh, video_en, or infographic.",
    )
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when likely deliverables are missing.")
    args = parser.parse_args()

    if not args.folder.exists() or not args.folder.is_dir():
        raise SystemExit(f"Missing package folder: {args.folder}")

    files = sorted([path for path in args.folder.iterdir() if path.is_file()])
    categories = classify(files)
    missing = []
    for key in ("sources", "publish_files"):
        if not categories[key]:
            missing.append(key)
    if categories["videos"] and not categories["english_videos"]:
        missing.append("english_videos")

    images = {path.name: image_info(path) for path in files if path.suffix.lower() in IMAGE_SUFFIXES}
    videos = {path.name: ffprobe(path) for path in files if path.suffix.lower() in VIDEO_SUFFIXES}
    media_errors = []
    for filename, info in {**images, **videos}.items():
        if isinstance(info, dict) and info.get("error"):
            media_errors.append({"file": filename, "error": info["error"]})

    text_blob = "\n".join(read_text(path) for path in files if path.suffix.lower() in TEXT_SUFFIXES)
    missing_terms = [term for term in args.expect_term if term not in text_blob]
    source_count_mismatch = None
    if args.expect_source_count is not None and len(categories["sources"]) != args.expect_source_count:
        source_count_mismatch = {
            "expected": args.expect_source_count,
            "actual": len(categories["sources"]),
        }
    missing_file_roles = []
    for role, pattern in args.expect_file_role:
        role_files = categories.get(role, [])
        if not any(matches_pattern(filename, pattern) for filename in role_files):
            missing_file_roles.append({"role": role, "pattern": pattern})
    official_notebooklm = {
        asset: official_notebooklm_status(asset, files, text_blob)
        for asset in OFFICIAL_NOTEBOOKLM_ASSETS
    }
    missing_official_notebooklm = [
        {"asset": asset, **official_notebooklm[asset]}
        for asset in args.expect_official_notebooklm
        if official_notebooklm[asset]["status"] != "verified"
    ]

    status = (
        "complete"
        if (
            not missing
            and not missing_terms
            and not source_count_mismatch
            and not missing_file_roles
            and not missing_official_notebooklm
            and not media_errors
        )
        else "partial"
    )
    result = {
        "folder": str(args.folder),
        "status": status,
        "file_count": len(files),
        "categories": categories,
        "missing_categories": missing,
        "missing_expected_terms": missing_terms,
        "source_count_mismatch": source_count_mismatch,
        "missing_file_roles": missing_file_roles,
        "official_notebooklm": official_notebooklm,
        "missing_official_notebooklm": missing_official_notebooklm,
        "media_errors": media_errors,
        "images": images,
        "videos": videos,
        "notes": {
            "pillow_available": Image is not None,
            "ffprobe_available": shutil.which("ffprobe") is not None,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.strict and status != "complete":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
