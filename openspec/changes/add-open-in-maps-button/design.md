## Context

See proposal.md - Why/What Changes for motivation and scope. Relevant existing pieces this builds on:

- `app.py`'s `view_item` route (`app.py:36-49`) renders `editor.html` with a `common_context` dict that includes `has_gps=data.has_gps(index)` but never the photo's actual coordinates - nothing today needs them in the browser, since the reverse-geocode button resolves the location server-side via a POST to `/items/<index>/reverse-geocode` (`app.py:147`, using `photo.gps` directly).
- `editor.html`'s header already has an established pattern for an icon-only, conditionally-disabled control: the geo-button (`editor.html:70-74`) uses a real `<button disabled title="...">`. A second pattern already exists for the nav-prev/nav-next links (`editor.html:38-44`): when unusable, the `href` is simply omitted and `aria-disabled="true"` is set instead, since anchors don't support a functional `disabled` attribute.
- The SVG icon sprite (`editor.html:11-30`) defines `icon-chevron-left/right`, `icon-plus`, `icon-trash`, `icon-sunrise`, `icon-geo`, `icon-spinner` as inline `<symbol>` elements, referenced via `<use href="#icon-...">`.
- `data.py`'s `has_gps(index)` (`data.py:110-114`) reads `self.photo_at(index).gps`, which is already an `(lat, lon)` tuple when present.

## Goals / Non-Goals

**Goals:**
- Let the user see the current photo's location on a map with one click, independent of and without altering the existing reverse-geocode button's behavior.
- Keep the control's implementation shape as simple as the feature itself: no server round trip, no async state, since building a maps URL from coordinates already in hand requires neither.

**Non-Goals:**
- Detecting the visitor's platform/browser to choose between a native `maps://`-style scheme and the web URL. The Apple Maps web URL already does this itself (Universal Link on Apple platforms, web fallback elsewhere); adding our own detection would duplicate that and risk getting it wrong.
- A keyboard shortcut for this control. The reverse-geocode button's shortcut exists because it's the frequent, primary action; this is an occasional fallback for when that result is unsatisfying, and it's a normal focusable link reachable by Tab like any other control.
- Changing anything about the reverse-geocode button's own behavior, position, or the "before add-title" ordering constraint it already has.

## Decisions

### Render as a disabled-anchor, not a disabled-button
The geo-button's `<button disabled>` pattern doesn't fit here: activating this control means navigating (opening a URL in a new tab), which is what an `<a href="..." target="_blank" rel="noopener">` does natively, with no JS required for the enabled case. For the disabled case, this reuses the *other* existing convention already in `editor.html` - the nav-prev/nav-next links, which omit `href` and set `aria-disabled="true"` plus a `title` when unusable - rather than inventing a third pattern. `rel="noopener"` is included because the opened tab is cross-origin.

Alternative considered: mirror the geo-button's `<button disabled>` shape exactly, with a small JS click handler calling `window.open(...)`. Rejected because it reintroduces a JS dependency for what a plain link already does, and disabled-anchor is already an established convention in this same file - no new pattern to learn or maintain.

### Pass `lat`/`lon` into the template, build the URL in Jinja
`app.py`'s `view_item` gains `lat`/`lon` (or `None`/`None`) in `common_context`, sourced from `data.photo_at(index).gps` when `has_gps` is true. The template builds the `href` directly (`https://maps.apple.com/?ll={{ lat }},{{ lon }}&q={{ lat }},{{ lon }}`) when coordinates are present, and omits `href` otherwise.

Alternative considered: build the full URL server-side and pass a single `maps_url` string. Rejected as a wash in simplicity either way; passing raw coordinates keeps the URL-construction logic in one place (the template) alongside the disabled/enabled branching that already lives there for the geo-button, rather than splitting "is there a URL" logic across Python and Jinja.

### Coordinate precision: pass through EXIF's decimal-degree floats unrounded
No rounding or truncation - Apple Maps accepts full-precision decimal degrees, and reverse-geocode's own Nominatim call already sends the same unrounded values today, so there's no existing precedent for rounding coordinates for external services in this codebase.

### New `icon-map` SVG symbol
A new inline `<symbol id="icon-map">` is added to the existing sprite block, styled consistently with the other icons already there (same `viewBox="0 0 24 24"`, stroke-based line-icon style matching `icon-geo`/`icon-plus`/etc.). No icon library dependency is introduced, consistent with how every other icon in this file is already hand-drawn inline.

## Risks / Trade-offs

- **[Apple Maps web URLs are an Apple product; behavior on non-Apple/non-Safari browsers depends on Apple's own web app, which this project doesn't control]** → Acceptable: the proposal explicitly chooses this URL because it degrades to a real, usable web map everywhere, rather than failing outright the way a bespoke `maps://` scheme would off Apple platforms.
- **[No keyboard shortcut means slightly less discoverability than the reverse-geocode button]** → Acceptable per Non-Goals; it's an occasional fallback action, and it's still reachable via Tab + Enter like any link.
- **[`target="_blank"` popups can be blocked by some browser configurations]** → Same risk profile as any link opening a new tab; no mitigation beyond the standard `rel="noopener"`, since this is user-gesture-initiated (a direct click), which browsers generally exempt from popup blocking.

## Migration Plan

Purely additive: one new template control, one new icon symbol, one new pair of template variables. No new dependencies, no route changes, no changes to any file the existing reverse-geocode or batch features depend on. No rollback concerns beyond reverting the change.
