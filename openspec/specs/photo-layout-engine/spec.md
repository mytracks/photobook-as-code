## Purpose

Photo layout engine for automatic arrangement of photos on pages. This capability handles photo discovery, ordering, grid layout calculations, aspect ratio preservation, and distribution of photos across pages.

## Requirements

### Requirement: Support incremental page rendering
The system SHALL support rendering pages incrementally using a generator pattern rather than returning all pages as a batch.

#### Scenario: Generator-based rendering
- **WHEN** rendering all pages for a photobook
- **THEN** system yields each rendered page one at a time via generator function

#### Scenario: On-demand page creation
- **WHEN** each page is requested from the renderer
- **THEN** system creates and returns that page image without requiring all previous or subsequent pages

#### Scenario: Memory-efficient rendering pipeline
- **WHEN** rendering multiple pages
- **THEN** system releases memory for each page after it is yielded to the caller

#### Scenario: Page rendering with photo distribution
- **WHEN** iterating through pages via generator
- **THEN** system correctly distributes photos according to layout calculation for each page

#### Scenario: Preserve rendering quality with streaming
- **WHEN** pages are rendered incrementally
- **THEN** each page has identical quality and appearance as batch rendering approach

### Requirement: Detect photo files
The system SHALL detect and filter supported image file formats (JPG, JPEG, PNG) from the specified source directory.

#### Scenario: Mixed file types
- **WHEN** source directory contains JPG, PNG, and other file types
- **THEN** system includes only JPG and PNG files for layout

#### Scenario: Case-insensitive extensions
- **WHEN** source directory contains files with extensions .jpg, .JPG, .jpeg, .JPEG, .png, .PNG
- **THEN** system recognizes all as valid photo files

#### Scenario: Subdirectories
- **WHEN** source directory contains subdirectories with photos
- **THEN** system behavior follows configuration (recursive or single-level)

### Requirement: Determine photo ordering
The system SHALL order photos consistently for layout placement.

#### Scenario: Alphabetical ordering by filename
- **WHEN** no specific ordering is specified
- **THEN** system orders photos alphabetically by filename

#### Scenario: EXIF date ordering
- **WHEN** configuration specifies date-based ordering
- **THEN** system orders photos by EXIF creation date

#### Scenario: Missing EXIF data
- **WHEN** photos lack EXIF date information
- **THEN** system falls back to file modification date

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

### Requirement: Handle aspect ratio variations
The system SHALL handle photos with different aspect ratios (portrait, landscape, square) by matching them to the orientations specified in the layout templates.

#### Scenario: Mixed orientations with templates
- **WHEN** a page contains both portrait and landscape photos
- **THEN** the system fits each photo into the position and size defined by the corresponding entry in the layout template, preserving aspect ratio.

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

### Requirement: Apply page margins
The system SHALL apply consistent margins around page content according to theme specifications.

#### Scenario: Standard margins
- **WHEN** theme specifies margin values
- **THEN** system applies equal margins on all sides of each page

#### Scenario: Bleed area
- **WHEN** configuration includes bleed specification
- **THEN** system extends content into bleed area for print preparation
