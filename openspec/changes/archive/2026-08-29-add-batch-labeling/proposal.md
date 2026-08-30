## Why

Manually opening every photo in the editor to type a day's date or look up its location doesn't scale to a book of hundreds of photos. The editor already has per-photo reverse-geocoding and per-photo date display; a user should be able to apply both across the whole book in one operation instead of clicking through it item by item.

## What Changes

- Add a new batch page in the web editor, reachable from the per-item editor's header, offering:
  - **Insert date on each new day** (on/off), with a choice of destination: as a plain-text label on the first photo of that day's caption, or as a new title item.
  - **Reverse-geocode every photo with GPS data** (on/off), with a choice of strictness: landmarks/POIs only, or landmarks falling back to city + country (the existing single-photo behavior).
  - A single **skip vs. append** setting shared by both features, controlling what happens when the target caption/title already has content: leave it alone, or add to it.
- The date text is formatted in the language of the browser that starts the batch (matching the locale-awareness the single-photo geocode feature already has for place names), using **Babel** (new dependency) for locale-aware month/weekday names, since the server has no OS locale data to draw on.
- A day already marked by an existing title (title-mode convention) suppresses text-label insertion on the photo that follows it, reusing the existing new-day/title-precedence logic the per-item editor already has.
- When a photo both starts a new day (text-label mode) and has GPS (geocoding enabled), both pieces of text land in that one caption in the same run - the date first, the geocoded location appended below it - regardless of the skip/append setting, which governs only pre-existing manual content.
- A resolved location text is inserted at most once per batch run: if reverse-geocoding resolves the same text (e.g. "Fernsehturm") for more than one photo, only the first such photo gets it - later photos in the same run that resolve to that same text have it withheld, without affecting an unrelated date marker on those photos.
- Reverse-geocoding is rate-limited to Nominatim's documented limit of 1 request/second. The limiter lives in the shared geocoding module so it protects the existing single-photo button too, not just the batch path.
- Because a full-book batch with geocoding enabled can take minutes, the batch runs as a background job with a polling progress view (counts, current item, cancel), not a single blocking request. Each item is saved to the YAML file as soon as it's processed, so a cancelled or interrupted run leaves no partial edits and - combined with the skip setting - can simply be re-run to pick up where it left off.
- The batch always operates on the entire book (every item in the merged photo+title sequence), independent of which item is currently open in the per-item editor.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `text-label-web-editor`: adds the batch page, its settings, the background job lifecycle (start/status/cancel), the day/GPS eligibility and skip-vs-append rules for both sub-features, POI-only resolution, and the shared reverse-geocoding rate limit.

## Impact

- `src/photobook_as_code/webapp/geocoding.py`: add a 1 req/sec throttle shared by all callers; add POI-only place-name resolution (reusing the existing "named place" preference, but without the city/country fallback).
- `src/photobook_as_code/webapp/app.py`: new routes for the batch settings page, starting a job, polling its status, and cancelling it.
- New module for the batch job itself (in-memory job store, background worker thread, per-item eligibility rules, Babel-based date formatting).
- `src/photobook_as_code/webapp/yaml_store.py`: a primitive for prepending to an existing title's content (append mode for title-mode date insertion onto a title that's already there).
- `src/photobook_as_code/webapp/templates/` and `static/`: new batch settings + progress UI, reusing the existing dark theme.
- `pyproject.toml`: new dependency on Babel.
- Tests: batch eligibility rules (new-day/title suppression, skip-vs-append, POI-only fallback), rate limiting, and the job lifecycle endpoints.
