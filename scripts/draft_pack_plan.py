#!/usr/bin/env python3
"""Draft content-operation files from a source preflight manifest."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PLATFORMS = ["wechat-video", "bilibili", "tiktok-en", "linkedin"]


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read source manifest: {path}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("Source manifest must be a JSON object.")
    return payload


def safe_base(value: str | None, fallback: str = "publish-pack") -> str:
    raw = value or fallback
    raw = re.sub(r"\s+", "", raw)
    raw = raw.replace("｜", "-").replace("|", "-")
    raw = re.sub(r'[\\/:*?"<>|#%&{}$!@`+=]', "-", raw)
    raw = re.sub(r"-+", "-", raw).strip("-")
    return raw[:60].rstrip("-") or fallback


def brief_source(manifest: dict[str, Any]) -> dict[str, Any]:
    text = manifest.get("text") if isinstance(manifest.get("text"), dict) else {}
    profile = manifest.get("content_profile") if isinstance(manifest.get("content_profile"), dict) else {}
    preflight = manifest.get("preflight") if isinstance(manifest.get("preflight"), dict) else {}
    images = manifest.get("images") if isinstance(manifest.get("images"), dict) else {}
    network_profile = manifest.get("network_profile") if isinstance(manifest.get("network_profile"), dict) else {}
    return {
        "title": manifest.get("title") or "",
        "author": manifest.get("author") or "",
        "date_published": manifest.get("date_published") or "",
        "source": manifest.get("canonical_url") or manifest.get("final_url") or manifest.get("source") or "",
        "description": manifest.get("description") or "",
        "content_type": profile.get("content_type") or "general_article",
        "package_mode": profile.get("recommended_package_mode") or "standard_article",
        "angles": profile.get("angle_suggestions") or [],
        "paragraph_count": text.get("paragraph_count"),
        "character_count": text.get("character_count"),
        "image_count": images.get("count"),
        "network_category": network_profile.get("category") or "",
        "recommended_capture": network_profile.get("recommended_capture") or "",
        "expected_notebooklm_sources": preflight.get("recommended_notebooklm_sources") or 1,
        "long_mode_reasons": preflight.get("long_mode_reasons") or [],
        "truncation_risks": preflight.get("truncation_risks") or [],
        "first_paragraphs": text.get("first_paragraphs") or [],
        "last_paragraphs": text.get("last_paragraphs") or [],
    }


def decision_gates(source: dict[str, Any], platforms: list[str], languages: list[str]) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    angles = source.get("angles") or []
    if len(angles) > 1:
        gates.append(
            {
                "id": "primary_angle",
                "prompt": "Choose one primary angle for the first publish wave.",
                "default": angles[0],
                "options": angles[:5],
                "why": "The primary angle changes the hook, the NotebookLM emphasis, and the platform drafts.",
            }
        )
    if source.get("package_mode") == "long_report":
        gates.append(
            {
                "id": "notebooklm_mode",
                "prompt": "Confirm whether to keep the long-report two-source notebook plan or force strict single-source NotebookLM.",
                "default": "two-source long-report mode",
                "options": [
                    "two-source long-report mode",
                    "strict single-source NotebookLM",
                ],
                "why": "Long reports can legitimately use a source-derived briefing companion, but some users prefer strict single-source notebooks.",
            }
        )
    if len(platforms) > 2 and len(languages) > 1:
        gates.append(
            {
                "id": "publish_priority",
                "prompt": "Confirm which publish surface should be treated as the lead asset.",
                "default": platforms[0] if platforms else "wechat-video",
                "options": platforms[:4] if platforms else [],
                "why": "This helps prioritize cover text, hook length, and which draft should be polished first.",
            }
        )
    return gates


def zh_companion(source: dict[str, Any], platforms: list[str]) -> str:
    angles = "\n".join(f"- {angle}" for angle in source["angles"]) or "- key tension"
    first = "\n".join(f"> {p}" for p in source["first_paragraphs"][:5])
    last = "\n".join(f"> {p}" for p in source["last_paragraphs"][-5:])
    return f"""# {source['title']}｜发布包简报伴侣

此文件是同源派生 briefing companion，用于帮助 NotebookLM 和发布文案保持结构清晰。它不是第二个外部信息来源。

## 来源

- 作者/机构：{source['author']}
- 发布时间：{source['date_published']}
- 来源链接：{source['source']}
- 内容类型：{source['content_type']}
- 发布包模式：{source['package_mode']}
- 预计 NotebookLM 来源数：{source['expected_notebooklm_sources']}
- 正文字数/段落/图片：{source['character_count']} / {source['paragraph_count']} / {source['image_count']}

