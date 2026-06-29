## Purpose

Template-based page layout system with orientation-aware positioning and sizing. This capability enables theme designers to create custom page layouts that accommodate different combinations of portrait and landscape photos with precise positioning and sizing controls.

## Requirements

### Requirement: Define layout templates in theme configuration
The system SHALL support layout template definitions within theme files that specify photo arrangements for different orientation combinations.

#### Scenario: Template with photo count
- **WHEN** theme defines a layout template
- **THEN** template specifies the total number of photos it accommodates

#### Scenario: Template with orientation sequence
- **WHEN** theme defines a layout template
- **THEN** template specifies the sequence of photo orientations (portrait/landscape)

#### Scenario: Multiple templates per theme
- **WHEN** theme configuration is loaded
- **THEN** theme can contain multiple layout templates for different photo combinations

### Requirement: Specify photo positions using center coordinates
The system SHALL support photo positioning using center point coordinates relative to page dimensions.

#### Scenario: Center point coordinates
- **WHEN** template defines a photo position
- **THEN** position is specified using x and y coordinates representing the center of the photo

#### Scenario: Relative coordinate system
- **WHEN** template specifies position coordinates
- **THEN** x and y values range from 0.0 to 1.0, relative to page width and height respectively

#### Scenario: Centered photo
- **WHEN** template positions a photo at (0.5, 0.5)
- **THEN** system places photo center at the exact center of the page

#### Scenario: Top-left quadrant photo
- **WHEN** template positions a photo at (0.25, 0.25)
- **THEN** system places photo center one quarter from left edge and one quarter from top edge

### Requirement: Specify photo sizes as percentage values
The system SHALL support photo sizing using percentage values relative to orientation-specific page dimensions.

#### Scenario: Landscape photo size
- **WHEN** template specifies size for a landscape photo
- **THEN** percentage value is relative to page width

#### Scenario: Portrait photo size
- **WHEN** template specifies size for a portrait photo
- **THEN** percentage value is relative to page height

#### Scenario: Half-width landscape photo
- **WHEN** template specifies 0.5 size for landscape photo
- **THEN** system renders photo at 50% of page width, maintaining aspect ratio

#### Scenario: Half-height portrait photo
- **WHEN** template specifies 0.5 size for portrait photo
- **THEN** system renders photo at 50% of page height, maintaining aspect ratio

### Requirement: Match photos to templates based on count and orientation
The system SHALL match the photos to be rendered with appropriate layout templates.

#### Scenario: Exact template match
- **WHEN** page contains N photos with specific orientations
- **THEN** system selects template that matches both count and orientation sequence

#### Scenario: Multiple matching templates
- **WHEN** multiple templates match the photo count and orientations
- **THEN** system prefers template where portrait/landscape order matches photo order

#### Scenario: Template order preference
- **WHEN** page has 1 landscape and 2 portrait photos in that order
- **THEN** system prefers template specifying [landscape, portrait, portrait] over [portrait, landscape, portrait]

#### Scenario: No matching template
- **WHEN** no template exists for the photo combination
- **THEN** system raises an error indicating missing template for specific orientation sequence

### Requirement: Preserve aspect ratios when rendering
The system SHALL maintain photo aspect ratios when positioning photos according to templates.

#### Scenario: Landscape photo in template
- **WHEN** template specifies position and size for landscape photo
- **THEN** system scales photo to fit specified width while maintaining aspect ratio

#### Scenario: Portrait photo in template
- **WHEN** template specifies position and size for portrait photo
- **THEN** system scales photo to fit specified height while maintaining aspect ratio

### Requirement: Support mixed orientations in single template
The system SHALL support templates that specify different orientations for different photo positions.

#### Scenario: Mixed orientation template
- **WHEN** template defines layout with both portrait and landscape photos
- **THEN** each photo position can have different orientation specification

#### Scenario: Complex orientation sequence
- **WHEN** template specifies sequence [landscape, portrait, portrait, landscape]
- **THEN** system matches pages with exactly that orientation sequence
