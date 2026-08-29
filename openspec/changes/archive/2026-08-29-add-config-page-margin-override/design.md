## Context

See proposal.md - Why for motivation. Today `theme.spacing.page_margin` is read in exactly two places, both in `renderer.py`'s `render_page`: to compute `usable_width`/`usable_height` (page dimensions minus margin on each side), and to offset each photo's center position (`center_x`/`center_y`). `distribute_photos` (in `layout.py`, called from `cli.py` before rendering) never reads `page_margin` - it only depends on `theme.max_layout_count`. The webapp does not load themes or render pages at all. So `page_margin` has exactly one consumer path: `cli.py` loads the theme, then eventually calls `render_all_pages(...)` (which calls `render_page(...)` per page), and that's the only place the value is read.

## Goals / Non-Goals

**Goals:**
- Let a YAML config override a theme's `spacing.page_margin` for that run, without modifying `renderer.py`, `layout.py`, or the theme file itself.
- Keep the override in the same unit and validation rules as the theme's own field, so the two are interchangeable from the renderer's point of view.

**Non-Goals:**
- `photo_margin` override (out of scope per proposal.md - theme-only, aesthetic choice).
- Any unit conversion (mm/inches) - pixels only, matching the rest of the schema.
- A general-purpose "override any theme field from config" mechanism - this change is scoped to `page_margin` specifically; a broader mechanism is a separate concern if it's ever needed.

## Decisions

**Apply the override once, immediately after theme load, via `dataclasses.replace`.** In `cli.py`, right after `theme = load_theme(pb_config.theme)`: if `pb_config.output.page_margin is not None`, replace the theme with `dataclasses.replace(theme, spacing=dataclasses.replace(theme.spacing, page_margin=pb_config.output.page_margin))` before `theme` is used by `distribute_photos` or `render_all_pages`. Because `page_margin` has exactly one consumer path (see Context), this single mutation point fully and correctly propagates the override everywhere it matters - `renderer.py` keeps reading `theme.spacing.page_margin` exactly as it does today, with no new parameter to thread through `render_page`/`render_all_pages`/`generate_output`. This mirrors an existing pattern already used in this codebase's own tests (`dataclasses.replace(clean_theme, text=dataclasses.replace(...))` in `test_renderer.py`) rather than introducing a new one.

Alternative considered and rejected: threading a `page_margin_override` parameter down through `render_page`/`render_all_pages` (the same shape used for the `transparent` flag in the prior change). Rejected because `page_margin` is consumed in only one function, unlike `transparent` which needed to reach `create_blank_page`, `draw_shadow`, and the text-compositing helpers - here, overriding the theme object once upstream is strictly simpler and touches fewer files.

**`output.page_margin: Optional[int] = None` on `OutputConfig`, distinguishing "unset" from explicit `0`.** Mirrors the existing `None`-means-unset convention already used by `OutputConfig.filename`/`directory`, but checked with `is not None` rather than truthiness - `0` is a legitimate, common override value (removing the tool's own margin entirely so only the print service's margin applies) and must not be conflated with "not set." (Note: the existing `filename`/`directory` checks in `config.py` use plain truthiness, which happens to be safe for strings where an empty string isn't a meaningful value anyway - `page_margin` cannot reuse that pattern since `0` is meaningful.)

**Validation in `load_config`, mirroring `themes.py`'s existing constraint.** `themes.py`'s `validate_theme` already rejects `theme.spacing.page_margin < 0`; the config-level override gets the same non-negative check, plus a type check (must be an integer), applied at config-load time alongside the other `output.*` validations (`format`, `transparent`+`format`) already there.

## Risks / Trade-offs

- [Risk] A user reading a printing service's margin spec in mm/inches has to convert to pixels at 300 DPI by hand → Mitigation: consistent with how every other dimension in this schema already works (`output.size`'s custom pixel form); accepted per proposal.md's unit decision.
- [Risk] Silent precedence confusion if a user expects the config value to merge with (rather than fully replace) the theme's margin → Mitigation: this is a full override, not a merge - single value, single meaning, matches how `theme:` selection itself already works (config picks a whole theme, not a diff against one).

## Migration Plan

Purely additive and opt-in (`output.page_margin` defaults to `None`, meaning "use the theme's value" - today's exact behavior). No migration steps; rollback is simply not setting the field.
