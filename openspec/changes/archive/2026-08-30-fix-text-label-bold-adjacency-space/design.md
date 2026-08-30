## Context

See proposal.md - Why for the bug itself. Relevant existing code, both in `src/photobook_as_code/renderer.py`:

- `_wrap_markdown_lines`: for each `TextSegment` (from `text_labels.parse_markdown_line`), tokenizes with `segment.text.split()`, flattening all segments of a source line into one list of `(word, font, word_width, word_height)` tuples. It adds one `space_width_for(font)` before every word except the very first in that flattened list (line ~231-240).
- `_draw_wrapped_lines`: walks the same flattened `word_infos` list and advances `current_x` by `space_width_for(font)` before every word except the first (line ~400-406).

Both places assume "two consecutive entries in the flattened list are always space-separated," which was a correct assumption before markdown segment splitting existed on this list, but breaks once one segment's text ends flush against the next segment's text with no whitespace in between (which is exactly what happens at a `**bold**` boundary with no adjacent space, per `parse_markdown_line`'s regex split - see `openspec/changes/archive/2026-08-20-text-label-word-wrap/design.md` for why the flattening approach was chosen in the first place).

Importantly, `parse_markdown_line` already preserves the real source whitespace verbatim inside each segment's `.text` (it slices the original line directly, e.g. `line[last_end:match.start()]`); no whitespace information is lost at parse time. It is lost only by the renderer's `str.split()` tokenization, which discards leading/trailing whitespace of each segment before the segments are flattened together.

## Goals / Non-Goals

**Goals:**
- Only insert a space between two consecutive rendered words when real whitespace existed between them in the source text, at both the packing (`_wrap_markdown_lines`) and drawing (`_draw_wrapped_lines`) stages.
- Keep the fix localized to tokenization/adjacency bookkeeping; do not change how word widths/heights are measured, how wrapping decisions are made, or the `TextSegment` public shape.

**Non-Goals:**
- Preserving the exact width of multiple consecutive whitespace characters (e.g. two spaces) between words. The prior word-wrap change already accepted collapsing any whitespace run to one space's width as a known trade-off; this fix does not change that.
- Any change to the web editor's raw-Markdown (no formatting) rendering, which is unaffected by this bug.

## Decisions

**Tokenize each segment into an alternating word/whitespace stream, not just words.**

Replace `segment.text.split()` with something like `re.findall(r'\S+|\s+', segment.text)`, which yields both word runs and whitespace runs as explicit tokens, in order, still per segment. While iterating tokens across all segments of a source line (in a single running loop, not per-segment-reset), track a `pending_space` boolean: a whitespace token sets it `True`; consuming a word token uses and then resets it to `False`. A space's width is added before a word only when `pending_space` is `True` and at least one word has already been placed on the current display line (i.e. never before the line's first word). This makes the space decision purely a function of "was there whitespace immediately before this word in the source," which is correct whether that whitespace was inside one segment or fell exactly at a segment boundary - the running `pending_space` flag naturally carries across the segment loop's iteration without needing new fields on `TextSegment`.

*Alternative considered*: add explicit `leading_space: bool` / `trailing_space: bool` fields to `TextSegment` at parse time. Rejected: it duplicates information already recoverable from `segment.text` itself, and would require `parse_markdown_line` to strip that whitespace out of `.text` (to avoid double-representing it), which is a larger, less localized change than fixing tokenization alone in the renderer.

*Alternative considered*: keep `.split()` per segment but special-case "does this segment's raw text start/end with whitespace" only at segment boundaries (leave intra-segment tokenization untouched). Rejected: it is effectively the same fix expressed with two code paths (intra-segment vs. inter-segment) instead of one uniform token stream, for no benefit - the uniform `\S+|\s+` stream handles both cases with the same logic.

**Carry the "has a space before it" decision into `word_infos` so the drawing pass doesn't re-derive it independently.**

Both `_wrap_markdown_lines` (packing/width accumulation) and `_draw_wrapped_lines` (x-advance while drawing) currently each independently assume "space before every word but the first." Once packing knows the correct per-word answer, extend each `word_infos` tuple with that boolean (e.g. `(word, font, word_width, word_height, has_leading_space)`) so drawing consumes the already-decided answer rather than re-deriving it from a `first_word` flag. This keeps the two passes' notion of spacing in sync by construction instead of by parallel maintenance.

## Risks / Trade-offs

- [Widening the `word_infos` tuple shape] → Both producer (`_wrap_markdown_lines`) and consumer (`_draw_wrapped_lines`) are updated together in this change; no other code constructs or consumes these tuples.
- [A segment boundary with no whitespace on either side but where the two adjacent segments are visually different styles (e.g. bold immediately followed by italic, no space)] → Same fix applies uniformly regardless of which styles are adjacent; the space decision depends only on source whitespace, not on style change.
