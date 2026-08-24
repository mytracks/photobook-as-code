## 1. Theme schema

- [x] 1.1 Add `line_spacing: int = 10` to `TextStyle` in `src/photobook_as_code/themes.py`
- [x] 1.2 Add `line_spacing: int = 10` to `TitleStyle` in `src/photobook_as_code/themes.py`
- [x] 1.3 Confirm no changes are needed to `Theme.from_dict`/`load_theme_file` (both style blocks already forward arbitrary keys via `**data.get(...)`) - verify by loading a theme YAML with `text: {line_spacing: 20}` and asserting `theme.text.line_spacing == 20`

## 2. Renderer

- [x] 2.1 In `render_text_label` (`renderer.py`), replace the hardcoded `line_spacing = 4` with `line_spacing = theme.text.line_spacing`
- [x] 2.2 In `render_title_slot` (`renderer.py`), replace the hardcoded `line_spacing = 4` with `line_spacing = theme.title.line_spacing`

## 3. Tests

- [x] 3.1 Add `test_themes.py` cases: `TextStyle()`/`TitleStyle()` default to `line_spacing == 10`, and both accept a custom `line_spacing` value via `Theme.from_dict`
- [x] 3.2 Run the full test suite (`pytest`) and confirm it passes, including `test_integration_text_labels.py::test_example_title_renders_with_visible_gap_between_heading_and_date` (its `gap > 20` assertion is a lower bound, so the larger default gap should not break it - verify rather than assume)

## 4. Manual verification

- [x] 4.1 Render a sample multi-line caption and title with the `clean` theme (default `line_spacing`) and visually confirm the increased spacing looks correct, e.g. via the `run` skill or existing example config
