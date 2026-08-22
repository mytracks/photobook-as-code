## Context

`render_text_label(draw, text_label, text_pos, page_width, page_height, theme)` in `src/photobook_as_code/renderer.py` currently computes `box_y = int(page_height * text_pos.y / 100)` from page dimensions alone (line ~154), before the label's own height is known. `box_height` is resolved later (line ~236-242): either `text_pos.height * page_height / 100` if the template specifies it, or auto-calculated from measured text content + padding.

The photo this label is attached to already has its pixel bounds computed in `render_page`, stored in `photo_placements[i]` as `(pos_x, pos_y, width, height)` (line ~344-364), but that tuple isn't passed to `render_text_label` today — only `page_width`/`page_height` are. See proposal.md for why `y` is moving to photo-relative semantics.

## Goals / Non-Goals

**Goals:**
- `y` resolves against the specific photo's pixel top/height, not the page.
- Slack-based interpolation (CSS `background-position`-style): `box_y = photo_top + (y / 100) * max(0, photo_height - label_height)`.
- Label height must be fully resolved (auto-calculated or from `text_pos.height`) before `box_y` is computed.

**Non-Goals:**
- `x`/`width` stay page-relative — out of scope per explicit decision.
- No opt-in flag or dual-mode support; this is a direct redefinition of `y`.
- No change to horizontal alignment, markdown parsing, background/padding rendering, or font handling.

## Decisions

**Pass photo pixel bounds into `render_text_label`.** Change its signature to accept `photo_pos_y: int, photo_height: int` (from `photo_placements[i]`) in place of relying on `page_height` for the y-axis. `page_width`/`page_height` are still needed for `x`/`width`. Update the call site in `render_page` (line ~415-423) to pass `photo_placements[i][1]` and `photo_placements[i][3]`.
- Alternative considered: pass the whole `photo_placements[i]` tuple through. Rejected in favor of only the two values actually used, keeping the function's contract explicit.

**Reorder computation: label height before `box_y`.** Move the `box_x`/`box_width` calculation (page-relative, unaffected) to stay early, but defer `box_y` until after `box_height` is resolved (post text-measurement pass). This only reorders existing code; no new measurement pass is introduced.

**Clamp slack at 0, not the `y` input.** Compute `slack = max(0, photo_height - label_height)` rather than clamping `y` itself, so `y: 100` with an oversized label still resolves to `box_y = photo_top` (top-aligned) rather than some negative or out-of-bounds offset.
- Alternative considered: clamp `box_y` post-hoc so the label's bottom never exceeds `photo_top + photo_height`. Equivalent in the oversized case but the slack-based clamp is a single formula with no separate bounds-check branch, and it matches the "top-aligned" framing from the requirement.

**No back-compat / dual-mode flag.** Confirmed with user: this is a deliberate breaking change to `y`'s meaning. `clean.yaml`'s existing `y` values (already mid-tuning, uncommitted) will need re-tuning as part of task work, not migration tooling.

## Risks / Trade-offs

- [Existing theme files with page-relative `y` values will render text in the wrong place after this change, silently — no validation error, just a visually wrong result] → Mitigation: this is accepted as an intentional breaking change (single theme file in the repo, already being hand-tuned); call it out prominently in the task list and re-tune `clean.yaml` as part of this change.
- [Photo pixel bounds can vary between the photo actually rendered vs. a failed-to-load photo, where `photo_placements[i]` stores `(0, 0, 0, 0)` — dividing/interpolating against a 0-height photo] → Mitigation: `render_page` already skips border/text rendering when `width == 0 or height == 0` (line ~398-399) before reaching the text-label branch, so this case never reaches `render_text_label`.

## Migration Plan

No automated migration — this is a single-theme codebase at present. As part of task work: re-tune `src/photobook_as_code/themes/clean.yaml`'s `text.y` values against the new semantics (visually verify via the existing demo/test config), and update any test fixtures/assertions in `tests/test_themes.py` and `tests/test_integration_text_labels.py` that encode the old page-relative behavior.
