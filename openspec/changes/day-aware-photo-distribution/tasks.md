## 1. Configuration schema

- [ ] 1.1 Add `new_page_per_day: bool = True` to `LayoutConfig` in `config.py`, and verify a config file without the field loads with it defaulting to `True`
- [ ] 1.2 Validate `layout.new_page_per_day` is a boolean when present in `validate_config`/its layout section, raising `ConfigurationError` on a non-boolean value, and verify with a test asserting the error message names the field
- [ ] 1.3 Add a `new_page_per_day: false` example to `tests/test_config.py` fixtures and verify it parses to `False`

## 2. Theme capacity

- [ ] 2.1 Add a helper (e.g. `Theme.max_layout_count` or a `themes.py` function) returning `max(t.count for t in theme.layouts)`, and verify it against each shipped theme (`clean`, `classic`, `modern`, `clean2`) returning 4
- [ ] 2.2 Raise `LayoutError` during distribution (not later in `match_template`) when a computed exact-mode density or a configured `photos_per_page` exceeds the theme's max count, and verify with a test asserting the error is raised before any rendering call is reached

## 3. Day-block segmentation

- [ ] 3.1 Add a function that partitions an ordered item sequence (photos + titles) into day-blocks using `sort_date.date()`/`timestamp.date()`, and verify with unit tests: all-one-day, several distinct days, a day that reappears later in the sequence stays a separate block (not merged with its earlier occurrence)
- [ ] 3.2 Verify a title landing on a different day than the preceding item starts a new block, and a title on the same day as the preceding item does not

## 4. Exact-`pages` mode: feasibility and merge fallback

- [ ] 4.1 Implement `P_min_days = Σ ceil(len(block)/M)` over day-blocks, and verify against a hand-computed example with mixed block sizes
- [ ] 4.2 Implement the greedy merge loop (merge the adjacent block pair freeing the most pages; tie-break by earliest boundary) that runs while `P_min_days > total_pages`, and verify with a test where the requested `pages` count is smaller than the number of distinct days, asserting the resulting block count is consistent and deterministic across repeated runs
- [ ] 4.3 Verify `new_page_per_day = false` reduces segmentation to a single block covering the whole sequence (i.e. reproduces pre-change behavior) with a regression test comparing output to the existing arithmetic distribution for a fixed input
- [ ] 4.4 Raise `LayoutError` when even a single fully-merged block still needs more pages than requested (`ceil(total_items/M) > total_pages`), and verify with a test
- [ ] 4.5 Log a `WARNING` (matching the existing `logger.warning` pattern in `photos.py`) identifying which day boundaries were merged, and verify via caplog/log-capture in a test

## 5. Exact-`pages` mode: dense pack and slack spend

- [ ] 5.1 Implement dense-packing of each (possibly merged) block at `M` items/page, producing an explicit item→page assignment, and verify total pages used equals the recomputed `P_min`
- [ ] 5.2 Implement slack computation (`total_pages - P_min`) and the orientation-tiered selection of two-item pages to split (both-match, one-match, no-match tiers), and verify with a test asserting fully-matching pages are split before partially-matching ones
- [ ] 5.3 Implement the even-spread subset selection within a tier (reusing the `round(i * interval)` approach from `_calculate_sparse_page_assignments`), and verify chosen split pages are spread across the page range rather than clustered, for a case where a tier has more candidates than slack requires
- [ ] 5.4 Implement the no-preference fallback reduction (page count > 2 down to > 1) for any slack remaining after all two-item pages are split, and verify it only activates when needed (test with `M` large enough to produce this case)
- [ ] 5.5 Verify total distributed items always equals total input items and total pages always equals the requested `pages`, across a range of randomized (but fixed-seed, recorded) input sizes

## 6. `photos_per_page` (flexible) mode day-breaks

- [ ] 6.1 Apply day-block segmentation to flexible mode when `new_page_per_day` is true, dense-packing each block independently at `min(photos_per_page, M)` with no slack-spending phase, and verify a day boundary produces an under-full page without affecting later days' page counts
- [ ] 6.2 Verify `new_page_per_day = false` in flexible mode reproduces the current simple sequential-fill behavior exactly (regression test)

## 7. `PhotoDistribution` interface

- [ ] 7.1 Replace the arithmetic dense-mode branch in `get_photos_for_page`/`get_photo_indices_for_page` with the explicit `photo_to_page_map` representation used by every mode (dense, day-aware, sparse), and verify `renderer.py`'s usage (`total_pages`, `get_photo_indices_for_page`) needs no changes by running the existing renderer test suite unmodified
- [ ] 7.2 Update `distribute_photos`'s signature to accept the ordered item sequence (for dates/orientations) and the theme's max count, alongside the existing `photos_per_page`/`total_pages`/`new_page_per_day` inputs, and verify existing callers are updated to match (see Section 8)

## 8. CLI wiring

- [ ] 8.1 Derive book orientation in `cli.py` from `get_paper_size_pixels()` (`portrait` if height ≥ width, else `landscape`), and verify with a unit test for both A4 (portrait) and a custom landscape size
- [ ] 8.2 Update the `distribute_photos` call site to pass the merged photo+title sequence, the active theme's max count, book orientation, and `pb_config.layout.new_page_per_day`, and verify `photobook --config <file>` still generates output end-to-end for an existing example config
- [ ] 8.3 Update progress/echo output if page-count messaging changes meaningfully (e.g. when merge fallback altered the effective distribution), and verify manually via `--verbose` output

## 9. Tests

- [ ] 9.1 Regression-test the exact 168-photos/100-pages scenario from the existing spec: assert no page is empty, and assert the under-full pages are no longer clustered only at the end (e.g. assert at least one under-full page appears in the first half of the book, for an input with day boundaries spread throughout)
- [ ] 9.2 Determinism test: run distribution twice on identical input (including a case that triggers merge fallback and one that triggers slack-splitting) and assert byte-identical `photo_to_page_map` output
- [ ] 9.3 End-to-end test combining day boundaries, title slots, and orientation-tiered splitting in one config, asserting the resulting page-by-page item list matches an expected, hand-verified layout
- [ ] 9.4 Update any existing `tests/test_layout.py` cases whose asserted per-page counts encode the old arithmetic clustering behavior (e.g. `test_exact_page_count_uneven_distribution`, `test_exact_page_count_168_photos_100_pages`) to reflect the new day/orientation-aware distribution, or to pin `new_page_per_day=false` where the test is specifically about the legacy arithmetic path

## 10. Documentation

- [ ] 10.1 Document `layout.new_page_per_day` (default, effect, interaction with `pages` vs `photos_per_page`) in README/example config
- [ ] 10.2 Document the day-boundary and orientation-matched-splitting rules, including the last-resort merge fallback, so users understand why a fixed-`pages` book's photo placement can shift after this change
