## ADDED Requirements

### Requirement: Parse text label entries
The system SHALL parse an optional `text_labels` section in the YAML configuration containing timestamped text entries.

#### Scenario: Valid text_labels section
- **WHEN** configuration includes `text_labels` array with valid entries
- **THEN** system parses all text label entries successfully

#### Scenario: Text label with ISO timestamp
- **WHEN** text label entry has `timestamp` field with ISO 8601 format
- **THEN** system parses timestamp correctly

#### Scenario: Text label with Unix epoch timestamp
- **WHEN** text label entry has `timestamp` field with Unix epoch integer
- **THEN** system parses timestamp correctly

#### Scenario: Text label with multi-line text
- **WHEN** text label entry has `text` field with YAML multi-line string (using | or >)
- **THEN** system preserves line breaks and text content

#### Scenario: Missing text_labels section
- **WHEN** configuration does not include `text_labels` section
- **THEN** system processes configuration normally without text labels

#### Scenario: Empty text_labels array
- **WHEN** configuration includes `text_labels: []`
- **THEN** system processes configuration normally with no text labels

#### Scenario: Invalid text label structure
- **WHEN** text label entry is missing required field (timestamp or text)
- **THEN** system reports validation error with clear message indicating missing field

#### Scenario: Text label with invalid timestamp format
- **WHEN** text label timestamp is not a valid ISO 8601 string or Unix epoch number
- **THEN** system reports validation error indicating invalid timestamp format

### Requirement: Validate text label data types
The system SHALL validate that text label fields have correct data types.

#### Scenario: Timestamp as string
- **WHEN** text label timestamp is a string (ISO 8601 format)
- **THEN** system accepts and parses it

#### Scenario: Timestamp as number
- **WHEN** text label timestamp is a number (Unix epoch)
- **THEN** system accepts and parses it

#### Scenario: Text as string
- **WHEN** text label text field is a string (single or multi-line)
- **THEN** system accepts it

#### Scenario: Text label as non-object
- **WHEN** text_labels array contains non-object entry (e.g., string or number)
- **THEN** system reports validation error indicating entry must be an object

#### Scenario: Timestamp as boolean or object
- **WHEN** text label timestamp field is boolean or object
- **THEN** system reports validation error indicating invalid timestamp type
