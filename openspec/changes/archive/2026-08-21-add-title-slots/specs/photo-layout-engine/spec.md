## MODIFIED Requirements

### Requirement: Match Layouts by Photo Count and Orientation
The system SHALL select a layout template that matches the number and orientation of the page's items — photos and title slots combined — for a given page.

#### Scenario: Successful match
- **WHEN** a set of photos (e.g., 2 landscape, 1 portrait) is passed to the layout engine
- **AND** a corresponding layout template exists in the theme
- **THEN** the system SHALL select that template for rendering.

#### Scenario: No matching template
- **WHEN** no layout template matches the photo count and orientation
- **THEN** the system SHALL raise a clear error message.

#### Scenario: Mixed items match by combined count and orientation
- **WHEN** a page's items include both photos and one or more title slots
- **THEN** the system matches a template using the total item count and each item's reported orientation (title slots included), exactly as it would for an all-photo page

### Requirement: Distribute photos across pages
The system SHALL distribute all page items — photos and title slots combined — across the specified or calculated number of pages according to layout constraints. When an explicit page count is provided, the system SHALL distribute page items evenly across ALL pages, ensuring maximum use of the requested page range. Title slots count toward `photos_per_page` and `pages` calculations identically to photos.

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

#### Scenario: Titles increase total slot count
- **WHEN** a photobook configuration defines N photos and M title entries
- **THEN** the system calculates page distribution using N + M as the total item count, not N alone

#### Scenario: Title slot placed within a page's item budget
- **WHEN** a title's chronological position falls within a page that would otherwise hold `photos_per_page` photos
- **THEN** the system counts the title as one of that page's items, reducing the number of photos placed on that page so the page's total item count still respects the configured budget
