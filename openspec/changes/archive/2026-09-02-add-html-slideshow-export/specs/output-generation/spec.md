## MODIFIED Requirements

### Requirement: Validate transparent background configuration
The system SHALL restrict `output.transparent` to output formats that support an alpha channel, and SHALL otherwise leave it unused rather than rejected.

#### Scenario: Transparent requested with unsupported format
- **WHEN** `output.transparent` is `true` and `output.format` is `jpg` or `pdf`
- **THEN** system raises a configuration error at load time rather than proceeding to render

#### Scenario: Transparent requested with png format
- **WHEN** `output.transparent` is `true` and `output.format` is `png`
- **THEN** system accepts the configuration and proceeds

#### Scenario: Transparent requested with html format
- **WHEN** `output.transparent` is `true` and `output.format` is `html`
- **THEN** system accepts the configuration and proceeds, without applying `output.transparent` in any way (an html slideshow has no bitmap alpha channel to control)

### Requirement: Support output directory specification
The system SHALL allow users to specify where output files are saved, except for `html` output, which always saves to the first entry of `photo_folders` regardless of any specified directory.

#### Scenario: Custom output directory
- **WHEN** configuration specifies output directory and `output.format` is `pdf`, `png`, or `jpg`
- **THEN** system saves generated files to specified location

#### Scenario: Default output location
- **WHEN** configuration does not specify output directory and `output.format` is `pdf`, `png`, or `jpg`
- **THEN** system saves output to current working directory

#### Scenario: Create missing directories
- **WHEN** specified output directory does not exist
- **THEN** system creates necessary directory structure

#### Scenario: Image page files land directly in the output directory
- **WHEN** output format is `png` or `jpg`
- **THEN** system writes each page's image file directly into the resolved output directory, without creating an intermediate per-run subfolder named after the base filename

#### Scenario: HTML output directory is always the first photo folder
- **WHEN** `output.format` is `html`
- **THEN** system saves the generated file into the first resolved entry of `photo_folders`, regardless of whether `output.directory` or `--output` specifies a different directory

#### Scenario: HTML directory override is ignored with a notice
- **WHEN** `output.format` is `html` and `output.directory` is set, or `--output` specifies a directory
- **THEN** system ignores that directory, saves into the first resolved `photo_folders` entry instead, and prints an informational note that the override was ignored
