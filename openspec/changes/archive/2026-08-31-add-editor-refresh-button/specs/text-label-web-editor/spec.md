## ADDED Requirements

### Requirement: Refresh the editor's view of external changes
The system SHALL let the user manually request that the editor re-read the photo folder from disk, discarding any cached photo listing built earlier in the running session, so photos added, removed, or renamed outside the editor become visible without restarting the server. The system SHALL provide this via a labeled control in the per-item editor's header, available regardless of whether the current item is a photo or a title. The system SHALL NOT provide a keyboard shortcut for this control, and SHALL NOT automatically detect or poll for external changes.

#### Scenario: Refresh control is always available
- **WHEN** the user views any item in the per-item editor
- **THEN** the header presents a labeled control that triggers a refresh, regardless of whether the current item is a photo or a title

#### Scenario: Newly added photos become visible
- **WHEN** a photo is added to the configured photo folder while the editor is running, and the user activates the refresh control
- **THEN** the newly added photo appears in the item sequence without requiring the server to be restarted

#### Scenario: Removed photos disappear
- **WHEN** a photo is deleted from the configured photo folder while the editor is running, and the user activates the refresh control
- **THEN** the removed photo no longer appears in the item sequence

#### Scenario: Pending edit is saved before refreshing
- **WHEN** the user has changed the current item's text and activates the refresh control
- **THEN** the system saves the pending edit before re-reading the photo folder, the same way other navigation actions do

#### Scenario: Refresh always lands on the first item
- **WHEN** the user activates the refresh control
- **THEN** the system navigates to the first item of the refreshed sequence, regardless of which item was being viewed before the refresh, so the navigation itself confirms the refresh took effect

#### Scenario: Thumbnail cache is left untouched
- **WHEN** the user activates the refresh control
- **THEN** the system does not clear previously rendered filmstrip thumbnails, relying instead on their existing per-photo content-based cache key to serve a fresh thumbnail if a photo file was replaced

#### Scenario: No keyboard shortcut
- **WHEN** the user looks for a keyboard shortcut to trigger a refresh
- **THEN** the system provides none; the control is only activated by clicking it

#### Scenario: No automatic detection
- **WHEN** external changes are made to the photo folder or the configuration file while the editor is open
- **THEN** the system does not detect or refresh automatically; the editor's view stays as it was until the user manually activates the refresh control

## MODIFIED Requirements

### Requirement: Report startup errors clearly
The system SHALL report a clear error and refuse to start the editing session if the configured file cannot be loaded or its photo path cannot be read. The system SHALL also report a clear error, instead of an unhandled server error, if the configuration file or photo path becomes invalid or unreadable during a running editing session - for example, after a hand-edit made while the server is running - whether encountered through the refresh control or through ordinary item navigation.

#### Scenario: Invalid or missing configuration file
- **WHEN** the editor is started with a configuration file that does not exist or fails validation
- **THEN** the system reports a clear error identifying the problem and does not start the editing session

#### Scenario: Inaccessible photo directory
- **WHEN** the configuration's photo path does not exist or is not readable
- **THEN** the system reports a clear error identifying the problem and does not start the editing session

#### Scenario: Configuration becomes invalid during a running session
- **WHEN** the user triggers the refresh control, or navigates to any item, while the configuration file cannot be loaded or fails validation
- **THEN** the system displays a clear error page identifying the problem instead of an unhandled server error, and the editing session remains running

#### Scenario: Photo directory becomes inaccessible during a running session
- **WHEN** the user triggers the refresh control, or navigates to any item, while the configuration's photo path does not exist or is not readable
- **THEN** the system displays a clear error page identifying the problem instead of an unhandled server error, and the editing session remains running
