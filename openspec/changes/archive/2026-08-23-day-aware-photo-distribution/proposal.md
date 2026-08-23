## Why

When a user fixes the page count (`layout.pages`), today's distribution (`layout.py:distribute_photos`, exact-page-count branch) is pure arithmetic over a bare photo count: the first `total % pages` pages get one extra item, the rest get one fewer, with no regard for which items actually land where. In practice this front-loads the book with dense pages and back-loads it with sparse ones (e.g. 168 photos across 100 pages puts 2 photos on each of the first 68 pages, then 1 photo on each of the remaining 32) — a book that reads dense-then-thin instead of following the trip it documents, and completely ignores day/event boundaries and photo orientation. We need day- and orientation-aware distribution rules so a fixed-page-count book reads well while flipping through it.

## What Changes

- `distribute_photos` is reworked to operate on the actual ordered sequence of page items (photos and title slots, each with a date and an orientation) instead of a bare item count, so it can make date/orientation-aware page-break decisions.
- **Primary rule**: a page break is always inserted before the first item of a new calendar day, so no single page mixes items from two different days — except where the feasibility fallback below relaxes it.
- **Secondary rule**: when the fixed `pages` count leaves "slack" pages to spend (today's uneven-remainder pages), that slack is preferentially spent turning a page that holds exactly 2 items into two full-page single-item pages, prioritized by how well the two items' orientations match the book's own page orientation (both match > one matches > neither matches). Reducing a page from more than 2 items down to more than 1 (e.g. 4 → 3) carries no orientation preference.
- Both the pages chosen to receive slack and the day-boundaries chosen to relax under the feasibility fallback are selected deterministically and spread evenly across the book's page range, rather than clustering at one end — reusing the interval-spacing idea `_calculate_sparse_page_assignments` already uses for sparse distribution.
- **Feasibility fallback (day rule is a last-resort-relaxable soft rule)**: the user's fixed `pages` count remains authoritative. When honoring every day boundary would require more pages than requested (or would force a page beyond the theme's max item-per-page count), the fewest, least-costly day boundaries are merged away instead — chosen deterministically, never at random and never arbitrarily at the end of the book.
- New `layout.new_page_per_day` boolean config field, default `true`, lets a user disable the whole day-boundary rule and fall back to the previous simple even-fill behavior.
- Book orientation (portrait vs. landscape), used to judge orientation match, is derived from the configured output page's pixel width vs. height (`config.py:get_paper_size_pixels`) — no new config field for it.
- The algorithm remains fully deterministic: the same configuration and photo files always produce the identical page-by-page distribution, with no reliance on set/dict iteration order, randomness, or filesystem enumeration order beyond the existing, already-deterministic photo sort.
- **BREAKING** (behavioral, not an API break): a fixed-`pages` photobook generated from an unchanged config and photo set will place photos differently than it did before this change — that's the intended fix, but existing users regenerating a previously-created book will see a different result.

## Capabilities

### New Capabilities

None

### Modified Capabilities

- `photo-layout-engine`: `distribute_photos` and the exact-page-count distribution requirement gain day-boundary page breaks, orientation-prioritized slack spending, and the deterministic feasibility fallback described above.
- `yaml-configuration`: `layout` configuration gains the `new_page_per_day` boolean field (default `true`), with validation.

## Impact

- `layout.py`: `distribute_photos`/`PhotoDistribution` reworked to consume the ordered item sequence (each item's date and orientation) plus the theme's max per-page item count, rather than a bare total count; `get_photo_indices_for_page` continues to be the interface `renderer.py` relies on.
- `config.py`: `LayoutConfig` gains `new_page_per_day: bool = True`, with validation for non-boolean values.
- `cli.py`: the call site now passes the merged photo+title item sequence and the active theme's per-page item capacity into distribution, instead of just an item count.
- `themes.py`: distribution needs each theme's max supported item count per page — this is already implicit in a theme's `layouts` list and just needs to be queried, not stored as a new field.
- `renderer.py`: unaffected as long as `PhotoDistribution.total_pages` / `get_photo_indices_for_page` keep their current shape.
- Tests: `tests/test_layout.py`, `tests/test_config.py`, `tests/test_cli.py` need new and updated coverage for day-boundary breaks, orientation-prioritized splitting, the merge fallback, and the `new_page_per_day` toggle.
