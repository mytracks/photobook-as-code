## Why

`text_labels` today can only overlay a short caption onto an existing photo. There's no way to give a photobook a large, prominent section title (e.g. a chapter heading like "# Auf nach Hamburg") that gets real space on the page and is accounted for when calculating how many pages a photobook needs.

## What Changes

- Add a `title` field to `text_labels` entries, as an alternative to the existing `text` field (mutually exclusive per entry), for large, multi-line, Markdown-formatted section titles.
- A `title` entry consumes a full photo slot rather than overlaying an existing photo. Title entries are merged chronologically with photos (by photo `sort_date`) into one ordered sequence of page items; when a title's timestamp exactly matches a photo's, the title comes first.
- Page/photo distribution (`distribute_photos`) now operates over the combined count of photos + titles, so a configured `pages` or `photos_per_page` value accounts for the additional slots titles introduce.
- Titles are matched into layout template slots by presenting a fixed `portrait` orientation to the existing template-matching engine (`match_template`), so no new template vocabulary or per-theme title layouts are required — titles simply land in whatever portrait-shaped cell the matched template already provides for that photo count.
- Titles render as theme-styled Markdown (`#`/`##`/`###` headings, `**bold**`, `_italic_`/`*italic*`, multi-line) filling their slot's box, using a new theme-level title style block (font family, size, color, alignment) distinct from the existing caption `text` style block.
- The existing `text`-keyed caption-overlay behavior (proximity-based association, per-slot `text:` positioning) is unchanged.

## Capabilities

### New Capabilities
- `title-slots`: Title entries as full photo-slot-consuming section headers — chronological merge/insertion of titles among photos, the exact-timestamp tie-break rule, and presenting titles as `portrait` orientation to the layout engine so they occupy an existing template slot.

### Modified Capabilities
- `text-labels`: Parsing and validation extended to accept a `title` field as an alternative to `text` on a `text_labels` entry (mutually exclusive; each entry has exactly one of `text` or `title`).
- `photo-layout-engine`: Distribution across pages accounts for the combined photo + title slot count, not just the photo count, when calculating `photos_per_page`/`pages`.
- `theme-system`: New theme-level style block for title formatting (font family, base font size, color, alignment), configurable independently from the existing caption `text` style block.

## Impact

- `config.py`: `validate_text_labels` extended for the `title` field and mutual exclusivity with `text`.
- `text_labels.py`: new chronological merge/insertion logic for titles, alongside the existing proximity-based association logic for captions (unchanged).
- `layout.py`: `distribute_photos` fed a combined item count; `match_template` accepts items that report a `portrait` orientation for titles.
- `themes.py`: new `TitleStyle` dataclass and theme YAML parsing for a `title:` style block.
- `renderer.py`: per-slot render loop gains a title branch (Markdown-formatted text fill instead of photo load/paste/border).
- `cli.py`: wiring to build the merged sequence and pass it through distribution/rendering.
- No breaking changes: `title` is a net-new optional key; existing configs using only `text` behave identically.
