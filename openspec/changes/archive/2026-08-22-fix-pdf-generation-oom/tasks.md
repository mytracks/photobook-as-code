## 1. Dependencies

- [x] 1.1 Add `pikepdf` to `pyproject.toml` dependencies and install it

## 2. Core implementation (`output.py`)

- [x] 2.1 Set `reportlab.rl_config.useA85 = False` once (module load or first `Canvas` creation), with a comment explaining why
- [x] 2.2 Thread `output.quality` through to `generate_pdf` (currently only passed to the JPG path) and use it as the JPEG quality for page embedding
- [x] 2.3 In `generate_pdf`, encode each page as JPEG (`page.save(buf, format='JPEG', quality=...)`) instead of PNG before handing it to `reportlab`
- [x] 2.4 Rewrite `generate_pdf`'s page loop to create a fresh `Canvas` per page, `drawImage` + `save()` it to a zero-padded single-page temp PDF inside a `tempfile.mkdtemp()`-managed directory, then drop the `Canvas`/`PDFDocument` reference and explicitly `gc.collect()` before the next page (reference-dropping alone isn't enough - `Canvas`/`PDFDocument` hold back-references to each other, so each page's object graph is a reference cycle that CPython's automatic cyclic GC doesn't sweep frequently enough on its own; confirmed by measurement, see design.md)
- [x] 2.5 After all pages are written, merge the interim single-page PDFs into the final output path with `pikepdf`, preserving page order
- [x] 2.6 Write the merge result to a temp path and move it into place only after the merge fully succeeds, so a partial/corrupt file never appears at the final output path
- [x] 2.7 Clean up the temp directory in a `finally` block on both success and failure paths

## 3. Tests

- [x] 3.1 Update `tests/test_integration_text_labels.py::TestOutputFormats::test_pdf_output_with_text` (and any other existing PDF-output tests) for the new implementation
- [x] 3.2 Add a test that reads back a generated PDF (e.g. via `pikepdf`) and asserts the correct page count and page order
- [x] 3.3 Add a test asserting the temp directory is removed after a successful run
- [x] 3.4 Add a test asserting temp files are cleaned up and no partial file is left at the output path when rendering raises partway through
- [x] 3.5 Run the full existing test suite and confirm no regressions in the untouched PNG/JPG output paths

## 4. Verification

- [x] 4.1 Run `photobook --config sevilla.yaml` (the original 198-page repro) end-to-end and confirm it completes successfully with a valid, non-empty PDF instead of being killed - completed in 61s, 198/198 pages, 419MB output, valid PDF (verified page count and A4 page size via pikepdf)
- [x] 4.2 Spot-check several pages of the resulting PDF for visual quality at JPEG quality 95 (photo fidelity, text/border crispness) - pages 1, 100, 198 extracted and visually reviewed at full 2480x3508 resolution: crisp text/title rendering, clean photo detail, no visible JPEG artifacts even in a dark gradient sky
- [x] 4.3 Confirm peak memory during the `sevilla.yaml` run no longer scales with page count - measured via /proc/<pid>/status VmRSS polling: peak ~325MB for the full 198-page run (was crashing via OOM kill before this change). Note: per-page finalization alone was NOT sufficient - reference cycles between reportlab's Canvas/PDFDocument required an explicit gc.collect() per page (see design.md); without it, peak RSS was measured climbing unbounded (5+ GB) and the process was still killed around page 160
