## ADDED Requirements

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
