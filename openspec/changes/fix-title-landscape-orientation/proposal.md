## Why

Title slots are hardcoded to report `portrait` orientation to the layout matcher (`TitleLabel.orientation` in `text_labels.py`), on the theory that a portrait-shaped slot is what a title needs. In practice this was a wording mistake in the original `add-title-slots` decision - the intent was for titles to render as wide, banner-like text, i.e. `landscape`. It went unnoticed because the `clean2` theme's `[portrait, landscape, landscape]` template happens to give its "portrait" slot a wide `1.0×0.33` box, so most titles rendered wide by coincidence. Whenever a title's neighboring photos are themselves both portrait, the matcher instead picks an all-portrait template, dropping the title into a genuinely narrow, tall slot - visibly "portrait mode" text where a wide title band was intended. This was reproduced on page 21 (and page 190) of `ostseekreuzfahrt.yaml`.

## What Changes

- **BREAKING**: `TitleLabel.orientation` now reports `landscape` instead of `portrait` for layout template matching. Any theme that lacks a landscape-inclusive layout template at a count where a title is used will now fail to match with a `LayoutError` where it previously succeeded (and, conversely, themes lacking a *portrait*-inclusive template at those counts - previously required - no longer need one for titles).
- Update `title-slots` spec requirement text, the `add-title-slots` design rationale reference in the README, and `docs/theme_migration.md` to describe titles as presenting `landscape` orientation, not `portrait`.
- No change to title content, styling, chronological merge/insertion behavior, or the timestamp tie-break rule - only the orientation value used for template matching.

## Capabilities

### Modified Capabilities
- `title-slots`: The "Present title slots as ... orientation for layout matching" requirement changes from `portrait` to `landscape`, including its scenario examples.

## Impact

- Code: `src/photobook_as_code/text_labels.py` (`TitleLabel.orientation`).
- Docs: `README.md` ("Title Slots" section), `docs/theme_migration.md`.
- Tests: existing unit/integration tests asserting `TitleLabel.orientation == 'portrait'` or asserting portrait-template matching for titles (in `tests/`) need updating to `landscape`.
- Themes: built-in themes (`classic`, `modern`, `clean`, `clean2`) need at least one landscape-inclusive layout template at each item count where a title can appear; verify none regress to a `LayoutError`. User-authored theme/config combinations relying on a portrait-only template at a title-bearing count will break and need a landscape-inclusive template added.
