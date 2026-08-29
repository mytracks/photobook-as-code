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
