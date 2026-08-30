## Context

See proposal.md for motivation. Relevant current state:

- `photos.py` already reads EXIF once per photo to get `date_taken` (`read_exif_date`, via `img._getexif()`), and separately reads dimensions; `PhotoMetadata` is the resulting per-photo record.
- `webapp/data.py`'s `PhotoDirectoryCache` caches the `collect_photos()` scan per running editor session, keyed by `(photo_folders, order)`. Any new per-photo field added to `PhotoMetadata` rides along in this cache for free - no extra file opens.
- `webapp/app.py` already has three POST endpoints (`/text`, `/title`, `/add-title`, `/delete-title`) that follow one shape: load `EditorData` fresh, validate the item type, mutate via `yaml_store`, return JSON. The new endpoint follows the same shape but calls an external service instead of `yaml_store`.
- `editor.js` already has an established async-button pattern (`addTitleButton`/`deleteTitleButton`: disable → `fetch().then().catch()` → re-enable/navigate) and an established locale pattern (server renders a fallback, client replaces it via `Intl.DateTimeFormat(undefined, ...)`).
- README.md advertises "Offline Operation: No cloud dependencies, works entirely locally" as a headline feature. This change is a deliberate, opt-in exception to that: it only calls out to the network when the user clicks the button.

## Goals / Non-Goals

**Goals:**
- One click turns a photo's GPS EXIF into a locale-appropriate, human-readable place name inserted into its caption.
- No blocking UI; clear in-progress and failure states.
- No new required runtime dependency, no new API-key configuration surface - consistent with how the rest of the app is configured (a single `--config` path, nothing else).

**Non-Goals:**
- Caching geocoding results (across photos or across runs).
- Making the geocoding provider configurable/pluggable - Nominatim is the only supported provider for this change.
- Reverse geocoding for title items (no photo, no EXIF).
- Any offline/bundled geocoding data.

## Decisions

**Server-side proxy endpoint, not a client-side call.** New `POST /items/<index>/reverse-geocode`, following the exact request/response shape of the existing action endpoints. The Flask process already has the photo's GPS coordinates (once EXIF parsing is extended) and already receives the browser's `Accept-Language` header on every request - forwarding it to Nominatim's `accept-language` parameter satisfies the locale requirement with no client-side locale logic at all. A client-side call was rejected: it would need the coordinates exposed in the page, and would call a third-party origin directly from the browser (CORS/usage-policy exposure) for no benefit over the proxy.

