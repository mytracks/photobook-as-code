## Purpose

Configuration parsing and validation for photobook generation. This capability handles YAML file loading, validation of required fields, paper size specifications, layout constraints, and theme selection.

## Requirements

### Requirement: Parse YAML configuration file
The system SHALL parse a YAML configuration file containing photobook settings and validate its structure.

#### Scenario: Valid configuration file
- **WHEN** user provides a YAML file with all required fields (photos path, output size)
- **THEN** system successfully parses the configuration and proceeds with generation

#### Scenario: Missing required fields
- **WHEN** user provides a YAML file missing required fields
- **THEN** system reports clear error message indicating which fields are missing

#### Scenario: Invalid YAML syntax
- **WHEN** user provides a file with invalid YAML syntax
- **THEN** system reports parsing error with line number and description

### Requirement: Validate photo source paths
The system SHALL validate that photo source paths specified in configuration exist and are accessible.

#### Scenario: Valid photo directory
- **WHEN** configuration specifies a directory containing photo files
- **THEN** system locates and lists all supported image files in that directory

#### Scenario: Non-existent path
- **WHEN** configuration specifies a path that does not exist
- **THEN** system reports error indicating the path cannot be found

#### Scenario: Empty directory
- **WHEN** configuration points to a directory with no supported image files
- **THEN** system reports error indicating no photos were found

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
