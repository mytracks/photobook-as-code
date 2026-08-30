## Context

See `proposal.md` for motivation. Relevant current state (`webapp/`):

- The editor is a server-rendered, one-item-per-page Flask app (`app.py` + `templates/editor.html`), not a client-side SPA. Every navigation action - previous/next, keyboard shortcuts, jump-to-number, add-title, delete-title - ultimately runs `editor.js`'s `navigate()`: save the pending field via `fetch()`, then `window.location.href = ...` to a real `/items/<index>` page load. The browser's native View Transitions API (`@view-transition { navigation: auto }` in `style.css`) supplies the smooth-transition requirement without any custom transition code.
- `EditorData` (`data.py`) already builds the full merged item list (photos + titles, in render order) on every request, and already computes `is_new_day(index)` per item - the exact grouping logic the per-item "new day" badge uses today. This is the same signal the filmstrip's day dividers need.
- `PhotoDirectoryCache` caches the *metadata* scan (`collect_photos`, which opens every file for EXIF/dimensions) once per running server process, keyed by `(photo_folders, order)`. It does not cache rendered image bytes.
- `item_image` (the existing photo route) resizes to 1600px/quality 85 via PIL, on demand, uncached, on every request. That is appropriately sized for "one photo per page load" and inappropriate for "up to hundreds of thumbnails on the same page."

## Goals / Non-Goals

**Goals:**
- Add the filmstrip as a fully server-rendered part of `editor.html`, consistent with the rest of the app - no introduction of client-side routing or a JS framework.
- Make the currently-displayed item's filmstrip highlight and scroll position correct "for free" on every navigation trigger, by deriving them from the same `index` the rest of the page already renders from, rather than adding separate client-side sync logic.
- Keep thumbnail serving cheap enough that a several-hundred-item book doesn't make every page load slow or hammer the server with expensive PIL work.

**Non-Goals:**
- No virtualization/windowing of the filmstrip DOM - plain `<img loading="lazy">` per cell, relying on native lazy-loading to bound the *initial* request burst. Revisit only if a real book size makes this untenable in practice.
- No client-side prefetching of thumbnails beyond native lazy-loading. Consistent with the precedent set in `speed-up-web-editor-navigation`, which considered and rejected prefetching machinery until it's shown to be needed.
- No live-updating of the filmstrip if the photo directory changes mid-session - same accepted limitation `PhotoDirectoryCache` already documents.
- No drag-to-reorder, multi-select, or editing from within the filmstrip itself - it is a navigation control only.

## Decisions

