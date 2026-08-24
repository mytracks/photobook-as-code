## MODIFIED Requirements

### Requirement: Navigate photos in configured order
The system SHALL let the user move forward and backward through the items of the configured photobook - photos and titles, interleaved in the same merged order the photobook renderer would use for that configuration - one item at a time. The system SHALL provide full-height click zones and a keyboard shortcut for this navigation, both usable regardless of where the page's focus currently is and regardless of whether the current or adjacent item is a photo or a title. The keyboard shortcut SHALL NOT intercept key combinations that carry native text-editing meaning inside a text field.

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

#### Scenario: Full-height click zones
- **WHEN** the user clicks anywhere within the left or right edge band of the current item's display area, spanning its full height
- **THEN** the system navigates to the previous item (left band) or next item (right band), applying the same first/last boundary rule as other navigation

#### Scenario: Keyboard shortcut navigates regardless of focus
- **WHEN** the user presses Cmd+Enter or Ctrl+Enter (either modifier accepted on any platform), including while a caption or title text field has focus
- **THEN** the system navigates to the next item, saving any pending text edit first as it does for other navigation actions

#### Scenario: Keyboard shortcut navigates backward with Shift
- **WHEN** the user presses Cmd+Shift+Enter or Ctrl+Shift+Enter, including while a caption or title text field has focus
- **THEN** the system navigates to the previous item, saving any pending text edit first as it does for other navigation actions

#### Scenario: Native text-editing shortcuts are not intercepted
- **WHEN** the user presses Cmd+Left Arrow, Cmd+Right Arrow, Ctrl+Left Arrow, or Ctrl+Right Arrow (with or without Shift held) while a caption or title text field has focus
- **THEN** the system does not navigate to a different item, and the browser's native text-editing behavior for that combination is left to run unmodified

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

## ADDED Requirements

### Requirement: Display title items without a photo
The system SHALL display a title item without a photo frame or image, showing only its editable title content and the actions that apply to a title.

#### Scenario: Title item has no image
- **WHEN** the user navigates to an item that is a title
- **THEN** the system does not display a photo image or reserve image display space for that item

#### Scenario: Caption field is photo-specific
- **WHEN** the user navigates to an item that is a title
- **THEN** the system does not display the photo caption field, since a title has no associated photo to caption

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
The system SHALL let the user, while viewing a photo item, create a new title positioned immediately before that photo in the item sequence, and SHALL navigate the user to the newly created title so its content can be edited immediately.

#### Scenario: Add title from a photo
- **WHEN** the user is viewing a photo and requests to add a title
- **THEN** the system creates a new `text_labels` entry with an empty `title` value and navigates the user to it, positioned immediately before that photo in the item sequence

#### Scenario: New title is timestamped to the photo
- **WHEN** the system creates a new title from a photo
- **THEN** the new entry's timestamp is set to that photo's own timestamp, so it sorts immediately before that specific photo and no other

#### Scenario: Add-title action is not available while viewing a title
- **WHEN** the user is viewing a title item
- **THEN** the system does not offer the add-title action from that item

### Requirement: Delete a title
The system SHALL let the user, while viewing a title item, delete that title's entry from the configuration file, and SHALL navigate to the photo that followed it in the item sequence, if one exists.

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
