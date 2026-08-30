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
- **WHEN** the user navigates to a different item by any means (previous/next controls, jump-to-number, keyboard shortcut, a filmstrip item, or after adding/deleting a title)
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

### Requirement: Reverse-geocode button availability
The system SHALL present a reverse-geocode control in the page header, positioned before the add-title control, for any photo item, and SHALL enable it only when that photo's EXIF data contains a GPS location; the control SHALL NOT be presented for title items, which have no associated photo or EXIF data. The control SHALL be icon-only, carrying no visible text, and SHALL identify itself to assistive technology via an accessible label.

#### Scenario: Photo with a GPS location
- **WHEN** the user views a photo whose EXIF data contains a GPS location
- **THEN** the reverse-geocode control is displayed in the page header, before the add-title control, and is enabled

#### Scenario: Photo without a GPS location
- **WHEN** the user views a photo whose EXIF data contains no GPS location
- **THEN** the reverse-geocode control is displayed but disabled, and communicates the reason it is disabled to the user

#### Scenario: Title item
- **WHEN** the user views a title item
- **THEN** the reverse-geocode control is not displayed

### Requirement: Reverse-geocode the current photo without blocking the page
The system SHALL, when the user activates an enabled reverse-geocode control, send the request asynchronously so the page remains responsive and usable while it is in flight, and SHALL visually indicate the in-progress state by replacing the control's icon with a loading indicator and disabling the control until the request completes (successfully or not).

#### Scenario: Request is asynchronous
- **WHEN** the user activates the reverse-geocode control
- **THEN** the system sends the request without blocking navigation, text editing, or any other page interaction

#### Scenario: Icon reflects the in-progress request
- **WHEN** a reverse-geocode request is in flight
- **THEN** the control displays a loading indicator in place of its normal icon, and is disabled

#### Scenario: Icon reverts when the request completes
- **WHEN** a reverse-geocode request completes, whether successfully or not
- **THEN** the control's icon reverts to its normal state, and the control becomes enabled again if the current photo still has a GPS location and no other request is in flight

### Requirement: Resolve a locale-appropriate place name for the location
The system SHALL resolve the current photo's GPS location to a human-readable place name, preferring the name of a specific named place near the coordinates (for example, a landmark or building) when one is known, and falling back to a city-and-country name when no specific named place is known. The resolved name SHALL be formatted in the language of the requesting browser's own locale, matching the locale-awareness already used for the item's displayed date.

#### Scenario: A named place is known near the coordinates
- **WHEN** the current photo's GPS location resolves to a specific named place (for example, a landmark or building)
- **THEN** the resolved text is that place's name

#### Scenario: No named place is known near the coordinates
- **WHEN** the current photo's GPS location does not resolve to any specific named place
- **THEN** the resolved text is the city and country nearest the coordinates

#### Scenario: Result matches the browser's locale
- **WHEN** two users with different browser locale settings reverse-geocode the same photo
- **THEN** each receives the resolved place name in their own browser's locale, without configuring anything in the editor

### Requirement: Insert the resolved location into the caption
The system SHALL insert a successfully resolved location into the current photo's caption field: replacing the field's content when it was empty, or appending the resolved text to the end of the field's existing content preceded by a newline when it was not empty. The system SHALL save the updated caption immediately, without requiring the user to take a separate save action.

#### Scenario: Caption field is empty
- **WHEN** a location is resolved for a photo whose caption field is empty
- **THEN** the resolved text becomes the caption field's entire content

#### Scenario: Caption field already has content
- **WHEN** a location is resolved for a photo whose caption field already has content
- **THEN** the resolved text is appended to the end of the existing content, separated from it by a newline

#### Scenario: Result is saved without a separate action
- **WHEN** a location is inserted into the caption field
- **THEN** the system saves the updated caption to the configuration file without requiring the user to move focus away from the field or take any other explicit save action

### Requirement: Report reverse-geocoding failures without altering the caption
The system SHALL, when a reverse-geocode request fails to produce a location (due to a network error, a service error, or no resolvable place for the given coordinates), leave the caption field's content unchanged and inform the user that the request did not succeed.

#### Scenario: Network or service error
- **WHEN** a reverse-geocode request fails due to a network or service error
- **THEN** the system leaves the caption field unchanged and displays a message indicating the request failed

