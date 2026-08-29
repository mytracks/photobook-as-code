## ADDED Requirements

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
