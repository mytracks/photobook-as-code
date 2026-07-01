## Purpose

Layout templates for precise photo positioning and sizing. This capability handles definition, matching, and layout application using templates defined in themes.

## Requirements

### Requirement: Layout Template Definition
The theme configuration SHALL support a `layouts` section, which is a list of layout templates.

#### Scenario: Valid layout template
- **WHEN** a theme YAML file contains a `layouts` section with a list of templates
- **THEN** the theme loader SHALL parse the templates without error.

### Requirement: Template Matching by Photo Count
The layout engine SHALL select a template that matches the number of photos to be placed on a page.

#### Scenario: Exact photo count match
- **WHEN** there are 3 photos to be placed on a page
- **AND** there is a layout template with `count: 3`
- **THEN** the layout engine SHALL select that template.

#### Scenario: No photo count match
- **WHEN** there are 4 photos to be placed on a page
- **AND** there is no layout template with `count: 4`
- **THEN** the layout engine SHALL raise an error.

### Requirement: Template Matching by Orientation
The layout engine SHALL select a template that matches the orientation of the photos.

#### Scenario: Exact orientation match
- **WHEN** there are 2 photos (landscape, portrait)
- **AND** there is a layout template with `orientations: [landscape, portrait]`
- **THEN** the layout engine SHALL select that template.

#### Scenario: Mismatched orientation
- **WHEN** there are 2 photos (landscape, portrait)
- **AND** the only template for 2 photos has `orientations: [portrait, portrait]`
- **THEN** the layout engine SHALL raise an error.

### Requirement: Photo Positioning
The renderer SHALL position photos on the page based on the `position` coordinates in the selected layout template.

#### Scenario: Centered photo
- **WHEN** a photo is placed using a template with `position: {x: 0.5, y: 0.5}`
- **THEN** the center of the photo SHALL be at the center of the page.

### Requirement: Photo Sizing
The renderer SHALL size photos on the page based on the `size` value in the selected layout template.

#### Scenario: Landscape photo sizing
- **WHEN** a landscape photo is placed with `size: 0.8`
- **THEN** the width of the photo SHALL be 80% of the page width.

#### Scenario: Portrait photo sizing
- **WHEN** a portrait photo is placed with `size: 0.6`
- **THEN** the height of the photo SHALL be 60% of the page height.