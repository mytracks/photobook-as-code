## MODIFIED Requirements

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

#### Scenario: Interior blank line preserved
- **WHEN** a `text` or `title` entry contains a blank line between two non-blank lines
- **THEN** system preserves that blank line in parsed content

#### Scenario: Leading and trailing blank lines trimmed
- **WHEN** a `text` or `title` entry's content has one or more blank lines at the very start or end (for example, from a YAML `|` block scalar's trailing newline, or a blank line typed immediately after `text: |`/`title: |`)
- **THEN** system trims those leading and trailing blank lines before parsing, so they produce no rendered content or spacing

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

## ADDED Requirements

### Requirement: Render blank lines with vertical spacing
The system SHALL render an interior blank line in `text` or `title` content as vertical spacing equal to one normal (non-heading) line of that content's base font size, rather than an imperceptible gap.

#### Scenario: Single blank line between content lines
- **WHEN** `text` or `title` content contains one blank line between two non-blank lines
- **THEN** the rendered output shows a vertical gap between those lines approximately equal to one line of normal text height

#### Scenario: Multiple consecutive blank lines
- **WHEN** `text` or `title` content contains two or more consecutive blank lines between non-blank lines
- **THEN** the rendered vertical gap is the sum of one line height per blank line (gaps stack additively)
