## 1. Configuration schema

- [x] 1.1 Extend `validate_text_labels` in `config.py` to accept an optional `title` field on a `text_labels` entry
- [x] 1.2 Add validation errors for the mutually-exclusive cases: neither `text` nor `title` present, or both present

## 2. Title parsing & chronological merge

- [x] 2.1 Add a title entry type in `text_labels.py` (or extend `TextLabel`) distinguishing `title` entries from `text` entries, sharing existing timestamp parsing (ISO 8601 / Unix epoch)
- [x] 2.2 Give the title item type an `.orientation` property that always returns `"portrait"`
- [x] 2.3 Implement chronological merge: insert each title into the already-ordered photo sequence at the first index where `photo.sort_date >= title.timestamp` (append at end if none), which also yields the title-wins-exact-tie rule for free
- [x] 2.4 Handle multiple titles landing at the same insertion boundary, ordered among themselves by their own timestamps (stable on exact ties)
- [x] 2.5 Leave `find_closest_photo`/`associate_text_labels_with_photos` (the `text` caption-overlay path) untouched and scoped to `text`-field entries only
- [x] 2.6 (Added during implementation, user-confirmed) Extend the shared `parse_markdown_line` regex to also treat `_text_` as italic, matching the original request's `_italics_` syntax - fixes both titles and existing `text` captions

## 3. Layout & distribution

- [x] 3.1 Update the call site(s) feeding `distribute_photos` to use the combined photo+title item count instead of the raw photo count
- [x] 3.2 Verify `get_photo_indices_for_page` / page slicing works correctly when fed the merged photo+title sequence (adjust only if it assumes a pure `PhotoMetadata` list)
- [x] 3.3 Verify `match_template` works unmodified for items exposing `.orientation` (photos and titles); loosen any type hints hard-coded to `PhotoMetadata` if needed

## 4. Theme styling

- [x] 4.1 Add a `TitleStyle` dataclass in `themes.py` mirroring `TextStyle` (`base_font_size`, `font_family`, `text_color`, background fields, `text_padding`) plus `align` (`left`/`center`/`right`, default `center`)
- [x] 4.2 Parse an optional `title:` block from theme YAML into `Theme.title`, defaulting when absent
- [x] 4.3 Validate `title.align` (must be `left`/`center`/`right`) and `title.base_font_size` (positive number) in `validate_theme`, raising `ThemeError` on invalid values
- [x] 4.4 Add a `title:` block with sensible defaults to the built-in themes (`clean`, `classic`, `modern`, `clean2`)

## 5. Rendering

- [x] 5.1 In `render_page`'s per-slot loop, detect when a page item is a title rather than a `PhotoMetadata`, and skip image load/fit/paste/border/shadow for that slot
- [x] 5.2 Render the title's Markdown content into the slot's position/size box using the existing two-pass measure-then-draw approach from `render_text_label`, reusing `parse_markdown_text` unmodified
- [x] 5.3 Apply `theme.title` styling (font, size, color, alignment) instead of `theme.text` when rendering a title slot
- [x] 5.4 Update `render_all_pages` to accept and thread through the merged photo/title sequence per page

## 6. CLI wiring

- [x] 6.1 Update `cli.py` to build the merged photo+title sequence after loading config, photos, and theme
- [x] 6.2 Update the distribution and render calls to use the merged sequence and its combined count
- [x] 6.3 Update progress/echo output to reflect title counts where relevant (e.g. "N photos, M titles")

## 7. Tests

- [x] 7.1 Config validation: `title` field accepted; both-present and neither-present error cases
- [x] 7.2 Chronological merge: between two photos, before all photos, after all photos, exact-timestamp tie (title first), multiple titles at the same insertion point
- [x] 7.3 `match_template` matches a title item as `portrait` orientation, including mixed photo+title pages
- [x] 7.4 Distribution: page/photos_per_page calculations using the combined photo+title count
- [x] 7.5 Theme `title:` block: parsing, defaults when absent, invalid `align`, invalid `base_font_size`
- [x] 7.6 Rendering test: a title slot renders formatted text with no photo image, border, or shadow
- [x] 7.7 Integration test: a config mixing `text` and `title` entries produces the expected merged sequence, page count, and per-page layout

## 8. Documentation

- [x] 8.1 Add a `title` usage example to `example-config.yaml` and/or README
- [x] 8.2 Document the `title:` theme style block and the "titles render in a portrait-shaped slot" constraint (themes need portrait-inclusive templates at the relevant counts) in theme documentation
