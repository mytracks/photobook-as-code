## ADDED Requirements

### Requirement: Override theme page margin from configuration
The system SHALL accept an optional `output.page_margin` integer field in the YAML configuration, specified in the same pixel unit as a theme's `spacing.page_margin`. When present, it overrides the selected theme's `spacing.page_margin` for that run; when absent, the theme's own value is used unchanged.

#### Scenario: Config overrides theme page margin
- **WHEN** configuration specifies `output.page_margin: 0` and the selected theme's `spacing.page_margin` is a non-zero value
- **THEN** system renders pages using a page margin of `0`, not the theme's value

#### Scenario: Missing page_margin falls through to theme
- **WHEN** configuration does not specify `output.page_margin`
- **THEN** system renders pages using the selected theme's own `spacing.page_margin` value, unchanged from today's behavior

#### Scenario: Explicit zero is a valid override
- **WHEN** configuration specifies `output.page_margin: 0`
- **THEN** system treats this as an explicit override to zero, not as equivalent to omitting the field

#### Scenario: Negative page_margin rejected
- **WHEN** configuration specifies `output.page_margin` as a negative integer
- **THEN** system reports a validation error at load time indicating `page_margin` must be non-negative, and does not proceed to render

#### Scenario: Non-integer page_margin rejected
- **WHEN** configuration specifies `output.page_margin` as a non-integer value (e.g. a string that is not numeric)
- **THEN** system reports a validation error at load time indicating `page_margin` must be an integer
