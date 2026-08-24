## MODIFIED Requirements

### Requirement: Consistent line-to-line spacing regardless of content
The system SHALL space consecutive rendered lines within a text or title box uniformly (by the theme's configured `line_spacing` for that content's style block, plus one line's height), independent of which lines contain tall letters or descenders and which do not.

#### Scenario: Mixed line content
- **WHEN** a multi-line text box has one line containing a descender and an adjacent line containing only letters with no ascenders or descenders
- **THEN** the vertical gap between those two lines equals the gap that would occur between two ordinary lines of text, not a gap that varies with which letters are present

#### Scenario: Default line spacing
- **WHEN** the theme does not specify `line_spacing` for the relevant style block (`text` or `title`)
- **THEN** consecutive rendered lines are spaced using a default gap of 10 pixels
