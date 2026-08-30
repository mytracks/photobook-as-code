## 1. Thumbnail serving

- [x] 1.1 Add a thumbnail cache (e.g. `ThumbnailCache`, keyed by resolved photo path) in `webapp/data.py`, alongside `PhotoDirectoryCache`, that resizes a photo to a small (~120px long edge) JPEG once and reuses it on subsequent lookups; verify with a unit test in `tests/test_webapp_data.py` that a second lookup for the same photo does not re-invoke the PIL resize path.
- [x] 1.2 Add `GET /items/<index>/thumbnail` in `webapp/app.py`, returning the cached small JPEG for the photo at that index (404 for a title index, mirroring `item_image`'s existing behavior); wire the cache instance through `create_app()` the same way `photo_cache` already is.
- [x] 1.3 Add a test in `tests/test_webapp_app.py` covering: thumbnail route returns a smaller image than `item_image` for the same photo, and 404s for a title item's index.

## 2. Filmstrip markup

- [x] 2.1 In `view_item` (`webapp/app.py`), pass the full merged item list (already available via `EditorData`/`data.items`) plus enough per-item info to render a filmstrip cell (index, is_title, and - for photos - the thumbnail URL) into the template context.
- [x] 2.2 In `templates/editor.html`, render a footer element after the caption field containing one cell per item: an `<img>` (thumbnail) for a photo, a bounded "T" placeholder for a title, each as a link/button targeting `/items/<index>`.
- [x] 2.3 Insert a day-boundary divider cell (with a compact date label) between consecutive items whose date differs, reusing the same day-comparison logic `EditorData.is_new_day` already implements for the single-item "new day" badge (extend/reuse rather than duplicate).
- [x] 2.4 Give the current item's cell a distinguishing class/attribute and `aria-current="true"`; give every cell an accessible name (photo: filename/position; title: identifies it as a title, not the bare "T").
- [x] 2.5 Add `loading="lazy"` to filmstrip `<img>` thumbnails.

## 3. Filmstrip behavior (JS)

- [x] 3.1 In `editor.js`, add a single delegated `click` listener on the filmstrip container that resolves the clicked cell, then runs the existing `save()`-then-navigate sequence (matching how `nav-prev`/`nav-next` already behave) to the clicked item's URL.
- [x] 3.2 On page load, scroll the current item's filmstrip cell into view (`scrollIntoView({ inline: "center", behavior: "instant" })`).
- [ ] 3.3 Manually verify, for the previous/next controls, the arrow-key shortcuts, jump-to-number, and add/delete-title, that after navigating the filmstrip's highlighted cell matches the new current item and is scrolled into view - confirming this needs no extra sync code beyond 3.2, since every trigger causes a full page reload. NOT DONE INTERACTIVELY: the user declined browser tooling this session, so this couldn't be clicked through in a real browser. Equivalent evidence gathered instead: every trigger navigates via the same `navigate()`/full-reload path (verified by reading `editor.js`), and a test-client fetch of an arbitrary `/items/<N>` confirms that page's filmstrip correctly marks cell N `aria-current` (see manual fixture check in the session). Left unchecked pending an actual browser click-through.

## 4. Layout

- [x] 4.1 In `style.css`, add filmstrip container styles: fixed height, horizontal `overflow-x: auto`, flex row of fixed-size cells, current-cell highlight style, title-cell placeholder style, day-divider style.
- [x] 4.2 Reduce `.photo`'s `max-height: 60vh` by the filmstrip's fixed height so the caption field remains reachable without page scrolling on a typical viewport. NOT VISUALLY VERIFIED: no browser tooling available this session; the `calc(60vh - var(--filmstrip-height))` rule is implemented but hasn't been eyeballed at real viewport heights.

## 5. Verification

- [x] 5.1 Run the full test suite (`pytest`) and confirm existing web editor tests still pass unchanged. (448 passed; two pre-existing tests updated to scope their assertions past the filmstrip's now-legitimate `<img>`/`data-index` markup - see commit/diff.)
- [ ] 5.2 Start the editor against a real multi-day, multi-title test fixture and manually confirm: filmstrip shows every item, day dividers land in the right places, clicking a distant filmstrip cell saves the current caption and navigates there, and the highlight/scroll-position track correctly across every navigation trigger listed in 3.3. PARTIALLY DONE: built a synthetic 9-photo/2-title/3-day fixture and drove it through the Flask test client - confirmed correct item order, correct day-divider placement (3 dividers, right labels), correct `aria-current` targeting, and correct/working thumbnail generation (120x90px, ~821 bytes vs. ~30KB full image, cached, 404s for a title index) against real JPEG files. The literal "click a distant cell in a browser" and visual layout checks are not done - left unchecked; see note on 3.3.

## 6. Cold-start thumbnail performance (follow-up from real-world 600-photo testing)

User-reported: opening a 600-photo book took ~1-2s for the filmstrip to fill in. Root-caused (see design.md addendum) to cold `ThumbnailCache` generation cost at real camera resolution (~12MP), serialized by the dev server's one-request-at-a-time handling - not a missing-cache problem in the sense first suspected, though the browser-caching gap was real too.

- [x] 6.1 Use `Image.draft()` in `_render_thumbnail` (`webapp/data.py`) to have libjpeg decode at a reduced scale before resizing, instead of full-resolution decode + throw away most of it; verified ~3x cold-render speedup on a synthetic 12MP photo (33.2ms -> 11.9ms), and added a regression test confirming output dimensions stay correctly bounded regardless of source resolution (`tests/test_webapp_data.py`).
- [x] 6.2 Add long-lived, `public`/`immutable` `Cache-Control` headers to the `/items/<index>/thumbnail` response (`webapp/app.py`) so the browser stops re-fetching already-seen thumbnails on every subsequent navigation, for the rest of the session; added a test asserting the header shape (`tests/test_webapp_app.py`).
- [x] 6.3 Considered and rejected `threaded=True` on the dev server as a fix: measured head-to-head with a real separate-process client (curl, not sharing a GIL with the server) against 60 concurrent thumbnail requests, threaded=True was slower (1.26s) than the current single-threaded default (0.28s) for this CPU-bound workload - not applied.
- [ ] 6.4 (Not done - deferred per user's choice) Pre-warm the thumbnail cache in a background thread at server startup, to hide the remaining cold-generation cost behind the time the user spends looking at the first item rather than paying it reactively while scrolling.

## 7. Caption-presence badge on photo cells (follow-up request)

- [x] 7.1 Add a `has_caption: bool` field to `FilmstripItem` and compute it in `EditorData.filmstrip_items()` (`webapp/data.py`) from `text_for(index)` being non-empty; `False` for title items.
- [x] 7.2 In `templates/editor.html`, render a small `aria-hidden="true"` "T" overlay badge on a photo cell when `item.has_caption` is true.
- [x] 7.3 Style the badge in `style.css`: small, positioned over a corner of the thumbnail, visually distinct from a title cell's full-size "T" placeholder.
- [x] 7.4 Add unit/integration tests: `filmstrip_items()` reports `has_caption` correctly for captioned/uncaptioned/empty-caption photos; markup test confirming the badge appears only for a captioned photo's cell.
- [x] 7.5 Run the full test suite and confirm it still passes. (456 passed.) Not visually eyeballed in a real browser - same standing limitation as the rest of this change's visual checks (no browser tooling available this session).
