## Purpose

Text label management for photobooks. This capability parses timestamped text entries from configuration, associates them with photos based on chronological proximity, and provides structures for rendering formatted text on photobook pages.

## Requirements

### Requirement: Parse text label entries from configuration
The system SHALL parse text label entries containing timestamps and text content from the photobook configuration.

#### Scenario: Valid text label entry
- **WHEN** configuration includes a text label with timestamp and text content
- **THEN** system successfully parses and stores the text label

#### Scenario: Multiple text labels
- **WHEN** configuration includes multiple text label entries
- **THEN** system parses all entries and maintains their order

#### Scenario: Multi-line text content
- **WHEN** text label contains line breaks
- **THEN** system preserves line breaks in parsed text

#### Scenario: ISO 8601 timestamp format
- **WHEN** text label uses ISO 8601 timestamp (e.g., "2026-06-15T14:30:00")
- **THEN** system parses timestamp correctly

#### Scenario: Unix epoch timestamp format
- **WHEN** text label uses Unix epoch timestamp (e.g., 1656163800)
- **THEN** system parses timestamp correctly

#### Scenario: Missing timestamp
- **WHEN** text label entry lacks timestamp field
- **THEN** system reports validation error indicating missing timestamp

#### Scenario: Missing text content
- **WHEN** text label entry lacks text field
- **THEN** system reports validation error indicating missing text

### Requirement: Associate text labels with photos by timestamp
The system SHALL match text labels to photos based on chronological proximity of timestamps.

#### Scenario: Single text label and single matching photo
- **WHEN** text label timestamp matches a photo's EXIF timestamp
- **THEN** system associates text label with that photo

#### Scenario: Text label between two photos
- **WHEN** text label timestamp falls between two photo timestamps
- **THEN** system associates text label with chronologically closest photo

#### Scenario: Equidistant timestamps
- **WHEN** text label timestamp is equidistant from two photos
- **THEN** system associates text label with earlier photo (deterministic tiebreaker)

#### Scenario: Multiple text labels for same page
- **WHEN** multiple text labels match photos on the same page
- **THEN** system maintains associations for all labels on that page

#### Scenario: Text label with no photos
- **WHEN** text label exists but no photos have been loaded
- **THEN** system handles gracefully without error (text label unused)

#### Scenario: Photo without text label
- **WHEN** photo has no matching text label
- **THEN** photo renders normally without text

### Requirement: Parse markdown formatting in text content
The system SHALL parse markdown formatting markers and provide structured format information for rendering.

#### Scenario: Italic text
- **WHEN** text contains `*italic*` markers
- **THEN** system identifies text segment as italic style

#### Scenario: Bold text
- **WHEN** text contains `**bold**` markers
- **THEN** system identifies text segment as bold style

#### Scenario: Heading level 1
- **WHEN** line starts with `#` followed by space
- **THEN** system marks line as heading with 1.5x font size multiplier

#### Scenario: Heading level 2
- **WHEN** line starts with `##` followed by space
- **THEN** system marks line as heading with 1.3x font size multiplier

#### Scenario: Heading level 3
- **WHEN** line starts with `###` followed by space
- **THEN** system marks line as heading with 1.2x font size multiplier

#### Scenario: Combined formatting
- **WHEN** text contains multiple markdown markers (e.g., `**bold *and italic* text**`)
- **THEN** system parses nested formatting correctly

#### Scenario: Malformed markdown
- **WHEN** text contains incomplete markdown markers (e.g., single `*` without closing)
- **THEN** system renders markers as literal text (graceful degradation)

#### Scenario: Plain text without markdown
- **WHEN** text contains no markdown markers
- **THEN** system renders text with default formatting

### Requirement: Provide text label data for rendering
The system SHALL provide text label content and formatting information to the renderer for each page.

#### Scenario: Text labels for page
- **WHEN** renderer requests text labels for a page
- **THEN** system provides list of text labels associated with photos on that page

#### Scenario: Formatted text segments
- **WHEN** renderer requests formatted text content
- **THEN** system provides text split into segments with style attributes (plain, italic, bold, heading level)

#### Scenario: Text positioning lookup
- **WHEN** renderer has photo placement and needs text position
- **THEN** system provides text content associated with that photo (if any)

#### Scenario: No text labels for page
- **WHEN** page has no associated text labels
- **THEN** system returns empty list (no error)
