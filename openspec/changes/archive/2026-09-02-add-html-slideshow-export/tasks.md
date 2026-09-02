## 1. Config schema

- [x] 1.1 Add `html` to `OutputConfig.format`'s allowed values and `config.py`'s format validator; verify `load_config` accepts `output.format: html` without error (unit test)
- [x] 1.2 Add `output.interval_seconds` to `OutputConfig` (default 5, must be a positive number); verify `load_config` rejects zero/negative/non-numeric values and accepts a valid override (unit test)
- [x] 1.3 Relax `output.transparent` validation to reject only `jpg`/`pdf` instead of "anything but `png`"; verify existing transparent+pdf/jpg rejection tests still pass and add a test that `transparent: true` with `format: html` no longer raises

## 2. HTML slideshow generation

- [x] 2.1 Add a new generation function that takes the ordered page-item sequence (from `merge_titles_with_photos`), the text-label associations (from `associate_text_labels_with_photos`), the active theme, and the output path, and writes one `.html` file; verify against a small fixture (2-3 photos, no captions) that a well-formed HTML file is produced
- [x] 2.2 Emit one slide per page item, photo or title, in sequence order; verify slide count and order match the input sequence for a fixture mixing photos and titles
- [x] 2.3 Translate caption/title Markdown (bold, italic, heading levels) into the equivalent HTML markup at generation time, reusing `text_labels.parse_markdown_text`'s parsed segments; verify against fixtures covering bold, italic, and each heading level
- [x] 2.4 Render a caption overlay (bottom-docked band, sized to its content) only for photos with an associated text label, styled from `theme.text.*`; verify a photo without a label produces no caption markup, and a photo with one does
- [x] 2.5 Render title slides centered in the viewport, styled from `theme.title.*`, with no photo; verify against a title-only fixture
- [x] 2.6 Resolve each photo's relative path from the output directory (POSIX-separated, percent-encoded), correct for photos in the first `photo_folders` entry and for photos in other entries; verify with a multi-folder fixture and with filenames containing spaces/non-ASCII characters
- [x] 2.7 Locate the active theme's font variant files using the same resolution logic `renderer._load_font_variants` uses, and embed them as base64 `@font-face` rules; verify generation still succeeds and falls back to a generic font (no failure) when a variant file can't be found
- [x] 2.8 Implement inline slideshow CSS/JS: autoplay at `output.interval_seconds`, loop back to the first slide after the last, pause/resume on click or spacebar, and step forward/backward on arrow keys; verify by exercising the generated file (e.g. via the `run` skill or a headless browser) that slides advance, loop, pause, and respond to manual navigation
- [x] 2.9 Implement just-in-time image loading with eviction: only the current slide's and the next slide's photo are ever loaded, and a slide's photo is released once the show advances past it; verify by inspecting the generated markup/script for this behavior and, where a headless browser is available, confirming no more than two photo requests are outstanding at once during a multi-slide run
- [x] 2.10 Add `alt` text (the photo's filename) to each photo slide's image

## 3. CLI wiring

- [x] 3.1 In `cli.py`, branch on `output.format == 'html'` before the layout/render stages, skipping `distribute_photos`/`render_all_pages`/theme-layout matching entirely and calling the new html generator directly with the merged page items and text-label associations; verify `photobook --config <fixture>.yaml` with `format: html` produces the expected file
- [x] 3.2 Force the html output directory to `resolve_photo_folders()[0]` regardless of `output.directory` or `--output`'s directory portion, printing an informational note when an override was given and discarded; verify with a fixture that sets `output.directory` that the file lands in the first photo folder and the note is printed
- [x] 3.3 Honor a filename override's basename (`-o custom.html` or `output.filename: custom.html`) while discarding any directory it implies for html; verify both override forms rename the file while it still lands in the first photo folder
- [x] 3.4 Raise a clear `OutputError` naming the path when the first photo folder isn't writable, with no fallback location attempted; verify with a read-only fixture directory

## 4. Docs and example config

- [x] 4.1 Add a documented `html` example (including `interval_seconds`) to `example-config.yaml` alongside the existing pdf example
- [x] 4.2 Update the `--output` CLI help text and README to note the html-format directory-override exception

## 5. Integration and regression coverage

- [x] 5.1 Add an end-to-end test generating html output from a fixture with photos, captions, and titles, and assert on slide count, caption/title presence, and relative path correctness (including a multi-folder fixture)
- [x] 5.2 Verify pdf/png/jpg generation, existing `output.directory` behavior, and existing `output.transparent`+`png` behavior are unchanged by running the existing output/config/CLI test suites
