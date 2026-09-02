## Context

See proposal.md - Why/What Changes for motivation and scope. Relevant existing shape:

- `merge_titles_with_photos` already produces one flat, chronologically-ordered list of page items (photos + title slots); `associate_text_labels_with_photos` already maps each photo to its nearest caption (or `None`). Both are format-agnostic today and need no changes.
- The pdf/png/jpg pipeline (`distribute_photos` → `match_template` → `render_page`) exists specifically to pack *multiple* items onto one print page using a theme's `LayoutTemplate`s, and to bake text as PIL bitmaps. A slideshow never packs multiple items onto one slide, so none of that machinery applies.
- `Theme.text`/`Theme.title` (font, color, background box, padding, line-spacing) are page-layout-independent styling and translate directly to CSS. `LayoutPhoto.text` (a caption's x/y/width/dock position) is defined *per grid-template slot* and has no equivalent for a single full-bleed photo slide — some themes may not even define a 1-photo template.
- `output-generation`'s existing `output.transparent` validation (`format != 'png'` → error) and directory/filename resolution (`get_output_directory`/`get_output_filename`) are written assuming pdf/png/jpg; html needs carve-outs in both without disturbing existing behavior for those formats.

## Goals / Non-Goals

**Goals:**
- Reuse the existing config/theme/text-label/title data model unchanged; html is purely a new consumer of already-parsed structures.
- Bound memory/bandwidth for arbitrarily large, arbitrarily long-running ("endless") slideshows regardless of photo count or file size.
- Produce one self-contained `.html` file with no other generated assets (no sidecar CSS/JS/font files).

**Non-Goals:**
- No thumbnailing/resizing pipeline — slides reference full-resolution originals, as requested.
- No exact positional parity with PDF/PNG captions: a caption reuses `theme.text.*` typography/box styling, but placement is a fixed bottom-docked band (see Decisions), not a replay of any particular `LayoutTemplate`'s per-slot `TextPosition`.
- No use of `theme.layouts` (grid templates) at all — irrelevant once every slide holds exactly one item.
- No video, music, transitions beyond a simple fade/cut, editing UI, or PWA/offline-service-worker behavior.
- No correction of photo EXIF orientation ourselves — relies on the browser's native (near-universal) EXIF-aware image rendering.
- No copy-photos-into-output-folder mode — relative paths to the originals only (rejected alternative; see Thread 1 discussion in the proposal's motivating exploration).

## Decisions

**Bypass the print pipeline entirely for `format: html`.** The CLI branches before `distribute_photos`: it builds slides directly from `merge_titles_with_photos(titles, photos)` + `associate_text_labels_with_photos`, with no `LayoutTemplate` matching, no PIL rendering, no DPI/paper-size math. Simpler than either theming path.

**Server-side (Python) markdown rendering, not client-side.** `text_labels.parse_markdown_text` already parses a caption/title's Markdown into `(segments, heading_level)` per line. The html generator walks that same structure once, at generation time, and emits the final `<strong>`/`<em>`/heading-sized `<span>` markup directly — no markdown library or parsing logic ships in the page's JS. Keeps the generated JS small and avoids a second markdown implementation.

**Caption placement: fixed bottom-docked band, theme-styled.** Since there's no single `LayoutPhoto.text` that means anything for a full-bleed single-photo slide, a caption renders as a band docked to the bottom of the photo's rendered (letterboxed) area, sized to its content, using `theme.text.{font_family, base_font_size, text_color, text_background_*, text_padding, line_spacing}` for styling and `theme.text.align` for its own text alignment. This keeps typographic identity consistent with PDF/PNG output without pretending a print-page slot position transfers to a full-viewport photo.

**Titles reuse `theme.title.*` as-is.** Unlike captions, a title slide already has no "photo cell" to be relative to in the print pipeline either (`render_title_slot` centers it in its full layout-slot box) — so centering it in the full viewport is a direct, faithful translation of existing behavior.

**Embed the theme's font as base64 `@font-face`, reusing the existing font-resolution path.** `_load_font_variants` in renderer.py resolves `theme.text.font_family`/`theme.title.font_family` to `/usr/share/fonts/truetype/dejavu/{font_family}[-Bold|-Oblique|-BoldOblique].ttf`, falling back to a default font if missing. The html generator reuses that same resolution to find the four variant files it needs (typically just `DejaVuSans*`, but a custom theme could name another installed family) and inlines them as base64 `@font-face` `src`s; if a variant file can't be found, its `@font-face` is skipped and the CSS `font-family` stack falls back to `sans-serif`, mirroring the PIL fallback. This keeps the single-file constraint (no external font requests) and gives the closest achievable visual parity with PDF/PNG without shipping a font-subsetting toolchain.

**JIT image loading, with eviction, not just deferred loading.** Every slide's `<img>` starts with `data-src` (not `src`), so nothing loads on page open. A small inline script sets `src` on the current slide and, immediately upon showing it, also sets `src` on the *next* slide — giving the full per-slide interval to download before it's needed. When a slide is left, its `src` is cleared back to unset (image dereferenced) so a decoded copy isn't retained; at most two full-resolution images are ever loaded at once, independent of how many slides exist or how long the show has been running. This is what makes "endless" safe for a large collection of large originals, both over `file://` and a slow web server.

**Directory is always forced for html; filename is not.** `output.directory` and the directory portion of `--output`/`output.filename` are discarded when `format: html` — the file always resolves under `resolve_photo_folders()[0]`. A bare filename override (`-o name.html`, or `output.filename: name.html` with no directory component) still renames the output; only the location is fixed. When an override's directory gets discarded, the CLI prints an informational note so a script/Makefile that passes `-o` out of habit isn't silently surprised. No fallback location is attempted if the first photo folder isn't writable — it's a clear `OutputError` instead, since there is, by design, no override to fall back to.

**Relative paths: POSIX-normalized and percent-encoded, computed per photo.** Each photo's `href`/`src` is `os.path.relpath(photo.path, output_dir)`, converted to `/`-separated form and percent-encoded segment-by-segment (`urllib.parse.quote`, `/` left unescaped) so spaces and non-ASCII names (e.g. the real `für Heinz` folder in this project's own configs) resolve correctly as URLs rather than raw filesystem paths. Works unchanged for both `file://` and http(s) hosting.

**`output.transparent` validation relaxed, not removed.** Change the check from "error unless format is exactly `png`" to "error only when format is `jpg` or `pdf`" — html silently ignores it (same treatment `output.quality` already gets outside jpg). This is what lets `heinz.yaml`/`karwendel.yaml`/`sevilla.yaml` (all currently `transparent: true`) be reused for html by only flipping `output.format`, per the project's explicit YAML-reuse requirement.

**New config field: `output.interval_seconds`.** Only meaningful for `format: html` (same pattern as `quality` being jpg-only); default 5, validated as a positive number.

**Minor: `alt` text from filename.** Each `<img>` gets `alt="{photo.filename}"` — essentially free, and better than an empty/missing alt.

## Risks / Trade-offs

- **Multi-folder configs only stay portable if sibling folders are copied too** when hosting on a web server, since relative paths can point outside the directory the html was written into → Mitigation: generation logs/prints the resolved list of source folders and their relative paths from the output location, so there's a ready-made checklist of what to copy.
- **First photo folder might not be writable** (read-only mount, synced/read-only library) and there's no override to fall back to by design → Mitigation: fail with a clear `OutputError` naming the path, rather than a raw `PermissionError` or a silent alternate location.
- **Very large individual photos still gate slide advancement** if the per-slide interval is shorter than the download time on a slow connection → Mitigation is partial: prefetching starts as early as possible (as soon as the current slide is shown, not right before it's needed), but no further guarantee is made; explicitly out of scope to add a "wait for load" vs. "advance anyway" policy beyond that in this change.
- **Filename collisions**: two different config files with the same stem pointed at the same first photo folder overwrite each other's html, same as pdf/png/jpg already do today (no `ensure_unique` behavior) → accepted, consistent with existing behavior.

## Migration Plan

Purely additive: a new `output.format` value, a new optional config field, and a loosened (never tightened) validation rule. No changes to existing pdf/png/jpg behavior, no data migration. `example-config.yaml` gets a documented `html` example alongside the existing pdf one.
