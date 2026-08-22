## Why

`render_text_label` in `src/photobook_as_code/renderer.py` has no word-wrapping: it only splits displayed lines on literal newlines from the parsed markdown, and if a single line's rendered width exceeds the text box's width, the per-segment width check breaks before drawing anything — the entire line silently vanishes rather than clipping partially or wrapping. This was always possible, but the recently shipped `photo-relative-text-x` change makes text boxes track a photo's actual rendered (often letterboxed, narrower) pixel width instead of the page's width, which makes the box far more likely to be narrower than a heading or caption line. Confirmed reproduction: on the `clean` theme's 4-photo layout, headings `# Auf nach Hamburg` and `# Hamburger Spendenparlament` render as an empty background box with no visible text at all.

## What Changes

- Add real word-wrapping to `render_text_label`: a display line that doesn't fit `text_box_width` is broken into multiple wrapped lines at word boundaries instead of being dropped entirely.
- Word-wrapping tokenizes each markdown-parsed line's styled segments into words, preserving each word's style (plain/bold/italic/heading) across the wrap.
- The auto-height calculation (used when `text.height` is omitted) accounts for the actual number of wrapped display lines, not just the number of markdown source lines, so the box grows taller to fit wrapped content — consistent with how it already auto-fits single-line content today.
- When `text.height` is explicitly set, wrapped lines that overflow the fixed height continue to clip at the boundary, same as today's per-line clipping behavior.
- Edge case: a single word wider than `text_box_width` on its own is still drawn (allowed to overflow the box's width) rather than being silently dropped — consistent with the goal that text should never disappear entirely.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `output-generation`: The "Render text labels on pages" requirement's "Text exceeds bounding box" scenario changes from clip-only to word-wrap-then-clip (only clipping when a fixed `text.height` is exceeded), and "Multi-line text rendering" is clarified to include lines produced by wrapping, not just literal newlines in the source text.

## Impact

- `src/photobook_as_code/renderer.py`: `render_text_label` — the first-pass measurement loop needs to tokenize segments into words and pack them into wrapped display lines bounded by `text_box_width`, replacing the current per-markdown-line width/height accumulation; the second-pass render loop draws each wrapped display line.
- `openspec/specs/output-generation/spec.md`: requirement text and scenarios for text rendering when content exceeds the bounding box.
- `tests/test_integration_text_labels.py`, `tests/test_renderer.py`: add coverage for wrapped rendering and auto-height growth from wrapping; existing assertions that assume no wrapping remain valid since none currently exercise an overflowing line.
