## ADDED Requirements

### Requirement: Define text positioning in layout templates
The system SHALL support optional text positioning specifications for each photo slot in layout templates.

#### Scenario: Layout template with text positions
- **WHEN** theme layout template includes text positioning for photo slots
- **THEN** system parses text position properties successfully

#### Scenario: Text position with coordinates
- **WHEN** text position specifies x, y, width, height as percentages
- **THEN** system stores position as bounding box for text rendering

#### Scenario: Text position with alignment
- **WHEN** text position specifies horizontal alignment (left, center, right)
- **THEN** system uses alignment for text rendering within bounding box

#### Scenario: Text position with vertical alignment
- **WHEN** text position specifies vertical alignment (top, middle, bottom)
- **THEN** system uses vertical alignment for text positioning

#### Scenario: Photo slot without text position
- **WHEN** photo slot in template does not include text position
- **THEN** system renders photo without text (no error)

#### Scenario: Template without any text positions
- **WHEN** layout template has no text position specifications
- **THEN** system renders all photos without text (backward compatible)

#### Scenario: Invalid text position coordinates
- **WHEN** text position coordinates are not numbers or are outside 0-100 range
- **THEN** system reports validation error indicating invalid coordinates

#### Scenario: Invalid text alignment value
- **WHEN** text alignment is not one of allowed values (left/center/right, top/middle/bottom)
- **THEN** system reports validation error indicating invalid alignment

### Requirement: Support text styling properties in themes
The system SHALL support optional text styling properties at the theme level for text rendering.

#### Scenario: Theme with base font size
- **WHEN** theme specifies base_font_size property
- **THEN** system uses specified size for rendering text

#### Scenario: Theme with font family
- **WHEN** theme specifies font_family property
- **THEN** system uses specified font for rendering text

#### Scenario: Theme with text color
- **WHEN** theme specifies text_color property
- **THEN** system uses specified color for rendering text

#### Scenario: Theme without text styling
- **WHEN** theme does not specify text styling properties
- **THEN** system uses default text styling (black, 12pt, sans-serif)

#### Scenario: Invalid font size
- **WHEN** theme specifies non-numeric or negative font size
- **THEN** system reports validation error indicating invalid font size

#### Scenario: Invalid color format
- **WHEN** theme specifies text_color that is not a valid color (hex, rgb, or name)
- **THEN** system reports validation error indicating invalid color