#### Scenario: No location can be resolved
- **WHEN** a reverse-geocode request completes but no location can be resolved for the given coordinates
- **THEN** the system leaves the caption field unchanged and displays a message indicating no location was found

### Requirement: Activate the reverse-geocode control via keyboard
The system SHALL let the user activate an enabled reverse-geocode control from the keyboard, without needing the mouse. The bare `G` key SHALL activate it when focus is not in the caption field or the jump-to-item field. Cmd+G or Ctrl+G (either modifier accepted on any platform) SHALL activate it regardless of where focus currently is, including while the caption field has focus. Neither form SHALL have any effect while the control is disabled or a request is already in flight.

#### Scenario: Bare shortcut activates the control outside text fields
- **WHEN** the user presses G while focus is not in the caption field or the jump-to-item field, and the reverse-geocode control is enabled
- **THEN** the system activates the reverse-geocode control as if it had been clicked

#### Scenario: Modifier shortcut activates the control while editing the caption
- **WHEN** the user presses Cmd+G or Ctrl+G while the caption field has focus, and the reverse-geocode control is enabled
- **THEN** the system activates the reverse-geocode control, inserting the resolved location into the caption per the insertion rule, and returns focus to the caption field afterward

#### Scenario: Shortcut has no effect when the control is unavailable
- **WHEN** the user presses G, Cmd+G, or Ctrl+G while the reverse-geocode control is disabled or a request is already in flight
- **THEN** the system takes no action

### Requirement: Access the batch operation from the editor
The system SHALL present a control in the per-item editor's header that navigates to a batch settings page, available regardless of whether the current item is a photo or a title.

#### Scenario: Batch control is always available
- **WHEN** the user views any item in the per-item editor
- **THEN** the header presents a control that navigates to the batch settings page

### Requirement: Configure the batch operation before running it
The system SHALL present a settings page, before any batch operation runs, letting the user independently enable or disable each of the following, with the settings page defaulting to both disabled:
- Inserting a date for each new day, with a choice of destination: a plain-text label on the first photo of that day, or a new title item.
- Reverse-geocoding every photo that has a GPS location, with a choice of strictness: landmarks/points of interest only, or landmarks falling back to a city and country name.

A single setting, shared by both of the above, SHALL control what happens when the target caption or title already has content: leave it unchanged, or add to it.

#### Scenario: Date destination only shown when date insertion is enabled
- **WHEN** the user enables date insertion on the settings page
- **THEN** the system presents the choice between text-label and title destinations

#### Scenario: Geocoding strictness only shown when geocoding is enabled
- **WHEN** the user enables reverse-geocoding on the settings page
- **THEN** the system presents the choice between POI-only and POI-with-city-fallback strictness

#### Scenario: Skip-or-append setting is always shown
- **WHEN** the user views the batch settings page
- **THEN** the system presents the shared skip-or-append setting regardless of which other options are enabled

### Requirement: Require at least one enabled action to start
The system SHALL NOT allow starting a batch operation for which both date insertion and reverse-geocoding are disabled.

#### Scenario: Both actions disabled
- **WHEN** the user leaves both date insertion and reverse-geocoding disabled
- **THEN** the system does not allow starting the batch operation

### Requirement: Determine which items are eligible for date-on-new-day insertion
When date insertion is enabled, the system SHALL consider an item eligible for a new date marker exactly where the per-item editor's own new-day indicator would appear - the first item (photo or title) whose date differs from the previously displayed item's date in the merged photo-and-title sequence, evaluated across the entire book from its first item to its last.

#### Scenario: First photo of a new day, no title at that boundary
- **WHEN** date insertion is enabled and a photo is the first item of a new day, with no title occupying that position
- **THEN** the system treats that photo as eligible for a new date marker

#### Scenario: A title already occupies the day boundary
- **WHEN** date insertion is enabled and a title is already the first item of a new day
- **THEN** the system treats that title, not the photo that follows it, as eligible for a new date marker

### Requirement: Insert the date as a text label on the eligible photo
When date insertion is enabled with the text-label destination, the system SHALL insert the formatted date into the caption of an eligible item only when that item is a photo (not a title), leaving any day whose eligible item is a title untouched by this destination.

#### Scenario: Eligible item is a photo
- **WHEN** text-label destination is selected and the eligible item for a new day is a photo
- **THEN** the system inserts the formatted date into that photo's caption, subject to the skip-or-append setting

