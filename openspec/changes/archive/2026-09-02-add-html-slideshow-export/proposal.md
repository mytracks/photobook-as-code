## Why

A photobook can currently only be exported as a print-ready PDF or a set of page images — there's no way to browse it interactively (on a TV, tablet, or via a shared link) without external tooling. The same YAML config already carries everything a slideshow needs (ordered photos, chronological titles, captions, theme styling), so a single self-contained HTML file that plays as an endless slideshow is a natural additional output format, reusing the config as-is.

## What Changes

- Add a new `output.format: html` value that generates a single self-contained `.html` file (inline CSS/JS, base64-embedded theme fonts) instead of PDF/PNG/JPG.
- One slide per page item (photo or title), built directly from the existing chronological merge (`merge_titles_with_photos`) and caption association (`associate_text_labels_with_photos`) — the print-oriented grid layout and theme-template matching (`distribute_photos`, `match_template`) are bypassed entirely for this format, since a slideshow never packs multiple photos onto one slide.
- Endless autoplay with a configurable per-slide interval, looping back to the first slide after the last, plus pause/step controls (click/spacebar to pause, arrow keys to step).
- Photos are referenced via relative `<img>` paths, never embedded or copied, so large originals aren't duplicated in the output; only the current and next slide's image are loaded at a time (JIT loading) to keep memory/bandwidth bounded regardless of collection size.
- Multi-folder configs are supported: photos outside the first `photo_folders` entry get `../`-style relative paths from wherever the HTML lands.
- **BREAKING** (scoped to `format: html` only): `output.directory` and the directory portion of `--output` are always ignored — the file is always written into the first `photo_folders` entry, with an informational note printed when an override was explicitly given. A filename override (`-o name.html` or `output.filename: name.html`) is still honored; only the directory it implies is discarded.
- `output.transparent`'s validation is relaxed so it no longer errors when combined with `format: html` — it's silently unused for html (same treatment `quality` already gets for non-jpg formats), while remaining rejected for `jpg`/`pdf`.

## Capabilities

### New Capabilities
- `html-slideshow-export`: Generates a single self-contained, endlessly-looping HTML slideshow (one slide per photo/title, captions and titles rendered as styled HTML/CSS from the active theme, embedded theme fonts, JIT image loading, relative photo paths, autoplay with pause/step controls) placed in the first photo folder.

### Modified Capabilities
- `output-generation`: `output.format` gains an `html` value; "Validate transparent background configuration" gains an html carve-out (ignored rather than rejected); "Support output directory specification" and "Handle output file naming" gain html-specific scenarios (directory/`--output` always forced to the first photo folder and ignored otherwise, with filename override still honored).

## Impact

- `src/photobook_as_code/config.py`: `OutputConfig` gains an `html` format value and a slide-interval field; `output.transparent` validation relaxed to reject only `jpg`/`pdf`.
- `src/photobook_as_code/cli.py`: new branch for `format: html` that skips `distribute_photos`/`render_all_pages`, forces the output directory to the first resolved photo folder (printing a note if `--output`/`output.directory` was set), and prints its own success/progress messaging.
- New module for building and writing the slideshow HTML (slide assembly from `merge_titles_with_photos` + `associate_text_labels_with_photos`, relative path resolution, font embedding).
- `src/photobook_as_code/themes.py`, `text_labels.py`, `photos.py`: reused as-is, no changes.
- Test coverage: new tests for html generation (slide content, JIT-loading markup, relative path resolution across single/multi-folder configs, directory-override-ignored behavior, transparent-with-html no longer erroring).
