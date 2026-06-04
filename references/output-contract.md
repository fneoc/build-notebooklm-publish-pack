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
<base>-content-plan.json
<base>-publish-ops-checklist.md
<base>-repurposing-calendar.md
<base>-summary-zh.txt
<base>-summary-en.txt
<base>-video-zh-notebooklm.mp4
<base>-video-en-notebooklm.mp4
<base>-infographic-horizontal.png
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
3. NotebookLM notebook state: expected and visible source count, language, generated cards, and download status.
4. Media validation: MP4 existence/probe result, image dimensions/aspect ratios.
5. Platform files generated.
6. Blockers or manual steps.

## Completeness Levels

- `complete`: source archive, bilingual media, image variants, publish files, and validation all exist.
- `partial`: source archive and copy exist, but at least one NotebookLM media asset is blocked or missing.
- `blocked`: source is missing, contaminated, inaccessible, or NotebookLM cannot be used.

Do not label a package `complete` from memory alone.
