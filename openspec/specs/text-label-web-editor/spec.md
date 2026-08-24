## Purpose

A browser-based editor that lets a user page through the photos of a single photobook configuration and write the `text` content of each photo's `text_labels` entry directly, saving edits back into the same YAML file.

## Requirements

### Requirement: Navigate between items
The system SHALL let the user move forward and backward through the items of the configured photobook - photos and titles, interleaved in the same merged order the photobook renderer would use for that configuration - one item at a time. The system SHALL provide always-visible previous/next controls in the page header and a keyboard shortcut for this navigation, both usable regardless of where the page's focus currently is and regardless of whether the current or adjacent item is a photo or a title. The keyboard shortcut SHALL NOT intercept key combinations that carry native text-editing meaning inside a text field.

#### Scenario: Sequential navigation
- **WHEN** the user requests the next or previous item
- **THEN** the system displays the adjacent item (photo or title) in the configured order

#### Scenario: First and last photo boundaries
- **WHEN** the user is viewing the first or last item in the order
- **THEN** the system does not allow navigating before the first or after the last item

#### Scenario: Order matches final photobook order
- **WHEN** the configuration specifies `layout.order: date` or `layout.order: alphabetical`, with or without `title` entries in `text_labels`
- **THEN** the item sequence shown in the editor matches the order photos and titles would be laid out in the generated photobook

#### Scenario: Titles appear in their merged position
- **WHEN** the configuration's `text_labels` contains one or more `title` entries
- **THEN** each title appears in the editor's sequence immediately before the first photo whose timestamp is at or after the title's own timestamp, matching the renderer's placement, and is appended at the end of the sequence if no such photo exists

#### Scenario: Header navigation controls
- **WHEN** the user views any item
- **THEN** the system displays previous and next navigation controls in the page header, visible without requiring the pointer to hover over the item's display area

#### Scenario: Keyboard shortcut navigates regardless of focus
- **WHEN** the user presses Cmd+Enter or Ctrl+Enter (either modifier accepted on any platform), including while a caption or title text field has focus
- **THEN** the system navigates to the next item, saving any pending text edit first as it does for other navigation actions

#### Scenario: Keyboard shortcut navigates backward with Shift
- **WHEN** the user presses Cmd+Shift+Enter or Ctrl+Shift+Enter, including while a caption or title text field has focus
- **THEN** the system navigates to the previous item, saving any pending text edit first as it does for other navigation actions

#### Scenario: Native text-editing shortcuts are not intercepted
- **WHEN** the user presses Cmd+Left Arrow, Cmd+Right Arrow, Ctrl+Left Arrow, or Ctrl+Right Arrow (with or without Shift held) while a caption or title text field has focus
- **THEN** the system does not navigate to a different item, and the browser's native text-editing behavior for that combination is left to run unmodified

#### Scenario: Smooth transition on navigation
- **WHEN** the user navigates to a different item by any means (previous/next controls, jump-to-number, keyboard shortcut, or after adding/deleting a title)
- **THEN** the system transitions to the new item with a smooth visual transition rather than an abrupt, unstyled page reload

### Requirement: Jump directly to an item by number
The system SHALL let the user navigate directly to any item by entering its position number, activated from the header's item position indicator.

#### Scenario: Activate the jump control
- **WHEN** the user clicks the item position indicator (for example, "2 / 264")
- **THEN** the system replaces it in place with a text input pre-filled with the current position, ready for the user to type a new number

#### Scenario: Confirm a valid position
- **WHEN** the user enters a number between 1 and the total item count and confirms it
- **THEN** the system saves any pending text edit and navigates to the item at that position, the same way other navigation actions do

#### Scenario: Reject an out-of-range or non-numeric entry
- **WHEN** the user enters a number outside the valid range, or non-numeric text, and confirms it
- **THEN** the system does not navigate, and returns the control to a state where the user can correct the entry

#### Scenario: Cancel without navigating
- **WHEN** the user dismisses the jump control (for example, by pressing Escape or moving focus away) without confirming a new position
- **THEN** the system returns to displaying the static position indicator and does not navigate

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
The system SHALL modify only the specific entry being edited, added, or deleted when saving, leaving all other content in the configuration file unchanged.

#### Scenario: Comments are preserved
- **WHEN** the configuration file contains comments on `text_labels` entries (for example, source filenames)
- **THEN** saving an edit to one entry's text or title leaves every other entry's comments intact

