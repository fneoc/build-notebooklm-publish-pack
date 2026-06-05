# Case Study: 睡前消息【2026-6-4】高考怕 KTV

This example documents a real end-to-end run of `build-notebooklm-publish-pack` on a user-pasted Chinese news digest. It is intentionally a process example: the raw article text, generated MP4 files, and full-size PNG files are not committed to the repository.

## Input

- Source title: 睡前消息【2026-6-4】高考怕KTV
- Source author: 睡前消息编辑部
- Source date: 2026-06-04 21:42
- Source form: user-pasted Markdown
- Primary angle: "考试前夜，谁在被按下暂停键？"
- Package base: `睡前消息-高考怕KTV-20260604`
- NotebookLM source strategy: strict single-source upload

The source covered five items:

- multiple local governments pausing KTV and entertainment venues during the Gaokao period.
- a reported SpaceX IPO item.
- Chinese acquisition pressure around Chilean transmission infrastructure.
- a proposed new unilateral U.S. tariff framework.
- China's Ministry of Education pushing admission notices back toward one page.

## Preflight Result

The source preflight classified the input as a short text-only article package:

- source kind: `markdown`
- package mode: `standard_article`
- paragraphs: 35
- text characters: 2172
- images: 0
- long mode: false
- recommended NotebookLM source count: 1
- truncation risks: none

Because the source was short and text-only, the run used one uploaded PDF rather than a long-report two-source setup.

## Run Flow

1. Save the pasted Markdown source as the canonical source archive.
2. Generate HTML, TXT, and PDF mirrors for upload and auditing.
3. Run source preflight and write `source-manifest.json` plus `source-preflight.txt`.
4. Generate bilingual briefing companions, NotebookLM prompts, scripts, summaries, platform drafts, and a 7-day repurposing calendar.
5. Open a logged-in Chrome NotebookLM session.
6. Create or claim a clean notebook.
7. Upload only `睡前消息-高考怕KTV-20260604.pdf`.
8. Verify visible source count equals `1`.
9. Generate the Chinese video overview and NotebookLM infographic.
10. Create a separate clean English run for the English video.
11. Download NotebookLM MP4/PNG outputs.
12. Verify videos with `ffprobe` and images with Pillow.
13. Copy official NotebookLM downloads into the package using output-contract filenames.
14. Create vertical and 4:3 masked image variants.
15. Run final strict audit with official NotebookLM expectations.

## Representative Commands

```bash
scripts/prepare_source.py "<source.md>" --output-dir "<package-folder>" --base "睡前消息-高考怕KTV-20260604"
scripts/draft_pack_plan.py "<package-folder>/睡前消息-高考怕KTV-20260604-source-manifest.json" --output-dir "<package-folder>" --base "睡前消息-高考怕KTV-20260604"
# Browser automation then follows references/notebooklm-automation.md.
scripts/audit_publish_pack.py "<package-folder>" --strict --expect-official-notebooklm video_zh --expect-official-notebooklm video_en --expect-official-notebooklm infographic
```

## Final Output Inventory

The completed package contained 38 files:

- source archive: Markdown, HTML, TXT, PDF, manifest, and preflight.
- bilingual prep: Chinese and English briefing companions, prompts, summaries, and scripts.
- NotebookLM media: Chinese MP4, English MP4, and horizontal infographic PNG.
- local image variants: vertical cover plus 3:4 and 4:3 masked versions.
- publishing files: 视频号, BILIBILI, 小红书, LinkedIn, TikTok, YouTube Shorts.
- operations files: execution note, automation log, downloads manifest, publish checklist, repurposing calendar.

Verified media:

- Chinese NotebookLM video: 1280x720, about 448 seconds, H.264/AAC.
- English NotebookLM video: 1280x720, about 447 seconds, H.264/AAC.
- NotebookLM infographic: 2752x1536.
- 4:3 masked variant: 2752x2064.
- 3:4 masked variant: 2752x3669.
- vertical local cover: 1080x1350.

## What This Example Proves

- The skill can start from pasted article text, not only URLs or PDFs.
- NotebookLM is treated as an automated production step rather than a manual handoff.
- Clean-source gating matters: the run verified `1` visible source before generation.
- English and Chinese videos can be handled as separate clean notebook runs.
- The final audit can distinguish official NotebookLM media from local fallback assets.
- A publish pack can be complete without committing heavyweight media files to GitHub.

## Files In This Example

- `notebooklm-automation-log.sample.json`: sanitized version of the automation evidence.
- `audit-summary.sample.json`: compact final audit evidence.

