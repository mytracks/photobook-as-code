## Purpose

A browser-based editor that lets a user page through the photos of a single photobook configuration and write the `text` content of each photo's `text_labels` entry directly, saving edits back into the same YAML file.

## Requirements

### Requirement: Navigate photos in configured order
The system SHALL let the user move forward and backward through the photos of the configured photo directory, one photo at a time, in the same order the photobook renderer would use for that configuration. The system SHALL provide full-height click zones and a keyboard shortcut for this navigation, both usable regardless of where the page's focus currently is.

#### Scenario: Sequential navigation
- **WHEN** the user requests the next or previous photo
- **THEN** the system displays the adjacent photo in the configured order (`layout.order`)

#### Scenario: First and last photo boundaries
- **WHEN** the user is viewing the first or last photo in the order
- **THEN** the system does not allow navigating before the first or after the last photo

#### Scenario: Order matches final photobook order
- **WHEN** the configuration specifies `layout.order: date` or `layout.order: alphabetical`
- **THEN** the photo sequence shown in the editor matches the order photos would be laid out in the generated photobook

#### Scenario: Full-height click zones
- **WHEN** the user clicks anywhere within the left or right edge band of the photo, spanning its full height
- **THEN** the system navigates to the previous photo (left band) or next photo (right band), applying the same first/last boundary rule as other navigation

#### Scenario: Keyboard shortcut navigates regardless of focus
- **WHEN** the user presses Cmd+Left Arrow or Cmd+Right Arrow (or Ctrl+Left Arrow / Ctrl+Right Arrow on non-Mac platforms), including while the caption text field has focus
- **THEN** the system navigates to the previous or next photo respectively, saving any pending caption edit first as it does for other navigation actions

### Requirement: Edit and autosave text content for the current photo
The system SHALL display an editable plain-text field containing the current photo's associated `text_labels` `text` content (empty if none exists), and SHALL save changes to that content without requiring an explicit save action.

#### Scenario: Existing text is shown for editing
- **WHEN** the user views a photo that already has an associated `text_labels` entry with a `text` field
- **THEN** the editable field is pre-filled with that entry's current text, unmodified

#### Scenario: Autosave on navigating away
- **WHEN** the user has changed the text field's content and then navigates to another photo or moves focus away from the field
- **THEN** the system saves the updated text to the YAML configuration file before the navigation completes, and confirms the save to the user

#### Scenario: No changes made
- **WHEN** the user views a photo's text and navigates away without changing it
- **THEN** the system does not rewrite the configuration file

#### Scenario: Saving empty text
- **WHEN** the user clears a photo's text field to empty and navigates away
- **THEN** the system saves an empty string as that entry's `text` value

#### Scenario: Raw Markdown, no rendering
- **WHEN** the user types Markdown syntax into the text field
- **THEN** the system stores the raw text as typed and does not render or preview it as formatted output

### Requirement: Auto-create a text_labels entry on first edit
The system SHALL create a new `text_labels` entry the first time text is saved for a photo that has no existing associated entry, using that photo's own timestamp.

#### Scenario: Photo with no existing entry
- **WHEN** the user types text for a photo that has no associated `text_labels` entry and navigates away
- **THEN** the system creates a new entry with the photo's timestamp and the entered text, positioned in chronological order among existing entries

#### Scenario: Configuration has no text_labels section yet
- **WHEN** the configuration file has no `text_labels` section at all
- **THEN** saving text for any photo creates the `text_labels` section along with the new entry

#### Scenario: Newly created entry is annotated
- **WHEN** the system creates a new entry for a photo
- **THEN** the entry identifies the source photo (for example, via a filename annotation), consistent with entries produced by the existing label-extraction feature

### Requirement: Preserve unrelated file content when saving
The system SHALL modify only the `text` value of the entry being edited (or add the one new entry described above) when saving, leaving all other content in the configuration file unchanged.

#### Scenario: Comments are preserved
- **WHEN** the configuration file contains comments on `text_labels` entries (for example, source filenames)
- **THEN** saving an edit to one entry's text leaves every other entry's comments intact

#### Scenario: Title entries are untouched
- **WHEN** the configuration file's `text_labels` section contains `title` entries interspersed with `text` entries
- **THEN** saving a `text` edit does not alter, move, or remove any `title` entry

