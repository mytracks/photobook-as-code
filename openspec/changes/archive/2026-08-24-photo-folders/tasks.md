## 1. Config parsing (`config.py`)

- [x] 1.1 Rename `PhotobookConfig.photos: str` to `photo_folders: List[str]`, update `load_config`'s required-field check from `'photos'` to `'photo_folders'`, and verify `ConfigurationError` names `photo_folders` when it's missing
- [x] 1.2 Rename `resolve_photos_path()` to `resolve_photo_folders()`, returning `List[Path]` with each entry resolved relative to the config file directory exactly as the single path is today, and verify with a unit test covering relative and absolute entries
- [x] 1.3 Rename `validate_photos_path()` to `validate_photo_folders()`: check every resolved folder exists and is a directory (erroring on the first failing one, naming that specific path), and verify with unit tests for a missing folder and a non-directory path
- [x] 1.4 Add validation that `photo_folders` is a non-empty YAML list, and verify `ConfigurationError` is raised for an empty list or non-list value

## 2. Photo discovery (`photos.py`)

- [x] 2.1 Change `discover_photos` to accept `directories: List[Path]`, discovering files in each directory independently and concatenating results before the existing dedup/sort step, and verify with a unit test using two fixture directories
- [x] 2.2 Dedupe the combined path list by resolved absolute path (extending the existing `sorted(set(photos))`), and verify with a unit test where two `photo_folders` entries resolve to the same directory
- [x] 2.3 Change `collect_photos` to accept `directories: List[Path]`, reading metadata across the merged path list and applying `order` exactly as it does today for a single directory, and verify with a unit test asserting `order: date` interleaves photos from two folders by EXIF date rather than grouping by folder
- [x] 2.4 Make an individual empty directory a no-op contribution rather than a `PhotoCollectionError`, raising that error only when the combined pool across all directories is empty, and verify with unit tests for (a) one empty + one non-empty folder succeeding, and (b) all folders empty raising the error

## 3. Call sites (`cli.py`, `webapp/data.py`)

- [x] 3.1 Update `cli.py` to call `validate_photo_folders`/`resolve_photo_folders`/`collect_photos` with the new list-based signatures, and verify `photobook --config <file>` runs end-to-end against a multi-folder fixture config
- [x] 3.2 Update `webapp/data.py`'s call sites the same way, and change `PhotoDirectoryCache`'s key from `(photos_dir: str, order)` to `(tuple of resolved folder paths, order)` so the cache is stable regardless of listing order, verified by a unit test asserting a cache hit when the same folder set is requested in a different order
- [x] 3.3 Update any user-facing error/help text in `cli.py` and `webapp/cli.py` that references "photos directory" (singular) to reflect multiple folders

## 4. Spec-covered edge case tests

- [x] 4.1 Add a test asserting `photo_folders` listed twice (or two paths resolving to the same directory) produces no duplicate photos in the final output, covering the "Duplicate or aliased folder entries" scenario
- [x] 4.2 Add a test asserting folder listing order in `photo_folders` has no effect on final photo order under both `layout.order: alphabetical` and `layout.order: date`

## 5. Real config files and fixtures

- [x] 5.1 Update `example-config.yaml`, `hamburg.yaml`, `karwendel.yaml`, `mondsee.yaml`, `sevilla.yaml` from `photos: <dir>` to a single-entry `photo_folders:` list, and verify `photobook --config <file>` still generates the same output as before the change for at least one of them
- [x] 5.2 Update `tests/fixtures/config-*.yaml` the same way, and verify the full test suite passes
- [x] 5.3 Add a new test fixture config using multiple `photo_folders` entries (e.g. pointing at `tests/fixtures/sample-photos-subset-1` and `sample-photos-subset-2`) for the multi-folder integration tests in section 3-4

## 6. Documentation

- [x] 6.1 Update `README.md`'s configuration examples and field reference from `photos:` to `photo_folders:`, including at least one multi-folder example
