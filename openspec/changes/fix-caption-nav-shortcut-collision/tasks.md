## 1. Update the keydown handler in editor.js

- [ ] 1.1 Remove the `ArrowLeft`/`ArrowRight`-with-modifier navigation branch from the `keydown` listener (`src/photobook_as_code/webapp/static/editor.js`), leaving the existing plain (no-modifier) Arrow-key navigation for the not-focused-in-caption case untouched. Verify by reading the diff that no remaining code path calls `preventDefault()` for `ArrowLeft`/`ArrowRight` when `metaKey` or `ctrlKey` is held.
- [ ] 1.2 Add a new branch for `Enter`: when `event.metaKey || event.ctrlKey` is true, call `preventDefault()`, set `FOCUS_CAPTION_FLAG` in `sessionStorage` if the caption textarea currently has focus (mirroring the removed branch's refocus behavior), and navigate to `nextZone` normally or `prevZone` when `event.shiftKey` is also held. Verify by reading the diff that plain `Enter` (no modifier held) is left completely untouched by the listener, so it still inserts a newline in the textarea via default browser behavior.
- [ ] 1.3 Confirm the boundary case (pressing the shortcut on the first or last photo, where `prevZone`/`nextZone` is absent) still no-ops via the existing `navigate()` guard (`if (!zone) { return; }`), requiring no new guard code.

## 2. Manual verification in a running editor

- [ ] 2.1 Start the editor locally (`photobook-edit-labels --config <file>`) against a small test photo directory/config, and verify Cmd+Enter / Ctrl+Enter navigates to the next photo and Cmd+Shift+Enter / Ctrl+Shift+Enter navigates to the previous photo, both with focus in the caption field and with focus elsewhere, and that navigation still stops at the first/last photo.
- [ ] 2.2 Verify plain Enter inside the caption field still inserts a newline and does not navigate.
- [ ] 2.3 Verify Cmd+Left/Right and Cmd+Shift+Left/Right inside the caption field now perform native caret/selection movement (line start/end) instead of navigating away (macOS), and that Ctrl+Left/Right performs native word-wise movement instead of navigating (Windows/Linux, or emulated via browser devtools platform override) — confirming the collision described in `proposal.md` is fixed.
- [ ] 2.4 Verify autosave still fires before navigation via the new shortcut: edit a caption, press Cmd+Enter (or Ctrl+Enter), and confirm the "Saved" status appears and the edit persists in the YAML config file, matching existing autosave behavior for click-zone and plain-Arrow navigation.

## 3. Regression check

- [ ] 3.1 Run the existing test suite (`pytest`) and confirm it passes, since no Python files are touched in this change.