#### Scenario: Eligible item is a title
- **WHEN** text-label destination is selected and the eligible item for a new day is a title
- **THEN** the system does not insert a date label onto the photo that follows the title

### Requirement: Insert the date as a title on the eligible item
When date insertion is enabled with the title destination, the system SHALL insert the formatted date as a title positioned at the eligible item's position: creating a new title (timestamped so it sorts immediately before the eligible photo) when the eligible item is a photo, or adding to the eligible item's own content when it is already a title, subject to the skip-or-append setting.

#### Scenario: Eligible item is a photo
- **WHEN** title destination is selected and the eligible item for a new day is a photo with no title before it
- **THEN** the system creates a new title, positioned immediately before that photo, containing the formatted date

#### Scenario: Eligible item is already a title, skip selected
- **WHEN** title destination and the skip setting are selected, and the eligible item for a new day is already a title
- **THEN** the system leaves that title's content unchanged and does not create a second title for the same day

#### Scenario: Eligible item is already a title, append selected
- **WHEN** title destination and the append setting are selected, and the eligible item for a new day is already a title
- **THEN** the system adds the formatted date as the first line of that title's existing content, leaving the rest of its content unchanged

### Requirement: Format the inserted date in the requesting browser's locale
The system SHALL format an inserted date using the language of the browser that started the batch operation, showing the day of month, full month name, and year - without a weekday name or time of day.

#### Scenario: Date formatted for the starting browser's locale
- **WHEN** a batch operation is started from a browser configured for a given language
- **THEN** every date the batch inserts during that run is formatted in that language, as day, full month name, and year only

### Requirement: Determine which photos are eligible for batch reverse-geocoding
When reverse-geocoding is enabled, the system SHALL consider every photo in the book whose EXIF data contains a GPS location eligible, independent of whether it is also eligible for a date marker; a photo with no GPS location is not eligible and is not counted as a failure.

#### Scenario: Photo has a GPS location
- **WHEN** reverse-geocoding is enabled and a photo's EXIF data contains a GPS location
- **THEN** the system attempts to resolve and insert a location for that photo

#### Scenario: Photo has no GPS location
- **WHEN** reverse-geocoding is enabled and a photo's EXIF data contains no GPS location
- **THEN** the system does not attempt to resolve a location for that photo, and does not count it as a failure

### Requirement: Resolve each eligible photo's location under the configured strictness
The system SHALL resolve an eligible photo's location the same way the single-photo reverse-geocode feature does when POI-with-city-fallback strictness is selected. When POI-only strictness is selected, the system SHALL resolve only a specific named place (for example, a landmark or building) and SHALL treat a photo with no such named place nearby as unresolved, without falling back to a city or country name.

#### Scenario: POI-with-city-fallback strictness
- **WHEN** POI-with-city-fallback strictness is selected and a photo's GPS location resolves to either a named place or, absent one, a city and country
- **THEN** the system inserts that resolved text, matching the single-photo feature's resolution behavior

#### Scenario: POI-only strictness, a named place is found
- **WHEN** POI-only strictness is selected and a photo's GPS location resolves to a specific named place
- **THEN** the system inserts that place's name

#### Scenario: POI-only strictness, no named place is found
- **WHEN** POI-only strictness is selected and a photo's GPS location resolves only to a city, town, village, or country, with no specific named place
- **THEN** the system leaves that photo's caption unchanged and does not count it as a failure

### Requirement: Apply the shared skip-or-append setting to pre-existing content
The system SHALL evaluate the skip-or-append setting against each target's content as it stood before the batch operation began: when skip is selected, the system SHALL leave a caption or title that already had content unchanged; when append is selected, the system SHALL add to that existing content the same way the single-photo reverse-geocode feature already does for captions - appended after a newline - and, for a title, as described under title-destination date insertion.

#### Scenario: Skip selected, target already has content
- **WHEN** skip is selected and a photo's caption (or a title's content) already had text before the batch operation began
- **THEN** the system does not modify that caption or title

#### Scenario: Append selected, target already has content
- **WHEN** append is selected and a photo's caption already had text before the batch operation began
- **THEN** the system appends the new text after a newline, leaving the existing text unchanged

#### Scenario: Target had no content
- **WHEN** a photo's caption (or a title's content) had no text before the batch operation began, regardless of the skip-or-append setting
- **THEN** the system inserts the new text as that caption's or title's entire content

