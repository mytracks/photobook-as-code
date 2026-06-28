## Context

The current implementation of photobook generation loads all page images into memory before outputting them. The `render_all_pages()` function returns `List[Image.Image]`, which is then passed to `generate_pdf()`, `generate_png_pages()`, or `generate_jpg_pages()`. For a 50-page photobook at A4 size (2480×3508 pixels) with 300 DPI, each page consumes approximately 26 MB of memory (RGB, 8-bit per channel), resulting in 1.3 GB total memory usage before output generation even begins.

This approach works for small photobooks (5-10 pages) but becomes problematic for:
- Large photobooks (50+ pages): Memory usage exceeds 1-2 GB
- High-resolution output: Custom dimensions larger than A4
- Resource-constrained environments: Low-memory systems, cloud containers with limited RAM

The existing pipeline in `cli.py` orchestrates the process but doesn't need to hold all pages in memory simultaneously.

## Goals / Non-Goals

**Goals:**
- Reduce peak memory usage by 80-90% for multi-page photobooks
- Enable generation of very large photobooks (100+ pages) without memory constraints
- Maintain identical output quality and file format compatibility
- Preserve existing CLI interface and configuration format
- Support streaming for PDF generation (most memory-intensive format)

**Non-Goals:**
- Optimizing PNG/JPG generation (these already process pages sequentially, but we'll update them for consistency)
- Changing the configuration YAML format or CLI arguments
- Modifying the quality or appearance of generated output
- Parallel page rendering (introduces complexity, out of scope for this change)
- Memory profiling UI or dashboard (verbose logging sufficient for v1)

## Decisions

### Decision 1: Use Generator Pattern for Page Rendering

**Chosen Approach:** Convert `render_all_pages()` from returning `List[Image.Image]` to a generator function that yields `Image.Image` one at a time.

**Rationale:**
- Python generators are memory-efficient and idiomatic for streaming data
- Minimal changes to calling code (iterating over generator vs list)
- Natural fit for the sequential page processing already happening in output functions

**Alternatives Considered:**
- **Callback pattern**: More complex, requires restructuring output functions to accept callbacks
- **Iterator class**: Overkill for this use case, generator is simpler
- **File-based intermediate storage**: Adds I/O overhead, temporary file cleanup complexity

### Decision 2: Refactor generate_pdf() to Accept Iterator

**Chosen Approach:** Change function signature from `pages: List[Image.Image]` to `pages: Iterator[Image.Image]`, process pages in loop without counting total upfront.

**Rationale:**
- ReportLab's canvas API supports incremental page addition via `showPage()`
- We don't need to know total page count before starting PDF generation
- Progress reporting can still work (from layout calculation, we know expected page count)

**Alternatives Considered:**
- **Two-pass approach**: First pass to count pages, second pass to render. Defeats purpose of streaming.
- **Buffering chunks**: Doesn't solve the fundamental problem, just reduces it slightly

### Decision 3: Update Progress Reporting to Use Expected Page Count

**Chosen Approach:** Calculate expected page count from layout distribution, pass to output functions for progress reporting.

**Rationale:**
- Layout calculation already determines how many pages will be generated
- Progress bar needs total count for percentage display
- No need to consume generator just to count items

**Implementation:**
- Add `total_pages` parameter to output functions
- Update `cli.py` to pass `distribution.total_pages` from layout calculation

### Decision 4: Keep PNG/JPG Generation Sequential (No Change)

**Chosen Approach:** Update PNG/JPG functions to accept iterators for API consistency, but behavior unchanged (already sequential).

**Rationale:**
- These functions already process pages one at a time in their loops
- Memory benefit comes primarily from PDF generation (most common use case)
- Consistent API across all output functions improves maintainability

## Risks / Trade-offs

**Risk:** Generator can only be consumed once, potential for bugs if code tries to iterate twice
→ **Mitigation:** Document generator behavior clearly, add assertions if needed. The current pipeline doesn't re-iterate over pages.

**Risk:** Progress reporting might be slightly less accurate if page rendering fails mid-stream
→ **Mitigation:** Error handling in generator will still log failures. Progress bar will show "X/Y pages" where Y is the expected count.

**Trade-off:** Slightly more complex code (generator vs simple list) for significant memory savings
→ **Acceptable:** The complexity is minimal (changing `return` to `yield`), and Python generators are well-understood.

**Trade-off:** Cannot easily inspect all pages after rendering for debugging
→ **Acceptable:** Logging at INFO level already shows per-page rendering progress. Verbose mode can add more details if needed.
