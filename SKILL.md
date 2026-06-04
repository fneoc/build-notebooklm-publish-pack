---
name: build-notebooklm-publish-pack
description: Build bilingual self-media publishing packages from arbitrary source content using NotebookLM video overviews, NotebookLM or locally generated infographics, ratio-masked images, and platform-specific publishing copy. Use when the user wants to turn an article, report, PDF, webpage, notes, transcript, or topic brief into Chinese and English videos/images plus publish-ready files for channels such as 视频号, BILIBILI, TikTok, YouTube Shorts, 小红书, or LinkedIn.
---

# Build NotebookLM Publish Pack

## Overview

Turn any sufficiently source-backed content into a dated publishing package with Chinese and English NotebookLM media, image variants, and channel-ready copy. Treat NotebookLM state as evidence-sensitive: verify the source count, visible language, downloaded files, and final filenames before claiming completion.

## Fast Decision

1. If the user names a specific source, date, folder, or content URL, resolve that first and create a package folder.
2. If the user wants "继续", "resume", or says assets already exist, audit the folder, Downloads, and any open NotebookLM tab before reusing anything.
3. If the package depends on NotebookLM, require a clean or verified single-source notebook per language/source set. Visible counts such as `2 个来源`, `5 个来源`, or unexpected old titles are contamination until disproved.
4. If NotebookLM is unavailable or generation is blocked, produce the source archive, local infographic fallback, publish copy, and an explicit blocker report instead of inventing media status.
5. If the user asks for a fully generalized workflow, avoid source-specific names such as `AI速递` unless they provide that brand or series.

## Workflow

1. Gather package inputs.
   - Source: URL, local file, PDF, notes, transcript, or user-provided brief.
   - Content title, target date, brand or series name, target audience, and platform list.
   - Output root. Default to the current workspace or a dated subfolder when the user gives no root.
   - Required languages. Default to Chinese plus English when the user asks for bilingual output.
2. Normalize the source archive.
   - Save or generate a source document suitable for NotebookLM, usually a PDF plus a text/HTML mirror.
   - Record title, source URL or file path, publication date if applicable, and extraction caveats.
   - For webpages, verify folded/hidden sections before summarizing.
   - Run `scripts/prepare_source.py <url-or-file> --dry-run` for webpages or long sources; keep the resulting manifest/preflight in the package when building.
   - For JS-heavy pages, video pages, social posts, paywalled pages, or blocked network content, read `references/network-source-handling.md`.
3. Choose the content strategy.
   - Use the preflight `content_profile` to pick a package mode and primary angle.
   - Run `scripts/draft_pack_plan.py <source-manifest.json> --output-dir <package-folder>` after saving the source manifest.
   - For stronger hooks and platform planning, read `references/content-strategy.md`.
4. Build the NotebookLM inputs.
   - Prefer one clean notebook for the Chinese package and one clean notebook for the English package when language outputs differ.
   - Upload only the intended source document(s).
   - Verify the visible source count before generating video or infographics.
   - For detailed NotebookLM handling, read `references/notebooklm-workflow.md`.
5. Download or create media.
   - Chinese video overview MP4.
   - English video overview MP4, or an English post-processed video when the user starts from an existing NotebookLM MP4.
   - NotebookLM infographics when available.
   - Local fallback or polished variants when NotebookLM images are missing.
   - Use `scripts/make_ratio_masks.py` for vertical and square/rich-preview mask variants.
6. Create publish files.
   - Generate one file per platform rather than one blended caption.
   - Include title, description/caption, hashtags, upload filenames, optional cover suggestion, location/scheduling notes only when relevant.
   - Treat `publish-draft-*` files from `draft_pack_plan.py` as starting points; final publish files should use the platform filenames in `references/output-contract.md`.
   - For platform fields, read `references/platform-publish-fields.md`.
7. Validate the final package.
   - Run `scripts/audit_publish_pack.py <package-folder>` to check likely deliverables and media dimensions.
   - Verify MP4s with `ffprobe` when available.
   - Verify image aspect ratios with Pillow or the audit script.
   - Report concrete saved paths and blockers.

## Output Contract

Use the pattern in `references/output-contract.md`. At minimum, a complete package should contain:

- source archive: PDF or equivalent source document, plus text/HTML when feasible
- Chinese summary or script
- English summary or script
- Chinese NotebookLM video MP4
- English NotebookLM video MP4
- at least one infographic or cover image
- vertical and square/rich-preview image variants when publishing to short-video platforms
- platform-specific publish-info text files
- execution note with validation results and blockers

## Happy Path Commands

```bash
scripts/prepare_source.py "<url-or-file>" --output-dir "<package-folder>" --base "<base>"
scripts/draft_pack_plan.py "<package-folder>/<base>-source-manifest.json" --output-dir "<package-folder>" --base "<base>"
scripts/audit_publish_pack.py "<package-folder>" --strict
```

Use `--dry-run` on `prepare_source.py` when evaluating an unfamiliar website before writing package files.
Run `scripts/self_test.py` after modifying this skill.

## Quality Rules

1. Do not claim a NotebookLM output exists until the file is visible on disk and verified.
2. Do not reuse an existing notebook unless the visible source count and content title match the package.
3. Do not skip current-state audits because a previous run or memory says the package is complete.
4. Keep bulky process materials out of the final folder unless the user needs them. Prefer a `process-materials/` subfolder or `/private/tmp` for temporary video work.
5. Preserve the user's brand, channel naming, and exact filenames when provided.
6. If a platform has different Chinese and English audiences, write separate copy rather than translating mechanically.

## Resources

- `scripts/audit_publish_pack.py`: audit deliverables, media dimensions, obvious missing files, and optional expected terms.
- `scripts/prepare_source.py`: preflight URLs, HTML, and PDFs; for Sohu pages, detect folded content, text length, image count, and long webpage mode.
- `scripts/draft_pack_plan.py`: turn a source manifest into bilingual briefing companions, NotebookLM prompts, and a publish operations checklist.
- `scripts/make_ratio_masks.py`: create blurred-background ratio variants without cropping source text.
- `scripts/self_test.py`: local regression test for generic HTML, Markdown, valid media audit, and bad media rejection.
- `references/content-strategy.md`: package modes, angle selection, bilingual handling, and self-media operating loop.
- `references/network-source-handling.md`: URL/source fallback guidance for JS-heavy pages, video pages, social posts, paywalls, and copied text.
- `references/notebooklm-workflow.md`: clean-source NotebookLM workflow and blocker handling.
- `references/output-contract.md`: generic package folder and filename contract.
- `references/platform-publish-fields.md`: channel-specific publish-copy fields.

## Common Prompts

- "Use this article to build a Chinese/English NotebookLM publishing package for 视频号, BILIBILI, and TikTok."
- "Continue the package in this folder, verify what already exists, and finish missing media/copy."
- "Turn this PDF into bilingual short-video assets and platform publishing text."
- "NotebookLM already made the English MP4; package it and create the publish copy."
