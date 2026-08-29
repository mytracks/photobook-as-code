## MODIFIED Requirements

### Requirement: Support output directory specification
The system SHALL allow users to specify where output files are saved.

#### Scenario: Custom output directory
- **WHEN** configuration specifies output directory
- **THEN** system saves generated files to specified location

#### Scenario: Default output location
- **WHEN** configuration does not specify output directory
- **THEN** system saves output to current working directory

#### Scenario: Create missing directories
- **WHEN** specified output directory does not exist
- **THEN** system creates necessary directory structure

#### Scenario: Image page files land directly in the output directory
- **WHEN** output format is `png` or `jpg`
- **THEN** system writes each page's image file directly into the resolved output directory, without creating an intermediate per-run subfolder named after the base filename

### Requirement: Handle output file naming
The system SHALL generate output files with meaningful names based on configuration or defaults.

#### Scenario: Custom output filename
- **WHEN** configuration specifies output filename
- **THEN** system uses specified name for output file(s)

#### Scenario: Default filename
- **WHEN** configuration does not specify output filename
- **THEN** system generates filename from configuration file name

#### Scenario: Prevent overwriting
- **WHEN** output file already exists
- **THEN** system either prompts for confirmation or appends timestamp to avoid overwriting

#### Scenario: Base filename used as page file prefix for image formats
- **WHEN** output format is `png` or `jpg` and the base filename is derived (e.g. `mondsee`)
- **THEN** system uses that base filename only as the prefix of each page's filename (e.g. `mondsee_page_001.jpg`), never as a directory name, and any extension implied by the output format is not appended to the directory path
