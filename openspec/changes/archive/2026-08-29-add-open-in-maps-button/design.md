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
- A bare-letter shortcut (like the reverse-geocode button's bare `G`). The reverse-geocode shortcut's bare form exists because it's the frequent, primary action; this remains an occasional fallback for when that result is unsatisfying, so only the modifier form is added.
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

### Alt+G, matched on `event.code` rather than `event.key`
Added to `editor.js`'s single existing `document`-level `keydown` listener: check `event.altKey`, and if the control is enabled (has an `href`), `preventDefault()` and call `mapsButton.click()` - a real click on an `<a href target="_blank">` opens the new tab exactly as a mouse click would, so no `window.open()` call is needed. Unlike the geocode shortcut, no focus is returned anywhere afterward, since activating this control never changes the caption field's content. Alt (not Cmd/Ctrl) is the modifier because it's the same physical key on every platform - no Mac/Windows pairing is needed the way Cmd needs Ctrl as its non-Mac equivalent.

The letter is matched via `event.code === "KeyG"`, not `event.key === "g"`: on macOS, Option+G composes the character "©" rather than producing the letter "g", so `event.key` would never match. `event.code` reports the physical key regardless of what character the modifier composes, which is exactly what's needed here.

This reuses "G" - the same letter as the reverse-geocode shortcut - since both concern the photo's GPS location; a small guard (`&& !event.altKey`) was added to that existing bare-`g`/Cmd+G branch so it can't also fire when Alt is held. Without it, on Windows/Linux (where Alt+letter keeps `event.key` as the plain letter, unlike macOS's Option composition), pressing Alt+G outside the caption field would satisfy the existing branch's own condition and trigger the reverse-geocode lookup at the same time as the new maps shortcut - two unrelated actions firing from one keypress.

No bare `g`-outside-Alt branch is added for this control (see Non-Goals) - the Alt modifier is required in every case, so the handler doesn't need the reverse-geocode branch's extra guard against firing while a text field has focus; Alt+G is treated as one unconditional combination, active everywhere.

#### Superseded: Cmd+M/Ctrl+M
The first attempt mirrored the reverse-geocode shortcut's modifier form directly: Cmd+M/Ctrl+M, checked via `event.metaKey || event.ctrlKey`. Discarded after manual testing: in Safari, Cmd+M is macOS's own "minimize window" shortcut (`Window > Minimize`), handled by the application before the keydown event ever reaches the page's JS - `preventDefault()` has no effect on a shortcut the DOM never sees. Alt+G doesn't have this problem: Option-key composition is handled entirely within the page's own keyboard event stream, not as an OS/app-chrome-level window action, so there's nothing for the browser to intercept ahead of the page.

## Risks / Trade-offs

- **[Apple Maps web URLs are an Apple product; behavior on non-Apple/non-Safari browsers depends on Apple's own web app, which this project doesn't control]** → Acceptable: the proposal explicitly chooses this URL because it degrades to a real, usable web map everywhere, rather than failing outright the way a bespoke `maps://` scheme would off Apple platforms.
- **[Alt-based shortcuts risk colliding with a browser's or OS's own menu-mnemonic handling]** → Low, and confirmed by manual testing: unlike Cmd+M (an OS/app-chrome-level window action the page never even sees), Option-key composition on macOS is delivered as an ordinary keydown event, so there's no equivalent structural reason to expect interception. Verified working in the user's own Safari - Alt+G opens Maps and does not also trigger the reverse-geocode lookup.
- **[`target="_blank"` popups can be blocked by some browser configurations]** → Same risk profile as any link opening a new tab; no mitigation beyond the standard `rel="noopener"`, since this is user-gesture-initiated (a direct click or a keydown in direct response to one), which browsers generally exempt from popup blocking.

## Migration Plan

Purely additive: one new template control, one new icon symbol, one new pair of template variables, one new keydown branch. No new dependencies, no route changes, no changes to any file the existing reverse-geocode or batch features depend on. No rollback concerns beyond reverting the change.
