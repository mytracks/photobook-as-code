## Why

Multi-line `text` and `title` content renders with only a hardcoded 4px gap between lines (`renderer.py`), which reads as cramped at the font sizes the built-in themes actually use (42-72px) and can't be tuned per theme.

## What Changes

- Add a `line_spacing` property (pixels, default `10`, replacing the current hardcoded `4`) to both the `text` and `title` theme style blocks, configured independently per block (same pattern as `base_font_size`, `text_padding`, etc.).
- `render_text_label` and `render_title_slot` use `theme.text.line_spacing` / `theme.title.line_spacing` respectively instead of the hardcoded constant.
- No validation is added for `line_spacing` (consistent with `base_font_size`/`text_padding` on `TextStyle`, which are likewise unvalidated today - only `TitleStyle.base_font_size`/`align` currently get bounds-checked).
- Existing themes that don't set `line_spacing` pick up the new default of `10` automatically (a visual change from today's effective `4`) - no theme file needs to change.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `theme-system`: `text` and `title` style blocks gain a `line_spacing` property.
- `text-labels`: the existing "Consistent line-to-line spacing regardless of content" requirement's gap is now theme-configured (default `10`, was an implicit `4`) instead of a fixed implementation constant.

## Impact

- `src/photobook_as_code/themes.py`: `TextStyle`, `TitleStyle` dataclasses gain `line_spacing: int = 10`.
- `src/photobook_as_code/renderer.py`: `render_text_label` (~line 395) and `render_title_slot` (~line 468) read `line_spacing` from the theme instead of the local hardcoded constant.
- Built-in themes (`clean`, `clean2`, `classic`, `modern`) are unaffected as files but render with a larger (10px vs 4px) inter-line gap by default.
- No config/schema migration needed - `line_spacing` is optional with a default, same as every other style property.
