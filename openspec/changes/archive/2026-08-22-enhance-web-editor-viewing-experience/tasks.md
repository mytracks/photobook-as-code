## 1. Derived photo data (`webapp/data.py`)

- [x] 1.1 Add `EditorData.display_date(index)`: formats `photo.date_taken` with weekday (e.g. "Saturday, June 14, 2025") using a manual leading-zero strip instead of platform-specific `strftime` flags; returns `photo.filename` instead when `date_taken` is `None`.
- [x] 1.2 Add `EditorData.is_new_day(index)`: `True` for index 0, otherwise compares `photos[index].sort_date.date()` to `photos[index - 1].sort_date.date()`.
- [x] 1.3 Extend `tests/test_webapp_data.py` covering: known EXIF date formatting, filename fallback when `date_taken` is `None`, new-day flag on first photo, new-day flag when date changes/stays the same between consecutive photos, new-day flag computed from `sort_date` even when the photo has no EXIF date (filename-fallback case).

## 2. Route wiring (`webapp/app.py`)

- [x] 2.1 Pass `date_display`, `is_new_day`, `photo_width`, `photo_height` (from `photo.width`/`photo.height`) into `render_template(...)` in `view_photo`.
- [x] 2.2 Extend `tests/test_webapp_app.py` to assert the new template variables are present/correct for a photo with a known date and one without.

## 3. Template markup (`webapp/templates/editor.html`)

- [x] 3.1 Add a date element centered above the photo, rendering `date_display`.
- [x] 3.2 Add a new-day indicator (icon + short visible text, e.g. "New day") next to the date, shown only when `is_new_day` is true, with appropriate `aria-label`/visible text for accessibility.
- [x] 3.3 Set the photo `<img>`'s `width`/`height` attributes (or an inline `aspect-ratio` style) from `photo_width`/`photo_height` so the browser reserves its display box before the image loads.
- [x] 3.4 Add left/right click-zone elements anchored to the photo's container (not full-page), positioned as bands over its outer edges; wire their `href`s the same way the existing prev/next links are wired so they degrade gracefully without JS.

## 4. Styling (`webapp/static/style.css`)

- [x] 4.1 Replace the `:root` color tokens with a fixed dark palette (background, foreground, muted, border, accent tuned for contrast on black); remove/repoint every rule that assumed a light background.
- [x] 4.2 Style the date element and new-day indicator for prominence (size, weight, spacing) centered above the photo.
- [x] 4.3 Style the click-zone bands: sized to ~15% of the photo's rendered width per side (minimum ~48px), invisible by default, with a subtle hover affordance (e.g. a fading-in chevron) and `cursor: pointer`.
- [x] 4.4 Verify the reserved image box (from task 3.3) renders as the dark background color with no shift once the real image paints in.

## 5. Navigation behavior (`webapp/static/editor.js`)

- [x] 5.1 Wire click handlers for the new left/right zone elements, reusing the existing `navigate()`/`save()`-before-navigate flow used by the current prev/next links.
- [x] 5.2 Add a `keydown` handler for `Cmd+ArrowLeft`/`Cmd+ArrowRight` (`event.metaKey`) and `Ctrl+ArrowLeft`/`Ctrl+ArrowRight` (`event.ctrlKey`) that calls `preventDefault()` and navigates regardless of `document.activeElement`, including while the caption textarea has focus.
- [x] 5.3 Confirm the existing bare-arrow-when-unfocused behavior is unchanged and still coexists with the new modifier-key handler.

## 6. Manual verification

- [x] 6.1 Run the editor against a real config (e.g. `sevilla.yaml` or `hamburg.yaml`) and page through photos in the browser, checking: dark theme throughout, date/new-day indicator correctness across a real day boundary, click zones and Cmd/Ctrl+Arrow navigation (including while typing a caption), and no visible layout jump as images load, at both a wide and a narrow window width.
- [x] 6.2 Run the full test suite (`pytest`) and confirm all webapp tests pass.
