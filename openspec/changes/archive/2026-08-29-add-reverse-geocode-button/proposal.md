## Why

Photos often carry a GPS location in their EXIF data, but a user writing a caption has to look that location up by hand (map, search engine) to name the place in the text. The web editor already surfaces other EXIF-derived facts (capture date); it should offer the same convenience for location, turning a manual lookup into a single click.

## What Changes

- Add an icon-only reverse-geocode button ("🌍", no text) to the editor header, positioned before "Add title before this photo". Hidden entirely for title items (no photo, no EXIF); present but disabled for a photo whose EXIF has no GPS location, with a tooltip explaining why.
- Clicking the button (when enabled) calls a new `POST /items/<index>/reverse-geocode` endpoint. The button's icon swaps to a loading indicator and the button disables for the duration of the request, so the page stays responsive.
- The endpoint resolves the photo's GPS coordinates server-side via Nominatim (OpenStreetMap), identified with User-Agent `mytracks-photobook-as-code`:
  - Prefers a named place/landmark (e.g. "St. Michaelis Church") when OpenStreetMap has one near the coordinates.
  - Falls back to city + country (e.g. "Hamburg, Germany") when no named place is found.
  - Forwards the browser's own `Accept-Language` header to Nominatim so the returned name matches the viewing browser's locale, the same way the existing date display already matches browser locale.
- On success, the result text is inserted into the caption field: it replaces empty content, or is appended after a newline when the field already has content. The field is saved immediately afterward, the same as other editor actions that don't wait for a blur event.
- On failure (no network, no result found, service error), an inline status message is shown (matching the existing save-status pattern) and the caption field is left unchanged.
- New GPS EXIF extraction in `photos.py`, alongside the existing capture-date extraction, exposed on `PhotoMetadata` and threaded through the editor's per-item data.
- A keyboard shortcut activates the button without the mouse: the bare `G` key when focus isn't in a text field, and Cmd+G/Ctrl+G from anywhere, including while the caption field is focused - mirroring how this editor's existing Cmd/Ctrl+Enter navigation shortcut already works both in and out of the text field.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `text-label-web-editor`: adds requirements for GPS-based button enablement/visibility, the reverse-geocode action and its request/response lifecycle, locale- and place-name-aware result formatting, and caption insertion behavior.

## Impact

- `src/photobook_as_code/photos.py`: new GPS EXIF extraction (mirrors the existing `read_exif_date`), new field on `PhotoMetadata`.
- `src/photobook_as_code/webapp/data.py`: expose GPS presence/coordinates for the current item.
- `src/photobook_as_code/webapp/app.py`: new `POST /items/<index>/reverse-geocode` endpoint; server-side call to Nominatim over stdlib `urllib.request` (no new runtime dependency), forwarding the request's `Accept-Language` header.
- `src/photobook_as_code/webapp/templates/editor.html`: new button and geotag/loading icons in the existing SVG sprite.
- `src/photobook_as_code/webapp/static/editor.js`: click handler, icon swap during the request, insertion logic, immediate autosave, error status.
- `src/photobook_as_code/webapp/static/style.css`: disabled-button and loading-icon styling.
- This is the one feature in the editor that requires live internet access (a call to the public Nominatim service); it only runs when the user clicks the button, and its absence doesn't block any other editor function.
- Tests: GPS EXIF parsing and the reverse-geocode endpoint (Nominatim call mocked/stubbed).
