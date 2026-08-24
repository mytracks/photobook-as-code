## Context

`_wrap_markdown_lines` and `_draw_wrapped_lines` in `renderer.py` measure each display line's height from the actual ink extent of its words (not a font-nominal metric - see the `fix-text-label-vertical-alignment` design doc), then advance to the next line by `line_height + line_spacing`, where `line_spacing` is a local variable hardcoded to `4` at both call sites (`render_text_label` line ~395, `render_title_slot` line ~468). See proposal.md for why a fixed 4px reads as cramped at the font sizes the built-in themes use.

## Goals / Non-Goals

**Goals:**
- Replace the hardcoded `4` with a per-style-block theme property, `line_spacing`, read independently for captions (`theme.text.line_spacing`) and titles (`theme.title.line_spacing`).
- Default to `10` when a theme doesn't specify it, so every existing theme file picks up the improved spacing with no edits.

**Non-Goals:**
- No CSS-style unitless multiplier (`line_height: 1.4` scaling with `base_font_size`) - considered and rejected in favor of a flat pixel value, consistent with every other numeric property on `TextStyle`/`TitleStyle` (`base_font_size`, `text_padding`, etc. are all concrete pixels, not ratios).
- No change to how a single line's own height is measured (still ink-based, unchanged from the vertical-alignment fix) - only the constant added between lines becomes configurable.
- No special handling for heading lines (`#`/`##`/`###`, which get a `font_size_multiplier` bump) - a flat pixel gap doesn't need to scale with the line's own font size the way a multiplier would have, so this concern from the exploration is moot with the pixel-gap approach.
- No new validation - `line_spacing` follows the existing precedent of `TextStyle.base_font_size`/`text_padding`, which are unvalidated today (only `TitleStyle.base_font_size`/`align` currently get bounds-checked, as a one-off from when title slots were added). A negative value is left as a theme author's own problem, same as a negative `text_padding` would be today.

## Decisions

**Add `line_spacing: int = 10` to both `TextStyle` and `TitleStyle` (`themes.py`), not a single shared theme-level value.** Both dataclasses already duplicate every other style property independently (`base_font_size`, `font_family`, `text_color`, ...), and `Theme.from_dict` constructs each via `**data.get('text'/'title', {})` - a plain dict-unpack with no per-field logic - so a new field with a default requires no parsing changes at all.

**No new validation.** Considered adding a non-negative check (matching the `borders.width`/`spacing.page_margin` pattern in `validate_theme`), but `TextStyle` numeric fields have no analogous checks today, so adding one only for `line_spacing` would be an inconsistent one-off. Left unvalidated for both style blocks.

## Risks / Trade-offs

- [Every theme's rendered output changes by default (4px → 10px gap) with no opt-out other than explicitly setting `line_spacing: 4`] → Mitigation: accepted - this is the explicit intent (proposal.md), and any golden-image/pixel-comparison tests that assumed the old 4px gap need their expected output regenerated (tasks.md).

## Migration Plan

No schema migration - `line_spacing` is optional with a default, like every other style property. Existing theme YAML files need no edits to pick up the new default; a theme wanting the old tighter spacing can set `line_spacing: 4` explicitly.
