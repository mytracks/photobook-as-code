## MODIFIED Requirements

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
