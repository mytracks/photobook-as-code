## MODIFIED Requirements

### Requirement: Distribute photos across pages
The system SHALL distribute all photos across the specified or calculated number of pages according to layout constraints. When an explicit page count is provided, the system SHALL distribute photos evenly across ALL pages, ensuring maximum use of the requested page range.

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
- **THEN** system generates exactly that many pages with photos distributed as evenly as possible across ALL pages

#### Scenario: Exact page count distributes across full range
- **WHEN** configuration specifies exact page count with photos exceeding page count (e.g., 168 photos, 100 pages)
- **THEN** system distributes photos across all 100 pages, with some pages getting multiple photos, ensuring no pages at the end remain empty

#### Scenario: Exact page count with excess pages - sparse distribution
- **WHEN** configuration specifies more pages than available photos (e.g., 8 photos, 15 pages)
- **THEN** system distributes photos evenly across all pages using interval-based spacing, with blank pages interspersed

#### Scenario: Sparse distribution spacing
- **WHEN** photos are distributed sparsely across pages (pages > photos)
- **THEN** system calculates spacing interval as total_pages / total_photos and places photos at evenly-spaced intervals

#### Scenario: Exact page count takes precedence
- **WHEN** configuration specifies both pages and photos_per_page
- **THEN** system uses the page count and calculates photos_per_page accordingly
