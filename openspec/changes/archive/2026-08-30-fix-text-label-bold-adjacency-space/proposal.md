## Why

Text like `**Cocktail**-Kurs` or `**links**, das Schloss` renders with a spurious space right after the closing `**`, producing `Cocktail -Kurs` and `links , das Schloss`. The Markdown parser correctly identifies segment boundaries with no source whitespace between them, but the renderer's word-wrap and drawing code always insert one space's width between any two consecutive words, regardless of whether a segment boundary is directly adjacent (no whitespace) or genuinely space-separated.

## What Changes

- Fix the word-wrap packing pass (`_wrap_markdown_lines`) and the drawing pass (`_draw_wrapped_lines`) in `renderer.py` so that a space is only inserted between two tokens when real whitespace existed between them in the source content - not merely because the tokens came from two different markdown segments.
- Preserve this distinction through tokenization: each segment currently loses, via `segment.text.split()`, whether it started or ended flush against an adjacent segment with no whitespace in between.

## Capabilities

### Modified Capabilities
- `text-labels`: adds a requirement that markdown emphasis/heading markers directly adjacent to surrounding text (no source whitespace at the boundary) render with no synthetic space inserted at that boundary.

## Impact

- `src/photobook_as_code/renderer.py`: `_wrap_markdown_lines` (word packing / width accumulation) and `_draw_wrapped_lines` (x-position advance while drawing) both currently assume a space between every consecutive word pair.
- Possibly `src/photobook_as_code/text_labels.py`: `parse_markdown_line` / `TextSegment` may need to expose enough boundary information (e.g. whether a segment is immediately followed by non-whitespace) for the renderer to make this distinction correctly.
- No change to the text-label web editor, which renders raw Markdown without formatting and is unaffected.
