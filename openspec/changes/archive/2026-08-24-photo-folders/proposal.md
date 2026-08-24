## Why

A photobook's photos currently must live in a single directory (`photos: <path>`). Real photobooks often draw from more than one source at once — e.g. two people's camera rolls from the same trip, or a shoot split across several export folders — and today that requires manually merging files into one directory before running the tool. Supporting multiple source folders directly in the YAML config removes that manual step.

## What Changes

- **BREAKING**: Rename the top-level `photos` field to `photo_folders` and change its type from a single directory string to a YAML list of directory strings. No backward-compatible single-string shorthand is supported — the field is always a list, even for one folder.
- Photo discovery scans every listed folder (non-recursively, same as today) and merges the results into one flat pool before applying the existing `layout.order` (`alphabetical` or `date`). The order folders are listed in `photo_folders` has no effect on the final photo order.
- Each folder is validated to exist and be a directory, same as today's single-path check. An individual folder is allowed to contain zero photos; the "no photos found" error only fires if the combined pool across all folders is empty.
- Folders are resolved to absolute paths and the combined photo list is deduplicated by resolved photo path, so listing the same folder twice (or two paths that resolve to the same directory) is a silent no-op rather than a duplicate-photos or validation error.
- Update all real config files (`example-config.yaml`, `hamburg.yaml`, `karwendel.yaml`, `mondsee.yaml`, `sevilla.yaml`) and test fixtures to the new `photo_folders` list syntax.
- Update `README.md` documentation for the new field.

## Capabilities

### Modified Capabilities
- `yaml-configuration`: "Parse YAML configuration file" and "Validate photo source paths" requirements change from a single `photos` path field to a `photo_folders` list field, including list-specific validation (each folder checked, combined-pool emptiness check, dedup behavior).
- `photo-layout-engine`: "Detect photo files" requirement changes from detecting files in one source directory to detecting and merging files across multiple source folders into one pool.

## Impact

- `src/photobook_as_code/config.py`: `PhotobookConfig.photos: str` → `photo_folders: List[str]`; `resolve_photos_path()` → `resolve_photo_folders()` returning `List[Path]`; `validate_photos_path()` validates each folder; required-field check updated.
- `src/photobook_as_code/photos.py`: `discover_photos`/`collect_photos` accept `directories: List[Path]` instead of a single `Path`, merging and deduplicating across folders.
- `src/photobook_as_code/cli.py`: updates call sites for the renamed config accessor and multi-folder collection.
- `src/photobook_as_code/webapp/data.py`: updates call sites; `PhotoDirectoryCache` key changes from `(photos_dir: str, order)` to a key derived from the resolved folder list.
- `openspec/specs/yaml-configuration/spec.md`, `openspec/specs/photo-layout-engine/spec.md`: requirement updates described above.
- `example-config.yaml`, `hamburg.yaml`, `karwendel.yaml`, `mondsee.yaml`, `sevilla.yaml`, `tests/fixtures/*.yaml`: field rename and list wrapping.
- `README.md`: documentation for `photo_folders`.
