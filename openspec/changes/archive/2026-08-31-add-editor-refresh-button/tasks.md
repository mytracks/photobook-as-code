## 1. Photo directory cache invalidation

- [x] 1.1 Add a `clear()` method to `PhotoDirectoryCache` in `src/photobook_as_code/webapp/data.py` that empties its internal cache dict, and verify with a unit test in `tests/test_webapp_data.py` that calling `clear()` then `get()` re-invokes the photo scan instead of returning the previously cached list.

## 2. Friendly configuration/photo error handling

- [x] 2.1 Add `src/photobook_as_code/webapp/templates/error.html`, styled consistent with the editor's dark theme, showing the failure's message and a "Try again" link back to the request path that failed.
- [x] 2.2 In `create_app()` (`app.py`), register `@app.errorhandler(ConfigurationError)` and `@app.errorhandler(PhotoCollectionError)` (imported from `..config` and `..photos`) that render `error.html` with the exception's message and return HTTP 500.
- [x] 2.3 Add tests in `tests/test_webapp_app.py`: overwrite the test config with invalid YAML (and separately, point its photo folder at a nonexistent path) after the app is created, request `GET /items/0`, and assert a 500 response rendering the friendly error template rather than an unhandled exception/traceback.

## 3. Refresh endpoint

- [x] 3.1 Add a `POST /refresh` route in `app.py` that calls `photo_cache.clear()` and returns `{"status": "ok"}` as JSON.
- [x] 3.2 Add a test in `tests/test_webapp_app.py` that adds a new photo file to the test fixture folder while the app is running, confirms `GET /items/<last-index>` (or the item count) still reflects the old, stale listing, then calls `POST /refresh` and confirms the new photo is now present in the item sequence.
- [x] 3.3 Add an equivalent test for a photo removed from the fixture folder between the initial load and the refresh.

## 4. Header control and client-side wiring

- [x] 4.1 Add an `icon-refresh` SVG symbol to the icon sprite already defined at the top of `templates/editor.html`, matching the style of the existing symbols (`icon-plus`, `icon-trash`, etc.).
- [x] 4.2 Add a "Refresh" control (icon + visible label, matching the existing `header-action` style) to the `header-actions` block in `editor.html`, positioned next to the existing "Batch…" control, rendered for both photo and title items, with no `data-shortcut`-style wiring.
- [x] 4.3 In `editor.js`, add a click handler for the new refresh button: call `save()`, then `fetch("/refresh", { method: "POST" })`, then on success navigate to `/items/0`; on failure, set the save-status text the same way the add-title/delete-title handlers already do.

## 5. Verification

- [x] 5.1 Run `pytest` and confirm the full suite passes, including all tests added above.
- [x] 5.2 Manually start the editor (`photobook-edit-labels --config <test-config>`), add and then remove a photo in its configured folder while the server keeps running, click Refresh each time, and confirm the item count updates and the view lands on item 1 (index 0) both times. (Verified by driving a running dev server over HTTP end-to-end - no browser was available in this environment - exercising the same request sequence a click would trigger: warmed the cache, added `c.jpg`, confirmed `/items/0` still reported "1 / 2" before refresh, then "1 / 3" after `POST /refresh`; then viewed the now-last item, removed it from disk, confirmed it still resolved (200) before refresh and 404'd with the count back at "1 / 2" after.)
- [x] 5.3 Manually break the running config's YAML (e.g. introduce a syntax error) and click Refresh; confirm a friendly error page appears instead of a stack trace, then fix the YAML and confirm the page's "Try again" link recovers into the normal editor view. (Same HTTP-driven approach: corrupted the YAML, confirmed `/items/0` returned 500 with "Couldn't load the photobook" / "Try again" and no "Traceback" text, then restored the YAML and confirmed the same path returned 200 again.)
