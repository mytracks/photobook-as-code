## ADDED Requirements

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
