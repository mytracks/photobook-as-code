## 1. GPS EXIF extraction

- [x] 1.1 Add `read_exif_gps(image_path) -> Optional[Tuple[float, float]]` to `photos.py`, parsing the `GPSInfo` IFD (tag 34853) and converting the DMS rational `GPSLatitude`/`GPSLongitude` values (with their `Ref` tags) into signed decimal degrees, following `read_exif_date`'s defensive try/except-and-log pattern; verify with unit tests in `tests/test_photos.py` covering a photo with GPS EXIF, a photo without any, and malformed/incomplete GPS tags (all returning `None` in the last two cases).
- [x] 1.2 Add a fixture photo with known GPS EXIF coordinates under `tests/fixtures/` (or generate one in test setup) so extraction, endpoint, and integration tests have a real input with a known expected lat/lon to assert against.
- [x] 1.3 Add a `gps` field to `PhotoMetadata` and populate it in `read_photo_metadata` alongside `date_taken`; verify `collect_photos()` surfaces the field via `tests/test_photos.py`.

## 2. Expose GPS availability to the editor

- [x] 2.1 Add a method to `EditorData` in `webapp/data.py` (e.g. `has_gps(index)`) reporting whether the current item is a photo with a known GPS coordinate; verify via `tests/test_webapp_data.py` for a photo with GPS, a photo without, and a title item.
- [x] 2.2 Pass GPS availability into `view_item`'s template context in `app.py`; verify via `tests/test_webapp_app.py` that the response context/markup differs correctly across the three cases above.

## 3. Reverse-geocoding backend

- [x] 3.1 Implement a Nominatim reverse-geocode client (e.g. `webapp/geocoding.py`) using `urllib.request`: `GET https://nominatim.openstreetmap.org/reverse` with `format=jsonv2`, `lat`, `lon`, `zoom=18`, `addressdetails=1`, `accept-language=<forwarded>`, header `User-Agent: mytracks-photobook-as-code`, and a bounded timeout (e.g. 10s); verify with unit tests that mock the HTTP call for a successful response, an HTTP/network error, and a timeout.
- [x] 3.2 Implement place-name resolution as a pure function of the parsed Nominatim response - prefer the top-level `name` field; otherwise assemble `city` (falling back to `town`/`village`) `+ country` from `address`; treat a fully empty/unusable response as "no location found"; verify with unit tests covering: named-place result, address-only fallback, missing city/town/village keys, and empty response.
- [x] 3.3 Add `POST /items/<index>/reverse-geocode` to `app.py`: 400 for a title index, 400 for a photo with no GPS, otherwise forward the request's `Accept-Language` header into the geocoding client and return `{"status": "ok", "text": "<resolved place name>"}` on success or a non-2xx JSON error body on failure/timeout; verify via `tests/test_webapp_app.py` covering all four outcomes, mocking the network call so tests don't hit the real service.

## 4. Editor markup

- [x] 4.1 Add `icon-geo` and `icon-spinner` `<symbol>` entries to the existing SVG icon sprite in `editor.html`, following the pattern of `icon-chevron-left`/`icon-plus`/etc.
- [x] 4.2 Add the reverse-geocode button to the page header, before the add-title control, rendered only for photo items; disabled (with an explanatory `title` tooltip) when the photo has no GPS, enabled otherwise; icon-only with an `aria-label` since it carries no visible text; verify via `tests/test_webapp_app.py` markup assertions for the GPS/no-GPS/title cases from task 2.2.

## 5. Editor behavior (client-side)

- [x] 5.1 Implement the click handler in `editor.js`, following the existing `addTitleButton` async pattern: disable the button, swap its icon `<use>` target to `#icon-spinner`, `fetch()` the new endpoint, and on success insert the returned text into the caption field (replace if empty, else append preceded by a newline) then call the existing `save()` immediately rather than waiting for blur; verify manually via the dev server against the GPS-tagged fixture photo from task 1.2, checking both the empty-field and existing-content cases.
- [x] 5.2 On a failed response, leave the caption field unchanged and set `#save-status` to an explanatory failure message (matching the existing add-title/delete-title failure message style); verify manually by pointing the endpoint at a forced-failure case (e.g. temporarily stub the endpoint to return an error) and confirming the field is untouched.
- [x] 5.3 In both the success and failure paths, revert the icon back to `#icon-geo` and re-enable the button once the request settles; verify manually that the button is usable again immediately after a completed request.

## 6. Styling

- [x] 6.1 Add disabled-state and spinner-animation (`@keyframes spin`) styles to `style.css`, consistent with the existing `.header-action`/`.nav-button` treatments; verify visually via the dev server in both the enabled, disabled, and in-progress states.

## 7. Docs

- [x] 7.1 Add a short note to README.md calling out that the reverse-geocode button is the one editor feature requiring internet access, and that it's fully opt-in (nothing else in the app is affected when offline); verify by reading the rendered section.

## 8. Keyboard shortcut

- [x] 8.1 Add a bare `G` keydown shortcut to `editor.js`'s existing keydown handler, guarded like the arrow-key shortcuts (ignored while the caption field or jump-to-item field has focus) and inert while the button is disabled; triggers the same click handler as a mouse click. Add a `title` tooltip mentioning the shortcut to the enabled button in `editor.html`, since it carries no visible text. Verified manually via the dev server.
- [x] 8.2 Add a Cmd+G/Ctrl+G keydown shortcut that works regardless of focus, including while the caption field is focused, mirroring the existing Cmd/Ctrl+Enter navigation shortcut's focus-independent behavior; on a successful lookup, refocus the caption field with the cursor at the end so a shortcut used while typing leaves the user back in the field. Verified manually via the dev server and full automated test suite (378 tests).
