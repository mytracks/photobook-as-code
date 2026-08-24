## MODIFIED Requirements

### Requirement: Display the current photo's date prominently
The system SHALL display the current photo's date in a prominent position centered above the photo, using the photo's real capture date when known, formatted according to the viewing browser's locale, and SHALL show the photo's filename in that position instead when no real capture date is known.

#### Scenario: Capture date is known
- **WHEN** the current photo has a known capture date (from its embedded EXIF metadata)
- **THEN** the system displays that date, centered above the photo, formatted to include the day of the week, using the date and time formatting conventions of the browser's configured locale

#### Scenario: Capture date is unknown
- **WHEN** the current photo has no embedded capture date
- **THEN** the system displays the photo's filename in that position instead of a date, rather than presenting an unverified filesystem date as if it were the capture date

#### Scenario: Formatting follows the browser's locale
- **WHEN** two users with different browser locale settings view the same photo's date
- **THEN** each sees the date and time formatted according to their own browser's locale (for example, weekday/month names, date component order, and 12-hour vs. 24-hour time), without needing to configure anything in the editor itself

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

## REMOVED Requirements

### Requirement: Navigate photos in configured order
**Reason**: Replaced by "Navigate between items" (see ADDED Requirements), where navigation is driven by always-visible previous/next controls in the page header instead of full-height hover click zones overlaid on the photo. The hover zones depended on a photo being present to darken on hover, which made them invisible on title pages with no photo - removing them outright (rather than fixing them in place) was the chosen direction.
**Migration**: No action needed. Keyboard shortcut navigation (arrow keys, Cmd/Ctrl+Enter) is unaffected. Any user relying on clicking the left/right half of the photo to navigate now uses the header's previous/next controls instead.

## ADDED Requirements

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
