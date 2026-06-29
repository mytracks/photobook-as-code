## ADDED Requirements

### Requirement: Detect photo orientations
The system SHALL detect and classify photo orientations as portrait, landscape, or square.

#### Scenario: Landscape photo detection
- **WHEN** photo width exceeds height
- **THEN** system classifies photo as landscape orientation

#### Scenario: Portrait photo detection
- **WHEN** photo height exceeds width
- **THEN** system classifies photo as portrait orientation

#### Scenario: Square photo detection
- **WHEN** photo width equals height
- **THEN** system classifies photo as square orientation (treated as landscape for template matching)

### Requirement: Match page photos to layout templates
The system SHALL match photos assigned to each page with appropriate layout templates from the theme.

#### Scenario: Count and orientation matching
- **WHEN** page has N photos with specific orientations
- **THEN** system searches for template matching both count and orientation sequence

#### Scenario: Multiple template matches with order preference
- **WHEN** multiple templates match count and orientations
- **THEN** system prefers template where orientation sequence matches photo order

#### Scenario: Missing template error
- **WHEN** no template matches the page's photo count and orientations
- **THEN** system raises error indicating the missing template specification

#### Scenario: Template with exact order match
- **WHEN** page contains [landscape, portrait, portrait] photos in that order
- **THEN** system selects template specifying [landscape, portrait, portrait] over other matches

### Requirement: Apply template-based positioning
The system SHALL position photos according to matched layout template specifications.

#### Scenario: Template position coordinates
- **WHEN** template specifies photo position as (x, y)
- **THEN** system places photo center at position relative to page dimensions

#### Scenario: Template size for landscape
- **WHEN** template specifies size S for landscape photo
- **THEN** system scales photo to S × page_width, maintaining aspect ratio

#### Scenario: Template size for portrait
- **WHEN** template specifies size S for portrait photo
- **THEN** system scales photo to S × page_height, maintaining aspect ratio
