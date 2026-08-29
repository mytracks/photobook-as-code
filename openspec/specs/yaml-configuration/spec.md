## Purpose

Configuration parsing and validation for photobook generation. This capability handles YAML file loading, validation of required fields, paper size specifications, layout constraints, and theme selection.

## Requirements

### Requirement: Parse YAML configuration file
The system SHALL parse a YAML configuration file containing photobook settings and validate its structure.

#### Scenario: Valid configuration file
- **WHEN** user provides a YAML file with all required fields (`photo_folders` list, output size)
- **THEN** system successfully parses the configuration and proceeds with generation

#### Scenario: Missing required fields
- **WHEN** user provides a YAML file missing required fields
- **THEN** system reports clear error message indicating which fields are missing

#### Scenario: Invalid YAML syntax
- **WHEN** user provides a file with invalid YAML syntax
- **THEN** system reports parsing error with line number and description

### Requirement: Validate photo source paths
The system SHALL accept a `photo_folders` field containing a YAML list of one or more directory paths, and SHALL validate that every listed folder exists and is a directory.

#### Scenario: Valid photo directory
- **WHEN** configuration specifies `photo_folders` as a list of one or more directories containing photo files
- **THEN** system locates and lists all supported image files across those directories, merged into one combined pool

#### Scenario: Non-existent path
- **WHEN** any directory listed in `photo_folders` does not exist
- **THEN** system reports an error indicating that specific path cannot be found

#### Scenario: Empty directory
- **WHEN** every directory listed in `photo_folders` contains no supported image files
- **THEN** system reports an error indicating no photos were found

#### Scenario: Individual folder with no photos
- **WHEN** one folder listed in `photo_folders` contains no supported image files but at least one other listed folder does
- **THEN** system does not report an error for the empty folder and proceeds using the photos found in the other folder(s)

#### Scenario: Duplicate or aliased folder entries
- **WHEN** `photo_folders` lists the same directory more than once, or lists two paths that resolve to the same directory
- **THEN** system deduplicates the combined photo pool by resolved photo path rather than reporting a validation error or including duplicate photos

### Requirement: Support standard paper sizes
The system SHALL support standard paper size specifications including DIN A4, US Letter, and custom dimensions.

#### Scenario: DIN A4 specification
- **WHEN** configuration specifies "A4" as output size
- **THEN** system uses dimensions 210mm x 297mm

#### Scenario: US Letter specification
- **WHEN** configuration specifies "Letter" as output size
- **THEN** system uses dimensions 8.5in x 11in

#### Scenario: Custom dimensions
- **WHEN** configuration specifies custom width and height
- **THEN** system uses the provided dimensions

### Requirement: Parse layout constraints
The system SHALL accept either photos-per-page or total-pages constraint and calculate the complementary value.

#### Scenario: Photos per page specified
- **WHEN** configuration specifies 4 photos per page with 20 photos total
- **THEN** system calculates 5 pages needed

#### Scenario: Total pages specified
- **WHEN** configuration specifies 5 pages with 20 photos total
- **THEN** system calculates 4 photos per page

#### Scenario: Uneven distribution
- **WHEN** photos don't divide evenly into specified pages
- **THEN** system distributes photos as evenly as possible across pages

### Requirement: Configure whether a new day forces a new page
The system SHALL accept an optional `layout.new_page_per_day` boolean field, defaulting to `true`, controlling whether photo/title distribution treats a calendar-day change as a forced page break.

#### Scenario: Default enables day-boundary page breaks
- **WHEN** configuration does not specify `layout.new_page_per_day`
- **THEN** the system behaves as if it were set to `true`

#### Scenario: Explicitly enabled
- **WHEN** configuration specifies `layout.new_page_per_day: true`
- **THEN** the system enables day-boundary page breaks during distribution

#### Scenario: Explicitly disabled
- **WHEN** configuration specifies `layout.new_page_per_day: false`
- **THEN** the system disables day-boundary page breaks during distribution

#### Scenario: Invalid type
- **WHEN** configuration specifies a non-boolean value for `layout.new_page_per_day`
- **THEN** system reports a validation error indicating the field must be a boolean

