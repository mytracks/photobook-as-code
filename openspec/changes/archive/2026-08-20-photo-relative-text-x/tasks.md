## 1. Renderer changes

- [x] 1.1 Update `render_text_label` in `src/photobook_as_code/renderer.py` to accept the associated photo's pixel left (`photo_pos_x`) and pixel width (`photo_width`), alongside the existing `photo_pos_y`/`photo_height`.
- [x] 1.2 Compute `box_width = int(photo_width * text_pos.width / 100)` from the photo's pixel width instead of `page_width`.
- [x] 1.3 Compute `box_x` via the slack formula when `text_pos.dock` is unset: `box_x = photo_pos_x + int(text_pos.x / 100 * max(0, photo_width - box_width))`.
- [x] 1.4 When `text_pos.dock` is `"left"` or `"right"`, override `box_x` to `0` or `page_width - box_width` respectively, ignoring `text_pos.x`.
- [x] 1.5 Update the call site in `render_page` to pass `photo_placements[i]`'s pixel left and width through (values already unpacked locally as `pos_x`/`width`).

## 2. Theme parsing changes

- [x] 2.1 Add `dock: Optional[str] = None` to `TextPosition` in `src/photobook_as_code/themes.py`.
- [x] 2.2 Validate `dock`, when present, is `"left"` or `"right"` (raise `ThemeError` otherwise), mirroring the existing `align` validation.
- [x] 2.3 Update `x`/`width` docstrings/comments in `themes.py` to describe the new photo-relative meaning.

## 3. Spec and theme cleanup

- [x] 3.1 Re-tune `text.x`/`text.width` values in `src/photobook_as_code/themes/clean.yaml` for the new photo-relative semantics (visually verify via existing demo/test config renders). Verified by rendering all three text-bearing templates (2-photo landscape/landscape, 4-photo landscape/landscape/portrait/landscape, 4-photo landscape-x4) at 2000x1500 with sample photos. Most existing values render correctly unchanged or even better than before: the redefinition fixes a latent bug where narrow/portrait photo cells previously got page-wide (not photo-wide) text boxes that spilled onto neighboring photos. Also confirmed box width now scales with a photo's actual rendered (post-letterboxing) pixel width, not its nominal cell size — a real, expected consequence of photo-relative width.
- [x] 3.2 Adopt `dock: left`/`dock: right` in `clean.yaml` where a caption is meant to sit flush against the page's outer edge, replacing any existing workaround that fakes this with a wide fixed-width box. The 4-photo template's bottom-right cell (a wide/short aspect that heavily letterboxes real photos) had `x: 75, width: 25` tuned for old page-relative math; reinterpreted as photo-relative it landed a tiny box floating inside the photo, nowhere near any edge. Replaced with `dock: right` so it pins to the page's true right border regardless of the photo's actual rendered width — confirmed by rendering.

## 4. Tests

- [x] 4.1 Update or add unit tests covering `x: 0` (left-aligned to photo), `x: 100` (right-aligned to photo), and `x: 50` (centered) against a photo's pixel bounds.
- [x] 4.2 ~~Add a test for the oversized-label clamp: label width greater than photo width left-aligns regardless of `x`.~~ Deliberately skipped: unreachable given `width`'s photo-relative bounds (0-100% of `photo_width` can never exceed `photo_width`), confirmed with user; corresponding spec scenario dropped. The defensive `max(0, ...)` clamp remains in code for symmetry with `y` but has no observable-behavior test.
- [x] 4.3 Add tests for `dock: left` and `dock: right`, confirming the label's edge lands at the page border regardless of the photo's horizontal position, and that `width` still derives from the photo's width.
- [x] 4.4 Add a validation test for an invalid `dock` value.
- [x] 4.5 Update any existing assertions in `tests/test_themes.py` and `tests/test_integration_text_labels.py` that encode the old page-relative `x`/`width` behavior.

## 5. Verification

- [x] 5.1 Render a sample photobook with the updated `clean.yaml` and confirm text labels visually align with their photos as expected at a few different `x` values and with `dock` set. Rendered all three text-bearing templates (2-photo, and both 4-photo variants) with sample fixture photos at 2000x1500; visually confirmed via saved PNGs that `x: 0/10/50/75/100`-style values and `dock: right` all land where expected relative to each photo.
- [x] 5.2 Run the full test suite and confirm it passes. 129 passed, 0 failed.