#### Scenario: Title entries are untouched
- **WHEN** the configuration file's `text_labels` section contains `title` entries interspersed with `text` entries
- **THEN** saving a `text` caption edit does not alter, move, or remove any `title` entry

#### Scenario: Other entries are untouched by title edits
- **WHEN** the user edits one title's content
- **THEN** only that entry's `title` value changes; every other `text_labels` entry - captions and other titles alike - is unchanged

#### Scenario: Other entries are untouched by title deletion
- **WHEN** the user deletes a title
- **THEN** only that entry is removed from `text_labels`; every other entry's content, comments, and order are unchanged

#### Scenario: Other configuration sections are untouched
- **WHEN** the configuration file contains `photos`, `output`, `layout`, or `theme` sections
- **THEN** saving a text or title edit, adding a title, or deleting a title preserves those sections' content and formatting, with the sole known exception of collapsing a redundant blank line within a run of multiple blank-line-separated comment-only groups trailing a mapping's last key (an inherent limitation of the YAML round-trip approach; see design.md)

#### Scenario: Ordering and formatting of untouched entries preserved
- **WHEN** the configuration file has a specific order and formatting for its `text_labels` entries
- **THEN** saving an edit to, adding, or deleting one entry does not reorder or reformat the other entries

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

### Requirement: Display the current item's date prominently
The system SHALL display the current item's date - whether the item is a photo or a title - in a prominent position centered above it, formatted according to the viewing browser's locale. For a photo, the system SHALL use the photo's real capture date when known and SHALL show the photo's filename in that position instead when no real capture date is known. For a title, the system SHALL use the title's own timestamp, which is always present.

#### Scenario: Photo capture date is known
- **WHEN** the current item is a photo with a known capture date (from its embedded EXIF metadata)
- **THEN** the system displays that date, centered above the photo, formatted to include the day of the week, using the date and time formatting conventions of the browser's configured locale

#### Scenario: Photo capture date is unknown
- **WHEN** the current item is a photo with no embedded capture date
- **THEN** the system displays the photo's filename in that position instead of a date, rather than presenting an unverified filesystem date as if it were the capture date

#### Scenario: Title date is always shown
- **WHEN** the current item is a title
- **THEN** the system displays that title's own timestamp, centered above it, formatted the same way as a photo's known capture date, since a title's timestamp is always present and never falls back to a filename-like label

#### Scenario: Formatting follows the browser's locale
- **WHEN** two users with different browser locale settings view the same item's date, whether it belongs to a photo or a title
- **THEN** each sees the date and time formatted according to their own browser's locale (for example, weekday/month names, date component order, and 12-hour vs. 24-hour time), without needing to configure anything in the editor itself

### Requirement: Indicate the first item of a new day
The system SHALL display a clearly visible indicator (an icon with accompanying text) next to the date whenever the current item's date differs from the previously displayed item's date in the configured order, considering photos and titles together as one sequence. The indicator SHALL be positioned to the left of the date/time and rendered as a filled, accent-colored badge so it reads as visually prominent rather than secondary.

#### Scenario: Date changes from the previous item
- **WHEN** the current item's date differs from the date of the item immediately before it in the configured order (whether that item is a photo or a title), or the current item is the first item in the order
- **THEN** the system displays the new-day indicator next to the date

#### Scenario: Date matches the previous item
- **WHEN** the current item's date is the same as the date of the item immediately before it in the configured order
- **THEN** the system does not display the new-day indicator

#### Scenario: A title as the first item of a new day carries the indicator, not the photo after it
- **WHEN** a title is the first item in the order whose date differs from the item before it, and one or more photos sharing the title's date immediately follow it
- **THEN** the system displays the new-day indicator on the title, and does not display it on the photos that follow, even though those photos' dates also differ from the item that preceded the title

#### Scenario: Indicator reflects display order, not calendar uniqueness
- **WHEN** the configuration uses `layout.order: alphabetical` and consecutive items in that order have different dates that are not chronologically adjacent
- **THEN** the system still displays the new-day indicator, since it reflects a change from the previously displayed item rather than a claim that the date is unique across the whole book

#### Scenario: Grouping uses best-available date even when display falls back to filename
- **WHEN** a photo has no EXIF capture date and is therefore shown with its filename instead of a date
- **THEN** the system still uses that photo's best-available date (falling back to file_modified) to determine whether the new-day indicator applies, comparing it the same way as for photos with a known capture date and for titles

### Requirement: Report startup errors clearly
The system SHALL report a clear error and refuse to start the editing session if the configured file cannot be loaded or its photo path cannot be read.