## 可选内容角度

{angles}

## 短视频核心叙事

1. 先提出冲突：这篇内容中最反直觉、最有讨论度的问题是什么？
2. 再给判断：作者给出的核心解释是什么？
3. 最后给行动：自媒体观众看完能立刻记住或实践什么？

## 长内容核心叙事

1. 这篇内容的主命题是什么？
2. 它依赖哪些关键证据、案例或数据？
3. 对管理者、创作者、从业者分别意味着什么？
4. 哪些观点适合做成图文卡片或视频章节？

## 平台

{", ".join(platforms)}

## 开头线索

{first}

## 结尾线索

{last}
"""


def en_companion(source: dict[str, Any], platforms: list[str]) -> str:
    angles = "\n".join(f"- {angle}" for angle in source["angles"]) or "- key tension"
    return f"""# {source['title']} | Publishing Brief Companion

This is a source-derived briefing companion for NotebookLM and publishing copy. It is not an independent external source.

## Source

- Author / organization: {source['author']}
- Published: {source['date_published']}
- Source URL: {source['source']}
- Content type: {source['content_type']}
- Package mode: {source['package_mode']}
- Expected NotebookLM sources: {source['expected_notebooklm_sources']}
- Text / paragraphs / images: {source['character_count']} / {source['paragraph_count']} / {source['image_count']}

## Editorial Angles

{angles}

## Video Story

1. Lead with the tension, not the tool.
2. Explain the core argument in plain language.
3. End with a practical takeaway for operators, creators, or managers.

## Long-Form Story

1. Main thesis.
2. Key evidence or cases.
3. Implications for teams and decision makers.
4. Visual moments that can become cards, covers, or chapters.

## Platforms

{", ".join(platforms)}
"""


def notebooklm_prompt(source: dict[str, Any], language: str, platforms: list[str]) -> str:
    if language == "zh":
        return f"""请基于上传的同源材料，生成一个适合自媒体发布的视频概览。

要求：
1. 语言使用中文，面向对科技、AI、商业和组织变革感兴趣的观众。
2. 先讲清楚这篇内容最有讨论度的矛盾或问题，再讲核心观点，最后给可执行启发。
3. 不要逐段复述报告。优先提炼 3-5 个有传播价值的观点。
4. 如果材料包含 briefing companion，它只是原文的同源结构化摘要，不是独立外部来源。
5. 适配平台：{", ".join(platforms)}。

标题：{source['title']}
内容类型：{source['content_type']}
建议角度：{", ".join(source['angles'])}
"""
    return f"""Create a media-ready video overview from the uploaded source-derived materials.

Requirements:
1. Use natural English for a global audience interested in AI, technology, business, or organizational change.
2. Lead with the most interesting tension, explain the core argument, and end with an actionable takeaway.
3. Do not mechanically summarize every section. Select 3-5 high-signal ideas.
4. If a briefing companion is uploaded, treat it as a source-derived structure aid, not as a separate external source.
5. Target platforms: {", ".join(platforms)}.

Title: {source['title']}
Content type: {source['content_type']}
Suggested angles: {", ".join(source['angles'])}
"""


def content_plan(source: dict[str, Any], base: str, platforms: list[str], languages: list[str]) -> dict[str, Any]:
    return {
        "base": base,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "languages": languages,
        "platforms": platforms,
        "decision_gates": decision_gates(source, platforms, languages),
        "package_files": {
            "source_manifest": f"{base}-source-manifest.json",
            "source_preflight": f"{base}-source-preflight.txt",
            "briefing_companion_zh": f"{base}-briefing-companion-zh.md",
            "briefing_companion_en": f"{base}-briefing-companion-en.md",
            "notebooklm_prompt_zh": f"{base}-notebooklm-prompt-zh.txt",
            "notebooklm_prompt_en": f"{base}-notebooklm-prompt-en.txt",
            "notebooklm_downloads_manifest": f"{base}-notebooklm-downloads-manifest.json",
            "notebooklm_automation_log": f"{base}-notebooklm-automation-log.json",
            "publish_ops_checklist": f"{base}-publish-ops-checklist.md",
            "repurposing_calendar": f"{base}-repurposing-calendar.md",
            "publish_draft_wechat_video": f"{base}-publish-draft-wechat-video.txt",
            "publish_draft_bilibili": f"{base}-publish-draft-bilibili.txt",
            "publish_draft_tiktok_en": f"{base}-publish-draft-tiktok-en.txt",
            "publish_draft_linkedin": f"{base}-publish-draft-linkedin.txt",
        },
        "angle_matrix": [
            {
                "angle": angle,
                "best_for": "short video" if index < 4 else "carousel or long post",
                "watchout": "Verify against the original source before publishing.",
            }
            for index, angle in enumerate(source["angles"])
        ],
    }


def platform_publish_draft(source: dict[str, Any], platform: str, base: str) -> str:
    primary_angle = source["angles"][0] if source["angles"] else "key tension"
    backup_angle = source["angles"][1] if len(source["angles"]) > 1 else "practical takeaway"
    title = source["title"] or base
    if platform == "wechat-video":
        return f"""短标题：{title[:28]}

