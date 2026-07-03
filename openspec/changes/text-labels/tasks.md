## 1. YAML Configuration Parsing

- [ ] 1.1 Add `text_labels` field to configuration schema in config.py
- [ ] 1.2 Implement text label parsing with timestamp and text fields
- [ ] 1.3 Add validation for timestamp formats (ISO 8601 and Unix epoch)
- [ ] 1.4 Add validation for required fields (timestamp, text)
- [ ] 1.5 Add validation for data types (timestamp as string/number, text as string)
- [ ] 1.6 Add unit tests for text label parsing with valid entries
- [ ] 1.7 Add unit tests for validation errors (missing fields, invalid formats)

## 2. Text Label Data Model

- [ ] 2.1 Create TextLabel class to store timestamp and text content
- [ ] 2.2 Create TextSegment class to store formatted text with style attributes
- [ ] 2.3 Implement markdown parser for italic (*text*)
- [ ] 2.4 Implement markdown parser for bold (**text**)
- [ ] 2.5 Implement markdown parser for heading levels (#, ##, ###)
- [ ] 2.6 Handle nested formatting (bold within italic, etc.)
- [ ] 2.7 Implement graceful degradation for malformed markdown
- [ ] 2.8 Add unit tests for markdown parsing with various combinations
- [ ] 2.9 Add unit tests for edge cases (unclosed markers, nested formatting)

## 3. Photo-Text Association Logic

- [ ] 3.1 Extract EXIF timestamps from photos in photos.py
- [ ] 3.2 Implement timestamp matching algorithm (find closest photo)
- [ ] 3.3 Implement deterministic tiebreaker for equidistant timestamps
- [ ] 3.4 Create function to associate text labels with photos by timestamp
- [ ] 3.5 Handle case where text label has no matching photo
- [ ] 3.6 Handle case where photo has no text label
- [ ] 3.7 Add unit tests for timestamp matching with single label/photo
- [ ] 3.8 Add unit tests for equidistant timestamp tiebreaker
- [ ] 3.9 Add unit tests for multiple labels on same page

## 4. Theme System Text Positioning

- [ ] 4.1 Add optional `text` field to photo slots in layout template schema
- [ ] 4.2 Parse text position coordinates (x, y, width, height as percentages)
- [ ] 4.3 Parse text alignment properties (horizontal: left/center/right)
- [ ] 4.4 Parse vertical alignment properties (top/middle/bottom)
- [ ] 4.5 Add validation for coordinate ranges (0-100)
- [ ] 4.6 Add validation for alignment values
- [ ] 4.7 Add theme-level text styling properties (base_font_size, font_family, text_color)
- [ ] 4.8 Implement defaults for missing text styling properties
- [ ] 4.9 Update existing theme files (classic, clean, modern) with example text positions
- [ ] 4.10 Add unit tests for text position parsing
- [ ] 4.11 Add unit tests for text styling validation

## 5. Layout Engine Integration

- [ ] 5.1 Pass text label associations to layout engine alongside photo data
- [ ] 5.2 Extract text position from template for each photo placement
- [ ] 5.3 Create data structure with photo placement + text label + text position
- [ ] 5.4 Handle layouts without text positions (skip text rendering)
- [ ] 5.5 Add unit tests for layout with text positions
- [ ] 5.6 Add unit tests for layout without text positions

## 6. Text Rendering in Output Generation

- [ ] 6.1 Add text rendering function to renderer.py
- [ ] 6.2 Implement font loading with font_family from theme
- [ ] 6.3 Implement fallback to default font if specified font unavailable
- [ ] 6.4 Render plain text with base font size and color
- [ ] 6.5 Render italic text segments with italic font style
- [ ] 6.6 Render bold text segments with bold font weight
- [ ] 6.7 Render heading text with size multipliers (1.5x, 1.3x, 1.2x)
- [ ] 6.8 Implement horizontal text alignment (left/center/right)
- [ ] 6.9 Implement vertical text alignment (top/middle/bottom)
- [ ] 6.10 Implement text clipping at bounding box boundaries
- [ ] 6.11 Implement multi-line text rendering with line spacing
- [ ] 6.12 Add unit tests for text rendering with various formats
- [ ] 6.13 Add unit tests for text alignment variations

## 7. Integration and End-to-End Testing

- [ ] 7.1 Create test fixture YAML with text labels
- [ ] 7.2 Create test theme with text positions
- [ ] 7.3 Add integration test for full pipeline (config → layout → render)
- [ ] 7.4 Test with single photo and single text label
- [ ] 7.5 Test with multiple photos and multiple text labels
- [ ] 7.6 Test with photos without text labels
- [ ] 7.7 Test with text labels without matching photos
- [ ] 7.8 Test with all markdown formatting combinations
- [ ] 7.9 Test backward compatibility (photobook without text labels)
- [ ] 7.10 Verify PDF output with text rendering
- [ ] 7.11 Verify PNG output with text rendering

## 8. Documentation

- [ ] 8.1 Add text labels section to README with example YAML
- [ ] 8.2 Document text label YAML format (timestamp, text fields)
- [ ] 8.3 Document supported markdown formatting
- [ ] 8.4 Document theme text positioning properties
- [ ] 8.5 Document text styling theme properties
- [ ] 8.6 Add example photobook configuration with text labels
- [ ] 8.7 Update theme documentation with text position examples
