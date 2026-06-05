#!/usr/bin/env python3
"""Run local regression tests for build-notebooklm-publish-pack."""

from __future__ import annotations

import json
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("Pillow is required for self_test.py") from exc


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "scripts" / "prepare_source.py"
DRAFT = ROOT / "scripts" / "draft_pack_plan.py"
AUDIT = ROOT / "scripts" / "audit_publish_pack.py"


def load_prepare_module():
    spec = importlib.util.spec_from_file_location("prepare_source", PREPARE)
    if spec is None or spec.loader is None:
        raise AssertionError("Could not load prepare_source.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(cmd: list[str], expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if expect_success and completed.returncode != 0:
        raise AssertionError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    if not expect_success and completed.returncode == 0:
        raise AssertionError(f"Command unexpectedly succeeded: {' '.join(cmd)}\nSTDOUT:\n{completed.stdout}")
    return completed


def make_mp4(path: Path) -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required for self_test.py")
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x245880:s=640x360:d=1",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(path),
        ]
    )


def write_html_fixture(path: Path) -> None:
    path.write_text(
        """<!doctype html><html><head><title>AI Teams Are Becoming Smaller and Faster</title>
<meta name="description" content="A practical field report on how small AI-native teams ship faster with agents.">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","headline":"AI Teams Are Becoming Smaller and Faster","author":{"name":"Example Research Lab"},"datePublished":"2026-06-04T09:00:00+08:00","description":"A field study about agent workflows and team design."}</script>
</head><body><main><article><h1>AI Teams Are Becoming Smaller and Faster</h1>
<p>The surprising shift is not that teams use AI tools, but that the coordination model changes.</p>
<p>In one case study, a four-person team replaced status meetings with an agent-readable operating log.</p>
<p>Managers should look for a complete problem, a visible demo loop, and permission to use tools.</p>
<img src="https://example.com/team-chart.png" width="1200" height="675">
<p>The practical takeaway: start with one real project, not a company-wide training program.</p>
</article></main></body></html>""",
        encoding="utf-8",
    )


def write_markdown_fixture(path: Path) -> None:
    path.write_text(
        """---
title: AI Native Operations Playbook
author: Ops Lab
date: 2026-06-04
description: A practical guide for running self-media operations with AI workflows.
---

# AI Native Operations Playbook

The core tension is that creators can produce more content than they can operate.

A useful system starts with source-backed packages, not random prompts.

![Workflow map](https://example.com/workflow-map.png)

Teams should build a weekly loop: capture sources, produce bilingual media, publish short hooks, and follow up with deep summaries.
""",
        encoding="utf-8",
    )


def prepare_and_draft(source: Path, package_dir: Path, base: str) -> dict[str, object]:
    run([sys.executable, str(PREPARE), str(source), "--output-dir", str(package_dir), "--base", base])
    manifest = package_dir / f"{base}-source-manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    run(
        [
            sys.executable,
            str(DRAFT),
            str(manifest),
            "--output-dir",
            str(package_dir),
            "--base",
            base,
            "--platform",
            "wechat-video",
            "--platform",
            "bilibili",
            "--platform",
            "tiktok-en",
            "--platform",
            "linkedin",
        ]
    )
    return payload


def add_valid_media(package_dir: Path, base: str) -> None:
    Image.new("RGB", (1280, 720), (36, 88, 128)).save(package_dir / f"{base}-infographic-horizontal.png")
    make_mp4(package_dir / f"{base}-video-en-notebooklm.mp4")


def add_verified_notebooklm_assets(package_dir: Path, base: str) -> None:
    Image.new("RGB", (2752, 1536), (42, 114, 134)).save(package_dir / f"{base}-infographic-horizontal-notebooklm.png")
    make_mp4(package_dir / f"{base}-video-zh-notebooklm.mp4")
    (package_dir / f"{base}-execution-note.txt").write_text(
        "\n".join(
            [
                "NotebookLM state: visible source count verified before generation.",
                "Chinese NotebookLM MP4 downloaded from Downloads and copied into the package.",
                "NotebookLM infographic downloaded from the ready card and verified with Pillow.",
                "English MP4 is still the locally generated fallback.",
            ]
        ),
        encoding="utf-8",
    )


def audit_complete(package_dir: Path) -> None:
    run(
        [
            sys.executable,
            str(AUDIT),
            str(package_dir),
            "--expect-term",
            "NotebookLM",
            "--expect-file-role",
            "sources=source-manifest",
            "--expect-file-role",
            "sources=briefing-companion",
            "--expect-file-role",
            "publish_files=bilibili",
            "--strict",
        ]
    )


