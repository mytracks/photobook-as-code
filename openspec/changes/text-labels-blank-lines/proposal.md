## Why

Text labels and titles already parse and preserve blank source lines end-to-end (a blank line becomes a display line with zero words), but the renderer gives that display line zero measured height — it only contributes the fixed 4px `line_spacing` gap. Next to 42-108px text, that gap is visually indistinguishable from nothing, so authors who write an explicit blank line to separate a heading from body text (as in `example-config.yaml:45`) see it silently swallowed.

## What Changes

- Blank display lines are measured with the height of a normal (heading level 0) line at the current text's `base_font_size`, instead of `0`. Consecutive blank lines stack additively (each contributes one line-height of gap).
- Leading and trailing blank lines are trimmed from parsed `text`/`title` content before line-splitting. This absorbs the YAML `|` block-scalar clip-chomping artifact (a trailing `\n` that authors didn't intentionally type) and an accidental blank line typed right after `title: |`, so only interior blank lines an author actually placed between content lines produce a gap.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `text-labels`: "Parse markdown formatting in text content" gains a scenario for blank-line handling (trimmed at the edges, preserved and given real height in the interior); "Provide text label data for rendering" is unaffected in shape but the rendered output for existing content changes.

## Impact

- `src/photobook_as_code/text_labels.py`: `parse_markdown_text` trims leading/trailing blank lines before splitting.
- `src/photobook_as_code/renderer.py`: `_wrap_markdown_lines` computes real height for a display line with no words, using the regular font at `base_font_size`.
- `example-config.yaml` and any other config with multi-line `text`/`title` entries using a leading/trailing blank line: rendered output changes (this is the intended fix, not a regression).
- No config schema changes; no breaking API changes to `TextLabel`/`TitleLabel`.
