## ADDED Requirements

### Requirement: Configure whether a new day forces a new page
The system SHALL accept an optional `layout.new_page_per_day` boolean field, defaulting to `true`, controlling whether photo/title distribution treats a calendar-day change as a forced page break.

#### Scenario: Default enables day-boundary page breaks
- **WHEN** configuration does not specify `layout.new_page_per_day`
- **THEN** the system behaves as if it were set to `true`

#### Scenario: Explicitly enabled
- **WHEN** configuration specifies `layout.new_page_per_day: true`
- **THEN** the system enables day-boundary page breaks during distribution

#### Scenario: Explicitly disabled
- **WHEN** configuration specifies `layout.new_page_per_day: false`
- **THEN** the system disables day-boundary page breaks during distribution

#### Scenario: Invalid type
- **WHEN** configuration specifies a non-boolean value for `layout.new_page_per_day`
- **THEN** system reports a validation error indicating the field must be a boolean
