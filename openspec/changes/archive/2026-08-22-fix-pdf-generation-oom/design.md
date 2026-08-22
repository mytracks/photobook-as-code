## Context

See `proposal.md` - Why for the motivation and the confirmed root cause. Two constraints shaped this design, both surfaced during investigation of `reportlab` 5.0.0's source (`pdfbase/pdfdoc.py`):

- `reportlab.pdfgen.canvas.Canvas` is a "build the whole document tree, serialize once" API: every `drawImage` call registers a `PDFImageXObject` in `self._doc.idToObject`, which is never released until `Canvas.save()`. There is no supported way to flush already-drawn pages from a single `Canvas` instance mid-document.
- `PDFImageXObject.loadImageFromSRC` (the path taken for a PNG-backed `ImageReader`, which is what the current code feeds it) fully decodes the image to raw RGB via `im.getRGBData()`, `zlib.compress`es it, and - because `reportlab.rl_config.useA85` defaults to `True` in this environment - ASCII85-encodes the result, inflating it ~33% and converting it to a Python string. `loadImageFromJPEG` is a materially cheaper path: it embeds the JPEG bytes via `DCTDecode` without decoding to raw pixels first.

The existing `output-generation` spec already requires PDF generation to keep peak memory bounded to roughly one page's worth (see `openspec/specs/output-generation/spec.md`, "Generate output with minimal memory footprint"). That requirement's wording is correct and unchanged by this design - the PDF path has simply never satisfied it.

## Goals / Non-Goals

**Goals:**
- Bound peak memory for PDF generation to (approximately) a single page's cost, independent of total page count, so page count 198 (or 2000) no longer risks an OOM kill.
- Reuse the existing `output.quality` config field for PDF page embedding rather than introducing new YAML/CLI surface.
- Leave `renderer.py` and the PNG/JPG output paths untouched - they already satisfy the memory-footprint requirement.

**Non-Goals:**
- Not introducing a user-configurable batch size or any other new tuning knob.
- Not pursuing lossless PDF page embedding - the JPEG trade-off is intentional (confirmed with the user) and only removable ambition here, not a compromise to walk back later.
- Not changing how photos are resized/composited into pages (`renderer.render_page`), only how the finished page image is turned into PDF output.
- Not addressing other `output-generation` requirements (CMYK, bleed, filename handling) - out of scope, unaffected by this bug.

## Decisions

### 1. Finalize each page to its own single-page temp PDF, then merge

For each page yielded by the `pages` iterator: create a fresh `Canvas` sized to the page dimensions, `drawImage` the page's JPEG bytes onto it, `save()` it to a zero-padded temp file (e.g. `page_00001.pdf`) inside a `tempfile.mkdtemp()`-managed directory, then let that `Canvas`/`PDFDocument` go out of scope before the next page starts. After all pages are written, merge the interim files in order into the final output path with `pikepdf`, then remove the temp directory.

This makes peak memory proportional to one page, not to total page count - the strongest bound available, and it matches the existing spec's literal wording without needing to touch it.

**Important refinement found during implementation:** dropping the reference alone was not sufficient. `Canvas` and its `PDFDocument` hold back-references to one another, so the object graph behind each finalized page is a *reference cycle*, not a plain chain CPython's refcounting can free the instant the variable is reassigned. Left to the generational collector's normal thresholds (which trigger on allocation *count*, not on bytes retained), these cycles - individually modest in object count but each anchoring several MB of image stream data - were confirmed experimentally to accumulate faster than automatic collection keeps up with: an end-to-end run against `sevilla.yaml` still grew unbounded and was killed around page 160 with per-page finalization alone, while adding an explicit `gc.collect()` immediately after each page's `Canvas.save()` kept peak RSS flat (~900MB-1GB) for the full 198 pages. `generate_pdf` now calls `gc.collect()` once per page for this reason - the small per-call cost (collection over a modest object graph) is what actually delivers the "roughly one page" bound this decision commits to, not the reference drop by itself.

