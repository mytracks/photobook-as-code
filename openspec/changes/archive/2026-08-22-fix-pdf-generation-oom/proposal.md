## Why

Generating PDF output for large photobooks (e.g. `sevilla.yaml`, 198 pages) crashes with a bare `Killed` in the shell and a 0-byte output file - an OOM kill (`SIGKILL`), invisible to Python's own error handling. The renderer's page generator is correctly memory-bounded, but `output.generate_pdf` hands each page to a single long-lived `reportlab` `Canvas`, which retains every embedded page image in memory (`self._doc.idToObject`) until the one final `c.save()` call. Peak memory therefore grows linearly and unboundedly with page count. This directly violates the existing `output-generation` capability's own "Generate output with minimal memory footprint" requirement, which the PNG/JPG output paths already satisfy but the PDF path never has.

## What Changes

- Finalize each rendered page to its own single-page temporary PDF immediately after rendering (a fresh `reportlab` `Canvas` per page, dropped and garbage-collected right after `save()`), instead of accumulating every page's image inside one long-lived `Canvas`/`PDFDocument`. Peak memory for the PDF path becomes bounded by a single page's cost, matching what the spec already requires.
- Merge the interim single-page PDFs into the final output file using `pikepdf` (new dependency), preserving page order, then clean up the temp directory.
- Encode each page as JPEG (reusing the existing `output.quality` config field, default 95) instead of PNG before embedding, so `reportlab` can use its `DCTDecode` passthrough path rather than decoding back to raw pixels and re-compressing. **BREAKING** (in effect, not in config surface): PDF page images become JPEG-compressed instead of losslessly embedded; no YAML/CLI changes required since `output.quality` already exists and already defaults to 95.
- Disable `reportlab`'s default ASCII85 stream encoding (`rl_config.useA85 = False`) for an additional ~25% reduction in retained bytes, with no quality impact.
- PNG and JPG output formats are unaffected - they already write one file per page with nothing retained.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `output-generation`: PDF page images are now embedded via JPEG compression at the configured quality level, rather than losslessly. The existing memory-footprint requirement's wording and scenarios are unchanged - this change makes the PDF path actually satisfy them, it doesn't alter what they require.

## Impact

- Code: `src/photobook_as_code/output.py` (`generate_pdf` rewritten around per-page finalize + merge); no changes expected to `renderer.py`, `generate_png_pages`, or `generate_jpg_pages`.
- Dependencies: adds `pikepdf` to `pyproject.toml`.
- Output: PDF files now contain JPEG-compressed (quality ~95) rather than losslessly-embedded page images; visually equivalent for photographic content, since source photos are already JPEG.
- No config or CLI surface changes - existing YAML files (including `sevilla.yaml`) work unmodified.