### Requirement: Combine date and geocoding results within the same run
When a single photo is eligible for both a text-label date marker and reverse-geocoding in the same batch run, the system SHALL insert both into that photo's caption - the date first, the geocoded location appended below it - regardless of the skip-or-append setting, which governs only content that existed before the batch operation began.

#### Scenario: Photo eligible for both in the same run
- **WHEN** a photo is the eligible item for a new day under text-label destination and also has a GPS location resolved during the same run
- **THEN** the system inserts the formatted date followed by the resolved location, both in that photo's caption

### Requirement: Suppress a duplicate reverse-geocoded location within one run
The system SHALL insert a given resolved location text into at most one photo's caption per batch run: the first eligible photo that resolves to that exact text has it inserted, and any later eligible photo in the same run that resolves to the same text has that text withheld. Withholding a duplicate location text SHALL NOT affect whether a date marker is inserted for that same photo.

#### Scenario: A later photo resolves to the same text as an earlier one
- **WHEN** a batch run's reverse-geocoding resolves the same location text for more than one eligible photo
- **THEN** the system inserts that text only into the first such photo, and withholds it from every later photo that resolves to the same text in that run

#### Scenario: Duplicate suppression leaves an unrelated date marker untouched
- **WHEN** a photo whose resolved location text duplicates an earlier photo's is also eligible for a text-label date marker in the same run
- **THEN** the system still inserts the date marker for that photo, withholding only the duplicate location text

#### Scenario: Duplicate suppression does not carry over to a later run
- **WHEN** the user starts a new batch operation after a previous one has finished
- **THEN** the system does not treat a location text used during the previous run as a duplicate in the new run

### Requirement: Rate-limit reverse-geocoding requests
The system SHALL wait at least one second between the start of one reverse-geocoding request and the start of the next, across all callers of the reverse-geocoding service (the single-photo button and the batch operation alike), matching the public geocoding service's documented usage limit.

#### Scenario: Batch operation reverse-geocodes multiple photos
- **WHEN** the batch operation resolves locations for more than one photo
- **THEN** the system waits at least one second between the start of each reverse-geocoding request

### Requirement: Run the batch operation as a non-blocking background job
The system SHALL start a batch operation as a background job and return the user to a progress view immediately, without requiring the browser to hold open a single long-running request for the operation's full duration.

#### Scenario: Starting the batch returns control immediately
- **WHEN** the user starts a batch operation from the settings page
- **THEN** the system begins processing in the background and shows a progress view without waiting for the operation to finish

### Requirement: Report batch progress while it runs
The system SHALL show, while a batch operation is running, how many items have been processed out of the total, and counts of items updated, skipped due to existing content, skipped due to no resolvable location (POI-only strictness), skipped due to a duplicate resolved location, and failed due to an error.

#### Scenario: Progress view updates as the batch runs
- **WHEN** the user views the progress page while a batch operation is running
- **THEN** the system shows the current processed-of-total count and the running counts for updated, skipped due to existing content, no-location-found, duplicate-location, and failed items

### Requirement: Allow cancelling a running batch operation
The system SHALL let the user cancel a running batch operation from the progress view; a cancelled operation SHALL stop starting new item updates but SHALL NOT undo items it already saved.

#### Scenario: User cancels a running batch
- **WHEN** the user cancels a batch operation while it is running
- **THEN** the system stops processing further items, and every item already saved before the cancellation remains saved

### Requirement: Persist each processed item immediately
The system SHALL save each item's update to the configuration file as soon as that item is processed, rather than deferring all updates to the end of the batch operation.

#### Scenario: Batch operation is interrupted
- **WHEN** a batch operation is cancelled or stops before reaching the end of the book
- **THEN** every item processed before the interruption has already been saved to the configuration file

### Requirement: Batch operation covers the entire book
The system SHALL run a batch operation over every item in the book, from its first item to its last, independent of which item is currently open in the per-item editor when the batch is started.

#### Scenario: Batch started while viewing an item partway through the book
- **WHEN** the user starts a batch operation while viewing an item that is neither the first nor the last in the book
- **THEN** the system processes every eligible item in the book, not only those after the current item

