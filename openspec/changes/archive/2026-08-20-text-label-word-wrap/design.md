## Context

`render_text_label` in `src/photobook_as_code/renderer.py` (line ~139-323) treats each markdown-parsed source line (`parsed_lines`, one `(segments, heading_level)` tuple per line from `parse_markdown_text`) as exactly one display line. The FIRST PASS (line ~197-248) measures each source line's total width/height via `draw.textbbox` per segment and accumulates `total_text_height` for auto-height. The SECOND PASS (line ~294-323) draws each source line's segments left-to-right, with a per-segment check (`if current_x + seg_width > text_box_x + text_box_width: break`) that silently drops the rest of the line — including the segment currently being checked — the moment a segment doesn't fit. There is no mechanism to break a line at a word boundary and continue on a new display line. `text_box_width = box_width - 2*padding` (line ~268) is already known before either pass runs, since `box_width` depends only on `photo_width`/`text_pos.width`, not on text measurement — so wrapping decisions can be made during the first pass without restructuring the box-width calculation. See `proposal.md` for why this now needs fixing.

## Goals / Non-Goals

**Goals:**
- A source line whose rendered width exceeds `text_box_width` wraps onto additional display lines at word boundaries, instead of the current all-or-nothing per-line clip.
- Auto-height (`text_pos.height is None`) sums the actual number of resulting display lines, so the box grows to fit wrapped content the same way it already grows to fit multiple source lines.
- Each wrapped word keeps the bold/italic/heading style of the segment it came from.
- A single word wider than `text_box_width` on its own is still drawn (allowed to overflow horizontally) rather than dropped.
- When `text_pos.height` is explicitly set and wrapped content still overflows it, remaining display lines clip at the height boundary — same behavior as today's per-line clip, just measured in display lines instead of source lines.

**Non-Goals:**
- No hyphenation or mid-word breaking — wrapping only happens at whitespace boundaries, consistent with the rest of the codebase assuming space-delimited (Latin-script) text.
- No font-size auto-shrinking to make text fit — the box grows (or clips, if `height` is fixed) instead of the text shrinking.
- No change to `text.width`'s meaning or the photo-relative position/dock logic from `photo-relative-text-x` — this change only affects line-breaking and height measurement.

## Decisions

**Tokenize each segment's text into words, not characters.** For each `TextSegment` in a source line, split `segment.text` on whitespace into words, each inheriting that segment's resolved font (already selected in the first pass via `segment.bold`/`segment.italic`/`font_size_multiplier`, line ~206-230). Each word is measured individually via `draw.textbbox`, same API already used per-segment today.
- Alternative considered: wrap at the segment granularity (treat each segment as an atomic unit). Rejected because segments commonly span several words with no inline formatting (e.g. a whole heading line is one segment), so segment-level wrapping would not actually solve the reported bug — the failing case is exactly a single multi-word segment wider than the box.

**Greedy word-wrap per source line, independently.** Within one source line, pack words left-to-right into a display line, adding a single space's width between consecutive words, until the next word would exceed `text_box_width`; then start a new display line. A literal newline in the source always starts a new source line (and thus at least one new display line) — wrapping never merges two source lines together, only splits one source line into more than one display line.
- Alternative considered: a more sophisticated line-breaking algorithm (e.g. minimizing raggedness across the whole paragraph, similar to TeX). Rejected as unnecessary complexity for photo captions, which are short; greedy wrap is what most simple renderers do and matches the existing code's overall simplicity.

**A word wider than `text_box_width` on its own occupies its own display line and is drawn anyway.** The packing loop places it alone (no other words share that line) and does not apply the width clip to it — this is the one case where a display line's measured width can exceed `text_box_width`.
- Alternative considered: keep dropping it (today's behavior). Rejected per the proposal's explicit goal that text should never silently disappear.
- Alternative considered: clip it at the box edge (draw only the part that fits). Rejected as more complex (would require sub-word clipping via character-level measurement) for a rare edge case; drawing the full overflowing word is simpler and still visible.

**First pass produces a flat list of display lines, each a list of word-infos, replacing `all_lines_info`'s current one-entry-per-source-line shape.** Each display line's entry is `(word_infos, line_height)` where `word_infos` is `[(word_text, font, word_width, word_height), ...]` — analogous to today's `segment_infos` but at word granularity and already wrap-resolved. `total_text_height` accumulates over these display lines instead of source lines, so auto-height (line ~250-253) needs no further change beyond consuming the new list.

**Second pass drops its per-segment width-clip-and-break, since packing already guarantees fit.** The existing check at line ~316 (`if current_x + seg_width > ...: break`) becomes unnecessary for normally-packed lines (the packing loop already ensured they fit) and would incorrectly truncate the intentionally-overflowing single-oversized-word case. The second pass instead just draws every word on every display line; the only remaining boundary check is the existing vertical one (line ~299, `if text_pos.height is not None and current_y > text_box_y + text_box_height: break`), which continues to clip whole display lines when a fixed height is exceeded — now operating over the (larger) set of wrapped display lines rather than source lines.

**Inter-word space width uses the font of the word being measured, not a fixed constant.** When summing a display line's width during packing, the space before each word (after the first) is measured via the same word's font (e.g. `draw.textbbox` on a single space character in that font) rather than a hardcoded pixel value, so spacing stays proportional to font size across heading/body text.

## Risks / Trade-offs

- [Splitting each segment's text on whitespace and rejoining with a single space could lose original double-spacing or non-breaking-space formatting within a segment] → Mitigation: accepted; captions are free-form text, not precision-formatted content, and this matches how most simple word-wrap implementations normalize whitespace.
- [More `draw.textbbox` calls (one per word instead of one per segment) increase rendering cost per label] → Mitigation: captions are short (a handful of words); the cost is negligible relative to photo loading/resizing elsewhere in `render_page`.
- [Wrapping assumes whitespace-delimited text; scripts without spaces (e.g. CJK) would not wrap correctly] → Mitigation: out of scope — the existing codebase (line-width accumulation, alignment) already assumes Latin space-delimited text throughout; not a regression introduced by this change.

## Migration Plan

No migration needed — this is an internal rendering-behavior fix with no config/schema changes. Existing theme files and text labels are unaffected; text that already fit within its box renders identically (a single-word-per-line or short-line case produces exactly one display line, same as today). Verify via the two reproduction cases from the proposal (`# Auf nach Hamburg`, `# Hamburger Spendenparlament` on `clean.yaml`'s 4-photo layout) rendering visibly instead of vanishing, plus existing text-label rendering tests continuing to pass unchanged.
