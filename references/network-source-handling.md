# Network Source Handling

Use this reference when a URL does not behave like a clean article page.

## Source Types

- Clean article or blog: run `scripts/prepare_source.py <url> --dry-run`, then save manifest/preflight.
- Research report or PDF: upload the original PDF to NotebookLM, optionally add a source-derived briefing companion for long reports.
- JavaScript-heavy page: use a browser capture, rendered PDF, or manually copied text. Then run `prepare_source.py` on the captured HTML, PDF, TXT, or Markdown.
- Video page: use transcript/subtitles when available. Treat the transcript as source; do not infer missing claims from title or thumbnail only.
- Social post or thread: use the post text, screenshots, and linked source separately. If only a social summary exists, label the package as commentary, not source-backed reporting.
- Paywalled or login-only page: stop or ask for an accessible source/capture. Do not bypass access controls.

## Preflight Decisions

After preflight, decide:

1. Is there enough source text to support a public package?
2. Is the source truncated, JS-only, or mostly navigation?
3. Is the content better as a short news update, long report, tutorial, opinion, or case study?
4. Does it need strict single-source NotebookLM, or a source-derived briefing companion?
5. Are there images or visual frameworks worth turning into covers/carousels?

## Fallbacks

If URL extraction fails:

1. Try the canonical or desktop/mobile variant of the URL.
2. Use browser-rendered capture when available.
3. Ask the user for copied text or a PDF if the site blocks automation.
4. Save the blocker in the execution note and still create a publish plan from any verified source materials.

## Never Do

- Do not invent body text from metadata.
- Do not treat thumbnails or headlines as a full source.
- Do not claim NotebookLM outputs from a notebook with an unexpected source count.
- Do not publish a package whose core hook cannot be traced back to the source.
