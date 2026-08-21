## Purpose

Title slots let a `text_labels` entry define a large, page-slot-consuming section title, positioned chronologically among photos and rendered with theme-configurable Markdown formatting, instead of being overlaid on an existing photo like a caption.

## ADDED Requirements

### Requirement: Title entries consume a full page slot
A `text_labels` entry with a `title` field SHALL occupy its own page slot, distinct from any photo, rather than being overlaid on an existing photo's rendered area.

#### Scenario: Title slot has no associated photo
- **WHEN** a text label entry has a `title` field
- **THEN** system renders it as an independent page item with no photo underneath, rather than attaching it to the closest photo

#### Scenario: Titles counted toward page slot totals
- **WHEN** a photobook defines photos and title entries together
- **THEN** the total number of page slots equals the number of photos plus the number of title entries

### Requirement: Merge titles chronologically among photos
The system SHALL insert each title entry into the ordered sequence of photos at the position corresponding to its timestamp, producing a single ordered sequence of page items (photos and titles combined).

#### Scenario: Title inserted between two photos
- **WHEN** a title's timestamp falls between two consecutive photos in the ordered photo sequence
- **THEN** system places the title item between those two photos in the merged sequence

#### Scenario: Title before all photos
- **WHEN** a title's timestamp is earlier than every photo's sort date
- **THEN** system places the title item at the start of the merged sequence

#### Scenario: Title after all photos
- **WHEN** a title's timestamp is later than every photo's sort date
- **THEN** system places the title item at the end of the merged sequence

#### Scenario: Multiple titles at the same insertion point
- **WHEN** two or more titles fall at the same position relative to the photo sequence
- **THEN** system orders them among themselves by their own timestamps, preserving configuration order for exact ties

### Requirement: Title takes precedence on exact timestamp tie with a photo
When a title's timestamp exactly equals a photo's sort date, the system SHALL place the title immediately before that photo in the merged sequence.

#### Scenario: Exact timestamp match
- **WHEN** a title entry's timestamp is exactly equal to a photo's sort date
- **THEN** system places the title item immediately before that photo in the merged sequence, not after

### Requirement: Present title slots as portrait orientation for layout matching
A title slot SHALL report `portrait` as its orientation when participating in layout template matching, so it can occupy any template slot a theme already defines for a portrait photo at that item count, without requiring dedicated title layout templates.

#### Scenario: Title matched into an existing portrait-capable template
- **WHEN** a page's items are, in order, one landscape photo and one title
- **THEN** the system selects a layout template whose orientations are `[landscape, portrait]`, exactly as it would for one landscape and one portrait photo

#### Scenario: No dedicated title template required
- **WHEN** a theme defines no layout template referencing a `title`-specific orientation
- **THEN** the system still renders title slots successfully, provided the theme has a template matching the page's item count with a portrait-shaped slot at the title's position

### Requirement: Render title slots as formatted text filling their layout slot
A title slot SHALL be rendered by filling its matched layout template slot's position/size box with the title's Markdown-formatted text, using the theme's title styling; it SHALL NOT load, fit, or paste a photo image, nor draw a photo border or shadow, for that slot.

#### Scenario: Title text fills its slot
- **WHEN** a page item at a given slot is a title
- **THEN** system renders that slot's box with the title's formatted text and applies no photo image, border, or shadow to it

#### Scenario: Title text supports the same Markdown formatting as captions
- **WHEN** a title's content includes headings (`#`, `##`, `###`), `**bold**`, `_italic_`/`*italic*`, or multiple lines
- **THEN** system renders the title with the same formatting rules used for caption (`text`) content

#### Scenario: Title styling comes from the theme's title style block
- **WHEN** rendering a title slot
- **THEN** system applies font family, size, color, and alignment from the theme's `title` style block (or its defaults if unspecified)
