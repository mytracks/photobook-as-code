## Purpose

Theme system for visual styling of photobook pages. This capability manages theme definitions, background styling, borders, spacing, and provides built-in and custom theme support.

## Requirements

### Requirement: Define theme structure
The system SHALL support theme definitions that specify visual styling properties for photobook pages. Themes SHALL also define layout templates.

#### Scenario: Theme file format
- **WHEN** system loads a theme
- **THEN** theme file contains properties for backgrounds, borders, spacing, colors, and layouts.

#### Scenario: Theme inheritance
- **WHEN** theme omits specific properties
- **THEN** system uses default values for unspecified properties

### Requirement: Layout Specification
The theme SHALL include a `layouts` section that defines page layouts for different photo counts and orientations.

#### Scenario: Valid layouts section
- **WHEN** a theme YAML file has a `layouts` section with valid template definitions
- **THEN** the theme loader SHALL parse it successfully.

#### Scenario: Missing layouts section
- **WHEN** a theme YAML file is missing the `layouts` section
- **THEN** the system SHALL raise an error.

### Requirement: Apply background styling
The system SHALL apply background styling to pages according to theme specifications.

#### Scenario: Solid color background
- **WHEN** theme specifies a solid background color
- **THEN** system fills page background with specified color

#### Scenario: White background default
- **WHEN** theme does not specify background
- **THEN** system uses white as default background color

### Requirement: Apply border styling to photos
The system SHALL apply border styling to photo frames according to theme specifications.

#### Scenario: Border width and color
- **WHEN** theme specifies border properties
- **THEN** system draws borders around photos with specified width and color

#### Scenario: No borders
- **WHEN** theme specifies no borders
- **THEN** system displays photos without frames

#### Scenario: Drop shadow effect
- **WHEN** theme includes shadow properties
- **THEN** system applies drop shadow to photo frames

### Requirement: Apply spacing rules
The system SHALL apply spacing between photo grid cells according to theme specifications.

#### Scenario: Uniform spacing
- **WHEN** theme specifies grid spacing value
- **THEN** system applies equal spacing between all grid cells

#### Scenario: Tight layout
- **WHEN** theme specifies minimal spacing
- **THEN** system places photos with minimal gaps

#### Scenario: Airy layout
- **WHEN** theme specifies generous spacing
- **THEN** system places photos with substantial gaps for breathing room

### Requirement: Provide default themes
The system SHALL include multiple default themes covering common aesthetic preferences.

#### Scenario: Clean theme
- **WHEN** user selects "clean" theme
- **THEN** system applies minimalist style with white background, thin borders, moderate spacing

#### Scenario: Classic theme
- **WHEN** user selects "classic" theme
- **THEN** system applies traditional style with cream background, visible borders, standard spacing

#### Scenario: Modern theme
- **WHEN** user selects "modern" theme
- **THEN** system applies contemporary style with no borders, tight spacing, high contrast

### Requirement: Support custom themes
The system SHALL allow users to define and use custom theme files.

#### Scenario: Custom theme file location
- **WHEN** user specifies path to custom theme file
- **THEN** system loads theme from specified location

#### Scenario: Theme validation
- **WHEN** custom theme file has invalid structure
- **THEN** system reports error indicating which properties are invalid

### Requirement: Maintain theme consistency across pages
The system SHALL apply theme styling consistently across all pages in a photobook.

#### Scenario: Multi-page consistency
- **WHEN** photobook contains multiple pages
- **THEN** all pages use identical theme styling properties
