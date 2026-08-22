## 1. YAML Configuration Parsing

- [x] 1.1 Add `text_labels` field to configuration schema in config.py
- [x] 1.2 Implement text label parsing with timestamp and text fields
- [x] 1.3 Add validation for timestamp formats (ISO 8601 and Unix epoch)
- [x] 1.4 Add validation for required fields (timestamp, text)
- [x] 1.5 Add validation for data types (timestamp as string/number, text as string)
- [x] 1.6 Add unit tests for text label parsing with valid entries
- [x] 1.7 Add unit tests for validation errors (missing fields, invalid formats)

## 2. Text Label Data Model

- [x] 2.1 Create TextLabel class to store timestamp and text content
- [x] 2.2 Create TextSegment class to store formatted text with style attributes
- [x] 2.3 Implement markdown parser for italic (*text*)
- [x] 2.4 Implement markdown parser for bold (**text**)
- [x] 2.5 Implement markdown parser for heading levels (#, ##, ###)
- [x] 2.6 Handle nested formatting (bold within italic, etc.)
- [x] 2.7 Implement graceful degradation for malformed markdown
- [x] 2.8 Add unit tests for markdown parsing with various combinations
- [x] 2.9 Add unit tests for edge cases (unclosed markers, nested formatting)

## 3. Photo-Text Association Logic

- [x] 3.1 Extract EXIF timestamps from photos in photos.py
- [x] 3.2 Implement timestamp matching algorithm (find closest photo)
- [x] 3.3 Implement deterministic tiebreaker for equidistant timestamps
- [x] 3.4 Create function to associate text labels with photos by timestamp
- [x] 3.5 Handle case where text label has no matching photo
- [x] 3.6 Handle case where photo has no text label
- [x] 3.7 Add unit tests for timestamp matching with single label/photo
- [x] 3.8 Add unit tests for equidistant timestamp tiebreaker
- [x] 3.9 Add unit tests for multiple labels on same page

## 4. Theme System Text Positioning

- [x] 4.1 Add optional `text` field to photo slots in layout template schema
- [x] 4.2 Parse text position coordinates (x, y, width, height as percentages)
- [x] 4.3 Parse text alignment properties (horizontal: left/center/right)
- [x] 4.4 Parse vertical alignment properties (top/middle/bottom)
- [x] 4.5 Add validation for coordinate ranges (0-100)
- [x] 4.6 Add validation for alignment values
- [x] 4.7 Add theme-level text styling properties (base_font_size, font_family, text_color)
- [x] 4.8 Implement defaults for missing text styling properties
- [x] 4.9 Update existing theme files (classic, clean, modern) with example text positions
- [x] 4.10 Add unit tests for text position parsing
- [x] 4.11 Add unit tests for text styling validation

## 5. Layout Engine Integration

- [x] 5.1 Pass text label associations to layout engine alongside photo data
- [x] 5.2 Extract text position from template for each photo placement
- [x] 5.3 Create data structure with photo placement + text label + text position
- [x] 5.4 Handle layouts without text positions (skip text rendering)
- [x] 5.5 Add unit tests for layout with text positions
- [x] 5.6 Add unit tests for layout without text positions

## 6. Text Rendering in Output Generation

- [x] 6.1 Add text rendering function to renderer.py
- [x] 6.2 Implement font loading with font_family from theme
- [x] 6.3 Implement fallback to default font if specified font unavailable
- [x] 6.4 Render plain text with base font size and color
- [x] 6.5 Render italic text segments with italic font style
- [x] 6.6 Render bold text segments with bold font weight
- [x] 6.7 Render heading text with size multipliers (1.5x, 1.3x, 1.2x)
- [x] 6.8 Implement horizontal text alignment (left/center/right)
- [x] 6.9 Implement vertical text alignment (top/middle/bottom)
- [x] 6.10 Implement text clipping at bounding box boundaries
- [x] 6.11 Implement multi-line text rendering with line spacing
- [x] 6.12 Add unit tests for text rendering with various formats
- [x] 6.13 Add unit tests for text alignment variations

## 7. Integration and End-to-End Testing

- [x] 7.1 Create test fixture YAML with text labels
- [x] 7.2 Create test theme with text positions
- [x] 7.3 Add integration test for full pipeline (config → layout → render)
- [x] 7.4 Test with single photo and single text label
- [x] 7.5 Test with multiple photos and multiple text labels
- [x] 7.6 Test with photos without text labels
- [x] 7.7 Test with text labels without matching photos
- [x] 7.8 Test with all markdown formatting combinations
- [x] 7.9 Test backward compatibility (photobook without text labels)
- [x] 7.10 Verify PDF output with text rendering
- [x] 7.11 Verify PNG output with text rendering

## 8. Documentation

- [x] 8.1 Add text labels section to README with example YAML
- [x] 8.2 Document text label YAML format (timestamp, text fields)
- [x] 8.3 Document supported markdown formatting
- [x] 8.4 Document theme text positioning properties
- [x] 8.5 Document text styling theme properties
- [x] 8.6 Add example photobook configuration with text labels
- [x] 8.7 Update theme documentation with text position examples

## 9. Text Background Overlay for Readability

- [x] 9.1 Add text background properties to TextStyle (enabled, color, opacity, padding)
- [x] 9.2 Implement semi-transparent background rendering before text
- [x] 9.3 Calculate actual text bounds for proper background sizing
- [x] 9.4 Add padding around text within background overlay
- [x] 9.5 Support configurable background color (hex format)
- [x] 9.6 Support configurable background opacity (0-100 range)
- [x] 9.7 Enable text background by default for readability
- [x] 9.8 Update unit tests for text styling with background properties
- [x] 9.9 Add spec requirements for text background overlay
- [x] 9.10 Document text background properties in README
- [x] 9.11 Create demo showing text rendered on top of photos

## 10. Text Rendering Order Fix

- [x] 10.1 Restructure render_page to use two-phase rendering
- [x] 10.2 Phase 1: Render all photos first
- [x] 10.3 Phase 2: Render all borders and text labels on top
- [x] 10.4 Store photo placements for efficient border/text rendering
- [x] 10.5 Ensure text labels are never obscured by subsequent photos
- [x] 10.6 Update spec with rendering order requirements
- [x] 10.7 Verify all tests pass with new rendering order
- [x] 10.8 Regenerate demos to verify fix
