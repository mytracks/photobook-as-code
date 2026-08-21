## ADDED Requirements

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
