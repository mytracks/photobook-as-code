## ADDED Requirements

### Requirement: Support layout templates in theme configuration
The system SHALL require layout template definitions within theme files.

#### Scenario: Layout templates section required
- **WHEN** theme file is loaded
- **THEN** theme MUST contain a layouts section with at least one template definition

#### Scenario: Missing layouts section
- **WHEN** theme file omits layouts section
- **THEN** system raises error indicating layouts section is required

#### Scenario: Template structure
- **WHEN** theme defines a layout template
- **THEN** template includes photo count, orientation sequence, and positioning specifications

#### Scenario: Multiple templates in theme
- **WHEN** theme file contains layouts section
- **THEN** theme can define multiple templates for different photo combinations

#### Scenario: Template photo specifications
- **WHEN** layout template defines photo positions
- **THEN** each photo specification includes orientation, position (x, y), and size as percentage
