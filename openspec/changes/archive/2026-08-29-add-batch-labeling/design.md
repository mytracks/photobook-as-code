## Context

See proposal.md - Why/What Changes for motivation and scope. Relevant existing pieces this builds on:

- `EditorData` (`webapp/data.py`) already computes the merged photo+title sequence in display order, `is_new_day(index)`, `is_title(index)`, `has_gps(index)`, and text/title lookups, backed by a `PhotoDirectoryCache` that avoids re-scanning the photo folder (expensive - it opens every file for EXIF) on every request.
- `yaml_store.py` already has round-trip-safe primitives for editing a caption (`save_photo_text`), inserting a new caption entry (`insert_new_entry`), inserting a new title (`insert_new_title_entry`/`insert_new_title`), and editing a title (`save_title_text`) - each doing its own `load_document`/`save_document` cycle so comments/formatting/unrelated content survive.
- `geocoding.py` calls Nominatim synchronously via `urllib.request`, with no throttling today; `app.py`'s `POST /items/<index>/reverse-geocode` calls it once per click.
- The CLI (`webapp/cli.py`) starts the app with plain `app.run(host, port)` - Werkzeug's dev server, single process, no debug/reloader.
- The devcontainer has no OS locale data installed beyond `C`/`C.utf8`/`POSIX`, so `locale.setlocale()` cannot produce German (or other) month/weekday names here or, most likely, in the shipped Docker image either.

## Goals / Non-Goals

**Goals:**
- Run date-insertion and reverse-geocoding across the whole book from one settings page, respecting Nominatim's 1 req/sec limit, without blocking the browser for the run's full duration.
- Make interruption (cancel, crash, closed tab) safe: no partial-item writes, and re-running is the resume mechanism.

**Non-Goals:**
- Multi-user or multi-process deployment of the web editor (it remains a single-user local tool, one config file, one browser tab at a time).
- Persisting job state across a server restart.
- General i18n of the rest of the editor UI - Babel is used only for formatting the inserted date text, not for the editor's own chrome.

## Decisions

### Background job with in-memory store + polling, not a blocking request or a streaming response
A full book with geocoding enabled can take minutes at 1 req/sec. A single blocking `POST` would hold a Werkzeug worker and the browser's connection open for that whole time with no progress feedback and no way to cancel. A chunked/streaming response was considered - it avoids a job store, but cancellation would depend on the browser dropping the connection and the server noticing (unreliable with Werkzeug's dev server), and progress is lost entirely if the tab closes.

Instead: `POST /batch/start` validates the form, snapshots the request's `Accept-Language` header (needed later for date formatting, and only available inside a request context), spawns a plain `threading.Thread` running the worker loop, and returns immediately. A module-level dict in the new `webapp/batch.py`, guarded by a `threading.Lock`, holds one `JobState` per job id (counts, current item description, state: running/done/cancelled/error). `GET /batch/status/<job_id>` reads it; `POST /batch/cancel/<job_id>` sets a `threading.Event` the worker checks between items (never mid-request, so a Nominatim call already in flight always completes).

This works with the CLI's existing plain `app.run(host, port)` unmodified - the worker thread is spawned explicitly by application code, not by Werkzeug's own per-request threading, so it runs concurrently with request handling regardless of Werkzeug's `threaded=` setting for incoming HTTP requests.

Only one job may run at a time (a second `POST /batch/start` while one is running is rejected); this app has exactly one user looking at exactly one config file, so supporting concurrent jobs would add complexity (per-job cancellation UI, job listing) with no real use case.

In-memory-only state means a server restart loses progress tracking for a running job - acceptable since every item already processed is already saved to the YAML file (see below), so nothing is lost, only the progress display.

### Reuse the existing per-item `yaml_store` primitives for every write
Rather than building a bulk-write path, the batch worker calls the same `save_photo_text`/`insert_new_entry`/`save_title_text`/`insert_new_title_entry` functions the per-item editor already uses (plus one new primitive for prepending to an existing title, see below), once per item that needs a write. Each call does its own full `load_document`/`save_document` round trip.

This is the same "durable as you go" design the spec requires (cancel-safety), reuses already-correct comment/formatting preservation instead of re-deriving it, and is cheap enough not to matter: a few hundred small YAML round-trips are milliseconds each, dwarfed by the geocoding rate limit's ~1 second per photo. No batching of multiple entries into one write is needed.

New primitive: `prepend_to_title_entry(config_path, text_labels, label, date_text)` in `yaml_store.py`, mirroring `save_title_text` but joining `date_text` and the existing title's content as `f"{date_text}\n\n{existing}"` - matching the manual convention already visible in `hamburg+potsdam.yaml` (a plain date line, blank line, then hand-written Markdown).

### One fixed `EditorData` snapshot per job, not re-derived mid-run
The worker computes `EditorData` once at job start (via the app's existing `PhotoDirectoryCache`, so it doesn't re-scan the photo folder) and walks its merged `items` list once, in order. All eligibility decisions - which item is the new-day boundary, whether a title already occupies it, which photos have GPS - are read from this one snapshot, never recomputed mid-run.

