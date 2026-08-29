## 1. Config

- [x] 1.1 Add `transparent: bool = False` field to `OutputConfig` in `config.py`, parsed from `data['output'].get('transparent', False)`
- [x] 1.2 Add validation: raise `ConfigurationError` when `output.transparent` is `True` and `output.format != 'png'`; add/extend `test_config.py` cases for `transparent: true` with each of `png` (accepted), `jpg` (rejected), `pdf` (rejected), and the default-`false` case with any format (accepted)

## 2. Renderer: transparent canvas plumbing

- [x] 2.1 Add `transparent: bool` parameter to `create_blank_page`; when `True`, return `Image.new('RGBA', (width, height), (0, 0, 0, 0))` instead of the opaque `RGB` fill; when `False`, return an opaque `RGBA` canvas (alpha=255) instead of `RGB`, so downstream drawing code has one image mode to handle
- [x] 2.2 Thread a `transparent: bool` parameter through `render_page` and `render_all_pages` down to `create_blank_page`, and flatten the finished page to `RGB` with `.convert('RGB')` at the end of `render_page` only when `transparent` is `False`; verify with a unit test in `test_renderer.py` that `render_page(..., transparent=True)` returns an `RGBA` image and `render_page(..., transparent=False)` returns `RGB`
- [x] 2.3 Verify photo pasting needs no changes: add a `test_renderer.py` case asserting that with `transparent=True`, pixels under a placed photo are fully opaque (alpha=255) while an untouched page-margin pixel is fully transparent (alpha=0)
- [x] 2.4 Verify `draw_border` needs no changes on the new opaque-`RGBA` default path: existing border tests continue to pass unmodified

## 3. Renderer: fix drop shadow alpha handling

- [x] 3.1 Remove the final `.convert('RGB')` in `draw_shadow` so it returns the alpha-composited `RGBA` result directly; update any caller/type assumptions accordingly
- [x] 3.2 Add a `test_renderer.py` case with `theme.borders.shadow=True` and `transparent=True`: assert a pixel in the shadow's soft-edge region has partial alpha (neither 0 nor 255) and a pixel fully outside both photo and shadow remains alpha 0
- [x] 3.3 Add a regression test rendering a page with `shadow=True` and `transparent=False` before/after this change (e.g. against `classic.yaml`) and assert the flattened RGB pixel values are unchanged

## 4. Renderer: fix text-background-box compositing

- [x] 4.1 Rewrite `_draw_text_background` to build the background box on an isolated, fully-transparent `RGBA` temp layer sized to the text box (instead of `page_img.paste(overlay, box, overlay)`) and merge it onto the page with `Image.alpha_composite`
- [x] 4.2 Move the corresponding text-glyph drawing (for both text labels and titles) onto its **own** isolated temp layer, separate from the box layer, composited with a second `Image.alpha_composite` call after the box's - **correction during implementation**: drawing glyphs onto the *same* layer as the box (as originally worded here) reproduces the exact bug being fixed, since Pillow's anti-aliased text blending is only correct against a destination pixel that starts fully transparent or fully opaque, and the box leaves its own region at partial alpha regardless of which image (page or temp layer) holds it. Two separate layers, each merged independently via `Image.alpha_composite`, avoids that. Verified algebraically that this produces byte-identical output to the old code for the opaque (non-transparent) case, since Porter-Duff "over" onto a fully-opaque destination reduces to the same linear blend the old paste-based shortcut happened to compute correctly in that one case.
- [x] 4.3 Add a `test_renderer.py` case with `text_background_enabled=True` and `transparent=True`: assert pixels fully outside the text box remain alpha 0, box-only pixels have the configured `text_background_opacity` alpha, and an anti-aliased glyph edge pixel's RGB is not contaminated by the box's `background_color` beyond what the theme's own text-over-box design intends (i.e. no fringe artifact reproducing the pre-fix bug at `(128, 0, 0, 64)`-style wrong values)
- [x] 4.4 Add a regression test rendering `clean.yaml` and `clean2.yaml` (both have `text_background_enabled: true`) with `transparent=False` before/after this change and assert the flattened RGB output is visually/pixel unchanged

## 5. Output generation

- [x] 5.1 Confirm `generate_png_pages` requires no code change: `page.save(path, format='PNG', ...)` already preserves an `RGBA` image's alpha channel; add a `test_output.py` case asserting a saved transparent-mode PNG round-trips with alpha intact (`Image.open(path).mode == 'RGBA'` and a known-transparent pixel reads back alpha 0)
- [x] 5.2 Confirm `generate_jpg_pages` and `generate_pdf` are unreachable with an `RGBA` page in practice (config validation in 1.2 prevents `transparent=True` with `jpg`/`pdf`), so no defensive conversion is required there

## 6. CLI wiring

- [x] 6.1 Pass `pb_config.output.transparent` through to `render_all_pages(...)` in `cli.py`
- [x] 6.2 Add a `test_cli.py` case running the CLI end-to-end with `output.transparent: true` and `format: png` against a small fixture config, asserting the generated PNG(s) are `RGBA` with transparent margins

## 7. End-to-end validation across shipped themes

- [x] 7.1 Render a small fixture book with each of `classic.yaml`, `clean.yaml`, `clean2.yaml`, `modern.yaml` at `transparent: true`, `format: png`, and visually inspect the output (e.g. save to `tests/output/` or view manually) for fringing/artifacts around shadows and text-background boxes
- [x] 7.2 Render the same fixture book with the same four themes at `transparent` unset (default) and confirm output is visually identical to pre-change output
