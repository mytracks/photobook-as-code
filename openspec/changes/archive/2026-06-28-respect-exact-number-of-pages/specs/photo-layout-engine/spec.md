## MODIFIED Requirements

### Requirement: Distribute photos across pages
The system SHALL distribute all photos across the specified or calculated number of pages according to layout constraints, generating exactly the page count specified when an explicit page count is provided.

#### Scenario: Exact division
- **WHEN** total photos divide evenly by photos-per-page
- **THEN** all pages contain exactly the specified number of photos

#### Scenario: Remainder photos
- **WHEN** total photos don't divide evenly
- **THEN** final page contains remaining photos

#### Scenario: Empty cells
- **WHEN** final page has fewer photos than grid capacity
- **THEN** system leaves remaining grid cells empty

#### Scenario: Exact page count with sufficient photos
- **WHEN** configuration specifies exact page count (layout.pages) with enough photos to distribute
- **THEN** system generates exactly that many pages with photos distributed as evenly as possible

#### Scenario: Exact page count with excess pages
- **WHEN** configuration specifies more pages than needed for available photos
- **THEN** system generates exactly the specified number of pages, with later pages containing fewer photos or empty

#### Scenario: Exact page count takes precedence
- **WHEN** configuration specifies both pages and photos_per_page
- **THEN** system uses the page count and calculates photos_per_page accordingly
