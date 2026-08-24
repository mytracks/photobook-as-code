## Why

The web editor works but has accumulated rough edges its users now feel directly: dates are always formatted in hardcoded English regardless of who's viewing them, there's no way to jump straight to a known item in a book of hundreds, the add/delete-title buttons dominate the page for an action taken rarely, hovering over an empty title page reveals nothing (the prev/next affordance silently depends on a photo being there to darken), and the overall interface reads as flat and dated rather than the "modern and clear" tool it's meant to be.

## What Changes

- **BREAKING**: Photo/title navigation moves from full-height hover zones overlaid on the photo to a pair of always-visible previous/next buttons in the page header, next to the item position indicator. The hover-zone click bands are removed entirely.
- The photo's capture date and time is formatted using the viewer's browser locale (via `Intl.DateTimeFormat`) instead of a hardcoded English format, so weekday/month names, date order, and 12/24-hour time follow the browser's language and region settings.
- The header's item position indicator ("2 / 264") becomes clickable: clicking it turns it into a text input pre-filled with the current position, where entering a number and confirming jumps directly to that item (out-of-range or non-numeric input is rejected without navigating).
- The "Add title before this photo" / "Delete title" actions move from a large, always-visible bordered button beneath the text field to a small labeled control in the header, alongside the navigation controls - present for the item type it applies to, absent for the other.
- The empty area above a title's text field (which has no photo to display) gets a visible bounded surface (background/border) instead of blank space indistinguishable from the page background, so a title page reads as an intentional slot rather than a rendering gap.
- Navigating between items (previous/next, jump-to-number, add/delete title) gets a smooth visual transition instead of a hard page reload, using the browser's native View Transitions API.
- General visual refresh: depth (subtle elevation) replaces flat hairline borders on the photo frame and text field, the date display gets stronger typographic hierarchy against the rest of the page, and the mixed emoji/HTML-entity icons (🌅, `&lsaquo;`/`&rsaquo;`) are replaced with one consistent inline-SVG icon set.

## Capabilities

### Modified Capabilities
- `text-label-web-editor`: navigation mechanism (header buttons replace hover zones, plus jump-to-number), locale-aware date formatting, title-action placement and prominence, title-page empty-area treatment, and transition behavior on navigation.

## Impact

- **Code**: `webapp/templates/editor.html` (header restructured into a toolbar; hover-zone markup removed; title-frame gets surface styling), `webapp/static/editor.js` (locale-based date formatting on load, jump-to-number input handling, header button wiring replacing nav-zone listeners, still reusing the existing save-before-navigate flow), `webapp/static/style.css` (header toolbar layout, icon set, elevation/typography treatment, view-transition CSS), and their corresponding tests.
- **No impact** on `app.py` routes, `data.py`, `yaml_store.py`, or the YAML persistence layer - every change here is presentational/interaction, not a change to what gets saved or how items are addressed or ordered.
- **No impact** on the render pipeline, output formats, theme system, or the `text_labels` YAML schema.
