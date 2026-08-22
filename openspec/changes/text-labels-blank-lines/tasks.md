## 1. Parsing: trim leading/trailing blank lines

- [x] 1.1 In `parse_markdown_text` (`src/photobook_as_code/text_labels.py`), trim leading and trailing blank lines from the split line list before building `(segments, heading_level)` tuples; leave interior blank lines untouched.
- [x] 1.2 Add/extend unit tests in `tests/test_text_labels.py` covering: a leading blank line is trimmed, a trailing blank line is trimmed (including the YAML `|` clip-chomping case), an interior blank line is preserved, and content with no blank lines is unaffected.

## 2. Rendering: real height for blank lines

- [x] 2.1 In `_wrap_markdown_lines` (`src/photobook_as_code/renderer.py`), when a source line has no words, set its display-line height to the regular font's line height at `base_font_size` (heading level 0) instead of `0`.
- [x] 2.2 Verify `line_spacing` still applies once per display line (including blank ones) so spacing composes the same way it does for non-blank lines.

## 3. Verification

- [x] 3.1 Add/extend a renderer test asserting a single interior blank line produces a vertical ink gap of roughly one line height (reuse the ink-detection helper already used in `tests/test_renderer.py`).
- [x] 3.2 Add/extend a renderer test asserting two consecutive interior blank lines produce roughly double the single-blank-line gap (additive stacking).
- [x] 3.3 Render `example-config.yaml`'s title entry (or an equivalent fixture) end-to-end and confirm no extra trailing gap appears below "30. April 2026" and a visible gap appears between the heading and the date line.
- [x] 3.4 Run the full test suite (`pytest`) and confirm no regressions in existing multi-line/heading text label tests.
