## Why

The web editor's keyboard shortcut for photo navigation (Cmd/Ctrl+Arrow, added in `enhance-web-editor-viewing-experience` so navigation works "even while the caption text field has focus") hijacks the native OS text-editing shortcut bound to the same keys: Cmd+Left/Right moves the caret to the start/end of a line on macOS, and Ctrl+Left/Right jumps by word on Windows/Linux. Because the handler calls `preventDefault()` unconditionally whenever a modifier is held, native caret movement (and Shift-extended selection) never gets a chance to run while typing a caption — a reflexive line-start/word-jump keypress instead silently navigates to a different photo, autosaving the one being edited and auto-focusing the caption field on the new one. In a workflow the editor was built around ("repeated over hundreds of photos per book"), this turns a common muscle-memory edit into a surprising, disorienting jump that risks the next keystrokes landing in the wrong photo's caption.

## What Changes

- Retire Cmd/Ctrl+Arrow (in any Shift-held form) as a photo-navigation trigger entirely. When a text field has focus, these combinations fall through to native browser/OS text-editing behavior instead of being intercepted, on both platforms.
- Introduce Cmd/Ctrl+Enter (navigate to next photo) and Cmd/Ctrl+Shift+Enter (navigate to previous photo) as the new keyboard shortcut for photo navigation. Plain Enter continues to insert a newline in the caption field, matching default `<textarea>` behavior; Cmd/Ctrl+Enter has no native meaning inside a `<textarea>` and no OS/browser-chrome reservation on either platform. The shortcut remains usable regardless of where focus currently is, reusing the existing save-before-navigate and refocus-caption-on-load behavior unchanged.
- Update the `text-label-web-editor` spec's keyboard-shortcut scenario to describe Cmd/Ctrl+Enter / Cmd/Ctrl+Shift+Enter, and drop the outdated "Ctrl+Arrow on non-Mac platforms" framing — the implementation has always accepted either modifier key on any platform, and the new shortcut keeps that same either-modifier, any-platform behavior.

**Out of scope for this change** (explicitly deferred):
- Any on-screen hint or affordance revealing the shortcut exists (it was undiscoverable before this change and stays that way for now).
- Adding an Escape-to-blur behavior or any other new caption-field interaction.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `text-label-web-editor`: the "Navigate photos in configured order" requirement's keyboard-shortcut scenario changes from Cmd/Ctrl+Arrow to Cmd/Ctrl+Enter (next) / Cmd/Ctrl+Shift+Enter (previous), and gains an explicit guarantee that native text-editing modifier+Arrow combinations (including Shift-extended selection) are never intercepted while a text field has focus.

## Impact

- `src/photobook_as_code/webapp/static/editor.js`: remove the ArrowLeft/ArrowRight-with-modifier branch of the `keydown` handler; add an Enter-with-modifier branch that checks `shiftKey` to pick direction. The `FOCUS_CAPTION_FLAG` sessionStorage refocus mechanic is reused unchanged, just triggered by the new chord.
- No changes to templates, CSS, routes, persistence/autosave logic, or dependencies.