### Requirement: Open-in-Maps button availability
The system SHALL present an "Open in Maps" control in the page header, positioned immediately after the reverse-geocode control and before the add-title control, for any photo item, and SHALL enable it only when that photo's EXIF data contains a GPS location; the control SHALL NOT be presented for title items, which have no associated photo or EXIF data. The control SHALL be icon-only, carrying no visible text, and SHALL identify itself to assistive technology via an accessible label.

#### Scenario: Photo with a GPS location
- **WHEN** the user views a photo whose EXIF data contains a GPS location
- **THEN** the open-in-Maps control is displayed in the page header, immediately after the reverse-geocode control and before the add-title control, and is enabled

#### Scenario: Photo without a GPS location
- **WHEN** the user views a photo whose EXIF data contains no GPS location
- **THEN** the open-in-Maps control is displayed but disabled, and communicates the reason it is disabled to the user

#### Scenario: Title item
- **WHEN** the user views a title item
- **THEN** the open-in-Maps control is not displayed

#### Scenario: Activating the control while disabled has no effect
- **WHEN** the user activates the open-in-Maps control while it is disabled
- **THEN** the system takes no action and does not open a new tab

### Requirement: Open the current photo's location in a maps application
The system SHALL, when the user activates an enabled open-in-Maps control, immediately open a new browser tab pointed at the current photo's GPS coordinates using an Apple Maps web URL (`https://maps.apple.com/?ll=<lat>,<lon>&q=<lat>,<lon>`, with `<lat>` and `<lon>` the photo's decimal-degree coordinates), without making any request to the application's own server.

#### Scenario: Activation opens a new tab centered on the photo's coordinates
- **WHEN** the user activates an enabled open-in-Maps control
- **THEN** the system opens a new browser tab navigating to the Apple Maps URL for that photo's GPS coordinates

#### Scenario: No server round trip or loading state
- **WHEN** the user activates an enabled open-in-Maps control
- **THEN** the system opens the new tab immediately, without contacting the application's own server and without displaying a loading indicator on the control

#### Scenario: Native maps app opens where available
- **WHEN** the user activates an enabled open-in-Maps control in a browser and operating system where the Apple Maps URL resolves to an installed native maps application
- **THEN** the operating system may open that application instead of displaying the page in the new browser tab, and the system does not attempt to detect or control this platform behavior

### Requirement: Activate the open-in-Maps control via keyboard
The system SHALL let the user activate an enabled open-in-Maps control from the keyboard, without needing the mouse. Alt+G (Option+G on macOS) SHALL activate it regardless of where focus currently is, including while the caption field has focus. The shortcut SHALL have no effect while the control is disabled, and SHALL NOT also trigger the reverse-geocode control's own "G" shortcut.

#### Scenario: Modifier shortcut activates the control regardless of focus
- **WHEN** the user presses Alt+G, including while the caption field has focus, and the open-in-Maps control is enabled
- **THEN** the system activates the open-in-Maps control as if it had been clicked, opening the Maps URL in a new tab

#### Scenario: Shortcut has no effect when the control is unavailable
- **WHEN** the user presses Alt+G while the open-in-Maps control is disabled
- **THEN** the system takes no action

#### Scenario: Does not also activate the reverse-geocode control
- **WHEN** the user presses Alt+G
- **THEN** the system does not activate the reverse-geocode control, even though both shortcuts share the "G" key

### Requirement: Display a filmstrip of all items for visual navigation
The system SHALL display a persistent, always-visible strip at the bottom of the per-item editor showing every item in the book's merged order (photos and titles), in a fixed-height, horizontally scrollable container, and SHALL let the user click any item in the strip to navigate to it.

#### Scenario: Filmstrip is always visible
- **WHEN** the user views any item in the per-item editor
- **THEN** the system displays the filmstrip below the caption field, with a fixed height that does not change as the user navigates

#### Scenario: Filmstrip contains every item
- **WHEN** the user views the filmstrip
- **THEN** it contains one cell for every item in the book's merged order, matching the same order used for previous/next navigation

#### Scenario: Clicking a filmstrip item navigates to it
- **WHEN** the user clicks a cell in the filmstrip
- **THEN** the system saves any pending text edit first, then navigates to that item, the same way other navigation actions do

#### Scenario: Filmstrip scrolls horizontally
- **WHEN** the book has more items than fit within the filmstrip's width
- **THEN** the user can scroll the filmstrip horizontally to reveal items outside the initially visible range

