## Why

Photobook page margins currently come exclusively from the selected theme's `spacing.page_margin`. Many photobook printing services already reserve their own margin around every page, so the theme's margin and the printer's margin stack, leaving photos smaller/more inset than necessary. Since margin needs vary per printing service rather than per visual style, users need to override it per book (per YAML config) without forking or duplicating a theme file just to change one number.

## What Changes

- Add an optional `output.page_margin` integer field to the YAML configuration. When set, it overrides the selected theme's `spacing.page_margin` for that run; when unset, behavior is unchanged (theme's own value applies).
- Same unit as the theme field: raw pixels at the implicit 300 DPI already used throughout this schema (e.g. `output.size`'s custom `"2480x3508"` form) - no new unit system.
- Validate `output.page_margin` at config-load time: must be a non-negative integer when present, matching the constraint `themes.py` already enforces on a theme's own `spacing.page_margin`.
- `0` is a valid, explicit override (fully removes the tool's own page margin) and must be distinguished from "not set" (falls through to the theme's value).
- Only `page_margin` is overridable this way - `photo_margin` (inter-photo spacing) stays theme-only, since it's a visual/aesthetic choice rather than something a printing service imposes.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `yaml-configuration`: adds the `output.page_margin` field and its validation rule (non-negative integer, distinguishing unset from explicit `0`).

## Impact

- `src/photobook_as_code/config.py`: new `OutputConfig.page_margin: Optional[int] = None` field and its validation in `load_config`.
- `src/photobook_as_code/cli.py`: after `load_theme(...)`, apply the override (when set) to the loaded theme via `dataclasses.replace` before it's used by `distribute_photos`/`render_all_pages`.
- No changes needed to `renderer.py`, `layout.py`, `output.py`, or `themes.py`: `distribute_photos` never reads `page_margin`, and the renderer keeps reading `theme.spacing.page_margin` exactly as it does today - the override is fully resolved before either is called.
- No changes needed to the webapp: it does not load themes or render pages.
