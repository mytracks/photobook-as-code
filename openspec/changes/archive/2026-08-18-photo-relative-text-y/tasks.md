## 1. Renderer changes

- [x] 1.1 Update `render_text_label` in `src/photobook_as_code/renderer.py` to accept the associated photo's pixel top (`photo_pos_y`) and pixel height (`photo_height`) instead of deriving `box_y` from `page_height`.
- [x] 1.2 Reorder internals so `box_height` (auto-calculated from measured text + padding, or from `text_pos.height`) is resolved before `box_y` is computed.
- [x] 1.3 Compute `box_y = photo_pos_y + (text_pos.y / 100) * max(0, photo_height - box_height)`.
- [x] 1.4 Update the call site in `render_page` (where `render_text_label` is invoked per photo) to pass `photo_placements[i]`'s pixel top and height through.

## 2. Spec and theme cleanup

- [x] 2.1 Re-tune `text.y` values in `src/photobook_as_code/themes/clean.yaml` for the new photo-relative semantics (visually verify via existing demo/test config renders). Verified by rendering both text-bearing layout templates (2-photo and 4-photo) at full page resolution: existing `y` values (4/35/55/82/88/95) already read correctly under the new per-photo formula — each lands at the same visual position relative to its own photo (near-top/mid/near-bottom as intended). No numeric changes needed; see session notes for the verification script.
- [x] 2.2 Confirm `openspec/specs/theme-system/spec.md`'s "Define text positioning in layout templates" requirement no longer describes a `valign` property after archive (delta already rewrites the "Text position with vertical alignment" scenario to describe `y`-based alignment instead).

## 3. Tests

- [x] 3.1 Update or add unit tests covering `y: 0` (top-aligned), `y: 100` (bottom-aligned), and `y: 50` (centered) against a photo's pixel bounds.
- [x] 3.2 Add a test for the oversized-label clamp: label height greater than photo height top-aligns regardless of `y`.
- [x] 3.3 Update any existing assertions in `tests/test_themes.py` and `tests/test_integration_text_labels.py` that encode the old page-relative `y` behavior.

## 4. Verification

- [x] 4.1 Render a sample photobook with the updated `clean.yaml` and confirm text labels visually align with their photos as expected at a few different `y` values.
- [x] 4.2 Run the full test suite and confirm it passes. 120 passed, 0 failed.
