## Context

See `proposal.md` - Why/What Changes for motivation and scope. This design covers only the presentation layer: `webapp/templates/editor.html`, `webapp/static/editor.js`, `webapp/static/style.css`. No route, data model, or persistence-layer change is involved (`app.py`, `data.py`, `yaml_store.py` are untouched).

Two existing mechanics carry over unchanged and everything below builds on them:
- `editor.js`'s `save()` (autosave the current text field on blur or before navigating) and `navigate(zone)` (prevent default, `save()`, then `window.location.href = zone.href`) - the pattern every new navigation trigger (header prev/next, jump-to-number) must reuse so in-progress edits are never lost.
- The server already renders `has_prev`/`has_next` and passes each item's real target URL; only the DOM shape those hrefs live in changes, not how they're computed.

## Goals / Non-Goals

**Goals:**
- Consolidate navigation and title actions into one header toolbar, replacing three separate interaction idioms (hover zones over the photo, a full-width button under the text field, a plain static span) with one consistent, always-visible one.
- Make the date/time display, jump-to-item, and navigation transitions feel native to the viewer's browser and platform, without adding a client-side framework or build step.
- Keep every change here progressive-enhancement-friendly and framework-free, consistent with the app's existing zero-build, server-rendered-HTML-plus-a-single-`<script>` architecture.

**Non-Goals:**
- No change to routes, item indexing, or the merged photo/title ordering logic.
- No general internationalization of interface copy ("Add title", "New day", etc.) - only the photo's own date/time value is locale-formatted, per the proposal's scope note.
- No confirmation step added to title deletion. Its current one-click-no-confirm behavior is unchanged by this proposal; it was raised during exploration as a separate, pre-existing risk this change doesn't worsen (delete only becomes more precisely targetable, not less safe), and is left for a future change if the user wants it addressed.

## Decisions

### Header becomes a toolbar: `[prev] position [next]  filename  ...  [contextual action]`
Layout, left to right: previous button, the position/jump control, filename - then, right-aligned, the one contextual action for the current item type (add-title on a photo, delete-title on a title). This groups "where am I / move" on the left and "what can I do here" on the right, and is a direct implementation of the pager pattern (`‹ 2/264 ›`) the user asked for.

**Boundary buttons stay present but disabled**, rather than being omitted the way today's `{% if has_prev %}` conditional anchor is. Rendering `<a>` without `href` and `aria-disabled="true"` when a direction isn't available keeps the toolbar's width and element order stable across the whole browsing session - an always-omit/insert approach would cause the toolbar to visibly reflow every time the user hits the first or last item. This also means a screen reader announces "previous, unavailable" at the start of the book instead of silently having no previous control at all, which is arguably better than today's behavior, not just different.

**Narrow-viewport handling**: the filename is the first thing to truncate (`text-overflow: ellipsis`) or drop below a width threshold; the toolbar itself never wraps to a second row. Position control and both action slots (nav + contextual) always stay visible since they're the load-bearing controls.

### Date/time formatting moves to the client, driven by `Intl.DateTimeFormat`
`data.py`'s `display_date()` keeps computing the filename-fallback case (still a server-side, tz-agnostic decision: does this photo have a known capture date at all), but for the known-date case the server now emits the raw capture timestamp as an ISO 8601 string (e.g. `data-date="2025-06-14T09:00:00"` on `.date-display`) alongside a plain-English fallback text for no-JS clients. On load, `editor.js` replaces that text using `new Intl.DateTimeFormat(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(isoString))` - the `undefined` locale argument means "use the browser's own locale," which is the actual requirement (not `Accept-Language`, which is a weaker, less precise proxy for the same thing).

EXIF capture times carry no timezone. Parsing an ISO string with no offset makes the JS `Date` treat it as local time in the *viewer's* browser - the same tz-agnostic wall-clock-time behavior the app already has today (today's Python-formatted string is equally tz-naive). No behavior change, just formatting language/convention now follows the viewer instead of always being English.

**Alternative considered**: format server-side using the `Accept-Language` header (e.g. via `babel`). Rejected - it's a new dependency, it's a materially weaker signal than the browser's actual `Intl` locale (no visibility into the user's manual 12h/24h override, etc.), and it would split date-formatting logic across two languages for no benefit given the editor already ships and runs its own JS.

### Jump-to-number: the position span becomes a real, focusable control
`<span class="position">` is replaced with a `<button class="position">2 / 264</button>` so it's keyboard-focusable and correctly announced as interactive (today's plain span is neither). Clicking or activating it (Enter/Space while focused) swaps it in place for a `<input type="text" inputmode="numeric" pattern="[0-9]*">` (not `type="number"` - no browser supports `.select()`/text selection on a number input, and it blocks non-numeric keystrokes at the OS level, which would make the "reject non-numeric entry" scenario unreachable; `inputmode="numeric"` still gets a numeric keypad on mobile), pre-filled with the current position and fully selected so typing immediately overwrites it. All validation (integer, range) is done in JS regardless of input type, so this has no effect on validation logic.

