## MODIFIED Requirements

### Requirement: Optimize file size
The system SHALL generate output files with reasonable file sizes while maintaining quality.

#### Scenario: Image compression
- **WHEN** generating output
- **THEN** system applies appropriate compression to embedded images

#### Scenario: Quality vs size balance
- **WHEN** user specifies quality level
- **THEN** system adjusts compression accordingly

#### Scenario: PDF page image compression
- **WHEN** a rendered page is embedded into PDF output
- **THEN** system encodes the page as JPEG at the configured output quality level (`output.quality`, default 95) rather than embedding it losslessly
