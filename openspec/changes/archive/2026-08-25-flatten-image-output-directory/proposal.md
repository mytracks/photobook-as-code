## Why

When output format is `png` or `jpg`, the CLI's default output path is built by appending a `.png`/`.jpg` extension to the base filename (as if constructing a single file path, like it does for `pdf`), then `generate_output()` treats that whole extension-bearing path as the *directory* to create and write pages into. The result is a directory literally named e.g. `mondsee.jpg`, containing the actual page files (`mondsee.jpg/mondsee_page_001.jpg`, ...). This looks like a bug (a directory named like a file) and buries the generated pages one level deeper than the output directory the user configured. No test or documentation covers this path-shaped-like-a-file behavior, confirming it is unintentional.

## What Changes

- For `png`/`jpg` output, page files are written directly into the configured/derived output directory - no extra subfolder is created.
- Directory and base-filename responsibilities are separated end-to-end instead of being encoded into one extension-bearing `Path` and re-split later: `generate_output()` takes an explicit output directory plus a base filename, rather than inferring the directory from an image-format path's parent-vs-self ambiguity.
- `prepare_output_path()` (used for the config-derived default path) no longer forces a `.png`/`.jpg` extension onto the path for image formats; the extension is only appended for `pdf`.
- CLI `--output` override: for `pdf`, unchanged - accepts either a file path or a directory. For `png`/`jpg`, `--output` is now always treated as the target directory (files are named `<base_filename>_page_NNN.<ext>` inside it, same as the config-derived default path). This narrows an existing ambiguity in the flag's documented "file path or directory" behavior for image formats specifically.
- Existing PDF output behavior is unchanged (single file at `output_dir/base_filename.pdf`), including silent overwrite of an existing file.
- No new collision detection for png/jpg: an existing page file with the same name is silently overwritten, matching current PDF behavior.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `output-generation`: the "Handle output file naming" and "Support output directory specification" requirements need a scenario clarifying that image-format pages are written directly into the output directory (no per-run subfolder named after the base filename).

## Impact

- `src/photobook_as_code/output.py`: `generate_output()` signature/logic (directory vs. base-filename handling for png/jpg), `prepare_output_path()` (extension handling for image formats).
- `src/photobook_as_code/cli.py`: the ~10 lines building the default `output_path` before calling `generate_output()`.
- `tests/test_output.py`: currently only covers `generate_pdf`; needs coverage added for the png/jpg directory-flattening behavior (no existing test exercises this path).
- No config schema changes - `output.directory` and `output.filename` keep their current meaning.
