## Why

Photobook creators need to add contextual text labels (captions, descriptions, dates, locations) alongside photos to tell richer stories. Currently, the system only supports photos without any text annotations. This change enables automatic placement of timestamped text labels that are matched to photos based on chronological proximity, with theme-controlled positioning and markdown-based formatting.

## What Changes

- Add text label entries to YAML configuration with timestamps and multi-line text content
- Automatic association of text labels to photos based on timestamp matching
- Theme-level text positioning and alignment specifications for each photo slot in templates
- Support for markdown formatting in text labels: italics (*), bold (**), and heading levels (#, ##, ###)
- Text rendering in output generation with proper typography and layout

## Capabilities

### New Capabilities

- `text-labels`: Text label management system that parses text entries from YAML, associates them with photos based on timestamps, and provides data structures for rendering text with markdown formatting

### Modified Capabilities

- `yaml-configuration`: Add parsing and validation of text label entries with timestamps and text content
- `theme-system`: Extend layout templates to include text positioning (coordinates, alignment) for each photo slot
- `output-generation`: Add text rendering with markdown parsing for styled text output on photobook pages

## Impact

- YAML configuration format extended with optional `text_labels` section
- Theme YAML format extended with text positioning properties in layout templates
- Photo metadata loading must extract EXIF timestamps for matching with text labels
- Renderer must handle text drawing with font styling based on markdown markers
- Layout engine needs to pass text label associations to renderer alongside photo placements
