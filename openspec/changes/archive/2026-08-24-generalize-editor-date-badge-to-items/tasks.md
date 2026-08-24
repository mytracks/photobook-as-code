## 1. Data layer (`data.py`)

- [x] 1.1 Generalize `EditorData.display_date` / `date_taken_iso` to branch on `is_title(index)`: read from `title_at(index).timestamp` (formatted the same way as a known photo capture date, no filename fallback) when the item is a title, and keep the existing photo-path behavior otherwise. Verify with unit tests asserting both a title's and a photo's `display_date`/`date_taken_iso`.
- [x] 1.2 Rewrite `is_new_day` to compare each item's own best-available date (photo: `sort_date.date()`; title: `timestamp.date()`) against the immediately preceding item in the merged `items` sequence, instead of comparing consecutive entries in `photos` alone. Verify with a new test: a title is the first item of a new day, and the same-day photo immediately following it does NOT get `is_new_day`.
- [x] 1.3 Confirm existing photo-only `is_new_day`/`display_date` tests and the title-in-between test (`test_photo_lookups_still_work_around_titles`) still pass unchanged under the new logic.

## 2. Route layer (`app.py`)

- [x] 2.1 Update `view_item` so both the title and photo branches pass `date_display`, `date_taken_iso`, and `is_new_day` (removing the current divergence where the title branch omits them). Verify by requesting `/items/<index>` for a title index and confirming the response context includes all three.

## 3. Template & styling (`editor.html`, `style.css`)

- [x] 3.1 Move the `.date-header` block out of the `{% if not is_title %}` guard so it renders above both photos and titles.
- [x] 3.2 Reorder the markup so the `new-day-badge` element precedes the `date-display` span in the DOM, and verify visually that the badge renders to the left of the date/time.
- [x] 3.3 Update the badge's `title` attribute text from "First photo of a new day" to "First item of a new day".
- [x] 3.4 Invert `.new-day-badge` styling to a filled treatment - `background: var(--accent)`, `color: var(--bg)`, dropping the translucent background/outline-only look - and verify visually that it reads as clearly more prominent than the surrounding date text.

## 4. Verification

- [x] 4.1 Run the full test suite (`pytest`) and confirm it passes, including the new title-date and title-new-day-badge tests from tasks 1.1-1.2.
- [x] 4.2 Launch the editor locally against a config with a title that starts a new day, and manually verify: the title shows a date/time, the title (not the following same-day photo) carries the left-positioned filled new-day badge, and a photo that legitimately starts a new day on its own still carries the badge as before.
