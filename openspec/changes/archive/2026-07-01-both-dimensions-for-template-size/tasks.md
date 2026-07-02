## 1. Schema & Validation Updates (`themes.py`)

- [x] 1.1 Add `LayoutPhotoSize` dataclass with `width: float` and `height: float` in `src/photobook_as_code/themes.py`.
- [x] 1.2 Update the `LayoutPhoto` dataclass to type `size` as `LayoutPhotoSize` instead of `float`.
- [x] 1.3 Update `Theme.from_dict` to extract `width` and `height` from the `size` dict when parsing `LayoutPhoto` and construct a `LayoutPhotoSize`.
- [x] 1.4 Add validation in `validate_theme` or `Theme.from_dict` to raise a `ThemeError` if `size` is not a valid dictionary with `width` and `height`.

## 2. Layout Engine Updates (`renderer.py`)

- [x] 2.1 Update `render_page_to_image` to read `spec.size.width` and `spec.size.height` instead of applying the scalar `size` conditionally based on orientation.
- [x] 2.2 Calculate `target_width` and `target_height` by multiplying `usable_width` and `usable_height` by `spec.size.width` and `spec.size.height` respectively.
- [x] 2.3 Remove the previous orientation-based layout branching logic for bounds since both dimensions are explicitly bounded now.

## 3. Built-in Themes Updates

- [x] 3.1 Update `src/photobook_as_code/themes/clean.yaml` to use `{width, height}` for all photo sizes.
- [x] 3.2 Update `src/photobook_as_code/themes/modern.yaml` to use `{width, height}` for all photo sizes.
- [x] 3.3 Update `src/photobook_as_code/themes/classic.yaml` to use `{width, height}` for all photo sizes.

## 4. Tests & Verification

- [x] 4.1 Update tests (if any) in `tests/test_themes.py` to assert the new `LayoutPhotoSize` parsing logic and expect exceptions on invalid sizes.
- [x] 4.2 Update tests (if any) in `tests/test_renderer.py` to match the new strict `{width, height}` bounding box scaling logic.
- [x] 4.3 Run `pytest` to ensure all tests pass successfully.
- [x] 4.4 Build a test photobook locally (e.g. `python -m photobook_as_code build`) to visually verify layout behavior remains correct.