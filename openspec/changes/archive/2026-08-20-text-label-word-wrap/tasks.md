## 1. Word-wrap in the renderer

- [x] 1.1 In `render_text_label`'s FIRST PASS, replace the per-segment measurement with per-word tokenization: split each `TextSegment.text` on whitespace, measure each word via `draw.textbbox` using that segment's already-resolved font, and pack words into display lines bounded by `text_box_width` (greedy word-wrap, one space's width between words).
- [x] 1.2 A word whose own width exceeds `text_box_width` occupies its own display line and is not further split or dropped.
- [x] 1.3 Replace `all_lines_info`'s one-entry-per-source-line shape with one entry per display line (`(word_infos, line_height, line_width)` — line_width added vs. the plan's `(word_infos, line_height)` so alignment/drawing don't need to re-sum word widths plus inter-word spacing in the second pass), and accumulate `total_text_height` over display lines.
- [x] 1.4 Update the SECOND PASS to draw each display line's words in sequence, removing the per-segment width-clip-and-break (packing already guarantees fit except the intentionally-overflowing oversized-word case).
- [x] 1.5 Keep the existing vertical clip (`text_pos.height is not None and current_y > text_box_y + text_box_height: break`) operating over display lines, so a fixed `height` still clips overflow the same way it does today.
- [x] 1.6 Keep per-line horizontal alignment (`align: left/center/right`) working against each display line's own measured width, unchanged in approach.

## 2. Tests

- [x] 2.1 Add a renderer test: a line wider than the box wraps onto multiple display lines instead of disappearing (assert visible pixels on more than one row within the box).
- [x] 2.2 Add a renderer test: auto-height (`text.height` unset) grows to fit the wrapped line count, not just the source line count.
- [x] 2.3 Add a renderer test: a single word wider than the box is still drawn (visible pixels present), even though it overflows the box's width.
- [x] 2.4 Add a renderer test: wrapped words retain their source segment's style (e.g. a bold word wrapped onto a new line still renders bold). DejaVuSansMono is monospace (identical advance width per weight), so this compares ink pixel *density*, not measured width, to detect boldness.
- [x] 2.5 Add a renderer test: with `text.height` explicitly set smaller than the wrapped content's total height, remaining display lines clip at the boundary.
- [x] 2.6 Reproduce the original bug report directly: render `clean.yaml`'s 4-photo mixed layout with `# Auf nach Hamburg` label using the theme's real text position/font and confirm ink now exists (not an empty background box). Uses the theme's real `spec.text` geometry with ink/background colors forced to pure white/black for unambiguous pixel detection, since the real theme's semi-transparent overlay blends with the underlying photo's own (untested) color.

## 3. Verification

- [x] 3.1 Run the full test suite and confirm it passes. 135 passed, 0 failed.
- [x] 3.2 Visually re-render the reproduction case from this change's proposal and confirm both previously-empty captions now show wrapped, readable text. "Auf nach Hamburg" wraps to two lines (centered), "Hamburger Spendenparlament" wraps to two lines (left-aligned), both fully visible with the box auto-grown to fit.
