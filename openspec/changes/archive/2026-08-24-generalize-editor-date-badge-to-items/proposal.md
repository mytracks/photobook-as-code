## Why

The web editor's "prominent date" and "new day" indicator were built photo-first, then titles were bolted on as a merged-sequence concept without folding into either. Titles carry a real, always-known timestamp (`text_labels.timestamp` is a required field), so they belong in both the date display and the new-day calculation the same way photos do. Today they're invisible to both: titles show no date/time at all, and the new-day badge is computed by comparing consecutive *photos* only, skipping over titles - so when a title is actually the first item of a new day, the badge lands on the photo that follows it instead of on the title.

## What Changes

- Display the date/time header above titles too, sourced from the title's own `timestamp`, using the same formatting as photos.
- Compute the "new day" indicator over the full merged item sequence (photos and titles together, in display order), comparing each item's own date to the immediately preceding item's date - not photo-to-photo, skipping titles. A title that is the first item of a new day now gets the badge instead of the photo after it.
- Reposition the new-day badge to the left of the date/time (currently renders to the right).
- Invert the badge's visual treatment: filled with the accent color background and dark (`--bg`) text, instead of the current translucent accent-tinted outline chip - for higher contrast and more visual weight.
- Update the badge's tooltip text from "First photo of a new day" to "First item of a new day" so it stays accurate now that a title can hold it.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `text-label-web-editor`: "Display the current photo's date prominently" and "Indicate the first photo of a new day" both become item-scoped (photo or title) rather than photo-only.

## Impact

- `src/photobook_as_code/webapp/data.py` - `EditorData.display_date`, `date_taken_iso`, and `is_new_day` generalize to read from whichever item type is at an index (photo or title) and compare against the merged `items` sequence instead of the `photos` sublist.
- `src/photobook_as_code/webapp/app.py` - `view_item` route stops omitting date/badge context on the title branch.
- `src/photobook_as_code/webapp/templates/editor.html` - `.date-header` block renders for both photos and titles; badge markup moves before the date-display span; tooltip text updated.
- `src/photobook_as_code/webapp/static/style.css` - `.new-day-badge` fill/text color inverted.
- `tests/test_webapp_data.py` - new coverage for a title being the first item of a new day (previously untested; existing title-in-between test happens to pass either way).
