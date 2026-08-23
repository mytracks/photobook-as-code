## ADDED Requirements

### Requirement: Words on a rendered line share a common baseline
The system SHALL render all words on the same display line of `text` or `title` content aligned to a common baseline, regardless of whether individual words contain tall (ascender/cap-height) letters, short (x-height only) letters, or descenders.

#### Scenario: Line mixes tall and short letterforms
- **WHEN** a rendered line contains both a word whose tallest letters reach cap-height or ascender height and a word made only of short (x-height) letters
- **THEN** both words render sitting on the same baseline, differing only in how far their ink extends above that baseline

### Requirement: Auto-sized text box padding is respected regardless of line content
The system SHALL render a `text` or `title` box's content so that the empty space above its first line and below its last line each match the theme's configured padding, regardless of which specific letters the content's words happen to contain.

#### Scenario: Content without descenders
- **WHEN** rendered text content contains no descending letters (e.g. "g", "y", "p") on any line
- **THEN** the box's top and bottom margins are each equal to the configured text padding

#### Scenario: Content with descenders on some but not all lines
- **WHEN** a multi-line text box has descenders in some lines' words but not in others
- **THEN** the box's bottom margin still equals the configured text padding, not less

### Requirement: Consistent line-to-line spacing regardless of content
The system SHALL space consecutive rendered lines within a text or title box uniformly (by the configured line spacing plus one line's height), independent of which lines contain tall letters or descenders and which do not.

#### Scenario: Mixed line content
- **WHEN** a multi-line text box has one line containing a descender and an adjacent line containing only letters with no ascenders or descenders
- **THEN** the vertical gap between those two lines equals the gap that would occur between two ordinary lines of text, not a gap that varies with which letters are present
