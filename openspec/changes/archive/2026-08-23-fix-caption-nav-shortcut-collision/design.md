## Context

See `proposal.md` - Why. The relevant code is a single `document`-level `keydown` listener in `editor.js` (currently ~lines 75-91): it computes `withModifier = event.metaKey || event.ctrlKey`, and for `ArrowLeft`/`ArrowRight` calls `preventDefault()` and navigates whenever `withModifier` is true, regardless of whether the caption `<textarea>` has focus. It never checks `event.shiftKey`, so Shift-held variants (native "extend selection to line/word boundary") are swallowed too. Because `preventDefault()` runs before the browser's own text-editing handling, native caret/selection behavior for these combinations never executes while the modifier is held.

## Goals / Non-Goals

**Goals:**
- Stop intercepting any key combination that carries native text-editing meaning inside a focused text field, on both macOS and Windows/Linux.
- Keep fast keyboard navigation available while the caption field has focus, without requiring the user to click or tab out of it first.
- Keep the shortcut's existing behavior of working identically regardless of platform (either modifier key accepted everywhere), since that's what the implementation has always actually done.

**Non-Goals:**
- No on-screen hint or other discoverability affordance for the shortcut (explicitly deferred in the proposal).
- No change to click-zone navigation, autosave-on-navigate semantics, or the `FOCUS_CAPTION_FLAG` refocus mechanic, beyond swapping which key combination triggers them.
- No new caption-field interactions (e.g., Escape-to-blur) beyond the shortcut swap.

## Decisions

**Retire the Arrow-based chord entirely rather than special-casing it by focus state.** An alternative would be to keep Cmd/Ctrl+Arrow working only when the caption is *not* focused (already true today, since plain-Arrow-without-modifier already navigates in that case) and introduce a separate chord only for the focused case. Rejected: two different shortcuts for the same action, selected by invisible focus state, is harder to learn than one shortcut that always works — and the "unfocused" case is already fully covered by the click zones, so the old chord buys nothing there that isn't already available.

**New chord: Cmd/Ctrl+Enter (next), Cmd/Ctrl+Shift+Enter (previous).** Enter has no native meaning inside a `<textarea>` beyond inserting a newline, and the modifier form of it is not claimed by either platform's text-editing conventions or by browser-chrome/OS-level shortcuts. Alternatives considered and rejected, each because it re-creates the same class of collision:
- Alt/Option+Arrow — native word-wise caret movement on macOS; browser back/forward history navigation on Windows/Linux.
- Cmd+Option+Arrow — Chrome/Safari tab-switching on macOS.
- Ctrl+Alt+Arrow — historically bound to display-rotation by some Windows GPU drivers.
- Page Up/Down — native caret movement/scrolling inside multi-line textareas.
- Cmd+[ / Cmd+] — Safari/Chrome browser back/forward on macOS, the bracket-key twin of the original Cmd+Arrow problem.

Cmd/Ctrl+Enter also has a fitting semantic precedent (Slack/Gmail use it for "commit this text and act"), which lines up with what `navigate()` already does here: save the caption, then advance.

**Keep accepting either modifier key on any platform**, rather than adding platform detection so only Cmd counts on Mac and only Ctrl counts elsewhere. This matches what the code has always actually done — the previous spec's "Ctrl+Arrow on non-Mac platforms" language described an OS branch that was never implemented — and there's no new requirement forcing platform-sniffing complexity to be introduced now.

**Delete the Arrow-modifier branch outright rather than adding a `shiftKey` exclusion to it.** This also restores native Cmd/Ctrl+Shift+Arrow (extend selection to line/word boundary) for free, since that combination is no longer touched by the handler at all — not just the plain-move case the proposal started from.

## Risks / Trade-offs

- **Muscle memory for the old shortcut breaks silently.** Anyone who had learned Cmd/Ctrl+Arrow for photo navigation will find it now edits text instead. → The shortcut was never surfaced on screen (and stays that way per this change's scope), so the population relying on memorized muscle memory for an undocumented chord is expected to be small; the click zones remain an unaffected, discoverable fallback throughout.
- **The new chord is just as undiscoverable as the one it replaces.** → Accepted for this change; a follow-up can add an on-screen hint without touching this behavior.
- **Enter's dual meaning inside the textarea.** Holding Cmd/Ctrl while pressing Enter to insert a newline mid-caption navigates instead of inserting one. → This is the same shape of trade-off as the bug being fixed, but for a much rarer gesture — deliberately holding a modifier while pressing Enter is not a reflex the way Cmd+Left is — and matches the common web convention where modifier+Enter means "submit," not "newline."

## Migration Plan

Not applicable: this is a client-side behavior change confined to `editor.js`, with no persisted data, API, or config-file format affected. The new behavior takes effect for a given browser tab on its next page load after the updated static asset is served.