This matters because title-mode date insertion creates new title entries as the run progresses; if eligibility were re-derived from a fresh `EditorData` after each write, newly-inserted titles would shift subsequent merged-sequence indices and could double-process or skip items. Since the worker instead tracks progress by walking the original snapshot's `photos` list and consulting the snapshot's precomputed `is_new_day`/`is_title` results (recorded once, before any writes), this can't happen. Writes are addressed by identity (a specific `PhotoMetadata` or `TextLabel`/`TitleLabel`), not by position in the merged sequence.

Identity alone isn't quite enough, though: `yaml_store.find_entry_index`/`find_title_entry_index` locate an entry by matching identity, but return its *index* into whatever `text_labels` list they were given - and `save_photo_text`/`prepend_to_title_entry` then apply that index to a document they load fresh from disk at call time. Passing the job-start snapshot's `text_labels` for this lookup broke under multiple sequential writes: an earlier write in the run (e.g. a new title inserted before a later entry) shifts that later entry's position in the actual file, so an index computed against the stale, job-start list lands on the wrong entry once applied to the now-different on-disk document. The fix is `batch._current_text_labels(config_path)`, which every write re-reads immediately beforehand (one extra `load_document` per write, negligible next to the rate limit) - eligibility still comes from the fixed snapshot, but *where to write* always comes from the current file.

### Rate limiter lives in `geocoding.py` itself
A module-level `_last_request_at` timestamp plus a `threading.Lock`, checked at the top of `reverse_geocode()`: if less than 1 second has passed since the last call anywhere in the process, sleep for the remainder before issuing the request. This protects the existing single-photo endpoint too (it just never notices in normal use, since a human can't click faster than 1/sec), and means the batch worker's loop doesn't need its own timing logic - it just calls `reverse_geocode()` for each eligible photo and the throttle is transparent.

### POI-only resolution as a stricter sibling of the existing resolver
`geocoding.resolve_place_name()` already prefers a named place and falls back to city/country. Batch's POI-only mode needs "named place, or nothing" - implemented as a `strict: bool` parameter (default `False`, preserving today's behavior for the single-photo button) rather than a second function, since the logic is a strict subset (skip the fallback branches) and keeping it in one function keeps the two modes visibly related.

### Deduplicate resolved location text within a run
Photos taken minutes apart near the same landmark commonly resolve to the identical text (e.g. several consecutive photos near the Fernsehturm all resolving to "Fernsehturm"), and inserting that same text into every one of their captions is noise, not signal. `JobState` carries a per-run `used_location_texts: Set[str]`, checked and updated in `_process_photo` right after `resolve_place_name` returns a non-`None` result: the first photo to produce a given text gets it inserted and the text is recorded; a later photo in the same run whose resolved text is already in the set has that piece withheld (tallied as a new `skipped_duplicate_location` counter) while any unrelated date-marker piece for that same photo is unaffected, since the two pieces are assembled independently in `new_pieces` before the single combined write. The set lives only on the `JobState` instance - nothing is persisted, so a later run starts with an empty set and can reuse any text again.

Matching is exact-string, not fuzzy/case-insensitive - simplest, and matches the motivating example ("Fernsehturm" repeating verbatim); a near-miss (different casing, a trailing detail Nominatim sometimes adds) is treated as a distinct text rather than guessed at.

### Date formatting via Babel
`babel.dates.format_date(dt, format="d. MMMM y", locale=<parsed from Accept-Language>)` produces "30. April 2026" for `de` and the equivalent for other languages, with no OS locale data required (confirmed unavailable in this devcontainer). The custom pattern (rather than Babel's `format="long"` preset) pins the day-month-year-only shape called for in the spec, independent of what a given locale's own "long" preset happens to include. `Accept-Language` can carry multiple weighted tags (e.g. `de-DE,de;q=0.9,en;q=0.8`); take the first tag, normalize `-` to `_`, and fall back to Babel's default (`en_US`) if it isn't a locale Babel recognizes.

## Risks / Trade-offs

- **[Nominatim occasionally returns 429 despite the 1 req/sec throttle]** → already surfaces as a `GeocodingError` (non-2xx is covered), counted in the batch's "failed" tally; no special-case handling needed.
- **[A batch job survives only as long as the server process]** → acceptable per Non-Goals; every already-processed item is durably saved regardless, so a restart only loses the progress *display*, not work.
- **[Two browser tabs both starting a batch]** → the single-active-job check makes the second `POST /batch/start` a no-op (rejected with a message pointing at the running job), so no double-processing.
- **[Full-book YAML round-trips add up to a few hundred small file writes]** → each is atomic (existing `save_document` writes to a temp file and `os.replace`s), so a crash mid-batch never leaves a corrupt config file, only a config file missing whatever hadn't been written yet.

## Migration Plan

Purely additive: new routes, templates, and one new dependency (Babel). No changes to `text_labels` YAML shape beyond what per-item editing already produces (plain `text`/`title` entries with `timestamp`), so existing configuration files and the CLI's non-batch behavior are unaffected. No rollback concerns beyond reverting the change.
