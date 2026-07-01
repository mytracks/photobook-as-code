## REMOVED Requirements

### Requirement: Calculate grid layout
**Reason**: This requirement is replaced by the new layout template system.
**Migration**: Themes must now define explicit layouts in their YAML files. The grid-based layout is no longer supported.

## ADDED Requirements

### Requirement: Match Layouts by Photo Count and Orientation
The system SHALL select a layout template that matches the number and orientation of photos for a given page.

#### Scenario: Successful match
- **WHEN** a set of photos (e.g., 2 landscape, 1 portrait) is passed to the layout engine
- **AND** a corresponding layout template exists in the theme
- **THEN** the system SHALL select that template for rendering.

#### Scenario: No matching template
- **WHEN** no layout template matches the photo count and orientation
- **THEN** the system SHALL raise a clear error message.

### Requirement: Prioritize Exact Orientation Order
The system SHALL prefer layout templates that match the exact order of photo orientations.

#### Scenario: Exact order preference
- **WHEN** photos are in the order [landscape, portrait, landscape]
- **AND** two templates exist: one for [landscape, portrait, landscape] and one for [landscape, landscape, portrait]
- **THEN** the system SHALL select the template with the exact order match.

## MODIFIED Requirements

### Requirement: Handle aspect ratio variations
The system SHALL handle photos with different aspect ratios (portrait, landscape, square) by matching them to the orientations specified in the layout templates.

#### Scenario: Mixed orientations with templates
- **WHEN** a page contains both portrait and landscape photos
- **THEN** the system fits each photo into the position and size defined by the corresponding entry in the layout template, preserving aspect ratio.
