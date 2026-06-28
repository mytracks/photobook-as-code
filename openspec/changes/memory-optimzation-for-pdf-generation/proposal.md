## Why

Current PDF generation loads all rendered page images into memory simultaneously, causing high memory consumption for large photobooks with many pages or high-resolution photos. For photobooks with 50+ pages at 300 DPI, memory usage can exceed 1-2 GB, limiting the tool's usability on resource-constrained systems.

## What Changes

- Implement streaming approach to PDF generation that processes pages one at a time
- Refactor `generate_pdf()` to accept a page generator/iterator instead of pre-rendered list
- Modify renderer to yield pages incrementally rather than returning complete list
- Add memory usage tracking and reporting in verbose mode
- Update progress reporting to work with streaming generation

## Capabilities

### New Capabilities
<!-- No new capabilities are being introduced -->

### Modified Capabilities
- `output-generation`: Change PDF generation from batch (all pages in memory) to streaming (one page at a time) approach to reduce memory footprint
- `photo-layout-engine`: Modify page rendering to support generator pattern for incremental page production

## Impact

**Code Changes:**
- `src/photobook_as_code/output.py`: Refactor `generate_pdf()` function signature and implementation
- `src/photobook_as_code/renderer.py`: Convert `render_all_pages()` to generator function
- `src/photobook_as_code/cli.py`: Update pipeline to handle streaming page generation

**Benefits:**
- Reduced peak memory usage by ~80-90% for large photobooks
- Enables generation of very large photobooks (100+ pages) on modest hardware
- Maintains identical output quality and functionality

**No Breaking Changes:**
- CLI interface remains unchanged
- Configuration format unchanged
- Output files identical to previous implementation
