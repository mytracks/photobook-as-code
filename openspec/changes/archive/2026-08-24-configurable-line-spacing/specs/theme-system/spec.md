## MODIFIED Requirements

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

#### Scenario: Theme with text line spacing
- **WHEN** theme specifies `text.line_spacing` (pixels)
- **THEN** system uses the specified gap between consecutive rendered lines of caption (`text`) content

#### Scenario: Theme without text line spacing
- **WHEN** theme does not specify `text.line_spacing`
- **THEN** system uses a default gap of 10 pixels between consecutive rendered lines of caption content

### Requirement: Support title styling properties in themes
The system SHALL support an optional theme-level `title` style block for title-slot rendering, independent from the `text` style block used for photo captions.

#### Scenario: Theme with title base font size
- **WHEN** theme specifies `title.base_font_size`
- **THEN** system uses the specified size for rendering title-slot text

#### Scenario: Theme with title font family
- **WHEN** theme specifies `title.font_family`
- **THEN** system uses the specified font for rendering title-slot text

#### Scenario: Theme with title text color
- **WHEN** theme specifies `title.text_color`
- **THEN** system uses the specified color for rendering title-slot text

#### Scenario: Theme with title alignment
- **WHEN** theme specifies `title.align` as one of `left`, `center`, or `right`
- **THEN** system aligns title-slot text accordingly within its slot

#### Scenario: Theme without title styling
- **WHEN** theme does not specify a `title` style block
- **THEN** system uses default title styling (centered alignment, larger base font size than the default caption style)

#### Scenario: Invalid title alignment
- **WHEN** theme specifies a `title.align` value other than `left`, `center`, or `right`
- **THEN** system reports validation error indicating invalid alignment

#### Scenario: Invalid title font size
- **WHEN** theme specifies a non-numeric or negative `title.base_font_size`
- **THEN** system reports validation error indicating invalid font size

#### Scenario: Title styling independent from text styling
- **WHEN** a theme defines both `text` and `title` style blocks with different font sizes or colors
- **THEN** system renders photo captions using the `text` block and title slots using the `title` block, without either affecting the other

#### Scenario: Theme with title line spacing
- **WHEN** theme specifies `title.line_spacing` (pixels)
- **THEN** system uses the specified gap between consecutive rendered lines of title-slot content, independently of `text.line_spacing`

#### Scenario: Theme without title line spacing
- **WHEN** theme does not specify `title.line_spacing`
- **THEN** system uses a default gap of 10 pixels between consecutive rendered lines of title-slot content
