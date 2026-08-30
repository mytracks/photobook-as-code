## ADDED Requirements

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
