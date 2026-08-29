## Context

See proposal.md - Why for motivation. Today `renderer.py` always renders each page as an opaque `RGB` image: `create_blank_page` fills the whole canvas with `theme.background.color`, photos are pasted on top, and two theme effects layer further content on top of that opaque backdrop:

- `draw_shadow` builds a soft-edged shadow on an isolated `RGBA` layer and merges it with `Image.alpha_composite` (the correct technique) - but then calls `.convert('RGB')` before returning, discarding the alpha it just computed correctly.
- `_draw_text_background` builds a solid-color, semi-transparent box and merges it with `page_img.paste(overlay, box, overlay)` - i.e. plain paste using the overlay's own alpha as a linear-interpolation mask. This only looks right because it currently always runs on top of a fully opaque destination.

Direct experimentation (Pillow 10.x, see conversation) confirmed the paste-based shortcut in `_draw_text_background` is mathematically wrong the moment the destination isn't fully opaque: pasting a 50%-opacity color onto a fully transparent pixel produces `(128, 0, 0, 64)` instead of the correct `(255, 0, 0, 128)` - both the resulting color and alpha are wrong, not just the alpha. The anti-aliased text glyphs drawn afterward on top of that box have the same defect: Pillow's `ImageDraw.text` blends ink color into the destination's RGB channels assuming the destination is opaque, regardless of its actual alpha, so partial-coverage edge pixels bake in the wrong color when the destination is only partially opaque. Plain photo pasting, solid borders, and text drawn directly onto a fully-transparent (alpha=0) region were all verified to already behave correctly - the bug is specific to layering a second translucent draw operation on top of a first non-opaque one via raw `ImageDraw`/`paste`, not to `Image.alpha_composite` itself.

3 of the 4 shipped themes exercise one of the affected effects (`classic.yaml`: `shadow: true`; `clean.yaml`/`clean2.yaml`: `text_background_enabled: true`), so this isn't an edge case to defer.

## Goals / Non-Goals

**Goals:**
- Genuinely transparent (alpha=0) backgrounds for opted-in PNG output - page margins, inter-photo gaps, and letterbox strips around a photo are never painted, rather than color-matched.
- Correct alpha compositing for shadow and text-background-box effects under transparent output, for all shipped themes.
- One rendering code path for opaque and transparent output - no parallel "transparent-mode" branch duplicating drawing logic.
- No visible change to today's default (opaque) output.

**Non-Goals:**
- Transparency for JPG or PDF output (JPG has no alpha channel; the PDF whole-book assembly workflow is explicitly not part of the paste-into-third-party-software use case this change targets).
- Print-service color-profile/ICC/CMYK handling - out of scope, unrelated to alpha.
- Backfilling full spec coverage of shadow/text-background-box behavior for the existing opaque path (only the transparent-relevant contract is specified; the opaque visual result is required to stay unchanged, not re-specified from scratch).

## Decisions

**Structural transparency, not chroma-keying.** Rejected an alternative where the page is still rendered opaque and then post-processed to punch out pixels matching `theme.background.color`: this would corrupt real photo content wherever a photo legitimately contains a color close to the background (e.g. a black-sky night photo against a black theme). Instead, non-content pixels are simply never painted.

**Single internal representation: always render `RGBA`, flatten only when needed.** `create_blank_page` gains a `transparent: bool` parameter: `True` starts the canvas at `(0,0,0,0)`; `False` keeps today's opaque fill but as `RGBA` (alpha=255) rather than `RGB`. All drawing helpers operate on `RGBA` unconditionally. `render_page` flattens to `RGB` with `.convert('RGB')` at the very end unless the caller requested transparent PNG output, in which case the `RGBA` image is returned as-is. This means the compositing fixes below apply identically to both code paths - there's no separate "transparent-safe" drawing logic to keep in sync with a legacy one. `render_all_pages`/`render_page` thread a `transparent: bool` down from `cli.py`'s `pb_config.output.transparent`.

**Fix `draw_shadow` by removing the final flatten.** It already does the correct thing internally (`Image.alpha_composite`); the only change is to stop discarding the result.

**Rewrite `_draw_text_background` and the text-glyph draw call that follows it to compose via isolated layers + `Image.alpha_composite`**, replacing the `paste(overlay, box, overlay)` shortcut. Concretely: build the background box and its text on a fully-transparent temporary `RGBA` layer sized to (at least) the text box, draw the opaque/anti-aliased glyphs onto that same isolated layer (so glyph-over-box compositing happens against a locally-opaque-where-painted, transparent-elsewhere layer, which Pillow's raw `ImageDraw` handles correctly per the experiments above), then merge that whole layer onto the page with one `Image.alpha_composite` call. This is the same pattern `draw_shadow` already uses, applied consistently. Alternatives considered and rejected (per user direction): disabling these effects under transparent output, or rejecting the config combination outright - both were rejected in favor of making the effects actually correct, since they're core to 3 of 4 shipped themes.

**Config surface: `output.transparent: bool`, default `false`, validated against `output.format` at config-load time** (alongside the existing `output.format` validation in `config.py`) - `true` is only accepted when `output.format == "png"`, otherwise it's a `ConfigurationError`. Chosen over a new `format: png-transparent` enum value (would complicate the existing format-validation error message and mix an orthogonal concern into the format enum) and over a CLI-only flag (inconsistent with `quality`/`size`/`format` all being config-driven, and this is a per-book, per-print-service setting that belongs with the rest of the output config).

## Risks / Trade-offs

- [Risk] Rewriting `_draw_text_background`'s internals changes the code path used even for today's default opaque case, not just the new transparent case → Mitigation: correct compositing over a fully-opaque destination is mathematically equivalent to the old paste-based result in the opaque case (the paste shortcut was only wrong when the destination had partial alpha); verify by rendering all four shipped themes before/after and confirming visually identical output, as part of tasks.md.
- [Risk] Some print services' photobook software may not alpha-blend correctly on import (e.g. binary transparency threshold instead of true alpha compositing), making soft shadow edges or anti-aliased text/photo edges look hard-edged or fringed despite correct source pixels → Mitigation: this is inherent to relying on a third party's PNG import behavior, not something this tool can control; documented as a known limitation. The user's own request already scopes this to "at least for those printing services that support that."
- [Risk] RGBA PNGs are somewhat larger than RGB PNGs at equivalent pixel dimensions → Mitigation: acceptable - opt-in only, and PNG output is already the largest/lossless option relative to JPEG.

## Migration Plan

Purely additive and opt-in (`output.transparent` defaults to `false`); no changes to default behavior, no data migration. Rollback is simply not setting the field (or setting it to `false`).
