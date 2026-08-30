## 1. Stable identity key

- [x] 1.1 Add a `photo_thumbnail_key(photo: PhotoMetadata) -> str` helper in `webapp/data.py`: a short (16 hex char) SHA-256-derived hash of `f"{photo.path}:{photo.file_modified.isoformat()}"`. Unit test: same photo (same path + mtime) yields the same key across two calls; two distinct photos yield different keys; the same path with a different `file_modified` yields a different key.
- [x] 1.2 Update `ThumbnailCache` (`webapp/data.py`) to key its internal dict by `photo_thumbnail_key(photo)` instead of `str(photo.path)`, so a file replaced in place under the same name (different mtime) no longer reuses a stale cached render even within one running server process. Update/extend its existing tests to cover this.

## 2. Route and lookup

- [x] 2.1 Add `EditorData.photo_by_thumbnail_key(key: str) -> Optional[PhotoMetadata]` (`webapp/data.py`): scans `self.photos`, returns the first photo whose `photo_thumbnail_key(...)` matches, or `None`. Unit test: looking up a known photo's key returns that photo; an unrecognized key returns `None`.
- [x] 2.2 Add `GET /photos/<key>/thumbnail` in `webapp/app.py`: resolve `key` via `photo_by_thumbnail_key`, 404 if not found, otherwise serve `thumbnail_cache.get(photo)` with the same `Cache-Control: public, immutable, max-age=...` headers the old route used. Remove the old `GET /items/<index>/thumbnail` route entirely (see design.md - no backward-compat shim).
- [x] 2.3 Update tests: rewrite the existing thumbnail-route tests (`tests/test_webapp_app.py`, currently targeting `/items/<index>/thumbnail`) to target the new `/photos/<key>/thumbnail` shape - smaller-than-main-image, 404 for an unknown/title key, cache-header assertions.

## 3. Filmstrip wiring

- [x] 3.1 Add a `thumbnail_key: Optional[str]` field to `FilmstripItem` (`webapp/data.py`), populated via `photo_thumbnail_key(...)` for photo items, `None` for title items; update `EditorData.filmstrip_items()` accordingly. Update its existing tests to also assert the key is present for photos and absent for titles.
- [x] 3.2 Update `templates/editor.html`'s filmstrip photo cell to build the thumbnail `<img src>` from `url_for('photo_thumbnail', key=item.thumbnail_key)` instead of `url_for('item_thumbnail', index=item.index)`. The cell's own navigation `href`/`data-index` (position-based, used for click-to-navigate and highlighting) are unchanged.
- [x] 3.3 Update the filmstrip markup tests (`tests/test_webapp_app.py`) that currently assert on `/items/<index>/thumbnail` appearing in a cell's markup to assert on the new `/photos/<key>/thumbnail` shape instead.

## 4. Regression coverage for the actual bug

- [x] 4.1 Add an integration test in `tests/test_webapp_app.py` reproducing the reported bug directly: record the thumbnail bytes served for a photo before adding a title before it, add the title, then assert the *same photo* (now at a shifted index) is served by its thumbnail URL, and that the URL itself is unchanged by the shift (proving a browser's long-lived cache would still be correct).
- [x] 4.2 Add the symmetric test for delete-title (shift the other direction).
- [x] 4.3 Add a test for the photo-folder-plus-restart scenario: build an `EditorData`/`ThumbnailCache` pair, note a photo's thumbnail key, simulate a folder change that shifts photo order (e.g. add a file that sorts earlier) by constructing a fresh `EditorData` over the updated directory (representative of a restart, since `PhotoDirectoryCache` is process-lifetime), and assert the original photo's thumbnail key is unchanged.

## 5. Verification

- [x] 5.1 Run the full test suite (`pytest`) and confirm it passes. (464 passed.)
- [x] 5.2 Manually reproduce the originally reported scenario against a real fixture: view the filmstrip, add a title before a photo whose thumbnail was already visible, confirm (via the test-client-based checks above, since browser tooling isn't available this session) that the shifted photo's thumbnail URL - and therefore what a real browser would show - is unaffected by the shift. Confirmed against a 9-photo/2-title fixture: added a title before p03.jpg, causing p06.jpg to shift from index 6 to index 7 - its thumbnail URL and served bytes were unchanged by the shift.