### 1. New thumbnail route + in-memory cache, separate from `item_image`
Add `GET /items/<index>/thumbnail`, returning a small (~120px on the long edge) JPEG. Back it with a cache keyed by resolved photo path (e.g. a dict on a per-`create_app()` object, mirroring `PhotoDirectoryCache`'s instantiation pattern), so the PIL resize+encode work happens once per photo per server process rather than once per page load. Title items have no thumbnail endpoint - the template renders the "T" placeholder purely in HTML/CSS, no image request involved.

**Alternative considered:** reuse `item_image` with a `?size=thumb` query param. Rejected - it mixes two very different performance profiles (one large uncached image vs. many small cached ones) into one route, and a shared cache keyed loosely by query string is more error-prone than a dedicated route with its own cache.

### 2. Filmstrip is rendered server-side from the same `EditorData` the rest of the page uses
No separate "fetch the item list" endpoint. `view_item` already has the full `items` sequence and the current `index`; the template loops over it once to render filmstrip cells alongside the existing single-item content. This is what makes the highlight/scroll-position-on-load requirement trivial: there is no client-side "which item is current" state to keep in sync, because the whole page - filmstrip included - is rebuilt from `index` on every request.

### 3. Day dividers reuse `is_new_day`, not a client-recomputed rule
The template calls the same per-item `is_new_day(index)` (or an equivalent computed once for the full item list) that already drives the single-item "new day" badge, iterating over consecutive items to decide where to emit a divider cell with its compact date label. One source of truth for "what counts as a new day" across both UI surfaces.

### 4. Delegated click handling in `editor.js`, not per-cell listeners
A single `click` listener on the filmstrip container, resolving the clicked cell via `event.target.closest(...)`, then running the same `save()`-then-`navigate()` sequence the prev/next controls use. This is a different pattern from today's per-element listeners (`prevZone`, `nextZone`, etc.), justified specifically by cell count - attaching hundreds of individual listeners has no benefit here.

### 5. Scroll-into-view is imperative JS run once on page load, not CSS-only
On `DOMContentLoaded`, find the cell matching the current `index` and call `scrollIntoView({ inline: "center", behavior: "instant" })` (`instant`/`auto`, not `smooth` - it's a fresh page load with nothing to animate from). This mirrors the existing small-imperative-JS style already used for e.g. the jump-to-number control and the `FOCUS_FIELD_FLAG` sessionStorage handoff.

### 6. Layout: fixed-height footer, in-flow (not an overlay)
The footer becomes a real flex child of `body` (which is already `display: flex; flex-direction: column`), at a fixed height. `.photo`'s existing `max-height: 60vh` shrinks by a corresponding fixed amount so the caption field stays reachable without scrolling on typical viewports. No fixed/sticky positioning, no z-index layering to reason about - confirmed acceptable per proposal discussion (photos get less display space; the bar is always visible, not collapsible).

## Risks / Trade-offs

- **[Risk]** A very large book (thousands of items) renders a proportionally large filmstrip DOM on every page load, and native `loading="lazy"` alone may not keep the request burst small enough on a slow connection. → **Mitigation**: not addressed now (no real book of that size exists yet, per the non-goals); the thumbnail cache means a second visit to the same book is cheap regardless, and windowing/virtualization is a contained, separable follow-up if it's ever needed.
- **[Risk]** The new thumbnail cache is process-lifetime, in-memory, and unbounded - a very large book could hold many small JPEGs in memory for the life of the server process. → **Mitigation**: thumbnails are small (~120px, JPEG-compressed), and this matches the existing `PhotoDirectoryCache` precedent of accepting unbounded-but-small process-lifetime caching for this single-user, single-session tool rather than building eviction logic that isn't needed yet.
- **[Trade-off]** Reserving fixed vertical space for the filmstrip permanently reduces the photo's maximum display size, on every item, including books with only a handful of photos where the filmstrip adds little value. → Accepted per proposal discussion; no conditional hide/show for small books.

## Migration Plan

Purely additive to `webapp/app.py` (new route), `webapp/data.py` (new cache), `webapp/templates/editor.html`, `webapp/static/editor.js`, and `webapp/static/style.css`. No YAML schema, CLI, or batch-operation changes. Rollback is reverting those files.

## Addendum: cold-start thumbnail performance (real-world testing)

After implementation, real-world testing against a 600-photo book showed the filmstrip taking ~1-2s to fill in on first open. Diagnosis (measured, not assumed):

- The test fixtures used during development are 1600x1200; real camera/phone photos are commonly ~12MP (e.g. 4032x3024). `_render_thumbnail`'s cost scales with source resolution: ~3ms/photo at 1600x1200 vs. **~33ms/photo at 4032x3024** (measured on a synthetic 12MP JPEG with photographic-like detail, not a flat-color image).
- The browser's `loading="lazy"` fetches some batch of near-viewport thumbnails on load; against a cold `ThumbnailCache`, a 60-photo batch at 12MP cost ~2s **because the dev server handles one request at a time** - this, not a missing-cache problem per se, is what produced the reported delay.
- **`threaded=True` on the dev server was considered and rejected**: measured head-to-head with a real separate-process client (curl - not sharing a GIL with the server, unlike an in-process benchmark) against 60 concurrent thumbnail requests: threaded=False (today's default) = 0.28s, threaded=True = 1.26s. Thread-creation/GIL overhead outweighs any real parallelism for this CPU-bound decode/resize/encode workload. Not applied.

Two fixes were applied instead:

1. **`Image.draft()` before resizing** (`_render_thumbnail`): tells libjpeg to decode at a reduced DCT scale instead of full resolution before immediately downscaling further. No-op for non-JPEG sources. Cut cold-render cost from ~33ms to ~12ms/photo (measured) on the same 12MP test image, with the final `.thumbnail()` call still enforcing the exact output size bound regardless of the draft scale libjpeg actually lands on.
2. **Long-lived `Cache-Control: public, max-age=31536000, immutable` on the thumbnail response**: this is the "browser-side caching" gap that prompted the investigation. It doesn't help the very first open (nothing's cached anywhere yet), but this tool's normal workflow is paging through the whole book one item at a time, and the filmstrip re-renders on every single navigation (full page reload, no client-side state) - without this header, every already-seen thumbnail was being re-fetched over the network on every subsequent item view, for the entire session. Justified by the same read-only-photo-directory-for-the-session assumption `PhotoDirectoryCache` already relies on elsewhere.

**Not applied**: pre-warming the thumbnail cache in a background thread at server startup (would hide the remaining cold-generation cost entirely behind the time the user spends on the first item) - deferred by user choice; the two fixes above were judged sufficient for now. Left as a documented option if the remaining first-open cost is ever worth eliminating.
