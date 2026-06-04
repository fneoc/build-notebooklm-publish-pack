# NotebookLM Workflow

Use this reference when the package requires NotebookLM video overviews, infographics, or source-grounded summaries.

## Clean Source Rules

1. Use a brand-new notebook when possible.
2. Reuse an existing notebook only after checking the visible source count, source title, and language state.
3. Upload only the source document(s) intended for this package.
4. Treat unexpected counts, old titles, or stale generated cards as contamination.
5. If the package needs separate Chinese and English outputs, prefer separate notebooks or clearly separate language runs.

## Source Preparation

1. Create a readable source PDF when the input is a webpage, pasted notes, transcript, or mixed files.
2. Keep a text or HTML mirror for auditing and later publish-copy generation.
3. Record source URL/path, capture date, author/publication date when known, and extraction caveats.
4. For webpages, expand folded content before extraction. Do not summarize recommendation lists as source content.
5. Run `scripts/prepare_source.py <url-or-file> --dry-run` before packaging webpages or long files. Use its source manifest and preflight text when writing the execution note.

## Long Webpage Mode

Use long webpage mode when any of these are true:

- the body exceeds 20,000 characters.
- the source has more than 10 substantive images.
- a Sohu page reports `hiddenRatio > 50`.

In long webpage mode:

1. Default to a single original source when the user requires strict single-source NotebookLM.
2. Otherwise allow two NotebookLM sources: the original PDF plus a derived briefing companion from the same source.
3. Label the companion clearly as source-derived, not a separate external source.
4. Record the expected visible source count in the execution note.
5. If NotebookLM shows a different source count than expected, stop and report contamination.
6. Preserve the full source archive even if the companion is used to guide video and infographic generation.

## Video Overview

1. Generate the NotebookLM video overview only after the source count is verified.
2. Wait for the ready card. If the card stays in a generating state, refresh the same clean notebook before rebuilding.
3. Prefer NotebookLM's own card menu download path for MP4 files.
4. If download automation fails, inspect the user's downloads folder and copy the verified MP4 into the package folder.
5. Verify each MP4 exists and is playable or probeable before claiming success.

## Infographics

1. Download NotebookLM infographic images when available.
2. If NotebookLM images are missing, create a local fallback clearly labeled as local or generated.
3. Preserve readable text. Do not crop captions, headings, or source labels when creating ratio variants.
4. Use `scripts/make_ratio_masks.py` for vertical and rich-preview masked variants.

## Language Handling

1. For Chinese platforms, write copy naturally in Chinese and keep titles short.
2. For English platforms, write copy for the English-speaking audience instead of literal translation.
3. Verify English MP4s are actually English before labeling them English.
4. If a user starts from an existing English NotebookLM MP4, validate that file first and do not rebuild NotebookLM unless requested.

## Blocker Reporting

Report a blocker when:

- NotebookLM is unavailable or requires manual login.
- The visible source count is contaminated.
- A requested video or infographic has not finished generating.
- The downloaded media cannot be found or verified.

Include what already exists, what was verified, and the next manual step.
