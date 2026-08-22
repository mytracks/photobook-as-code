## 1. Renderer: empty text renders nothing

- [x] 1.1 In `render_text_label` (renderer.py), add an early return immediately after `parsed_lines = parse_markdown_text(text_label.text)` when `parsed_lines` is empty - before the background box or any text is drawn.
- [x] 1.2 Add/extend renderer tests covering: `text: ""` draws nothing (no background, no text) under a theme with `text_background_enabled: true`; a non-empty `text` still renders as before (regression guard).

## 2. Timestamp stub extraction logic

- [x] 2.1 Add a function that takes a list of `PhotoMetadata` and returns stub data grouped by identical `sort_date`, sorted chronologically, each group carrying its timestamp and the filenames that share it (independent of any `layout.order` the photos were originally collected in).
- [x] 2.2 Add a function that formats that grouped data as a `text_labels:` YAML text block: 2-space indented list items, `timestamp:` as a quoted ISO-8601 string (`sort_date.isoformat()`), `text: ""`, and a trailing `# filename[, filename...]` comment on the timestamp line.
- [x] 2.3 Unit tests: distinct timestamps produce one stub each; photos sharing an identical timestamp collapse into one stub with comma-joined filenames; output order is chronological even when input photo order is alphabetical.

## 3. CLI integration

- [x] 3.1 Add an `--extract-labels` boolean flag to the `photobook` command in cli.py.
- [x] 3.2 When the flag is set: load and validate the config, collect photos (as today), build and print the stub block from 2.1/2.2 to stdout, then exit successfully - skipping theme loading, layout calculation, rendering, and output generation entirely. `--output` has no effect in this mode.
- [x] 3.3 Update the command's docstring/help text to document `--extract-labels`.
- [x] 3.4 Add a CLI-level test invoking `--extract-labels` against a fixture config/photo set, asserting stdout contains the expected stub block and that no output file is written.

## 4. Documentation

- [x] 4.1 Add a short subsection under README.md's "Text Labels" section describing `--extract-labels`: what it prints, that it ignores the config's existing `text_labels`, and that duplicate timestamps collapse into one stub with multiple filenames noted.
