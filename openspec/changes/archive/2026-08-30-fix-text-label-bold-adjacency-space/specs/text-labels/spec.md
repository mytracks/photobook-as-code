## ADDED Requirements

### Requirement: No synthetic space at markdown segment boundaries with no source whitespace
The system SHALL render two adjacent text segments produced by markdown parsing (for example, a bold or italic run followed by, or following, plain text) with no space between them when the source content had no whitespace at that boundary. The system SHALL still render a space at a segment boundary when the source content had whitespace there, and SHALL still separate individual words within a single segment by a space, unchanged from existing behavior.

#### Scenario: Bold run immediately followed by a hyphenated suffix
- **WHEN** text content is `**Cocktail**-Kurs`
- **THEN** the rendered output reads `Cocktail-Kurs` with no space between the bold word and the hyphen

#### Scenario: Bold run immediately followed by punctuation and more text
- **WHEN** text content is `**links**, das Schloss`
- **THEN** the rendered output reads `links, das Schloss` with no space before the comma

#### Scenario: Bold run followed by a real space
- **WHEN** text content is `**bold** word`
- **THEN** the rendered output reads `bold word` with exactly one space between them

#### Scenario: Plain text within a single segment keeps single-space word separation
- **WHEN** a single text segment (no markdown boundary involved) contains multiple words separated by whitespace
- **THEN** the rendered output separates those words by a single space each, unchanged from existing behavior
