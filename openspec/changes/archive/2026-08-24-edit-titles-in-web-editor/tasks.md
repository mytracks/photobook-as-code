## 1. YAML persistence for titles (`webapp/yaml_store.py`)

- [x] 1.1 Add `find_title_entry_index(text_labels, label: TitleLabel)`, matching on `(timestamp, title)` the same way `find_entry_index` matches captions; verify with a unit test in `tests/test_webapp_yaml_store.py` that it locates the correct entry among mixed `text`/`title` entries.
- [x] 1.2 Add `insert_new_title_entry(document, photo, title_text="")`, structurally parallel to `insert_new_entry` but writing a `title` key timestamped with `photo.sort_date`, inserted in chronological order, annotated with the photo's filename comment; verify with a unit test that the new entry lands at the correct chronological position and a `text_labels` section is created if absent.
- [x] 1.3 Add `save_title_text(config_path, text_labels, label, new_text)`, parallel to `save_photo_text`, updating the located entry's `title` value in place; verify with a unit test that only the target entry's `title` value changes and comments/ordering elsewhere are untouched.
- [x] 1.4 Add `delete_title_entry(config_path, text_labels, label)`, removing the located entry from the round-trip document and saving; verify with a unit test that exactly one entry is removed and all other entries (including other titles and captions) keep their content, comments, and order.
- [x] 1.5 Verify existing caption-related tests in `tests/test_webapp_yaml_store.py` (e.g. `test_title_entry_untouched_by_insert`) still pass unchanged, confirming caption operations still leave titles alone.

## 2. Merged item sequence (`webapp/data.py`)

- [x] 2.1 Change `EditorData` to build its sequence via `merge_titles_with_photos(parse_title_labels(config.text_labels), photos)`, storing it as `self.items: List[Union[PhotoMetadata, TitleLabel]]`; keep `self.photos` and caption `associations` as today (captions only ever key off photos).
- [x] 2.2 Add `EditorData.item_at(index)`, `EditorData.is_title(index)` (or equivalent type check), and `EditorData.count` now reflecting `len(items)`; verify with unit tests in `tests/test_webapp_data.py` that a config with interleaved `title`/`text` entries produces the same order `merge_titles_with_photos` would.
- [x] 2.3 Add a helper to map a merged-sequence index that is a photo to its underlying photo index (for caption lookup/display-date/new-day logic, which stay photo-scoped); verify existing `text_for`, `display_date`, `is_new_day` behavior is unchanged for photo items via updated tests.
- [x] 2.4 Add `EditorData.title_text_for(index)` returning the current title's content (or `""` if newly created with none yet); verify with a unit test.
- [x] 2.5 Verify `tests/test_webapp_data.py`'s existing ordering/date/new-day tests pass with configs that include no titles (pure regression check - merged sequence with zero titles must equal the old photo-only sequence).

## 3. Routes (`webapp/app.py`)

- [x] 3.1 Rename `/photos/<index>` (and `/photos/<index>/image`) to `/items/<index>` (and `/items/<index>/image`), branching the GET handler on whether the item at `index` is a photo or a title and passing the right template context for each; verify with updated tests in `tests/test_webapp_app.py`.
- [x] 3.2 Rename `POST /photos/<index>/text` to `POST /items/<index>/text`, 400 if the item at `index` is not a photo; verify existing `TestSaveText` cases pass under the new path plus a new case asserting 400 on a title index.
- [x] 3.3 Add `POST /items/<index>/title` to save title content via `yaml_store.save_title_text`, 400 if the item at `index` is not a title; verify with a new test class mirroring `TestSaveText`.
- [x] 3.4 Add `POST /items/<index>/add-title` that calls `yaml_store.insert_new_title_entry` using the current photo, returns the index to redirect to (the current index, since the new title takes its place), 400 if the item at `index` is not a photo; verify with a test asserting the response's redirect index and that a subsequent GET at that index shows an empty title ready for editing.
- [x] 3.5 Add `POST /items/<index>/delete-title` that calls `yaml_store.delete_title_entry`, computes and returns the redirect target per design.md's index arithmetic (same index if a following item exists, `index - 1` if the deleted title was last, root redirect if the sequence is now empty), 400 if the item at `index` is not a title; verify with tests covering: a following photo exists, the title was last, and the title was the only item.
- [x] 3.6 Verify `TestPhotoDirectoryCaching` and 404-boundary tests still pass against the renamed routes and the larger (photo+title) `count`.

## 4. Templates and frontend (`webapp/templates/editor.html`, `webapp/static/editor.js`, `webapp/static/style.css`)

- [x] 4.1 Split the item page template into a photo view (existing photo-frame + caption field + "Add title" button) and a title view (no photo frame, title text field, "Delete title" button), sharing the existing header/date-header/nav-zone markup; verify by running the dev server and visually checking both views render correctly for a config with titles (per this project's "test the golden path in a browser" convention).
- [x] 4.2 Wire the "Add title" button to `POST /items/<index>/add-title`, then navigate to the returned index and set the existing session-storage auto-focus flag so the new title's field is focused immediately, mirroring the current Cmd/Ctrl+Enter caption auto-focus behavior.
- [x] 4.3 Wire the "Delete title" button to `POST /items/<index>/delete-title`, then navigate to the returned redirect index.
- [x] 4.4 Update `editor.js`'s save/navigate logic to post to `/items/<index>/text` or `/items/<index>/title` depending on the current item type, and to save-before-navigate for both field types on prev/next, click-zone, and keyboard-shortcut navigation (reusing the existing save-on-blur/navigate pattern).
- [x] 4.5 Add minimal styling for the title-only view and the add/delete buttons, consistent with the existing dark theme; verify visually in the browser.

## 5. Documentation

- [x] 5.1 Update the `README.md` section describing `photobook-edit-labels` to mention that titles can now be viewed, added, and deleted alongside captions.

## 6. Full verification

- [x] 6.1 Run the full test suite (`pytest`) and confirm all `tests/test_webapp_*.py` tests pass, including renamed-route and new title-specific cases.
- [x] 6.2 Start `photobook-edit-labels` against a config with interleaved titles and photos (e.g. `karwendel.yaml`) and manually walk through: navigating across a title, editing a title's text and confirming autosave, adding a title from a photo and confirming it appears immediately before that photo with the photo's timestamp, and deleting a title and confirming the file and navigation land on the following photo.
