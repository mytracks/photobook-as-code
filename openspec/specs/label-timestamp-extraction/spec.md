## Purpose

Lets a user discover the timestamps of their photos without inspecting EXIF data by hand, by printing empty, ready-to-paste `text_labels` stub entries for every photo in a config's photo directory.

## Requirements

### Requirement: Extract-labels flag prints stubs instead of generating a photobook
The system SHALL provide an `--extract-labels` CLI flag that, when passed alongside `--config`, collects photos from the configured photo directory and prints a `text_labels` YAML block to stdout, then exits without loading a theme, computing layout, or producing any rendered output file.

#### Scenario: Flag passed with a valid config
- **WHEN** the user runs the CLI with `--config <file>` and `--extract-labels`
- **THEN** the system loads and validates the configuration, collects photos, prints the `text_labels` stub block to stdout, and exits successfully without generating a photobook

#### Scenario: Flag passed with an invalid config or photo path
- **WHEN** the user runs the CLI with `--extract-labels` and the configuration is invalid or the photos path cannot be found
- **THEN** the system reports the same configuration/photo-collection error it would report without the flag, and does not print a stub block

### Requirement: One stub entry per distinct photo timestamp
The system SHALL emit exactly one stub entry per distinct timestamp among the collected photos, using each photo's best-available date (EXIF capture time, falling back to file modification time) as its timestamp.

#### Scenario: Photos with distinct timestamps
- **WHEN** the collected photos each have a different timestamp
- **THEN** the printed output contains one stub entry per photo, each annotated with that photo's filename

#### Scenario: Multiple photos sharing an identical timestamp
- **WHEN** two or more collected photos have the exact same timestamp
- **THEN** the printed output contains a single stub entry for that timestamp, annotated with all contributing filenames

### Requirement: Stub entries are empty and chronologically ordered
The system SHALL print stub entries sorted chronologically by timestamp, each with an empty `text` field, regardless of the configuration's `layout.order` setting.

#### Scenario: Config specifies alphabetical layout order
- **WHEN** the configuration's `layout.order` is `alphabetical`
- **THEN** the printed stub entries are still ordered chronologically by timestamp, not by filename

#### Scenario: Stub content field
- **WHEN** a stub entry is printed
- **THEN** its `text` field is an empty string, and it includes a trailing comment naming the source photo filename(s) for that timestamp

### Requirement: Extraction ignores the configuration's existing text_labels
The system SHALL print the full set of stub entries for every collected photo without reading, merging, or comparing against any `text_labels` already present in the configuration.

#### Scenario: Config already has text_labels entries
- **WHEN** the configuration file already contains a non-empty `text_labels` section
- **THEN** the printed output still includes a stub entry for every collected photo timestamp, unaffected by the existing entries
