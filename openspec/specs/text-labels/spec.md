## Purpose

Text label management for photobooks. This capability parses timestamped text entries from configuration, associates them with photos based on chronological proximity, and provides structures for rendering formatted text on photobook pages.

## Requirements

### Requirement: Parse text label entries from configuration
The system SHALL parse text label entries containing a timestamp and either `text` or `title` content from the photobook configuration. Each entry SHALL have exactly one of `text` or `title`.

#### Scenario: Valid text label entry
- **WHEN** configuration includes a text label with timestamp and `text` content
- **THEN** system successfully parses and stores the text label

#### Scenario: Valid title entry
- **WHEN** configuration includes a text label with timestamp and `title` content
- **THEN** system successfully parses and stores the entry as a title

#### Scenario: Multiple text labels
- **WHEN** configuration includes multiple text label entries, in any mix of `text` and `title`
- **THEN** system parses all entries and maintains their order

#### Scenario: Multi-line text content
- **WHEN** a `text` or `title` entry contains line breaks
- **THEN** system preserves line breaks in parsed content

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
- **WHEN** a text label entry has neither a `text` nor a `title` field
- **THEN** system reports validation error indicating that one of `text` or `title` is required

#### Scenario: Both text and title present
- **WHEN** a text label entry has both a `text` and a `title` field
- **THEN** system reports validation error indicating that `text` and `title` are mutually exclusive

### Requirement: Associate text labels with photos by timestamp
The system SHALL match `text`-field text labels to photos based on chronological proximity of timestamps. `title`-field entries are not associated with a photo by proximity; they are positioned as their own page slot per the title-slots capability.

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

#### Scenario: Title entries excluded from proximity association
- **WHEN** a text label entry has a `title` field instead of `text`
- **THEN** system does not attempt to associate it with a photo by proximity; it is handled as a title slot instead

### Requirement: Parse markdown formatting in text content
The system SHALL parse markdown formatting markers in both `text` and `title` content and provide structured format information for rendering.

#### Scenario: Italic text
- **WHEN** text contains `*italic*` markers
- **THEN** system identifies text segment as italic style

#### Scenario: Underscore italic text
- **WHEN** text contains `_italic_` markers
- **THEN** system identifies text segment as italic style, identically to `*italic*`

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

#### Scenario: Title content uses the same markdown parsing as text content
- **WHEN** a `title` entry's content contains markdown markers (headings, bold, italic, or combinations)
- **THEN** system parses it with the same rules applied to `text` content

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

### Requirement: Empty text content renders nothing
The system SHALL render no visual output - neither text glyphs nor a background - for a `text`-field text label whose content is an empty string or parses to zero content lines.

#### Scenario: Empty text string
- **WHEN** a text label's `text` field is an empty string
- **THEN** the renderer draws no text and no background box for that label

#### Scenario: Text that parses to zero content lines
- **WHEN** a text label's `text` field contains only blank lines (all lines trimmed away by markdown parsing)
- **THEN** the renderer draws no text and no background box for that label

#### Scenario: Non-empty text content
- **WHEN** a text label's `text` field contains at least one non-blank content line
- **THEN** the renderer draws the text and, if the active theme enables it, the background box, unchanged from existing behavior