视频描述：
{title}
看点：{primary_angle}
启发：{backup_angle}
来源：{source['author'] or source['source']}

#AI #科技 #自媒体 #NotebookLM

上传文件名：
{base}-video-zh-notebooklm.mp4
{base}-infographic-vertical-3x4-mask.png
{base}-infographic-rich-4x3-mask.png
"""
    if platform == "bilibili":
        return f"""标题：{title}

简介：
这期把「{title}」做成一个 source-backed 发布包。
核心看点：{primary_angle}
进一步讨论：{backup_angle}

分区建议：知识 / 科技 / AI
标签：AI, 科技, NotebookLM, 自媒体运营

上传文件名：
{base}-video-zh-notebooklm.mp4
封面：{base}-infographic-horizontal.png
"""
    if platform in {"tiktok-en", "youtube-shorts-en"}:
        return f"""Title: {title[:70]}

Caption:
The key tension: {primary_angle}.
The practical takeaway: {backup_angle}.
Source-backed, edited for a short-form audience.

#AI #Tech #NotebookLM #CreatorWorkflow

Upload filename:
{base}-video-en-notebooklm.mp4
Cover:
{base}-infographic-horizontal.png
"""
    if platform == "linkedin":
        return f"""Headline: {title}

Post draft:
One useful way to read this source: {primary_angle}.

The operational takeaway is not just to summarize the material, but to turn it into a repeatable publishing loop: short video, deep summary, visual card, and follow-up Q&A.

Source: {source['source']}

Assets:
- {base}-video-en-notebooklm.mp4
- {base}-infographic-horizontal.png
"""
    return f"""Platform: {platform}
Title: {title}
Primary angle: {primary_angle}
Backup angle: {backup_angle}
Source: {source['source']}
"""


def repurposing_calendar(source: dict[str, Any], platforms: list[str]) -> str:
    primary_angle = source["angles"][0] if source["angles"] else "key tension"
    backup_angle = source["angles"][1] if len(source["angles"]) > 1 else "practical takeaway"
    return f"""# 7-Day Repurposing Calendar

Source: {source['title']}

## Day 0: Primary Short Video

- Angle: {primary_angle}
- Platforms: {", ".join(platforms)}
- Asset: NotebookLM video overview plus cover/infographic
- Goal: introduce the topic with one clear tension

## Day 1: Deep Summary

- Angle: {backup_angle}
- Format: long caption, BILIBILI column, LinkedIn post, or WeChat article
- Goal: explain the argument and why it matters

## Day 2: Visual Card Or Carousel

- Angle: visual framework or checklist
- Format: infographic, carousel, or image post
- Goal: give viewers something saveable

## Day 3: Practical Checklist

- Angle: what to do next
- Format: checklist post or short follow-up video
- Goal: convert insight into action

## Day 4: Quote Or Contrarian Clip

- Angle: strongest quote, surprising detail, or objection
- Format: short clip, quote card, or comment reply
- Goal: create discussion

## Day 5: Audience Q&A

- Angle: answer likely questions from comments
- Format: Q&A post or threaded update
- Goal: keep the topic alive without repeating the same caption

## Day 6: Roundup And Next Hook

- Angle: what this source connects to next
- Format: weekly roundup or teaser for the next package
- Goal: build a recurring self-media rhythm
"""


def ops_checklist(source: dict[str, Any], platforms: list[str]) -> str:
    platform_lines = "\n".join(f"- [ ] {platform}: publish file names match final assets" for platform in platforms)
    gates = decision_gates(source, platforms, ["zh", "en"])
    gate_lines = "\n".join(
        f"- [ ] {gate['prompt']} Default: {gate['default']}. Why: {gate['why']}"
        for gate in gates
    ) or "- none"
    risks = "\n".join(f"- {risk}" for risk in source["truncation_risks"]) or "- none detected"
    return f"""# Publish Ops Checklist

