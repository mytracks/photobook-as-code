## 1. Packing pass: correct adjacency tracking

- [x] 1.1 In `_wrap_markdown_lines` (`src/photobook_as_code/renderer.py`), replace the per-segment `segment.text.split()` tokenization with a word/whitespace token stream (e.g. `re.findall(r'\S+|\s+', segment.text)`) iterated in one running loop across all segments of a source line, tracking a `pending_space` flag that is set by a whitespace token and consumed (and reset) by the next word token.
- [x] 1.2 Only add `space_width_for(font)` to `added_width` when `pending_space` is true AND a word has already been placed on the current display line (never before the line's first word) - verify via a unit test that `**Cocktail**-Kurs` packs as a single unbroken run with no space-width added between "Cocktail" and "-Kurs".
- [x] 1.3 Extend each entry appended to `current_words` (and thus each `word_infos` tuple) with the resolved `has_leading_space` boolean for that word, so the drawing pass can consume the decision instead of re-deriving it.

## 2. Drawing pass: consume the same adjacency decision

- [x] 2.1 Update `_draw_wrapped_lines` (`src/photobook_as_code/renderer.py`) to unpack the widened `word_infos` tuple and advance `current_x` by `space_width_for(font)` only when the word's `has_leading_space` flag is true, replacing the current `if not first_word` check.
- [x] 2.2 Verify `line_width` (used for center/right alignment in `_draw_wrapped_lines`) still matches the sum of word widths plus only-the-actually-inserted space widths, since it is computed during packing (task 1) and consumed unchanged during drawing - confirm via a test that centered/right-aligned wrapped text with a no-space segment boundary still aligns correctly.

## 3. Tests

- [x] 3.1 Add a rendering test reproducing `**Cocktail**-Kurs` (following the existing `_render_wrap_box`/`_has_ink`/`_count_ink` pixel-measurement pattern already used in `tests/test_renderer.py`, e.g. `test_text_label_wrap_bug_reproduction_with_clean_theme`) that asserts no gap-sized run of background-only pixels appears between the bold word's ink and the following hyphen's ink, and verify it fails against the pre-fix code and passes after the fix.
- [x] 3.2 Add the same style of test for `**links**, das Schloss`, asserting no phantom space renders before the comma.
- [x] 3.3 Add a regression test for `**bold** word` (real space present in source) asserting exactly one space-width gap is still rendered between the two words, so the fix does not remove intentional spacing.
- [x] 3.4 Add a regression test for a plain (non-markdown) multi-word segment confirming words within a single segment are still separated by a single space each, unchanged.
- [x] 3.5 Run the full test suite (`pytest tests/test_renderer.py tests/test_text_labels.py`) and confirm all tests pass, including the pre-existing word-wrap and baseline-alignment tests unaffected by this change.
