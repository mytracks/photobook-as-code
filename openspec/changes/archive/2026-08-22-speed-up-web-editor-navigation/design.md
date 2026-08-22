## Context

See `proposal.md` for motivation and the measured numbers. Relevant current state:

- `EditorData.load_editor_data(config_path)` (`webapp/data.py`) does two things on every call: `load_config()` (cheap YAML parse, ~ms) and `collect_photos(photos_dir, order, recursive=False)` (`photos.py`) — which opens *every* photo file with PIL to read EXIF date and dimensions. Measured at ~150-170ms for a real 168-photo album, independent of disk-cache warmth (CPU-bound in PIL decode/EXIF parsing, not I/O).
- `app.py`'s `_load_data_or_404()` helper calls `load_editor_data()` fresh, and is itself called independently from three routes: `view_photo`, `photo_image`, `save_text`. A single "edit caption, click Next" round trip therefore triggers the full rescan three times (~450ms), for one photo actually being viewed.
- `cli.py`'s `main()` already calls `load_editor_data(config)` once at startup for eager validation — that result is currently discarded rather than reused by the server that starts immediately after.
- This re-parse-per-request behavior was a deliberate original design choice (see the archived `add-text-label-web-editor` change's design.md, decision #2): re-parsing the *YAML config* fresh on every request means hand-edited `text_labels` content is always reflected without cache-invalidation logic. That rationale is about the YAML file's caption content, not about the photo directory's file listing — nothing in the existing spec promises the latter stays live.

## Goals / Non-Goals

**Goals:**
- Eliminate the redundant photo-directory rescans: one scan per running server process instead of one per request.
- Preserve today's "config always re-parsed fresh" behavior for `text_labels`/captions exactly as-is — this change touches only the photo-listing half of `load_editor_data()`.
- Keep `load_editor_data()` usable exactly as today (always-fresh, no caching) for callers that don't opt in — the CLI's startup validation call and every existing test that calls it directly, so no existing test needs to change.

**Non-Goals:**
- Detecting mid-session changes to the photo directory (add/remove/rename) without a restart — explicitly out of scope; see the accepted trade-off in `proposal.md`.
- Caching/optimizing the per-image resize+encode step in `photo_image` (~100ms, measured) — a separable, smaller win; not part of this change.
- Any client-side prefetching of adjacent photos — considered and deliberately not pursued; see `Alternatives considered` below.

## Decisions

### 1. A `PhotoDirectoryCache` class, one instance per `create_app()` call — not a module-level global
```python
class PhotoDirectoryCache:
    def __init__(self):
        self._cache: dict[tuple[str, str], list[PhotoMetadata]] = {}

    def get(self, photos_dir: Path, order: str) -> list[PhotoMetadata]:
        key = (str(photos_dir), order)
        if key not in self._cache:
            self._cache[key] = collect_photos(photos_dir, order=order, recursive=False)
        return self._cache[key]
```
`create_app()` creates one instance and passes it to every `_load_data_or_404()` call. Keying by `(photos_dir, order)` rather than a single unconditional cache means that in the unlikely event `layout.order` is hand-edited mid-session, the next request naturally misses the cache and re-scans once under the new key — free correctness for a case we're not even trying to solve.

**Alternative considered**: a bare module-level `dict` cache in `data.py`. Rejected — it would be shared across every `create_app()` call within a process (harmless for the single-app CLI usage today, but a latent test-isolation hazard: parallel or repeated `create_app()` calls in the test suite would share state through global mutable module state for no benefit). A per-instance object passed explicitly is no more code and removes the risk entirely.

### 2. `load_editor_data()` gains an optional `photo_cache: Optional[PhotoDirectoryCache] = None` parameter
When omitted, behavior is byte-for-byte identical to today (always calls `collect_photos()` fresh). Only `app.py`'s route handlers pass a cache instance. This means:
- `cli.py`'s existing startup-validation call needs no change (and could optionally be wired to reuse the same cache the server then uses, saving that one-time rescan too — worth doing, since `create_app()` already exists at that point in `cli.py`'s call sequence, but this is a minor addition, not the core of the change).
- Every existing test in `test_webapp_data.py` that calls `load_editor_data(config_path)` directly continues to exercise the always-fresh path unchanged.

### 3. The YAML config parse (`load_config()`) is untouched
Still called fresh on every request. It's cheap (millisecond-scale even at hundreds of `text_labels` entries, per the original design's own measurement) and is what makes autosaved captions show up immediately on the very next request — that property is preserved exactly.

## Risks / Trade-offs

- **[Risk]** Photos added/removed/renamed in the photo directory while the server is running are not picked up until restart (see `proposal.md`) → **Mitigation**: none needed for this tool's actual usage pattern (captioning an already-finalized set of photos); documented here and in the proposal rather than solved, consistent with how the original editor's design.md documented similar known limitations (e.g. the YAML round-trip's blank-line collapsing) rather than engineering them away.
- **[Risk]** If `layout.order` is hand-edited mid-session, the *first* request after the edit still pays one fresh rescan (not zero) → **Mitigation**: this is strictly better than today (which pays that cost on *every* request), and the cache-key design makes it correct automatically with no explicit invalidation logic.

## Alternatives considered

**Client-side prefetching of adjacent photos**, the originally-requested direction: rejected as the primary fix because it doesn't address the actual bottleneck (the redundant rescan happens on the *current* photo's own three requests regardless of prefetching) and would add two more full rescans per view (one per prefetched neighbor) on top of today's three. Once this cache fix lands, per-request cost drops to ~100ms (just the current photo's resize/encode) and the original complaint — perceptible lag on every navigation — is resolved without prefetching. Prefetching remains available as a later, separate, smaller optimization if the remaining ~100ms is ever worth hiding further.

## Migration Plan

Purely additive/internal change to `webapp/data.py` and `webapp/app.py` — no schema, dependency, or persisted-state changes, and no route contract changes. Rollback is reverting those two files.
