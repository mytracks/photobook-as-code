## Why

The web editor's job is to page through many photos quickly and write dated captions for them, but its current light, minimally-styled interface fights that workflow: a white background competes with photos for attention, the photo's date (the key context for writing a caption) isn't visually emphasized, day boundaries aren't visible at all, navigation only works via small corner links or arrow keys with focus elsewhere, and the layout visibly jumps as each image loads. These are all friction in a task that's inherently high-navigation-volume and repeated over hundreds of photos per book.

## What Changes

- Switch the editor to a fixed dark theme (no light/dark toggle) so photos read cleanly against a black background.
- Display the current photo's date prominently, centered above the photo:
  - Uses the photo's real EXIF capture date when available, formatted with weekday (e.g. "Saturday, June 14, 2025").
  - Falls back to showing the filename instead of the date when no EXIF date exists, rather than presenting an unreliable filesystem-modified date as if it were the capture date.
- Add a first-of-day indicator (icon + short visible text, e.g. "New day") next to the date whenever the current photo's date differs from the previously displayed photo's date — evaluated against display order, so it behaves the same way under both `layout.order: date` and `layout.order: alphabetical`.
- Replace corner-only navigation with full-height click zones on the left and right, shown as overlay bands on the photo's own edges so they're clickable at any window width, plus a keyboard shortcut (Cmd+Arrow on Mac, Ctrl+Arrow elsewhere) that navigates even while the caption field has focus.
- Reserve the photo's real aspect ratio in the layout (using the photo's already-known width/height) so the page no longer jumps when an image finishes loading.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `text-label-web-editor`: the "Display the current photo" requirement gains dark theme presentation, prominent date display (with filename fallback), a first-of-day indicator, and layout-shift-free image loading; the "Navigate photos in configured order" requirement gains full-height click-zone navigation and a keyboard shortcut that works while the caption field is focused.

## Impact

- `src/photobook_as_code/webapp/static/style.css`: dark theme tokens, click-zone band styling, date/badge styling, reserved image aspect-ratio box.
- `src/photobook_as_code/webapp/templates/editor.html`: date/badge markup, click-zone elements, photo width/height passed through for aspect-ratio reservation.
- `src/photobook_as_code/webapp/static/editor.js`: click-zone handlers, Cmd/Ctrl+Arrow handling active even when the caption textarea has focus.
- `src/photobook_as_code/webapp/data.py` / `app.py`: expose each photo's display date (or filename fallback) and a new-day flag to the template.
- No changes to persistence, autosave behavior, the YAML round-trip, or any new dependencies.
