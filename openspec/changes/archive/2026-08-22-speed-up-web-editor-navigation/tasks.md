## 1. Photo directory cache (`webapp/data.py`)

- [x] 1.1 Add `PhotoDirectoryCache`: a small class holding a `dict[tuple[str, str], list[PhotoMetadata]]` keyed by `(str(photos_dir), order)`, with a `get(photos_dir, order)` method that computes via `collect_photos()` on first access and returns the cached list thereafter.
- [x] 1.2 Add an optional `photo_cache: Optional[PhotoDirectoryCache] = None` parameter to `load_editor_data()`. When `None` (the default), call `collect_photos()` directly exactly as today. When provided, call `photo_cache.get(photos_dir, config.layout.order)` instead. The `load_config()` call and everything else in the function stays unchanged.

## 2. Wire the cache into the Flask app (`webapp/app.py`)

- [x] 2.1 In `create_app()`, construct one `PhotoDirectoryCache()` instance and pass it as `photo_cache=` in every call inside `_load_data_or_404()`.
- [x] 2.2 Optionally reuse the same cache for the CLI's eager startup validation: give `create_app()` an optional `photo_cache` parameter (default constructs its own if not given), and update `cli.py`'s `main()` to construct one `PhotoDirectoryCache`, pass it to both the validation `load_editor_data(config, photo_cache=...)` call and `create_app(config, photo_cache=...)`, so the startup validation's scan isn't thrown away.

## 3. Tests

- [x] 3.1 Add a test confirming `load_editor_data()` without a `photo_cache` argument is unaffected (existing tests already cover this implicitly by continuing to pass unchanged, but add one explicit test that two calls with no cache each independently re-scan — e.g. by asserting call counts via monkeypatching `collect_photos`).
- [x] 3.2 Add a test confirming that with a shared `PhotoDirectoryCache`, two calls to `load_editor_data()` for the same `(photos_dir, order)` only invoke the underlying directory scan once (monkeypatch/spy on `collect_photos` and assert call count).
- [x] 3.3 Add a test confirming a `PhotoDirectoryCache` used across two different `order` values (e.g. `"date"` then `"alphabetical"` on the same directory) scans once per distinct key, not once total.
- [x] 3.4 Extend `tests/test_webapp_app.py` (or add a new test) confirming that navigating across multiple routes in one `create_app()`-created app (e.g. `GET /photos/0`, then `GET /photos/0/image`, then `GET /photos/1`) only triggers one underlying photo-directory scan for that app instance.

## 4. Manual verification

- [x] 4.1 Re-run the timing measurement from the proposal (`load_editor_data` called twice in a row, with and without a shared cache) against a real config (e.g. `hamburg.yaml`) to confirm the second call drops from ~150ms to near-zero.
- [x] 4.2 Run the editor against a real config, page through several photos including with unsaved caption edits, and confirm navigation feels noticeably faster with no change in correctness (captions still save, dates/new-day indicator still correct).
- [x] 4.3 Run the full test suite (`pytest`) and confirm all tests pass.
