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

### Requirement: Support text background overlay for readability
The system SHALL support optional text background overlay properties to ensure text remains readable when rendered over photos.

#### Scenario: Theme with text background
- **WHEN** theme specifies text_background_enabled as true
- **THEN** system renders semi-transparent background behind text

#### Scenario: Theme with text background color
- **WHEN** theme specifies text_background_color property
- **THEN** system uses specified color for text background overlay

#### Scenario: Theme with text background opacity
- **WHEN** theme specifies text_background_opacity (0-100)
- **THEN** system uses specified opacity for text background (0=transparent, 100=opaque)

#### Scenario: Theme with text padding
- **WHEN** theme specifies text_padding property
- **THEN** system adds specified padding around text within background overlay

#### Scenario: Theme without text background
- **WHEN** theme does not enable text_background or uses default
- **THEN** system renders text with semi-transparent background (default enabled for readability)

#### Scenario: Text background covers entire bounding box
- **WHEN** text is rendered with background enabled
- **THEN** background overlay is drawn first, then text is drawn on top

#### Scenario: Text labels rendered on top of all photos
- **WHEN** page contains multiple photos with text labels
- **THEN** system renders all photos first, then all text labels on top

#### Scenario: Text not obscured by other photos
- **WHEN** text label is positioned over first photo and second photo is rendered
- **THEN** text from first photo remains visible (not covered by second photo)

#### Scenario: Invalid text background opacity
- **WHEN** theme specifies text_background_opacity outside 0-100 range
- **THEN** system reports validation error indicating invalid opacity value
