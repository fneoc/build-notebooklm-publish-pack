# Output Contract

Use this contract for generic packages. Preserve user-provided naming exactly when they specify filenames or a brand convention.

## Folder

Default folder:

```text
<output-root>/<YYYYMMDD>/
```

If the work is not date-based, use:

```text
<output-root>/<safe-title-slug>/
```

## Recommended Files

Use `<base>` as the brand or content slug plus date when available, for example `market-report-20260604`.

```text
<base>.pdf
<base>.html
<base>.txt
<base>-source-manifest.json
<base>-source-preflight.txt
<base>-briefing-companion-zh.md
<base>-briefing-companion-en.md
<base>-notebooklm-prompt-zh.txt
<base>-notebooklm-prompt-en.txt
<base>-notebooklm-downloads-manifest.json
<base>-notebooklm-automation-log.json
<base>-content-plan.json
<base>-publish-ops-checklist.md
<base>-repurposing-calendar.md
<base>-summary-zh.txt
<base>-summary-en.txt
<base>-video-zh-notebooklm.mp4
<base>-video-en-notebooklm.mp4
<base>-infographic-horizontal.png
<base>-infographic-horizontal-notebooklm.png
<base>-infographic-vertical.png
<base>-infographic-vertical-3x4-mask.png
<base>-infographic-rich-4x3-mask.png
<base>-publish-wechat-video.txt
<base>-publish-bilibili.txt
<base>-publish-tiktok-en.txt
<base>-publish-youtube-shorts-en.txt
<base>-publish-draft-wechat-video.txt
<base>-publish-draft-bilibili.txt
<base>-publish-draft-tiktok-en.txt
<base>-publish-draft-linkedin.txt
<base>-execution-note.txt
```

## Execution Note

The execution note should include:

1. Source inputs and retrieval/capture method.
2. Source preflight result: title, date, text length, image count, truncation risks, and long-mode decision.
3. NotebookLM automation state: browser surface used, notebook URL/title, expected and visible source count, uploaded filenames, language, generated cards, and download status.
4. NotebookLM timing: automation start, upload completion, generation start, polling interval, approximate wait time, refresh/retry decisions, and whether work continued on images/copy while video generated.
5. Download harvesting: ready-card title, original downloaded filename, source folder such as `~/Downloads`, copied package filename, and validation result.
6. Official-vs-fallback status for each media asset: Chinese video, English video, NotebookLM infographic, local fallback images, and post-processed variants.
7. Media validation: MP4 existence/probe result, image dimensions/aspect ratios.
8. Platform files generated.
9. Blockers and automation recovery steps.

## Completeness Levels

- `complete`: source archive, bilingual media, image variants, publish files, and validation all exist.
- `partial`: source archive and copy exist, but at least one NotebookLM media asset is blocked or missing.
- `blocked`: source is missing, contaminated, inaccessible, or NotebookLM cannot be used.

Do not label a package `complete` from memory alone.
When a user specifically requires official NotebookLM media, treat local fallback assets as `partial` until `scripts/audit_publish_pack.py` passes with the relevant `--expect-official-notebooklm` flags.
Do not mark NotebookLM media as blocked until an automated upload/generation/download attempt has been made or the browser/account state prevents that attempt.
