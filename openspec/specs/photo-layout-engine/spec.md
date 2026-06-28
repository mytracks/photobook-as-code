## Purpose

Photo layout engine for automatic arrangement of photos on pages. This capability handles photo discovery, ordering, grid layout calculations, aspect ratio preservation, and distribution of photos across pages.

## Requirements

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

### Requirement: Calculate grid layout
The system SHALL calculate grid dimensions that accommodate the specified photos-per-page count.

#### Scenario: Perfect square grid
- **WHEN** photos-per-page is 4
- **THEN** system creates 2x2 grid layout

#### Scenario: Rectangular grid
- **WHEN** photos-per-page is 6
- **THEN** system creates appropriate rectangular grid (e.g., 2x3 or 3x2)

#### Scenario: Single photo per page
- **WHEN** photos-per-page is 1
- **THEN** system creates single-photo layout maximizing photo size

### Requirement: Handle aspect ratio variations
The system SHALL handle photos with different aspect ratios (portrait, landscape, square) within the same layout.

#### Scenario: Mixed orientations in grid
- **WHEN** page contains both portrait and landscape photos
- **THEN** system fits each photo within its grid cell preserving aspect ratio

#### Scenario: Consistent cell sizes
- **WHEN** grid layout is applied
- **THEN** all grid cells have equal dimensions regardless of photo aspect ratios

#### Scenario: Letterboxing or pillarboxing
- **WHEN** photo aspect ratio doesn't match cell aspect ratio
- **THEN** system centers photo within cell with appropriate padding

### Requirement: Distribute photos across pages
The system SHALL distribute all photos across calculated number of pages according to layout constraints.

#### Scenario: Exact division
- **WHEN** total photos divide evenly by photos-per-page
- **THEN** all pages contain exactly the specified number of photos

#### Scenario: Remainder photos
- **WHEN** total photos don't divide evenly
- **THEN** final page contains remaining photos

#### Scenario: Empty cells
- **WHEN** final page has fewer photos than grid capacity
- **THEN** system leaves remaining grid cells empty

### Requirement: Apply page margins
The system SHALL apply consistent margins around page content according to theme specifications.

#### Scenario: Standard margins
- **WHEN** theme specifies margin values
- **THEN** system applies equal margins on all sides of each page

#### Scenario: Bleed area
- **WHEN** configuration includes bleed specification
- **THEN** system extends content into bleed area for print preparation
