## Why

The prior change (`2026-08-18-photo-relative-text-y`) redefined text label `y` to be relative to the associated photo's pixel bounds, explicitly leaving `x`/`width` page-relative as a non-goal. That leaves the two axes in inconsistent frames of reference: a theme author positions `y` relative to the photo but `x` relative to the whole page, and must still mentally replicate the page's layout math for horizontal placement. Separately, there is no way today to intentionally break out of a photo's bounds and anchor a label flush to the page's actual outer edge — useful for captions that should sit at the true margin regardless of which photo slot they're attached to.

## What Changes

- **BREAKING**: Redefine `text.x` in layout templates from "percentage of page width" to "percentage of the associated photo's width," using the same slack-interpolation formula as `y`: `box_x = photo_left + (x / 100) * max(0, photo_width - label_width)`. `x: 0` aligns the label's left edge with the photo's left edge; `x: 100` aligns the label's right edge with the photo's right edge.
- **BREAKING**: Redefine `text.width` from "percentage of page width" to "percentage of the associated photo's width," keeping it a mandatory field (no auto-sizing introduced by this change).
- Add a new optional `text.dock` field (`left` or `right`) as an escape hatch: when set, the label's corresponding edge is pinned to the literal page border (pixel `0` for `left`, `page_width` for `right`) instead of interpolating within the photo, and `x` is ignored. `width` keeps its normal meaning (percentage of the photo's width) — only the position anchor changes, not the sizing reference. No margin is applied; the label can sit flush against the true page edge, consistent with how text positioning already ignores `page_margin` today.
- `dock` applies to the horizontal axis only; `y` remains photo-relative with no equivalent bottom-border escape hatch (out of scope).
- No new opt-in flag or dual-mode support for `x`/`width` — this is a direct redefinition, matching the precedent set by the `y` change.
- `render_text_label` needs the associated photo's horizontal pixel bounds (`photo_pos_x`, `photo_width`) passed in, mirroring how `photo_pos_y`/`photo_height` were threaded through for the `y` change.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `theme-system`: The "Define text positioning in layout templates" requirement's `x`/`width` semantics change from page-relative to photo-relative, and gains an optional `dock` field for pinning a label to the page's literal left or right border.

## Impact

- `src/photobook_as_code/renderer.py`: `render_text_label` signature and internals — needs `photo_pos_x`/`photo_width`; `box_x` calculation moves from a page-percentage formula to the photo-relative slack formula (or the `dock` pin when set). Call site in `render_page` updated to pass the photo's horizontal pixel bounds.
- `src/photobook_as_code/themes.py`: `TextPosition` gains a `dock` field (optional, validated as `left`/`right` when present); `x`/`width` validation and docstrings updated to describe the new photo-relative meaning.
- `src/photobook_as_code/themes/clean.yaml`: existing `text.x`/`text.width` values are page-relative today and must be re-tuned to the new photo-relative meaning (and optionally adopt `dock` where a theme author wants a label flush to the page edge).
- `openspec/specs/theme-system/spec.md`: requirement text and scenarios for text positioning.
- `tests/test_themes.py`, `tests/test_integration_text_labels.py`: assertions relying on old page-relative `x`/`width` behavior.
