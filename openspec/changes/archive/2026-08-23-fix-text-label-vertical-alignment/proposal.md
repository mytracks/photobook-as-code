## Why

Caption and title text renders visibly too low. Root cause: the renderer measures a line's height from PIL's *tight ink bounding box* (`draw.textbbox`, per word) but then draws each word with `draw.text`'s default `anchor="la"` (ascender-relative), a different vertical reference. The gap between those two references depends on which letters a word contains, so words on the same line drawn at the same `current_y` land at different visual heights - e.g. in the real caption "Ein neuer Morgen" (DejaVuSansMono 42px, `clean` theme), "neuer" (all x-height letters) sags ~8px below "Ein" and "Morgen" (which have taller letters), and the auto-height box's configured bottom padding shrinks from 12px to ~4px because the tallest word's descender already eats into it. Existing unit tests use uniform all-caps placeholder words (`AAAA`/`BBBB`/`CCCC`) with loose "ink present somewhere in this band" assertions, so this mismatch went undetected until real prose exposed it.

## What Changes

- Change how wrapped text lines are measured and drawn (`_wrap_markdown_lines` / `_draw_wrapped_lines` in `renderer.py`) so every word on a line is positioned from one consistent vertical reference, instead of mixing tight-ink-bbox measurement with ascender-anchored drawing.
- Ensure a text box's configured padding is respected symmetrically top and bottom for auto-computed height, instead of being effectively squeezed at the bottom by descenders.
- Apply the same fix to title-slot rendering (`render_title_slot`), which shares the same measurement/draw helpers and the same vertical-centering math.
- No changes to markdown parsing, word-wrap line-breaking decisions, or any public config/theme field - this is a rendering-geometry fix only.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `text-labels`: add a requirement that rendered text (in both `text` and `title` content, per this capability's existing shared-rendering scenarios) positions all words on a line at a consistent vertical alignment, and that a text box's configured padding is respected on all sides - replacing today's ascender-anchor/tight-ink-bbox mismatch.

## Impact

- `src/photobook_as_code/renderer.py`: `_wrap_markdown_lines`, `_draw_wrapped_lines`, `render_text_label`, `render_title_slot`.
- `tests/test_renderer.py`: wrap/blank-line tests assert pixel bands derived from the same tight-bbox measurement being changed; they'll need review against whichever vertical reference the fix adopts (some may need their expected bands recomputed, not just re-passed).
- No config/schema changes; `text_labels.py` parsing is untouched.
- Visual output changes for any existing photobook using `text` or `title` labels: rendered captions/titles shift by a few pixels vertically. The shift is small and mostly invisible for all-caps or short single-word text, but noticeable for normal mixed-case prose - i.e. every real photobook's captions.
