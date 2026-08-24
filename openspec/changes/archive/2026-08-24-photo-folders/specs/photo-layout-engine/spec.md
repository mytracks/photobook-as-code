## MODIFIED Requirements

### Requirement: Detect photo files
The system SHALL detect and filter supported image file formats (JPG, JPEG, PNG) from each of the configured source folders, and SHALL merge the results across all folders into one combined pool before ordering and layout.

#### Scenario: Mixed file types
- **WHEN** a source folder contains JPG, PNG, and other file types
- **THEN** system includes only JPG and PNG files from that folder for layout

#### Scenario: Case-insensitive extensions
- **WHEN** a source folder contains files with extensions .jpg, .JPG, .jpeg, .JPEG, .png, .PNG
- **THEN** system recognizes all as valid photo files

#### Scenario: Subdirectories
- **WHEN** a source folder contains subdirectories with photos
- **THEN** system behavior follows configuration (recursive or single-level)

#### Scenario: Multiple source folders merged
- **WHEN** more than one folder is configured
- **THEN** system detects photo files independently in each folder and merges them into a single combined pool, deduplicated by resolved photo path, before ordering is applied
