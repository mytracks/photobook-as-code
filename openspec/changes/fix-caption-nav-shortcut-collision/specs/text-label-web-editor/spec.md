## MODIFIED Requirements

### Requirement: Navigate photos in configured order
The system SHALL let the user move forward and backward through the photos of the configured photo directory, one photo at a time, in the same order the photobook renderer would use for that configuration. The system SHALL provide full-height click zones and a keyboard shortcut for this navigation, both usable regardless of where the page's focus currently is. The keyboard shortcut SHALL NOT intercept key combinations that carry native text-editing meaning inside a text field.

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
- **WHEN** the user presses Cmd+Enter or Ctrl+Enter (either modifier accepted on any platform), including while the caption text field has focus
- **THEN** the system navigates to the next photo, saving any pending caption edit first as it does for other navigation actions

#### Scenario: Keyboard shortcut navigates backward with Shift
- **WHEN** the user presses Cmd+Shift+Enter or Ctrl+Shift+Enter, including while the caption text field has focus
- **THEN** the system navigates to the previous photo, saving any pending caption edit first as it does for other navigation actions

#### Scenario: Native text-editing shortcuts are not intercepted
- **WHEN** the user presses Cmd+Left Arrow, Cmd+Right Arrow, Ctrl+Left Arrow, or Ctrl+Right Arrow (with or without Shift held) while the caption text field has focus
- **THEN** the system does not navigate to a different photo, and the browser's native text-editing behavior for that combination (moving or extending the selection to the start/end of the line on macOS, or by word on Windows/Linux) is left to run unmodified