**Alternatives considered:**
- *Batch ~20 pages per `Canvas`* - fewer temp files and merge operations, but the memory bound becomes `batch_size x per-page cost` instead of one page, and needs a tuning constant to justify and maintain. Rejected - per-page finalization removes the constant entirely and gives a strictly stronger guarantee, at a disk-I/O cost that's irrelevant for a non-interactive CLI job.
- *Monkeypatch/extend `reportlab.Canvas` to flush objects mid-document* - not supported by `reportlab`'s model (it needs the complete object graph to build the xref table at save time); would effectively reimplement what an explicit merge step already does, with more fragility.
- *Switch to a different PDF-writing library entirely (e.g. `img2pdf`)* - sidesteps the problem differently (never decodes JPEGs at all), but is a bigger structural change and would lose `reportlab`'s general drawing API. Not needed - per-page finalization already fixes the actual defect.

### 2. Embed pages as JPEG instead of PNG

Replace `page.save(buf, format='PNG')` with `page.save(buf, format='JPEG', quality=pb_config.output.quality)` before handing the buffer to `reportlab`. This routes through `loadImageFromJPEG`'s `DCTDecode` passthrough instead of `loadImageFromSRC`'s decode-to-raw-pixels-then-zlib path, eliminating both the wasted PNG encode/decode round trip and the much larger retained raw-pixel-derived stream.

`output.quality` already exists (`config.py:26`, default 95) and is already used for `--format jpg`; reusing it for PDF page embedding means no new config surface and gives PDF the same quality level JPG output already uses.

**Alternatives considered:** Keep PNG (lossless) and rely only on per-page finalization + `useA85=False`. Per-page finalization alone already fixes the crash, but JPEG is the single biggest cut to per-page retained memory (and to final file size) and was explicitly confirmed as an acceptable trade-off, since source photos are already JPEG-compressed - one further high-quality (95) JPEG generation on the composited page is not a meaningful quality loss for print.

### 3. Disable `reportlab`'s ASCII85 encoding

Set `reportlab.rl_config.useA85 = False` once (top of `output.py`, or immediately before the first `Canvas` is created). A85 is a transport encoding with no compression or quality benefit here - disabling it is a ~25% cut to whatever stream bytes are retained, on top of the JPEG change, for free.

This mutates third-party library global state for the process. Acceptable because the CLI is single-purpose and single-invocation (no concurrent unrelated `reportlab` usage to interfere with); flagged with a comment at the call site so it isn't mistaken for an accident.

### 4. Merge interim PDFs with `pikepdf`

Add `pikepdf` (QPDF-backed) as a new dependency for the merge step. QPDF copies page/image streams without decoding their content, so merge-time memory scales with compressed size, not decoded pixels - it's the standard tool for large, low-memory PDF assembly in Python.

**Alternative considered:** `pypdf` (pure Python, already a common choice, no C-extension). Rejected: it's built for correctness/manipulation rather than low-memory throughput on large files, and merging ~198 already-substantial interim PDFs the pypdf way risked reintroducing a smaller version of the exact accumulation problem this change fixes.

## Risks / Trade-offs

- **Lossy PDF page embedding** (previously lossless) → Mitigated by using quality 95 (already this project's existing default) and by source photos already being JPEG; confirmed acceptable with the user before adopting this design.
- **Global `reportlab.rl_config.useA85 = False` mutation** → Scoped in practice to this one-shot CLI process; commented at the call site.
- **More temp files / disk I/O during generation** (~one file per page vs. one continuous stream) → Irrelevant for a non-interactive, page-count-scale CLI job; temp directory is cleaned up in a `finally` block on both success and failure.
- **New dependency (`pikepdf`, a C-extension via libqpdf)** → Directly targets the failure mode (large-file, low-memory PDF assembly); mature and widely used.
- **Partial failure mid-render** (e.g. page 150 of 198 raises) → Interim temp files must not leak, and the final output path must never contain a partial/corrupt file. Temp directory cleanup runs in a `finally`; the final output file is only written (or replace an existing one) after the merge over *all* interim files completes successfully - write to a temp path first and move it into place, consistent with how `output.py` already handles output path preparation.

## Migration Plan

- No data migration - this is a generation-path bug fix with no persisted state.
- Add `pikepdf` to `pyproject.toml` dependencies.
- No YAML or CLI changes for existing users; `output.quality` already defaults to 95, so existing configs (including `sevilla.yaml`) get the fix automatically at an already-familiar quality level.
- Acceptance check: `sevilla.yaml` (198 pages, the original repro) should complete successfully and produce a valid, correctly-ordered PDF.
- Rollback: revert the change - no persisted state to unwind.