#### Scenario: Invalid or missing configuration file
- **WHEN** the editor is started with a configuration file that does not exist or fails validation
- **THEN** the system reports a clear error identifying the problem and does not start the editing session

#### Scenario: Inaccessible photo directory
- **WHEN** the configuration's photo path does not exist or is not readable
- **THEN** the system reports a clear error identifying the problem and does not start the editing session

### Requirement: Display title items without a photo
The system SHALL display a title item without a photo frame or image, showing only its editable title content and the actions that apply to a title. The area that would otherwise hold a photo SHALL still be visually bounded (a distinct background and/or border) rather than blank space indistinguishable from the surrounding page.

#### Scenario: Title item has no image
- **WHEN** the user navigates to an item that is a title
- **THEN** the system does not display a photo image or reserve image display space for that item

#### Scenario: Caption field is photo-specific
- **WHEN** the user navigates to an item that is a title
- **THEN** the system does not display the photo caption field, since a title has no associated photo to caption

#### Scenario: Empty area reads as an intentional slot
- **WHEN** the user navigates to an item that is a title
- **THEN** the area above the title's text field has a visible boundary distinguishing it from the page background, rather than being indistinguishable blank space

### Requirement: Edit and autosave title content
The system SHALL display an editable field containing the current title item's content (its `title` value), and SHALL save changes to that content without requiring an explicit save action, the same autosave behavior used for photo captions.

#### Scenario: Existing title content is shown for editing
- **WHEN** the user views a title item
- **THEN** the editable field is pre-filled with that title's current content, unmodified

#### Scenario: Autosave on navigating away
- **WHEN** the user has changed a title's content and then navigates to another item or moves focus away from the field
- **THEN** the system saves the updated content to the YAML configuration file before the navigation completes, and confirms the save to the user

#### Scenario: No changes made
- **WHEN** the user views a title's content and navigates away without changing it
- **THEN** the system does not rewrite the configuration file

#### Scenario: Raw Markdown, no rendering
- **WHEN** the user types Markdown syntax (including heading markers) into a title's text field
- **THEN** the system stores the raw text as typed and does not render or preview it as formatted output

### Requirement: Add a title before the current photo
The system SHALL let the user, while viewing a photo item, create a new title positioned immediately before that photo in the item sequence, via a labeled control presented in the page header rather than a large, permanently visible button beneath the caption field, and SHALL navigate the user to the newly created title so its content can be edited immediately.

#### Scenario: Add title from a photo
- **WHEN** the user is viewing a photo and requests to add a title
- **THEN** the system creates a new `text_labels` entry with an empty `title` value and navigates the user to it, positioned immediately before that photo in the item sequence

#### Scenario: New title is timestamped to the photo
- **WHEN** the system creates a new title from a photo
- **THEN** the new entry's timestamp is set to that photo's own timestamp, so it sorts immediately before that specific photo and no other

#### Scenario: Add-title action is not available while viewing a title
- **WHEN** the user is viewing a title item
- **THEN** the system does not offer the add-title action from that item

#### Scenario: Add-title control is unobtrusive
- **WHEN** the user views a photo item
- **THEN** the add-title control is presented as a small labeled control in the page header, not as a large bordered button occupying its own row beneath the caption field

### Requirement: Delete a title
The system SHALL let the user, while viewing a title item, delete that title's entry from the configuration file via a labeled control presented in the page header rather than a large, permanently visible button beneath the title field, and SHALL navigate to the photo that followed it in the item sequence, if one exists.

#### Scenario: Delete removes the entry
- **WHEN** the user is viewing a title and requests to delete it
- **THEN** the system removes that title's entry from `text_labels` and saves the configuration file

#### Scenario: Navigates to the following photo
- **WHEN** the user deletes a title that has a photo after it in the item sequence
- **THEN** the system navigates the user to that following photo after the deletion completes

#### Scenario: Deleting the last item in the sequence
- **WHEN** the user deletes a title that is the last item in the item sequence
- **THEN** the system navigates the user to the item that is now last (previously immediately before the deleted title), or to the editor's start if the sequence is now empty

#### Scenario: Delete action is not available while viewing a photo
- **WHEN** the user is viewing a photo item
- **THEN** the system does not offer the delete-title action from that item

#### Scenario: Delete-title control is unobtrusive
- **WHEN** the user views a title item
- **THEN** the delete-title control is presented as a small labeled control in the page header, not as a large bordered button occupying its own row beneath the title field
