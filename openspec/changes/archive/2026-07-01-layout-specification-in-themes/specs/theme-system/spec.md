## MODIFIED Requirements

### Requirement: Define theme structure
The system SHALL support theme definitions that specify visual styling properties for photobook pages. Themes SHALL also define layout templates.

#### Scenario: Theme file format
- **WHEN** system loads a theme
- **THEN** theme file contains properties for backgrounds, borders, spacing, colors, and layouts.

#### Scenario: Theme inheritance
- **WHEN** theme omits specific properties
- **THEN** system uses default values for unspecified properties

## ADDED Requirements

### Requirement: Layout Specification
The theme SHALL include a `layouts` section that defines page layouts for different photo counts and orientations.

#### Scenario: Valid layouts section
- **WHEN** a theme YAML file has a `layouts` section with valid template definitions
- **THEN** the theme loader SHALL parse it successfully.

#### Scenario: Missing layouts section
- **WHEN** a theme YAML file is missing the `layouts` section
- **THEN** the system SHALL raise an error.
