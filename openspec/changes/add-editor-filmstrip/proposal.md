## Why

The web editor shows one item at a time with prev/next and jump-to-number navigation, but neither lets a user visually locate a specific point in a book of hundreds of items. Jump-to-number requires already knowing a position; prev/next requires stepping through everything in between. A persistent, always-visible filmstrip of thumbnails lets a user recognize a photo by sight and jump straight to it.

## What Changes

- Add a fixed-height footer bar to the per-item editor, always visible below the caption field, showing every item in the book's merged order (photos and titles) as a horizontally scrollable strip of small cells.
- A photo cell shows only that photo's thumbnail image, no caption or date text.
- A title cell shows a bounded placeholder cell containing only a "T" glyph, no title text.
- A compact date-labeled divider is inserted between consecutive cells whenever the item's date differs from the previous item's date (reusing the same day-boundary logic already used for the per-item "new day" indicator), so the strip reads as a scannable timeline rather than an undifferentiated row.
- The cell for the currently displayed item is visually highlighted (and marked `aria-current`) and is scrolled into view automatically whenever the editor loads a new item - whether reached by clicking a filmstrip cell, the header's prev/next controls, a keyboard shortcut, jump-to-number, or add/delete-title - since every one of those already causes a full page reload that re-renders the whole page, filmstrip included, from the same current-item index.
- Clicking a filmstrip cell saves any pending caption/title edit first, exactly like the existing prev/next controls, then navigates to that item.
- Add a new small (thumbnail-sized) photo image endpoint and an in-memory cache for its output, since the existing full-size image endpoint (1600px, uncached, resized on demand) is not suited to serving on the order of hundreds of thumbnails per page load.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `text-label-web-editor`: adds a persistent filmstrip footer for visual navigation across the whole book, including the day-boundary divider markers, current-item highlighting kept in sync across every navigation path, and a new thumbnail image endpoint backing it.

## Impact

- `webapp/app.py`: new route for small thumbnail images; existing `view_item` route's template context gains whatever the filmstrip needs to render (it already has access to the full merged item list via `EditorData`).
- `webapp/data.py`: likely reuse/extend `PhotoDirectoryCache` (or a sibling cache) for rendered thumbnail bytes, keyed the same read-only-directory way the existing photo metadata cache is.
- `webapp/templates/editor.html`: new footer markup rendering all items.
- `webapp/static/editor.js`: delegated click handling on the filmstrip (save-then-navigate, matching the existing prev/next pattern) and scroll-into-view-on-load for the current cell.
- `webapp/static/style.css`: fixed-height footer layout; the photo display area's available height shrinks to accommodate it.
- No changes to the YAML config format, the CLI, or the batch operation.
