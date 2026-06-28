## ADDED Requirements

### Requirement: Generate output with minimal memory footprint
The system SHALL generate PDF and image output files using a streaming approach that processes pages incrementally rather than loading all pages into memory simultaneously.

#### Scenario: Large photobook PDF generation
- **WHEN** user generates a PDF with 50+ pages
- **THEN** system processes pages one at a time, keeping only the current page in memory

#### Scenario: Memory usage for multi-page output
- **WHEN** generating output with multiple pages
- **THEN** peak memory usage SHALL NOT exceed memory required for a single page plus output file overhead

#### Scenario: Sequential page processing
- **WHEN** pages are rendered for output
- **THEN** system renders each page on-demand during output generation rather than pre-rendering all pages

#### Scenario: Generator-based page iteration
- **WHEN** output generation receives rendered pages
- **THEN** system accepts page iterator that yields pages one at a time

## MODIFIED Requirements

### Requirement: Report generation progress
The system SHALL provide progress feedback during output generation process using pre-calculated page count rather than batch size.

#### Scenario: Page rendering progress
- **WHEN** system is rendering pages
- **THEN** system displays progress indicator showing current page being processed

#### Scenario: Progress with streaming generation
- **WHEN** pages are generated via streaming
- **THEN** progress indicator shows "Page X of Y" where Y is the expected total from layout calculation

#### Scenario: Completion notification
- **WHEN** output generation completes successfully
- **THEN** system displays success message with output file location

#### Scenario: Generation failure
- **WHEN** output generation fails
- **THEN** system reports error message with specific failure reason
