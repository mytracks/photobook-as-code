## 1. Core Fix

- [x] 1.1 In `src/photobook_as_code/text_labels.py`, change `TitleLabel.orientation` to return `'landscape'` instead of `'portrait'`, and update its docstring/comment accordingly. Verify by running `python -c "from photobook_as_code.text_labels import TitleLabel; from datetime import datetime; assert TitleLabel(timestamp=datetime.now(), title='x').orientation == 'landscape'"`.

## 2. Update Tests

- [x] 2.1 In `tests/test_text_labels.py`, rename `test_orientation_is_always_portrait` to `test_orientation_is_always_landscape`, update its docstring and assertion to `'landscape'`. Verify with `pytest tests/test_text_labels.py -k orientation -v`.
- [x] 2.2 In `tests/test_layout.py`, rename `test_title_matches_as_portrait_orientation` to `test_title_matches_as_landscape_orientation`, update its docstring and the `LayoutTemplate`/expected match so the title now matches the template's `landscape` slot instead of its `portrait` slot. Verify with `pytest tests/test_layout.py -k title -v`.
- [x] 2.3 Run the full test suite (`pytest tests/ -v`) and fix any other test that asserts title/portrait matching or relies on a title being treated as `portrait` for the orientation-matched page-splitting preference (`photo-layout-engine`'s slack-spending rule, `book_orientation` comparisons). Verify all tests pass.

## 3. Update Documentation

- [x] 3.1 In `README.md`'s "Title Slots" section, change "a title always renders into a portrait-shaped cell... themes need at least one layout at each relevant photo count that includes a **portrait**-shaped slot" to describe `landscape` instead. Verify by re-reading the rendered section for consistency with the new behavior.
- [x] 3.2 In `docs/theme_migration.md`, update the title-orientation paragraph ("A title always presents as `portrait` orientation for this matching...") to `landscape`, including the example about a theme missing the now-required orientation. Verify by re-reading the section for consistency.

## 4. Verify Built-in Themes and Real Configs

- [x] 4.1 Confirm each built-in theme (`classic`, `modern`, `clean`, `clean2`) still has at least one landscape-inclusive layout template at every item count it defines (already verified during design for counts 1-4 on all four; re-check after any theme edits). Verify with a quick script grouping each theme's `layouts` by `count` and checking for a `landscape` orientation entry.
- [x] 4.2 Re-render `ostseekreuzfahrt.yaml` (theme `clean2`) end-to-end and confirm page 21 and page 190 now place their titles in a wide/landscape-shaped slot with no `LayoutError`. Verify by inspecting the generated page 21 and page 190 output images.