- **Enter** (or the input losing focus via a same-page "confirm" affordance) with a valid, in-range value: run the existing `save()`, then navigate to `/items/<n - 1>` - reusing the same save-before-navigate call every other navigation trigger uses, not a separate code path.
- **Invalid value** (out of `[1, total]`, non-numeric, or empty) on confirm: do not navigate; leave the input in place so the user can correct it (per the spec, no silent clamping).
- **Escape**, or blur without an explicit confirm: discard the input and revert to the static button, without navigating. Blur-cancels (rather than blur-submits) specifically to avoid an accidental navigation from an incidental focus change, which would be jarring compared to every other control in this app being explicit-action-triggered.

### Hover-zone navigation is removed outright, not just restyled
The `.nav-zone` overlay links, their opacity-on-hover CSS, and the black-gradient background are deleted entirely rather than fixed in place - per the user's explicit direction, prev/next now lives solely in the header. This is also what makes the title-page "invisible frame" problem (proposal point 4 from exploration) structurally disappear rather than needing a separate fix: there's no longer a hover affordance anchored to the photo's presence for the title-frame's absence to break.

The header prev/next controls stay real `<a href="...">` elements (not `<button>` + JS-only handlers), matching the existing pattern's progressive-enhancement property: they work as plain links even without JS, and `editor.js` intercepts the click only to run `save()` first when JS is available.

### Title actions become header controls, not a body button
"Add title" and "Delete title" move into the header's right-aligned contextual slot, rendered as a small icon+label control (not the current full-width bordered button). Exactly one is ever shown per item, mirroring today's `{% if is_title %}` mutual exclusivity - no new state to track. These remain JS-driven `fetch()` calls (as they are today; there was never a no-JS `<form>` fallback for them), so this change is purely placement and visual weight, not a behavior or progressive-enhancement change.

### Empty title-frame gets its own surface, independent of the nav-zone fix
Even with hover zones gone, `.title-frame` is still visually bare space today. It gets the same kind of bounded surface treatment the photo already has implicitly via its own border (`background: var(--surface)`, a border, and a border-radius matching the photo/textarea), so a title page reads as "an intentional slot with no photo" rather than "a gap where something is missing."

### Cross-document View Transitions for all navigation
Add `@view-transition { navigation: auto; }` to `style.css`. This is a native, CSS-only opt-in for the browser to automatically cross-fade between full page loads on same-origin navigations - covering link clicks (header prev/next) and script-driven navigations (`window.location.href = ...` used by jump-to-number and add/delete-title) alike, with no JS changes needed beyond what already exists.

**Alternative considered**: rewrite navigation to be `fetch`-and-replace (SPA-style partial updates) to get a smooth transition. Rejected - it would mean taking on client-side routing/state management the app has deliberately avoided so far, for a benefit the native View Transitions API gets for free at a fraction of the complexity.

### Visual system: elevation, type hierarchy, and one inline SVG icon set
- Replace the flat `1px solid var(--border)` on `.photo` and `textarea` with a soft `box-shadow`-based elevation (e.g. a subtle shadow plus a hairline border), so these read as raised surfaces against the near-black background rather than flat-outlined boxes.
- Give `.date-display` materially more size/weight contrast against the surrounding metadata (position, filename) so it reads as the page's clear focal point, matching its role as the one thing centered and standalone on the page. Exact scale is an implementation-time call, not frozen here.
- Replace the emoji (🌅) and HTML-entity chevrons (`&lsaquo;`/`&rsaquo;`) with one small inline `<svg>` icon set (chevron-left, chevron-right, plus, trash, sunrise), defined once as a hidden `<symbol>` sprite in `editor.html` and referenced via `<use>`, using `currentColor` so every icon automatically follows its button's existing text color/hover state instead of needing its own color rules.
- Use the existing `--accent` color on the textarea's focus state (currently `--muted`), giving the one moment of active editing the app's one accent color instead of a neutral gray.

## Risks / Trade-offs

- **Removing the full-height hover click zones removes a very large, easy-to-hit navigation target** (previously the entire left/right half of the photo) in favor of small header buttons → this is a real, deliberate trade-off, not a side effect: it directly resolves the "too prominent" and "invisible frame" problems at the cost of a smaller click target. Keyboard shortcuts (arrow keys, Cmd/Ctrl+Enter) remain unchanged and are the low-effort path for anyone who relied on the large hit area for rapid paging.
- **Cross-document View Transitions aren't supported in every browser** → this is an inherent progressive enhancement: unsupported browsers simply ignore the `@view-transition` rule and keep today's instant navigation with zero visual regression. No feature-detection branching is needed.
- **A busier header (five potential elements: prev, position, filename, next, contextual action) risks crowding on narrow viewports** → mitigated by the truncation priority above (filename first), and by keeping the toolbar a single non-wrapping row.
- **Boundary buttons changing from "absent" to "present but disabled" is a small, real behavior change** for anyone relying on their absence (e.g. a screen-reader user who previously heard nothing) → judged an improvement (an announced, disabled control communicates the boundary explicitly) rather than a regression, but worth naming since it's not purely additive.
