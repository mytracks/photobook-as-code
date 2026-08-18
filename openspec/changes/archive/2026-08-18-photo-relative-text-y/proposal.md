## Why

Text label `y` is currently a percentage of the *page* height, but a photo's actual pixel position on the page is computed dynamically from the layout template plus `page_margin`/`photo_margin`. To place a label relative to "its" photo, a theme author has to mentally replicate that layout math. Redefining `y` as a percentage of the associated *photo's* height removes that indirection: `y=0` means the label's top edge aligns with the photo's top edge, `y=100` means the label's bottom edge aligns with the photo's bottom edge.

## What Changes

- **BREAKING**: Redefine `text.y` in layout templates from "percentage of page height" to "percentage of the associated photo's height," using the CSS `background-position`-style slack formula: `box_y = photo_top + (y / 100) * max(0, photo_height - label_height)`.
- Slack is floored at 0: when the label's rendered height exceeds the photo's height, the label top-aligns with the photo regardless of `y`.
- `text.x` and `text.width` are unchanged (remain percentages of page width) — text labels typically extend from page edges, not photo edges.
- No new field or opt-in flag is introduced; existing `y` values in theme files take on the new meaning directly and must be re-tuned.
- `render_text_label` needs the associated photo's pixel position and height (already computed in `render_page` as `photo_placements[i]`, not currently passed through) to perform the calculation. Auto-calculated label height (from text content, when `text.height` is unset) must be resolved before `box_y` is computed, reversing the current order of operations.
- Fix the stale `theme-system` spec scenario describing a `valign` (top/middle/bottom) property — `valign` was already removed from the code in a prior change; the spec never caught up. Its "Text position with vertical alignment" scenario is rewritten to describe vertical alignment via `y` (the OpenSpec archive tooling requires MODIFIED requirements to retain every current scenario title, so the title is kept and its content corrected rather than deleted).

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `theme-system`: The "Define text positioning in layout templates" requirement's `y` semantics change from page-relative to photo-relative; the stale `valign` scenario is removed.

## Impact

- `src/photobook_as_code/renderer.py`: `render_text_label` signature and internals (needs photo pixel bounds; height-before-position ordering), and its call site in `render_page`.
- `src/photobook_as_code/themes/clean.yaml`: existing `text.y` values are page-relative today and must be re-tuned to the new photo-relative meaning.
- `openspec/specs/theme-system/spec.md`: requirement text and scenarios for text positioning.
- `tests/test_themes.py`, `tests/test_integration_text_labels.py`: any assertions relying on old page-relative `y` behavior.
