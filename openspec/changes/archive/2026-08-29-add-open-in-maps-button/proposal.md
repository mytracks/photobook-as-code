## Why

The single-photo reverse-geocode button resolves a GPS location to a place name automatically, but that automatic resolution is sometimes wrong or too generic (e.g. it names a neighborhood when the user wants the actual landmark, or the nearest specific place isn't the one they meant). When that happens, the user has no way in the editor to see the location for themselves and decide what to write - they'd have to leave the app, find the coordinates some other way, and look them up manually.

## What Changes

- Add a second icon-only header control next to the existing reverse-geocode button: an "Open in Maps" button, enabled under the same condition (the current photo's EXIF data contains a GPS location).
- Clicking it opens `https://maps.apple.com/?ll=<lat>,<lon>&q=<lat>,<lon>` in a new browser tab, centered on the photo's coordinates. This is a plain link, not an async request - there is no loading state and no server round trip.
- Alt+G (Option+G on macOS) activates the control regardless of where focus currently is, including while the caption field has focus - mirroring the focus-independent part of the existing reverse-geocode shortcut, and reusing "G" since both actions concern the photo's GPS location. Unlike the reverse-geocode shortcut, there is no bare-letter variant; this remains an occasional fallback action, not a frequent one. (Cmd+M/Ctrl+M was tried first but rejected: Cmd+M is macOS's own "minimize window" shortcut, intercepted by Safari before the page's JS ever sees the keydown event - not something a web page can override.)
- On Apple platforms (Safari/macOS/iOS with the Maps app installed), this URL is a Universal Link and the OS may open it directly in the native Maps app instead of a browser tab; on every other platform/browser it opens Apple's web Maps, so the control degrades gracefully everywhere without requiring platform detection.
- Add a new map icon to the editor's SVG icon sprite.
- The current photo's GPS coordinates (not previously sent to the browser - only a `has_gps` boolean was) are now passed to the template so the link's URL can be built.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `text-label-web-editor`: adds a new requirement for an "open in Maps" control in the per-item editor header, alongside the existing reverse-geocode button requirements.

## Impact

- `src/photobook_as_code/webapp/app.py`: pass the current photo's `lat`/`lon` (or a pre-built maps URL) into the `view_item` render context when `has_gps` is true.
- `src/photobook_as_code/webapp/templates/editor.html`: new header control (disabled-anchor pattern, matching the nav-button convention) and a new `icon-map` SVG symbol.
- `src/photobook_as_code/webapp/static/editor.js`: new Alt+G handler in the existing keydown listener, and a small guard added to the existing bare-`g`/Cmd+G branch so it no longer fires when Alt is held.
- No changes to `geocoding.py`, `batch.py`, or any backend route - this is a pure link, no new endpoint.
