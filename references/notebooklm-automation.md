# NotebookLM Automation

Use this reference whenever a package needs NotebookLM media. The default is automated browser execution, not a manual upload handoff.

## Browser Surface

1. Prefer the user's logged-in Chrome session because NotebookLM usually depends on Google account state.
2. Use the `chrome:control-chrome` skill when available, following its browser-client setup and documentation before interacting with Chrome.
3. Use the in-app browser only when it is already authenticated for NotebookLM or the user explicitly wants that surface.
4. The user's request to build a NotebookLM package authorizes uploading the prepared source PDF or source-derived companion to NotebookLM for this package. Do not ask again unless the file contains unrelated sensitive data.

## Automated Run Contract

For each language run, automation should attempt these steps before declaring NotebookLM blocked:

1. Open `https://notebooklm.google.com/`.
2. Create a new notebook, or use a freshly empty notebook when new-notebook creation is not exposed.
3. Upload only the intended source files:
   - strict single-source mode: `<base>.pdf` or the original source PDF.
   - long-report two-source mode: original PDF plus source-derived briefing companion.
4. Wait for upload and source ingestion to finish.
5. Verify visible source count equals the expected count and the source title matches the package.
6. Trigger video overview generation.
7. Trigger infographic or image generation when the UI exposes it.
8. Poll video/image readiness every 60-90 seconds. For long reports, allow about 15 minutes before treating generation as stale.
9. Download finished MP4/PNG assets from NotebookLM's own card or detail menu.
10. If the browser download event times out, inspect `~/Downloads` by modification time before declaring failure.
11. Copy verified assets into the package folder using the output-contract filenames.
12. Update `<base>-notebooklm-downloads-manifest.json` and `<base>-execution-note.txt` with source count, card titles, original download filenames, copied filenames, durations/dimensions, and blocker details.

## Source Count Gate

Before generating or accepting any NotebookLM asset:

- expected count must be recorded in the execution note.
- visible count must match expected count.
- source title(s) must match the current package.
- old generated cards from a different topic must be ignored or rejected.

If visible count is wrong, do not generate. Try one clean-notebook rebuild. If still wrong, report contamination.

## Downloads

Preferred download path:

1. Open the ready NotebookLM card or detail page.
2. Use `更多选项` / more-options menu.
3. Click `下载` / download.
4. Check `~/Downloads` for the newest matching MP4/PNG if the automation download promise does not fire.
5. Validate MP4 with `ffprobe` and image files with Pillow before copying.

Downloaded filenames may differ from the package contract. Preserve the original name in the downloads manifest and copy the file to the canonical package filename.

## Blocker Rules

Only report a manual blocker after automation has actually attempted the relevant step and failed. Good blockers include:

- NotebookLM requires login or account selection.
- CAPTCHA or Google security challenge appears.
- Browser extension/control session is unavailable.
- File chooser refuses the upload after retry.
- NotebookLM rejects the file or never finishes ingestion.
- Video or image generation is still running after a reasonable polling window.
- Downloaded media cannot be found or verified.

Do not write "user should upload the PDF manually" as the default next step. Write the exact automated step that failed and what evidence was observed.