### Requirement: Validate theme selection
The system SHALL validate that the specified theme exists and is available.

#### Scenario: Valid theme name
- **WHEN** configuration specifies an available theme name
- **THEN** system loads the theme configuration

#### Scenario: Invalid theme name
- **WHEN** configuration specifies a non-existent theme
- **THEN** system reports error listing available themes

#### Scenario: Missing theme specification
- **WHEN** configuration does not specify a theme
- **THEN** system uses default theme

### Requirement: Override theme page margin from configuration
The system SHALL accept an optional `output.page_margin` integer field in the YAML configuration, specified in the same pixel unit as a theme's `spacing.page_margin`. When present, it overrides the selected theme's `spacing.page_margin` for that run; when absent, the theme's own value is used unchanged.

#### Scenario: Config overrides theme page margin
- **WHEN** configuration specifies `output.page_margin: 0` and the selected theme's `spacing.page_margin` is a non-zero value
- **THEN** system renders pages using a page margin of `0`, not the theme's value

#### Scenario: Missing page_margin falls through to theme
- **WHEN** configuration does not specify `output.page_margin`
- **THEN** system renders pages using the selected theme's own `spacing.page_margin` value, unchanged from today's behavior

#### Scenario: Explicit zero is a valid override
- **WHEN** configuration specifies `output.page_margin: 0`
- **THEN** system treats this as an explicit override to zero, not as equivalent to omitting the field

#### Scenario: Negative page_margin rejected
- **WHEN** configuration specifies `output.page_margin` as a negative integer
- **THEN** system reports a validation error at load time indicating `page_margin` must be non-negative, and does not proceed to render

#### Scenario: Non-integer page_margin rejected
- **WHEN** configuration specifies `output.page_margin` as a non-integer value (e.g. a string that is not numeric)
- **THEN** system reports a validation error at load time indicating `page_margin` must be an integer

### Requirement: Parse text label entries
The system SHALL parse an optional `text_labels` section in the YAML configuration containing timestamped text entries.

#### Scenario: Valid text_labels section
- **WHEN** configuration includes `text_labels` array with valid entries
- **THEN** system parses all text label entries successfully

#### Scenario: Text label with ISO timestamp
- **WHEN** text label entry has `timestamp` field with ISO 8601 format
- **THEN** system parses timestamp correctly

#### Scenario: Text label with Unix epoch timestamp
- **WHEN** text label entry has `timestamp` field with Unix epoch integer
- **THEN** system parses timestamp correctly

#### Scenario: Text label with multi-line text
- **WHEN** text label entry has `text` field with YAML multi-line string (using | or >)
- **THEN** system preserves line breaks and text content

#### Scenario: Missing text_labels section
- **WHEN** configuration does not include `text_labels` section
- **THEN** system processes configuration normally without text labels

#### Scenario: Empty text_labels array
- **WHEN** configuration includes `text_labels: []`
- **THEN** system processes configuration normally with no text labels

#### Scenario: Invalid text label structure
- **WHEN** text label entry is missing required field (timestamp or text)
- **THEN** system reports validation error with clear message indicating missing field

#### Scenario: Text label with invalid timestamp format
- **WHEN** text label timestamp is not a valid ISO 8601 string or Unix epoch number
- **THEN** system reports validation error indicating invalid timestamp format

### Requirement: Validate text label data types
The system SHALL validate that text label fields have correct data types.

#### Scenario: Timestamp as string
- **WHEN** text label timestamp is a string (ISO 8601 format)
- **THEN** system accepts and parses it

#### Scenario: Timestamp as number
- **WHEN** text label timestamp is a number (Unix epoch)
- **THEN** system accepts and parses it

#### Scenario: Text as string
- **WHEN** text label text field is a string (single or multi-line)
- **THEN** system accepts it

#### Scenario: Text label as non-object
- **WHEN** text_labels array contains non-object entry (e.g., string or number)
- **THEN** system reports validation error indicating entry must be an object

#### Scenario: Timestamp as boolean or object
- **WHEN** text label timestamp field is boolean or object
- **THEN** system reports validation error indicating invalid timestamp type