**Nominatim (OpenStreetMap), no API key.** Free, no key, supports both `accept-language` and structured `addressdetails`. Alternatives considered: Photon (comparable, but less consistent locale/POI naming); a commercial keyed provider (rejected - would require adding the app's first-ever secret/API-key configuration surface, and the app has none today).

**HTTP client: stdlib `urllib.request`, no new dependency.** This is a single GET request; `requests` isn't used anywhere else in the codebase (dependency list is currently Pillow, reportlab, click, PyYAML, Flask, ruamel.yaml, pikepdf). Request carries an explicit `User-Agent: mytracks-photobook-as-code` header, since Nominatim's usage policy blocks/deprioritizes requests without a real identifying User-Agent.

**Nominatim request shape:**
```
GET https://nominatim.openstreetmap.org/reverse
    ?format=jsonv2&lat=<lat>&lon=<lon>&zoom=18&addressdetails=1
    &accept-language=<forwarded Accept-Language>
```
`zoom=18` requests the finest resolution Nominatim offers (building/POI level), which is what makes a named-landmark result possible at all.

**Place-name resolution:** prefer the response's top-level `name` field (populated when the resolved OSM object itself carries a name - a building, monument, plaza, etc.). When `name` is absent, assemble `city + country` from `address` (`city`, falling back to `town`/`village` when Nominatim used one of those keys instead, then `country`). No response, an empty `address`, or a network/HTTP error is treated as "no location found."

**GPS EXIF extraction:** new `read_exif_gps(image_path) -> Optional[Tuple[float, float]]` in `photos.py`, mirroring `read_exif_date`'s structure - reads the `GPSInfo` IFD (tag 34853), converts the DMS rational `GPSLatitude`/`GPSLongitude` values using their `Ref` tags into signed decimal degrees, and returns `None` on any missing/malformed data (same broad try/except-and-log-debug pattern already used for dates, so a corrupt GPS tag disables the button rather than breaking the page). Result becomes a new optional field on `PhotoMetadata`, populated in `read_photo_metadata` right alongside `date_taken` - covered by `PhotoDirectoryCache` automatically.

**Endpoint behavior:** loads `EditorData` the same way the existing endpoints do; 400s for a title index or a photo with no GPS; otherwise calls Nominatim synchronously within the request (acceptable - this is a single-user local server, not a shared service) with a bounded timeout, and returns `{"status": "ok", "text": "<resolved place name>"}` on success or a non-2xx JSON error body on failure.

**Client-side handler:** new handler in `editor.js` following the existing `addTitleButton` shape - disable the control, swap its `<use>` target from `#icon-geo` to `#icon-spinner` (CSS `@keyframes spin`), `fetch()` the endpoint, then on success insert the returned text per the empty/non-empty rule and call the existing `save()` immediately (not waiting for blur), or on failure set the existing `#save-status` message - and in both cases revert the icon and re-enable the control.

**New icons:** `icon-geo` and `icon-spinner` added to the existing inline `<svg class="icon-sprite">` in `editor.html`, as new `<symbol>` entries alongside `icon-chevron-left`/`icon-plus`/etc.

**Keyboard shortcut:** added to the same `document.addEventListener("keydown", ...)` handler that already implements arrow-key navigation and Cmd/Ctrl+Enter, following its established two-tier pattern (a bare key outside text fields, a modifier-combined key that also works inside them):
- Bare `G` - guarded exactly like the arrow-key case (ignored when `document.activeElement` is the caption textarea or the jump-to-item input), then calls `geoButton.click()`, reusing the existing click handler's disable/spinner/fetch/insert/save/revert logic rather than duplicating it.
- Cmd/Ctrl+G - unguarded by focus, mirroring Cmd/Ctrl+Enter's existing "works while typing" behavior, so the caption field never has to lose focus for the user to trigger a lookup.
- Both forms are inert whenever `geoButton.disabled` is true, which is already true both when the current photo has no GPS and while a request is in flight - no separate "in-flight" check needed.
- On a successful lookup, the handler now calls `textarea.focus()` and places the cursor at the end (factored out as `focusTextareaAtEnd()`, reused by the pre-existing post-navigation autofocus logic) so a Cmd/Ctrl+G lookup from inside the caption field leaves the user back in the field, ready to keep typing after the inserted text.

## Risks / Trade-offs

- **[Risk]** The only feature in this app requiring live internet access, in an app whose README advertises fully offline operation → **Mitigation:** strictly opt-in (nothing calls out to the network unless the user clicks this one button), fails gracefully (caption is left untouched on any failure), and every other feature remains fully offline. Worth a one-line callout in README.
- **[Risk]** Nominatim's public instance enforces a 1 req/sec usage policy and can block traffic with no identifying User-Agent → **Mitigation:** explicit `User-Agent: mytracks-photobook-as-code`; this editor's usage pattern (one manual click at a time, one local user) is inherently far under that limit.
- **[Risk]** OpenStreetMap's named-place coverage is inconsistent by region - remote/rural coordinates (this project's own example configs include hiking photobooks like `karwendel.yaml`) will often have nothing named nearby → **Mitigation:** the city+country fallback (per proposal/specs) means the button still produces a useful result in that case; only truly unresolvable coordinates fall through to the "no location found" failure.
- **[Risk]** GPS EXIF can be present but malformed (bad rational values, missing ref tags) → **Mitigation:** same defensive, log-and-return-None pattern as the existing date extraction - treated as "no GPS," button disabled, page never breaks.
- **[Risk]** The geocode call runs synchronously inside the Flask worker handling the request, so a slow/hanging Nominatim response ties up that worker for its duration → **Mitigation:** acceptable for a single-user local tool; a bounded request timeout (e.g. 10s) ensures a hung upstream surfaces as a failure instead of hanging indefinitely.
- **[Risk]** Cmd+G/Ctrl+G is a native "find next" shortcut in some browsers (active only when that browser's own find bar is open) → **Mitigation:** `event.preventDefault()` runs before the browser's own handling for this keydown; the two only actually collide in the rare case of the find bar being open at the same moment, an acceptable trade-off for a shortcut that must also work while the caption field has focus (the same trade-off this app already made for Cmd/Ctrl+Enter navigation).

## Migration Plan

Purely additive - no data migration, no changes to existing endpoints or file formats. Rollback is deleting the new endpoint, button, and icons; nothing else depends on them.