#### Scenario: Other configuration sections are untouched
- **WHEN** the configuration file contains `photos`, `output`, `layout`, or `theme` sections
- **THEN** saving a text edit preserves those sections' content and formatting, with the sole known exception of collapsing a redundant blank line within a run of multiple blank-line-separated comment-only groups trailing a mapping's last key (an inherent limitation of the YAML round-trip approach; see design.md)

#### Scenario: Ordering and formatting of untouched entries preserved
- **WHEN** the configuration file has a specific order and formatting for its `text_labels` entries
- **THEN** saving an edit to one entry does not reorder or reformat the other entries

### Requirement: Photos and other files are never modified
The system SHALL treat the photo directory as read-only and SHALL write only to the single configuration file it was started with.

#### Scenario: Viewing and editing does not touch photo files
- **WHEN** the user views or edits text for any number of photos
- **THEN** no file in the configured photo directory is created, modified, or deleted

#### Scenario: Only the configured file is written
- **WHEN** the system saves an edit
- **THEN** the only file written on disk is the YAML configuration file the editor was started with

### Requirement: Display the current photo
The system SHALL render the currently selected photo's image in the browser alongside its editable text field, and SHALL reserve the image's display space in advance so that no visible layout shift occurs while the image loads.

#### Scenario: Photo image is visible
- **WHEN** the user navigates to a photo
- **THEN** the system displays that photo's image in the browser

#### Scenario: No layout shift while loading
- **WHEN** the user navigates to a photo and its image has not yet finished loading
- **THEN** the system reserves the image's final display space using the photo's real aspect ratio, so the caption field and other page elements do not move once the image finishes loading

### Requirement: Present the editor in a dark theme
The system SHALL present the entire editor interface using a fixed dark color theme (dark background, light text) with no user-facing option to change it.

#### Scenario: Dark background throughout
- **WHEN** the user views any page of the editor
- **THEN** the background is a dark/black color and all text and controls are legible against it

#### Scenario: Theme is not configurable
- **WHEN** the user looks for a way to switch between light and dark themes
- **THEN** the system provides no such option; the dark theme is the only theme

### Requirement: Display the current photo's date prominently
The system SHALL display the current photo's date in a prominent position centered above the photo, using the photo's real capture date when known, and SHALL show the photo's filename in that position instead when no real capture date is known.

#### Scenario: Capture date is known
- **WHEN** the current photo has a known capture date (from its embedded EXIF metadata)
- **THEN** the system displays that date, centered above the photo, formatted to include the day of the week

#### Scenario: Capture date is unknown
- **WHEN** the current photo has no embedded capture date
- **THEN** the system displays the photo's filename in that position instead of a date, rather than presenting an unverified filesystem date as if it were the capture date

### Requirement: Indicate the first photo of a new day
The system SHALL display a clearly visible indicator (an icon with accompanying text) next to the date whenever the current photo's date differs from the previously displayed photo's date in the configured order.

#### Scenario: Date changes from the previous photo
- **WHEN** the current photo's date differs from the date of the photo immediately before it in the configured order, or the current photo is the first photo in the order
- **THEN** the system displays the new-day indicator next to the date

#### Scenario: Date matches the previous photo
- **WHEN** the current photo's date is the same as the date of the photo immediately before it in the configured order
- **THEN** the system does not display the new-day indicator

#### Scenario: Indicator reflects display order, not calendar uniqueness
- **WHEN** the configuration uses `layout.order: alphabetical` and consecutive photos in that order have different dates that are not chronologically adjacent
- **THEN** the system still displays the new-day indicator, since it reflects a change from the previously displayed photo rather than a claim that the date is unique across the whole book

#### Scenario: Grouping uses best-available date even when display falls back to filename
- **WHEN** a photo has no EXIF capture date and is therefore shown with its filename instead of a date
- **THEN** the system still uses that photo's best-available date (falling back to the photo file's own timestamp) to determine whether the new-day indicator applies, comparing it the same way as for photos with a known capture date

### Requirement: Report startup errors clearly
The system SHALL report a clear error and refuse to start the editing session if the configured file cannot be loaded or its photo path cannot be read.

#### Scenario: Invalid or missing configuration file
- **WHEN** the editor is started with a configuration file that does not exist or fails validation
- **THEN** the system reports a clear error identifying the problem and does not start the editing session

#### Scenario: Inaccessible photo directory
- **WHEN** the configuration's photo path does not exist or is not readable
- **THEN** the system reports a clear error identifying the problem and does not start the editing session
