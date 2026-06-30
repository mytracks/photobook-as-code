## 1. Theme YAML Schema Extension

- [x] 1.1 Add required `layouts` section to theme loading in `themes.py`
- [x] 1.2 Parse layout template objects with count, and photos arrays
- [x] 1.3 Validate layout template structure (required fields: count, photos)
- [x] 1.4 Parse photo specifications with orientation, position (x, y), and size
- [x] 1.5 Add validation for position coordinates (0.0-1.0 range)
- [x] 1.6 Add validation for size percentages (0.0-1.0 range)
- [x] 1.7 Store parsed layout templates in theme object
- [x] 1.8 Add error message when layouts section is missing from theme

## 2. Photo Orientation Detection

- [x] 2.1 Add orientation detection function in `photos.py`
- [x] 2.2 Classify photos as landscape (width > height)
- [x] 2.3 Classify photos as portrait (height > width)
- [x] 2.4 Classify square photos (width == height) as landscape
- [x] 2.5 Store orientation metadata with photo objects

## 3. Template Matching Logic

- [x] 3.1 Create template matcher module in `layout.py`
- [x] 3.2 Implement match by photo count function
- [x] 3.3 Implement match by orientation sequence function
- [x] 3.4 Implement order-preference scoring (exact sequence match scores higher)
- [x] 3.5 Select best template from multiple matches
- [x] 3.6 Raise informative error when no template matches (include expected orientations)

## 4. Template-Based Rendering

- [x] 4.1 Update renderer to accept layout template parameter
- [x] 4.2 Implement center-point positioning from template coordinates
- [x] 4.3 Convert relative coordinates (0.0-1.0) to absolute pixel positions
- [x] 4.4 Implement orientation-specific sizing (width for landscape, height for portrait)
- [x] 4.5 Scale photos to template size while maintaining aspect ratio
- [x] 4.6 Apply template positioning for each photo in sequence

## 5. Integration and Flow

- [x] 5.1 Update page rendering flow to detect photo orientations
- [x] 5.2 Match page photos to template from theme layouts
- [x] 5.3 Pass matched template to renderer for template-based positioning
- [x] 5.4 Remove grid layout calculation code from layout.py
- [x] 5.5 Remove grid-based rendering code from renderer.py

## 6. Error Handling and Validation

- [x] 6.1 Add error message for missing template with specific orientation sequence
- [x] 6.2 Add error message for invalid position coordinates (out of 0.0-1.0 range)
- [x] 6.3 Add error message for invalid size percentages
- [x] 6.4 Add error message for malformed layouts section in theme YAML
- [x] 6.5 Add error message when theme is missing layouts section

## 7. Update Default Themes

- [x] 7.1 Update clean.yaml with layout templates for 1-6 photos
- [x] 7.2 Update modern.yaml with layout templates for 1-6 photos
- [x] 7.3 Update classic.yaml with layout templates for 1-6 photos
- [x] 7.4 Cover common orientation combinations (LL, PP, LP, PL, LLP, LPP, etc.)
- [x] 7.5 Document template structure with comments in themes
- [x] 7.6 Test each updated theme with various photo combinations (using `photobook` CLI)

## 8. Testing

- [x] 8.1 Test orientation detection for landscape, portrait, and square photos
- [x] 8.2 Test template matching with exact orientation sequence
- [x] 8.3 Test order-preference when multiple templates match
- [x] 8.4 Test error raised when no template matches
- [x] 8.5 Test error raised when theme missing layouts section
- [x] 8.6 Test center-point positioning at various coordinates
- [x] 8.7 Test orientation-specific sizing (landscape relative to width, portrait to height)
- [x] 8.8 Test aspect ratio preservation with template sizing
- [x] 8.9 Test edge cases (single photo, all same orientation, complex sequences)
- [x] 8.10 Test all default themes with real photo sets

## 9. Documentation

- [x] 9.1 Document template YAML structure with examples
- [x] 9.2 Document coordinate system (0,0 = top-left, 0.5,0.5 = center)
- [x] 9.3 Document orientation-specific sizing behavior
- [x] 9.4 Document order-preference matching algorithm
- [x] 9.5 Document error messages and how to resolve them
- [x] 9.6 Document breaking change and migration guide for custom themes
