## Context

See proposal.md for motivation. Relevant current state:

- `text_labels.py` associates each caption (`text`) with its single *closest* photo by timestamp distance (`find_closest_photo`) and overlays it on that photo; the photo/slot count is untouched.
- `layout.py:distribute_photos` computes pages purely from a photo count; `layout.py:match_template` selects a theme layout template by comparing `count` and a list of `orientation` strings (`landscape`/`portrait`) — it only ever reads `.orientation` off whatever it's given, no other structural requirement.
- `themes.py:Theme` carries one theme-level `TextStyle` (`theme.text`) used for caption rendering, plus per-slot `TextPosition` blocks embedded in layout templates for caption placement.
- `renderer.py:render_page` does two passes per page: paste all photos, then draw borders/captions on top.

## Goals / Non-Goals

**Goals:**
- Titles consume a full page slot, chronologically merged with photos, and are counted in page/photo distribution.
- Titles reuse the existing template-matching engine unmodified.
- Titles get independent, theme-configurable styling (font, size, color, alignment) from captions.

**Non-Goals:**
- Not changing the existing caption (`text`) overlay behavior in any way.
- Not introducing a parallel "title layout" template vocabulary in themes.
- Not supporting a title orientation other than `portrait` (explicit product decision — see Decisions).

## Decisions

### 1. Titles present as `portrait` orientation to the layout engine
A title is wrapped in a small item type exposing `.orientation` that always returns `"portrait"`. `match_template()` needs no code change: it already does generic `count` + sorted/ordered string-list comparison over whatever list it's handed, so a title slots into any layout template a theme already uses for a portrait photo at that photo count.

**Alternative considered:** a distinct `"title"` orientation value, with themes authoring dedicated title-inclusive template variants. Rejected — it multiplies the combinations themes must define (every count × every position a title could occupy) for no behavioral benefit, since portrait-inclusive templates already exist at most counts in the built-in themes.

**Trade-off accepted:** a title's box shape is whatever geometry the matched template gives a portrait photo at that count. Themes can't give titles a distinctly-shaped slot (e.g. a full-width banner) without also reshaping their portrait photo slots at that count.

### 2. Chronological merge algorithm
Photos arrive already ordered per `layout.order` (`alphabetical` or `date`). Titles are inserted into that existing sequence, not re-sorted globally with it: for each title, find the first index `i` where `photos[i].sort_date >= title.timestamp` and insert immediately before it (append at the end if no such index exists). Using `>=` rather than `>` is what makes the tie-break rule fall out for free: when a title's timestamp exactly equals a photo's `sort_date`, that photo is itself the first index satisfying `>=`, so the title lands immediately before it, with no special-case code needed. Multiple titles landing at the same boundary stay adjacent, ordered by their own timestamps (stable on exact ties, by input order).

**Alternative considered:** always re-sort the fully-merged sequence by timestamp regardless of `layout.order`. Rejected — it would silently override an explicit `alphabetical` choice for photo display order. The boundary-scan approach keeps the photo ordering the user asked for and places titles relative to it; under `order: date` this is exactly chronological, under `order: alphabetical` it's a best-effort placement against non-monotonic dates (documented behavior, not an error).

### 3. Distribution operates on the merged sequence length
`distribute_photos()` itself is unchanged — it already only takes a count and a list to slice. The caller now computes `total_slots = len(photos) + len(titles)` and passes the merged sequence (not the raw photo list) through `distribute_photos`/`get_photo_indices_for_page`, so a configured `pages` or `photos_per_page` naturally accounts for titles.

### 4. Rendering: title slots skip photo handling and draw Markdown text
In `render_page`'s per-slot loop, when the page item at a slot is a title (not a `PhotoMetadata`), the slot's `position`/`size` box is used directly as a text frame (no image load, fit, paste, border, or shadow). Text is parsed with the existing, unmodified `parse_markdown_text`/`parse_markdown_line` (headings, bold, italic, multi-line) and word-wrapped/drawn with the same two-pass measure-then-draw approach `render_text_label` already uses for captions, styled from the new theme-level title style rather than `theme.text`.

### 5. New theme-level `title` style block
A new `TitleStyle` dataclass, parsed from an optional `title:` section in theme YAML, mirrors `TextStyle`'s shape (`base_font_size`, `font_family`, `text_color`, background fields, `text_padding`) plus `align` (`left`/`center`/`right`, default `center` — titles read more like headings than left-aligned captions). Default `base_font_size` is larger than `theme.text`'s (titles are meant to be prominent). Kept as an independent block so a theme can style captions and titles differently; a theme omitting `title:` gets built-in defaults, same pattern as `theme.text` today.

### 6. Config schema
`text_labels` entries gain an optional `title` string field, mutually exclusive with `text` (validation error if both or neither are present). The shared `timestamp` field and its parsing (ISO 8601 / Unix epoch) are unchanged and apply to both kinds of entry.

## Risks / Trade-offs

- **[Risk]** A page's combined item count (photos + titles landing in the same distribution bucket) can exceed the largest `count` a theme defines templates for (built-in themes currently cap at 4) → `LayoutError`. **Mitigation:** none added beyond the existing clear error; this is the same class of failure themes already have for any unsupported `photos_per_page`/count today. Documented as a constraint for theme/config authors.
- **[Risk]** Because titles always report `portrait`, a page's exact orientation mix (e.g. 3 landscape + 1 title) needs a theme template with that literal count/orientation combination available. If a theme only defines all-landscape templates at a given count, adding a title there fails to match. **Mitigation:** none automatic; document that using titles requires the theme to have portrait-inclusive templates at the relevant counts.
- **[Risk]** Under `layout.order: alphabetical`, title placement is a best-effort boundary scan rather than truly chronological (see Decision 2). **Mitigation:** documented behavior; no error.
- **[Trade-off]** Reusing `portrait` orientation (Decision 1) avoids combinatorial template growth but ties a title's shape to whatever a theme's portrait photo slot looks like at that count.

## Migration Plan

Purely additive: existing configs (no `title` entries) and existing themes (no `title:` style block) behave identically to today. No data migration, no flag, no rollback concern beyond normal code review.
