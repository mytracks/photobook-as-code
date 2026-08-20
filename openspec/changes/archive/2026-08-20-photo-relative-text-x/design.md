## Context

`render_text_label(draw, text_label, text_pos, page_width, page_height, photo_pos_y, photo_height, theme)` in `src/photobook_as_code/renderer.py` (line ~139) currently computes horizontal placement from page dimensions alone, before the vertical (photo-relative) calculation runs:

```python
box_x = int(page_width * text_pos.x / 100)
box_width = int(page_width * text_pos.width / 100)
```

`render_page`'s call site (line ~424-434) already has the photo's full pixel bounds in `photo_placements[i]` as `(pos_x, pos_y, width, height)`, but today only unpacks `pos_y`/`height` to pass through — `pos_x`/`width` are available locally (line ~405) and just need to be threaded into the call. See `proposal.md` for why `x`/`width` are moving to photo-relative semantics, matching `y`'s existing precedent (`2026-08-18-photo-relative-text-y`).

## Goals / Non-Goals

**Goals:**
- `x` resolves against the specific photo's pixel left edge/width, using the same slack-interpolation formula already used for `y`.
- `width` resolves as a percentage of the photo's pixel width instead of the page's.
- An optional `dock: left | right` on `TextPosition` overrides the horizontal anchor to pin the label's edge to the literal page border (pixel `0` or `page_width`), ignoring `x` and `page_margin`, while `width` keeps resolving from the photo's width regardless of `dock`.

**Non-Goals:**
- No auto-width (unlike `height`, `width` stays mandatory) — this change only touches how `x`/`width` are anchored and scaled, not whether `width` can be omitted.
- No vertical equivalent of `dock` (no bottom-border pin for `y`) — horizontal only, per explicit decision.
- `dock` does not respect `page_margin`; it hugs the literal pixel edge, consistent with how text positioning already ignores `page_margin` today.
- No opt-in flag or dual-mode support; this is a direct redefinition of `x`/`width`, matching the precedent set by the `y` change.

## Decisions

**Pass photo pixel bounds (`pos_x`, `width`) into `render_text_label`, alongside the already-passed `pos_y`/`height`.** Add `photo_pos_x: int, photo_width: int` parameters. Update the call site in `render_page` (line ~425-434) to pass `pos_x` and `width` from the already-unpacked `photo_placements[i]` tuple — no new data needs to be computed or stored, since `photo_placements` already carries all four values.
- Alternative considered: pass the whole `photo_placements[i]` tuple through instead of four scalars. Rejected for the same reason the `y` change rejected it — keeps the function's contract explicit about exactly which values it uses.

**Compute `box_width` from `photo_width` before `box_x`.** Unlike the `y`/`height` change (where height must be resolved from a text-measurement pass before `box_y` can be computed), `width` here is always explicit (`text_pos.width`), so `box_width = int(photo_width * text_pos.width / 100)` has no ordering dependency on text measurement. `box_x` is then computed either via the slack formula or the `dock` pin, both of which only need `box_width` and `photo_pos_x`/`photo_width` (or `page_width` for `dock`).

**`dock` short-circuits the slack formula, not `box_width`.** When `text_pos.dock` is `"left"`, `box_x = 0`; when `"right"`, `box_x = page_width - box_width`. `box_width` is computed identically whether or not `dock` is set (always from `photo_width`), so a docked label's size still tracks its photo's size — only its horizontal anchor point changes. `text_pos.x` is read but ignored when `dock` is set.
- Alternative considered: let `dock` also switch `width`'s reference from `photo_width` to `page_width`, so a docked label sizes itself against the page instead of the photo. Rejected per the confirmed decision that `dock` is purely a position anchor override, not a sizing override — keeps `width`'s meaning consistent regardless of `dock`, avoiding a second hidden mode.

**`dock` validated in `themes.py` alongside `x`/`width`/`align`.** `TextPosition` gains `dock: Optional[str] = None`; when present it must be `"left"` or `"right"` (`ThemeError` otherwise), mirroring the existing `align` validation pattern. `x` remains required and validated as 0-100 even when `dock` is set (it's simply unused at render time) — no special-casing needed in the parser, keeping validation independent of cross-field interaction.

**Clamp slack at 0, not the `x` input** (mirrors the `y` decision). `slack = max(0, photo_width - box_width)`; `box_x = photo_pos_x + int(text_pos.x / 100 * slack)` for the non-docked case, so an oversized label left-aligns with the photo rather than resolving to a negative offset.

**No back-compat / dual-mode flag.** This is a deliberate breaking change to `x`'s and `width`'s meaning, confirmed with the user — same posture as the `y` change. `clean.yaml`'s existing `text.x`/`text.width` values are page-relative today and will need re-tuning as part of task work.

## Risks / Trade-offs

- [Existing theme files with page-relative `x`/`width` values will render text in the wrong horizontal place after this change, silently — no validation error, just a visually wrong result] → Mitigation: accepted as an intentional breaking change (single theme file in the repo); re-tune `clean.yaml` as part of this change and visually verify via the existing demo/test config.
- [A label `dock`ed to a border on a photo positioned near the opposite edge could visually overlap or detach from its photo, since `dock` deliberately ignores the photo's horizontal position] → Mitigation: this is the intended use case (labels that should sit at the true page margin regardless of photo placement); no mitigation needed beyond documenting the behavior in the spec.
- [`photo_placements[i]` stores `(0, 0, 0, 0)` for a photo that failed to load, which would make `photo_width` 0 and the slack formula degenerate] → Mitigation: unchanged from the `y` change — `render_page` already skips border/text rendering when `width == 0 or height == 0` (line ~407-408) before reaching `render_text_label`, so this case never reaches the new code path either.

## Migration Plan

No automated migration — single-theme codebase at present. As part of task work: re-tune `src/photobook_as_code/themes/clean.yaml`'s `text.x`/`text.width` values against the new photo-relative semantics (visually verify via the existing demo/test config), adopt `dock` where a theme author wants a label flush to the page edge, and update any test fixtures/assertions in `tests/test_themes.py` and `tests/test_integration_text_labels.py` that encode the old page-relative behavior.
