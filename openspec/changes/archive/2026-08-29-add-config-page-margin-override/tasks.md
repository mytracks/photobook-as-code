## 1. Config

- [x] 1.1 Add `page_margin: Optional[int] = None` field to `OutputConfig` in `config.py`, parsed from `data['output'].get('page_margin')`
- [x] 1.2 Add validation in `load_config`: when `output.page_margin` is present, reject a non-integer value and reject a negative value, each with a `ConfigurationError` message naming `page_margin`
- [x] 1.3 Add `test_config.py` cases (mirroring the `TestOutputTransparentConfig` pattern): unset defaults to `None`, a non-negative integer (including `0`) is accepted and stored exactly, a negative integer is rejected, and a non-integer value (e.g. a non-numeric string) is rejected

## 2. CLI wiring

- [x] 2.1 In `cli.py`, immediately after `theme = load_theme(pb_config.theme)`, apply the override when `pb_config.output.page_margin is not None`: `theme = dataclasses.replace(theme, spacing=dataclasses.replace(theme.spacing, page_margin=pb_config.output.page_margin))` (add the `dataclasses` import)
- [x] 2.2 Add a `test_cli.py` case running the CLI end-to-end with `output.page_margin: 0` against a theme whose own `spacing.page_margin` is non-zero, asserting the rendered output reflects a zero margin (e.g. a photo pixel present at the very edge of the page that the theme's own margin would otherwise leave blank)
- [x] 2.3 Add a `test_cli.py` case confirming that omitting `output.page_margin` leaves output unchanged from today's behavior (theme's own margin applies) - reuse/extend an existing rendering test's assertions rather than duplicating theme geometry math

## 3. End-to-end validation

- [x] 3.1 Run the full test suite and confirm no regressions
- [x] 3.2 Render a small fixture book with `output.page_margin: 0` and with `output.page_margin` unset, using the same theme, and visually confirm the margin difference matches expectations
