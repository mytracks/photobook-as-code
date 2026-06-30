## 1. Theme YAML Schema Extension

- [ ] 1.1 Add required `layouts` section to theme loading in `themes.py`
- [ ] 1.2 Parse layout template objects with count, and photos arrays
- [ ] 1.3 Validate layout template structure (required fields: count, photos)
- [ ] 1.4 Parse photo specifications with orientation, position (x, y), and size
- [ ] 1.5 Add validation for position coordinates (0.0-1.0 range)
- [ ] 1.6 Add validation for size percentages (0.0-1.0 range)
- [ ] 1.7 Store parsed layout templates in theme object
- [ ] 1.8 Add error message when layouts section is missing from theme

## 2. Photo Orientation Detection

- [ ] 2.1 Add orientation detection function in `photos.py`
- [ ] 2.2 Classify photos as landscape (width > height)
- [ ] 2.3 Classify photos as portrait (height > width)
- [ ] 2.4 Classify square photos (width == height) as landscape
- [ ] 2.5 Store orientation metadata with photo objects

## 3. Template Matching Logic

- [ ] 3.1 Create template matcher module in `layout.py`
- [ ] 3.2 Implement match by photo count function
- [ ] 3.3 Implement match by orientation sequence function
- [ ] 3.4 Implement order-preference scoring (exact sequence match scores higher)
- [ ] 3.5 Select best template from multiple matches
- [ ] 3.6 Raise informative error when no template matches (include expected orientations)

## 4. Template-Based Rendering

- [ ] 4.1 Update renderer to accept layout template parameter
- [ ] 4.2 Implement center-point positioning from template coordinates
- [ ] 4.3 Convert relative coordinates (0.0-1.0) to absolute pixel positions
- [ ] 4.4 Implement orientation-specific sizing (width for landscape, height for portrait)
- [ ] 4.5 Scale photos to template size while maintaining aspect ratio
- [ ] 4.6 Apply template positioning for each photo in sequence

## 5. Integration and Flow

- [ ] 5.1 Update page rendering flow to detect photo orientations
- [ ] 5.2 Match page photos to template from theme layouts
- [ ] 5.3 Pass matched template to renderer for template-based positioning
- [ ] 5.4 Remove grid layout calculation code from layout.py
- [ ] 5.5 Remove grid-based rendering code from renderer.py

## 6. Error Handling and Validation

- [ ] 6.1 Add error message for missing template with specific orientation sequence
- [ ] 6.2 Add error message for invalid position coordinates (out of 0.0-1.0 range)
- [ ] 6.3 Add error message for invalid size percentages
- [ ] 6.4 Add error message for malformed layouts section in theme YAML
- [ ] 6.5 Add error message when theme is missing layouts section

## 7. Update Default Themes

- [ ] 7.1 Update clean.yaml with layout templates for 1-6 photos
- [ ] 7.2 Update modern.yaml with layout templates for 1-6 photos
- [ ] 7.3 Update classic.yaml with layout templates for 1-6 photos
- [ ] 7.4 Cover common orientation combinations (LL, PP, LP, PL, LLP, LPP, etc.)
- [ ] 7.5 Document template structure with comments in themes
- [ ] 7.6 Test each updated theme with various photo combinations

## 8. Testing

- [ ] 8.1 Test orientation detection for landscape, portrait, and square photos
- [ ] 8.2 Test template matching with exact orientation sequence
- [ ] 8.3 Test order-preference when multiple templates match
- [ ] 8.4 Test error raised when no template matches
- [ ] 8.5 Test error raised when theme missing layouts section
- [ ] 8.6 Test center-point positioning at various coordinates
- [ ] 8.7 Test orientation-specific sizing (landscape relative to width, portrait to height)
- [ ] 8.8 Test aspect ratio preservation with template sizing
- [ ] 8.9 Test edge cases (single photo, all same orientation, complex sequences)
- [ ] 8.10 Test all default themes with real photo sets

## 9. Documentation

- [ ] 9.1 Document template YAML structure with examples
- [ ] 9.2 Document coordinate system (0,0 = top-left, 0.5,0.5 = center)
- [ ] 9.3 Document orientation-specific sizing behavior
- [ ] 9.4 Document order-preference matching algorithm
- [ ] 9.5 Document error messages and how to resolve them
- [ ] 9.6 Document breaking change and migration guide for custom themes