### Requirement: Filmstrip photo cells show only a thumbnail
The system SHALL render each photo item's filmstrip cell as a small thumbnail image of that photo, with no caption text or date displayed on the cell, other than the small caption-presence overlay described below.

#### Scenario: Photo cell shows a thumbnail
- **WHEN** a photo item appears in the filmstrip
- **THEN** its cell displays a thumbnail image of that photo and no caption or date text

### Requirement: Filmstrip photo cells indicate whether they have a caption
The system SHALL display a small "T" overlay badge on a photo's filmstrip cell when that photo has non-empty caption text, and SHALL NOT display it when the photo's caption is empty or absent. The badge SHALL NOT display the caption's own text content.

#### Scenario: Photo has a non-empty caption
- **WHEN** a photo item with non-empty caption text appears in the filmstrip
- **THEN** its cell displays a small "T" overlay badge over the thumbnail

#### Scenario: Photo has no caption or an empty caption
- **WHEN** a photo item with no associated caption, or an associated caption whose text is empty, appears in the filmstrip
- **THEN** its cell does not display the overlay badge

#### Scenario: Badge does not leak caption content
- **WHEN** a photo's filmstrip cell displays the caption-presence badge
- **THEN** the badge shows only the "T" glyph, never the caption's own text

### Requirement: Filmstrip title cells show a placeholder, not the title's text
The system SHALL render each title item's filmstrip cell as a bounded placeholder cell containing only a "T" glyph, visually distinct from a photo cell, without displaying the title's own text content.

#### Scenario: Title cell shows a placeholder
- **WHEN** a title item appears in the filmstrip
- **THEN** its cell displays a bounded placeholder containing the letter "T" and does not display the title's text content

### Requirement: Filmstrip indicates day boundaries
The system SHALL display a compact, date-labeled divider between two consecutive filmstrip cells whenever the later item's date differs from the earlier item's date, determined the same way as the per-item editor's own new-day indicator (considering photos and titles together as one sequence).

#### Scenario: Date changes between consecutive items
- **WHEN** two consecutive items in the filmstrip have different dates
- **THEN** the system displays a divider with a compact date label between their cells

#### Scenario: Date matches between consecutive items
- **WHEN** two consecutive items in the filmstrip have the same date
- **THEN** the system does not display a divider between their cells

### Requirement: Filmstrip highlights and tracks the current item
The system SHALL visually highlight the filmstrip cell for the item currently displayed in the per-item editor, and SHALL keep that highlight correct across every navigation trigger - filmstrip clicks, previous/next controls, keyboard shortcuts, jump-to-number, and adding or deleting a title.

#### Scenario: Current item is highlighted
- **WHEN** the user views any item
- **THEN** the filmstrip cell corresponding to that item is visually highlighted, distinguishing it from every other cell

#### Scenario: Highlight follows non-filmstrip navigation
- **WHEN** the user navigates using the header's previous/next controls, a keyboard shortcut, jump-to-number, or by adding or deleting a title
- **THEN** the filmstrip's highlighted cell updates to match the newly displayed item

#### Scenario: Current cell scrolls into view
- **WHEN** the editor loads a new item, by any navigation trigger
- **THEN** the system scrolls the filmstrip so the current item's cell is visible without requiring the user to scroll manually

### Requirement: Serve a small thumbnail image for filmstrip cells
The system SHALL serve each photo's filmstrip thumbnail at a substantially smaller size than the item's main display image, suitable for a strip that may contain hundreds of cells on the same page, without degrading the responsiveness of loading the currently displayed photo.

#### Scenario: Thumbnail is smaller than the main image
- **WHEN** the system serves a photo's filmstrip thumbnail
- **THEN** the served image is scaled to a small display size and does not require decoding or transferring the same amount of data as the item's main display image

### Requirement: Filmstrip cells are accessible to assistive technology
The system SHALL give each filmstrip cell an accessible name that identifies its item without relying on the visual thumbnail or "T" glyph alone.

#### Scenario: Photo cell accessible name
- **WHEN** a screen reader user reaches a photo's filmstrip cell
- **THEN** it announces an accessible name identifying it as that photo (for example, its filename or position), not merely an unlabeled image

#### Scenario: Title cell accessible name
- **WHEN** a screen reader user reaches a title's filmstrip cell
- **THEN** it announces an accessible name identifying it as a title item, not merely the letter "T"
