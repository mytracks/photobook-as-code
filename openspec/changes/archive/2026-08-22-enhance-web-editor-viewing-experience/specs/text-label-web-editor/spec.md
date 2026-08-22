## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Display the current photo
The system SHALL render the currently selected photo's image in the browser alongside its editable text field, and SHALL reserve the image's display space in advance so that no visible layout shift occurs while the image loads.

#### Scenario: Photo image is visible
- **WHEN** the user navigates to a photo
- **THEN** the system displays that photo's image in the browser

#### Scenario: No layout shift while loading
- **WHEN** the user navigates to a photo and its image has not yet finished loading
- **THEN** the system reserves the image's final display space using the photo's real aspect ratio, so the caption field and other page elements do not move once the image finishes loading
