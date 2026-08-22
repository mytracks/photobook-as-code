## Context

See `proposal.md` for motivation. Relevant current state:

- `templates/editor.html` + `static/style.css` + `static/editor.js` are plain server-rendered Jinja2/vanilla-JS, no build step (per the original editor's design.md decision #4) — this change keeps that shape.
- `EditorData` (`webapp/data.py`) already builds the ordered photo list and text associations fresh per request; it's the natural place to add the two new per-photo computations this change needs.
- `PhotoMetadata` (`photos.py`) already carries `date_taken` (EXIF, may be `None`), `file_modified` (always set, from `stat().st_mtime`), and real `width`/`height` (populated by actually opening the file with PIL during `collect_photos`) — no new metadata extraction is required anywhere.
- `PhotoMetadata.sort_date` already implements the fallback chain `date_taken or file_modified` and is always defined in practice, since `file_modified` is unconditionally set.
- `editor.js` already has a `keydown` listener that navigates on bare `ArrowLeft`/`ArrowRight`, but only when the caption textarea does not have focus (`document.activeElement !== textarea`).

## Goals / Non-Goals

**Goals:**
- Implement all five improvements from the proposal with no new runtime dependencies and no client-side build step.
- Keep `EditorData` as the single place that computes derived per-photo display data, consistent with its existing role.
- Keep the server stateless/re-parse-per-request behavior of the existing editor untouched.

**Non-Goals:**
- No touch/swipe gesture support (not requested).
- No thumbnail pre-fetching/pre-loading of adjacent photos (out of scope; the loading-jump fix is a layout fix, not a performance optimization).
- No change to autosave, the YAML round-trip writer, or the save endpoint's contract.

## Decisions

### 1. Compute date display and new-day flag in `EditorData`
Add `EditorData.display_date(index)` and `EditorData.is_new_day(index)`:
- `display_date`: if `photo.date_taken` is set, format it with weekday (e.g. "Saturday, June 14, 2025"), built with `strftime("%A, %B %d, %Y")` and a manual leading-zero strip on the day number (rather than the non-portable `%-d`/`%#d` platform-specific format codes) — avoids a Windows/Linux `strftime` portability trap for a single-line formatting need. If `date_taken` is `None`, return the photo's filename instead (the spec's fallback behavior), so the caller never has to re-check which case it's in.
- `is_new_day`: compares `photos[index].sort_date.date()` to `photos[index - 1].sort_date.date()` (or `True` for index 0). Deliberately uses `sort_date` (the existing `date_taken`-or-`file_modified` fallback), not `display_date`'s value — so the day-boundary signal stays computable even for photos with no EXIF date, per the spec's "grouping uses best-available date even when display falls back to filename" scenario.

**Alternative considered**: compute these in the Flask route (`app.py`) instead. Rejected — `EditorData` already owns "derive per-photo facts from the ordered photo list," and route handlers stay thin, matching the existing split.

### 2. Full-height click zones are anchored to the photo, not the page
The user asked for zones "spanning the full height" of the page, but also (resolving the narrow-viewport question) chose to have them "overlay bands on the photo's own edges" so they work at any window width. Doing both literally would make the zones cover the full page height *and* sit at the photo's edges — which, given the caption textarea sits directly below the photo at the same column width, would place invisible click zones on top of the textarea's left/right edges, intercepting clicks meant for placing the text cursor or selecting text.

**Decision**: zones span the photo's own height (not the full page height), positioned as bands over the outer ~15% of the photo's rendered width on each side (minimum ~48px for a comfortable click/tap target), with a subtle hover affordance (a chevron that fades in) so an otherwise-invisible click region is discoverable. This is a narrower reading of "full height" than the literal request — flagged here explicitly since it's a deliberate scope refinement, not an oversight. It still replaces today's small corner text links with a dramatically larger, always-visible-at-any-width target, which is the actual goal behind the request.

**Alternative considered**: literal full-page-height zones, with an explicit exclusion rectangle carved out over the textarea's bounding box. Rejected as needless complexity (recomputing/observing the textarea's box on every resize) for a marginal height gain, given the photo is already the tallest single element on the page.

### 3. Keyboard shortcut: `Cmd`/`Ctrl`+Arrow works everywhere, including inside the textarea
`editor.js` adds a `keydown` handler that checks `event.metaKey` (Mac) or `event.ctrlKey` (Windows/Linux) together with `ArrowLeft`/`ArrowRight`, calls `preventDefault()`, and navigates regardless of `document.activeElement` — including while the caption textarea is focused. This intentionally overrides the browser's native "move caret to line start/end" (Mac) or "move caret by word" (Windows/Linux) behavior for that key combination while the field is focused; confirmed as an acceptable trade-off. The existing bare-arrow-when-unfocused behavior is unchanged and remains available for browsing without a modifier key.

### 4. New template variables, no new template objects
`view_photo` gains `date_display`, `is_new_day`, `photo_width`, `photo_height` as flat kwargs to `render_template`, matching the existing flat-kwargs style (`index`, `total`, `filename`, `text`, `has_prev`, `has_next`) rather than passing a richer photo object into Jinja.

### 5. Layout-shift fix uses the photo's real dimensions, not a generic placeholder
`editor.html` sets the `<img>`'s `width`/`height` attributes (or an inline `aspect-ratio` style) from `photo_width`/`photo_height`, which the browser uses to reserve the correct box before the image byte stream arrives — this alone eliminates the shift with no JavaScript and no guessed/generic placeholder box. The reserved space renders as the theme's background color (dark) until the image paints in; no shimmer/spinner is added, keeping this a pure layout fix rather than a new loading-affordance feature.

## Risks / Trade-offs

- **[Risk]** Click zones sized to the photo's height, not the full page, is a narrower interpretation of "spanning the full height" than literally requested → **Mitigation**: still a large, discoverable, always-present target at any window width; flagged explicitly above for the user to react to before implementation.
- **[Risk]** Overriding `Cmd`/`Ctrl`+Arrow inside the textarea removes native line/word-jump cursor movement while composing a caption → **Mitigation**: deliberate, user-confirmed trade-off (see proposal discussion); plain arrow keys for in-field cursor movement are unaffected.
- **[Risk]** The new-day flag uses `sort_date`, which falls back to filesystem `file_modified` for photos with no EXIF date — a copied/re-exported photo could show a spurious day boundary → **Mitigation**: same known limitation as the date-display fallback itself; the spec already frames the indicator as a display-order signal, not an authoritative per-day claim.
- **[Risk]** Reserving image space assumes `photo_width`/`photo_height` are non-zero → **Mitigation**: `collect_photos` already opens every photo file with PIL to populate these; a file that fails to open already breaks image serving today, so this introduces no new failure mode.

## Migration Plan

Purely additive/styling change within the existing `webapp` module — no schema, dependency, or persistence changes. Rollback is reverting the CSS/HTML/JS/template/data.py edits; there is no persisted state specific to this change.
