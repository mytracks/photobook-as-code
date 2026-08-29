## 1. Geocoding foundations

- [x] 1.1 Add a module-level, thread-safe 1 req/sec throttle to `geocoding.reverse_geocode()` (last-call timestamp + `threading.Lock`) and verify with a test that two calls in quick succession are at least ~1s apart (patching the sleep/clock so the test doesn't actually wait a full second)
- [x] 1.2 Add a `strict: bool = False` parameter to `resolve_place_name()` that, when `True`, returns `None` unless the response has a named place (no city/country fallback); verify with tests covering both branches, confirming `strict=False` behavior is unchanged from today
- [x] 1.3 Add `Babel` to `pyproject.toml` dependencies and confirm `pip install -e .` (or equivalent) resolves it

## 2. Date formatting

- [x] 2.1 Add a `format_batch_date(dt: datetime, accept_language: str) -> str` helper (new or existing module) that parses the first tag out of an `Accept-Language` header, falls back to a default locale when unparseable/unrecognized by Babel, and formats as day/full-month-name/year via `babel.dates.format_date(..., format="d. MMMM y", ...)`; verify with tests for a German tag, an unrecognized tag (fallback), and a multi-tag header (first tag wins)

## 3. YAML store primitive

- [x] 3.1 Add `prepend_to_title_entry(config_path, text_labels, label, date_text)` to `yaml_store.py`, joining `date_text` and the title's existing content as `f"{date_text}\n\n{existing}"` when existing content is non-empty, or setting it to `date_text` alone when empty; verify with a test asserting the file's other entries/comments/formatting are untouched (mirroring the existing `save_title_text` tests)

## 4. Batch job engine

- [x] 4.1 Create `webapp/batch.py` with a `JobState` (total, processed, updated, skipped_existing, skipped_no_poi, failed, current_label, status: running/done/cancelled/error) and a module-level `{job_id: JobState}` store guarded by a `threading.Lock`
- [x] 4.2 Implement the eligibility pass: given a fixed `EditorData` snapshot, compute for each merged-sequence index whether it's a new-day boundary (reusing `is_new_day`) and whether that boundary's item is a title or a photo; verify with tests covering: photo-boundary with no title, title-boundary suppressing the following photo, and the alphabetical-order case already covered by `is_new_day` itself
- [x] 4.3 Implement the date-insertion step per settings (text-label vs. title destination), including: skip-vs-append against pre-batch content, creating a new title via `insert_new_title_entry` when title-mode's boundary has no existing title, and calling `prepend_to_title_entry`/leaving-unchanged when it does; verify with tests for each of the four destination×existing-content combinations from the spec
- [x] 4.4 Implement the geocoding step per settings (POI-only vs. fallback strictness), including: eligibility (has GPS), calling `reverse_geocode`/`resolve_place_name(strict=...)`, skip-vs-append against pre-batch caption content, and tallying `skipped_no_poi` when strict resolution finds nothing; verify with tests mocking `geocoding.reverse_geocode`
- [x] 4.5 Implement the same-photo combination rule: when a photo gets both a date label and a geocoded location in one run, write the date first and the location appended below it, regardless of the skip/append setting; verify with a test for a photo that is both a day boundary (text-label mode) and GPS-eligible
- [x] 4.6 Implement the worker loop that walks the fixed snapshot once in order, applies 4.3/4.4/4.5 per item, updates `JobState` after each item, saves each write immediately via the existing `yaml_store` functions, and checks a `threading.Event` for cancellation between items (never mid-request); verify with a test running the loop against a small fixture config and asserting the file reflects a mid-run cancellation correctly (already-processed items saved, remainder untouched)
- [x] 4.7 Reject starting a job while one is already running (single active job at a time); verify with a test asserting a second start attempt is rejected without disturbing the running job's state
- [x] 4.8 Deduplicate resolved location text within one run: track resolved texts already inserted this run on `JobState` (`used_location_texts`), and when a later eligible photo resolves to a text already in that set, withhold it (tallied as a new `skipped_duplicate_location` counter) without affecting an unrelated date-marker write for that same photo; surface the new counter on the progress page; verify with tests for a repeated location being inserted only once, a duplicate not suppressing that photo's own date marker, and the dedup set not carrying over into a fresh run

## 5. Flask routes

- [x] 5.1 Add `GET /batch` rendering the settings page (date insertion + destination, geocoding + strictness, shared skip/append, Start control disabled unless at least one action is enabled)
- [x] 5.2 Add `POST /batch/start` that validates the submitted settings, rejects if a job is already running, snapshots the request's `Accept-Language` header, computes the `EditorData` snapshot via the app's existing `PhotoDirectoryCache`, spawns the worker thread, and redirects/responds with the new job id; verify with a test asserting the endpoint returns promptly (does not block for the job's duration) using a stubbed/short-circuited worker
- [x] 5.3 Add `GET /batch/progress/<job_id>` rendering the progress page, and `GET /batch/status/<job_id>` returning the current `JobState` as JSON for polling; verify with a test asserting the JSON shape (counts, current item, status)
- [x] 5.4 Add `POST /batch/cancel/<job_id>` setting the job's cancellation event; verify with a test asserting a subsequent status poll reflects the cancelled state and the worker loop stops advancing

## 6. UI

- [x] 6.1 Add a "Batch…" control to the per-item editor's header (`editor.html`/`editor.js`), navigating to `/batch`, present for both photo and title items
- [x] 6.2 Build the batch settings page template: toggles for date insertion (with destination sub-choice) and geocoding (with strictness sub-choice), the shared skip/append setting, and a Start control that's disabled unless at least one action is enabled
- [x] 6.3 Build the progress page: a progress bar/count, the running tallies (updated/skipped/no-POI/failed), current item, and a Cancel control; JS polls `/batch/status/<job_id>` (e.g. every 1s) and stops polling once the job reaches a terminal state
- [x] 6.4 Style both pages to match the editor's existing fixed dark theme (reuse `style.css` patterns rather than introducing a new visual language)

## 7. Integration & docs

- [x] 7.1 Add an end-to-end test exercising the full batch flow against a small multi-day, multi-GPS fixture config (start → poll to completion → assert final file content matches all the spec's eligibility/combination/skip-append rules)
- [x] 7.2 Update `README.md`'s Web Editor section to describe the batch feature, its settings, and the rate-limit-driven runtime expectation for larger books