## Source

- Title: {source['title']}
- Expected NotebookLM sources: {source['expected_notebooklm_sources']}
- Long mode reasons: {", ".join(source['long_mode_reasons']) or "none"}

## Before NotebookLM

- [ ] Source PDF or source document exists.
- [ ] Source manifest and preflight are saved.
- [ ] If using a briefing companion, label it as source-derived.
- [ ] Browser automation is attempted before NotebookLM is reported blocked.
- [ ] A clean NotebookLM notebook is created or verified empty through browser automation.
- [ ] Only the intended source file(s) are uploaded automatically.
- [ ] NotebookLM visible source count equals {source['expected_notebooklm_sources']}.
- [ ] Video overview generation is triggered through NotebookLM automation.
- [ ] Infographic/image generation is triggered through NotebookLM automation when the UI exposes it.
- [ ] For long reports, allow about 15 minutes for video generation and poll every 60-90 seconds before rebuilding.
- [ ] If a download event times out, check `~/Downloads` by modification time before marking the asset blocked.
- [ ] NotebookLM automation log records browser surface, notebook URL/title, uploaded filenames, generation status, downloads, and blockers.
- [ ] Execution note names which video/image files are official NotebookLM downloads and which are local fallback.

## Content Quality

- [ ] The hook names the real tension or surprising point.
- [ ] The summary is not a mechanical section-by-section recap.
- [ ] Chinese and English copy are separately written for their audiences.
- [ ] Claims are traceable to the original source.

## Decision Gaps

{gate_lines}

## Platforms

{platform_lines}

## Truncation Risks

{risks}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--base")
    parser.add_argument("--platform", action="append", dest="platforms", help="Repeat to set platforms.")
    parser.add_argument("--language", action="append", dest="languages", choices=["zh", "en"], help="Repeat to set languages.")
    args = parser.parse_args()

    manifest = load_manifest(args.source_manifest)
    source = brief_source(manifest)
    base = safe_base(args.base or (manifest.get("preflight") or {}).get("recommended_base_name") or source["title"])
    platforms = args.platforms or DEFAULT_PLATFORMS
    languages = args.languages or ["zh", "en"]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, str] = {}
    plan = content_plan(source, base, platforms, languages)
    plan_path = args.output_dir / f"{base}-content-plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    outputs["content_plan"] = str(plan_path)

    if "zh" in languages:
        path = args.output_dir / f"{base}-briefing-companion-zh.md"
        path.write_text(zh_companion(source, platforms), encoding="utf-8")
        outputs["briefing_companion_zh"] = str(path)
        prompt_path = args.output_dir / f"{base}-notebooklm-prompt-zh.txt"
        prompt_path.write_text(notebooklm_prompt(source, "zh", platforms), encoding="utf-8")
        outputs["notebooklm_prompt_zh"] = str(prompt_path)
    if "en" in languages:
        path = args.output_dir / f"{base}-briefing-companion-en.md"
        path.write_text(en_companion(source, platforms), encoding="utf-8")
        outputs["briefing_companion_en"] = str(path)
        prompt_path = args.output_dir / f"{base}-notebooklm-prompt-en.txt"
        prompt_path.write_text(notebooklm_prompt(source, "en", platforms), encoding="utf-8")
        outputs["notebooklm_prompt_en"] = str(prompt_path)

    checklist_path = args.output_dir / f"{base}-publish-ops-checklist.md"
    checklist_path.write_text(ops_checklist(source, platforms), encoding="utf-8")
    outputs["publish_ops_checklist"] = str(checklist_path)
    calendar_path = args.output_dir / f"{base}-repurposing-calendar.md"
    calendar_path.write_text(repurposing_calendar(source, platforms), encoding="utf-8")
    outputs["repurposing_calendar"] = str(calendar_path)
    for platform in platforms:
        safe_platform = safe_base(platform, "platform").lower()
        path = args.output_dir / f"{base}-publish-draft-{safe_platform}.txt"
        path.write_text(platform_publish_draft(source, platform, base), encoding="utf-8")
        outputs[f"publish_draft_{safe_platform}"] = str(path)
    print(json.dumps({"outputs": outputs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
