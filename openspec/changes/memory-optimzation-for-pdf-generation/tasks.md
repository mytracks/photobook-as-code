## 1. Refactor Renderer to Generator Pattern

- [x] 1.1 Convert `render_all_pages()` to generator function that yields pages one at a time
- [x] 1.2 Update function signature and docstring to indicate it returns an Iterator[Image.Image]
- [x] 1.3 Test that generator correctly yields all pages with proper photo distribution
- [x] 1.4 Verify memory is released after each page is yielded

## 2. Update PDF Generation for Streaming

- [x] 2.1 Change `generate_pdf()` function signature to accept `Iterator[Image.Image]` instead of `List[Image.Image]`
- [x] 2.2 Add `total_pages` parameter for progress reporting
- [x] 2.3 Update loop to work with iterator (cannot use `len()` or index access)
- [x] 2.4 Update progress logging to use `total_pages` parameter
- [x] 2.5 Test PDF generation with streamed pages produces identical output to batch approach

## 3. Update PNG Generation for Consistency

- [x] 3.1 Change `generate_png_pages()` to accept `Iterator[Image.Image]` instead of `List[Image.Image]`
- [x] 3.2 Add `total_pages` parameter for progress reporting
- [x] 3.3 Update function to iterate over pages without requiring list
- [x] 3.4 Update progress logging to use `total_pages` parameter
- [x] 3.5 Test PNG generation with iterator produces correct sequential files

## 4. Update JPG Generation for Consistency

- [x] 4.1 Change `generate_jpg_pages()` to accept `Iterator[Image.Image]` instead of `List[Image.Image]`
- [x] 4.2 Add `total_pages` parameter for progress reporting
- [x] 4.3 Update function to iterate over pages without requiring list
- [x] 4.4 Update progress logging to use `total_pages` parameter
- [x] 4.5 Test JPG generation with iterator produces correct sequential files

## 5. Update CLI Pipeline Integration

- [x] 5.1 Update `cli.py` to pass iterator from `render_all_pages()` to output functions
- [x] 5.2 Pass `distribution.total_pages` to output functions for progress reporting
- [x] 5.3 Update progress bar logic to work with expected page count
- [x] 5.4 Verify error handling still works correctly with generator pattern
- [x] 5.5 Test complete pipeline from config to output with streaming generation

## 6. Add Memory Usage Logging (Verbose Mode)

- [x] 6.1 Add memory tracking imports (psutil or tracemalloc)
- [x] 6.2 Log peak memory usage in verbose mode before and after page rendering
- [x] 6.3 Add memory statistics to completion message in verbose mode
- [x] 6.4 Test that verbose output shows memory reduction compared to previous implementation

## 7. Update Type Hints and Documentation

- [x] 7.1 Update type hints in renderer.py for Iterator[Image.Image]
- [x] 7.2 Update type hints in output.py for Iterator[Image.Image]
- [x] 7.3 Update docstrings to document generator behavior and memory benefits
- [x] 7.4 Add note about generators being single-use to relevant docstrings

## 8. Testing and Validation

- [x] 8.1 Test small photobook (5 pages) - verify identical output
- [x] 8.2 Test medium photobook (20 pages) - verify memory reduction
- [x] 8.3 Test large photobook (50 pages) - verify memory reduction and performance
- [x] 8.4 Test all output formats (PDF, PNG, JPG) with streaming generation
- [x] 8.5 Verify progress reporting works correctly across all formats
- [x] 8.6 Test error handling (invalid photo, disk full, etc.) with generator
- [x] 8.7 Run existing test suite to ensure no regressions