def audit_verified_notebooklm(package_dir: Path) -> None:
    run(
        [
            sys.executable,
            str(AUDIT),
            str(package_dir),
            "--expect-official-notebooklm",
            "video_zh",
            "--expect-official-notebooklm",
            "infographic",
            "--strict",
        ]
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="notebooklm-publish-pack-selftest-") as tmp:
        root = Path(tmp)
        prepare_module = load_prepare_module()
        assert prepare_module.source_profile("https://www.youtube.com/watch?v=abc")["category"] == "video_page"
        assert prepare_module.source_profile("https://www.xiaohongshu.com/explore/abc")["category"] == "social_post"

        html_source = root / "generic.html"
        html_package = root / "generic-pack"
        html_package.mkdir()
        write_html_fixture(html_source)
        html_manifest = prepare_and_draft(html_source, html_package, "generic")
        assert html_manifest["source_kind"] == "html"
        assert html_manifest["content_profile"]["content_type"] == "case_study"
        add_valid_media(html_package, "generic")
        add_verified_notebooklm_assets(html_package, "generic")
        audit_complete(html_package)
        audit_verified_notebooklm(html_package)

        md_source = root / "ops.md"
        md_package = root / "markdown-pack"
        md_package.mkdir()
        write_markdown_fixture(md_source)
        md_manifest = prepare_and_draft(md_source, md_package, "markdown")
        assert md_manifest["source_kind"] == "markdown"
        assert md_manifest["content_profile"]["content_type"] == "tutorial"
        md_plan = json.loads((md_package / "markdown-content-plan.json").read_text(encoding="utf-8"))
        assert md_plan["decision_gates"]
        assert md_plan["decision_gates"][0]["id"] == "primary_angle"
        assert md_plan["package_files"]["notebooklm_automation_log"] == "markdown-notebooklm-automation-log.json"
        md_checklist = (md_package / "markdown-publish-ops-checklist.md").read_text(encoding="utf-8")
        assert "Decision Gaps" in md_checklist
        assert "Browser automation is attempted before NotebookLM is reported blocked" in md_checklist
        assert "Video overview generation is triggered through NotebookLM automation" in md_checklist
        assert (md_package / "markdown-repurposing-calendar.md").exists()
        assert (md_package / "markdown-publish-draft-bilibili.txt").exists()
        assert not (md_package / "markdown-publish-bilibili.txt").exists()
        add_valid_media(md_package, "markdown")
        audit_complete(md_package)

        text_only_package = root / "text-only-pack"
        text_only_package.mkdir()
        (text_only_package / "text-only-source-manifest.json").write_text(
            json.dumps({"files": [{"path": "text-only-source-manifest.json", "role": "source_manifest"}]}, ensure_ascii=False),
            encoding="utf-8",
        )
        (text_only_package / "text-only-source-preflight.txt").write_text("NotebookLM\n", encoding="utf-8")
        (text_only_package / "text-only-briefing-companion-zh.md").write_text("NotebookLM\n", encoding="utf-8")
        (text_only_package / "text-only-publish-draft-wechat-video.txt").write_text("NotebookLM\n", encoding="utf-8")
        run([sys.executable, str(AUDIT), str(text_only_package), "--strict"])

        pdf_source = root / "report.pdf"
        pdf_source.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n")
        pdf_package = root / "pdf-pack"
        pdf_package.mkdir()
        run([sys.executable, str(PREPARE), str(pdf_source), "--output-dir", str(pdf_package), "--base", "pdf-report"])
        pdf_manifest = json.loads((pdf_package / "pdf-report-source-manifest.json").read_text(encoding="utf-8"))
        assert pdf_manifest["source_kind"] == "pdf"
        assert pdf_manifest["network_profile"]["category"] == "pdf_report"

        bad_package = root / "bad-pack"
        bad_package.mkdir()
        (bad_package / "bad-source-manifest.json").write_text('{"files":[]}', encoding="utf-8")
        (bad_package / "bad-briefing-companion-zh.md").write_text("NotebookLM", encoding="utf-8")
        (bad_package / "bad-publish-bilibili.txt").write_text("NotebookLM", encoding="utf-8")
        (bad_package / "bad-video-en-notebooklm.mp4").write_bytes(b"not an mp4")
        (bad_package / "bad-infographic.png").write_bytes(b"not a png")
        run([sys.executable, str(AUDIT), str(bad_package), "--strict"], expect_success=False)

        fallback_package = root / "fallback-pack"
        fallback_package.mkdir()
        (fallback_package / "fallback-source-manifest.json").write_text(
            json.dumps({"files": [{"path": "fallback-source-manifest.json", "role": "source_manifest"}]}, ensure_ascii=False),
            encoding="utf-8",
        )
        (fallback_package / "fallback-publish-bilibili.txt").write_text("NotebookLM\n", encoding="utf-8")
        (fallback_package / "fallback-execution-note.txt").write_text(
            "English MP4 is still the locally generated fallback.\n",
            encoding="utf-8",
        )
        make_mp4(fallback_package / "fallback-video-en-notebooklm.mp4")
        run(
            [
                sys.executable,
                str(AUDIT),
                str(fallback_package),
                "--expect-official-notebooklm",
                "video_en",
                "--strict",
            ],
            expect_success=False,
        )

    print("self_test ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
