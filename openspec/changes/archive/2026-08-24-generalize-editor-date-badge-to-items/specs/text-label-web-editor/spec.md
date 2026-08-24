## REMOVED Requirements

### Requirement: Display the current photo's date prominently
**Reason**: Replaced by an item-scoped requirement - titles carry their own timestamp and now get the same prominent date display photos do.
**Migration**: See "Display the current item's date prominently" below.

### Requirement: Indicate the first photo of a new day
**Reason**: Replaced by an item-scoped requirement - the new-day comparison now walks the full merged sequence of photos and titles, so a title can be the item that carries the indicator instead of always falling on a photo.
**Migration**: See "Indicate the first item of a new day" below.

## ADDED Requirements

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
