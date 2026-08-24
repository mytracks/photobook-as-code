## Why

The web editor (added in `add-text-label-web-editor`) lets a user page through photos and edit their `text` captions, but `title` entries in `text_labels` are completely invisible to it — that change explicitly deferred title editing as future work. Titles must currently be added, edited, or removed by hand-editing the YAML and reasoning about timestamp ordering relative to photos, which is exactly the manual bookkeeping the editor was built to remove for captions.

## What Changes

- **BREAKING**: The editor's browsing sequence changes from "photos only" to the same merged photo+title sequence the photobook renderer already produces (via the existing `merge_titles_with_photos`), so titles appear in the editor exactly where they'll appear in the rendered book. The route changes from `/photos/<index>` to `/items/<index>`, where `<index>` now indexes into the merged sequence instead of the photo list alone.
- When the current item is a title, the editor displays a text-only page (no photo frame) with an editable field for the title's content, autosaved the same way captions are today (including its Markdown-as-raw-text handling).
- When the current item is a photo, a new "Add title" action creates a new, empty title entry positioned immediately before that photo (using the photo's own timestamp, relying on existing tie-breaking in `merge_titles_with_photos`) and navigates the user to it for editing. This action is only available from a photo; it is not offered when viewing a title.
- When the current item is a title, a new "Delete title" action removes that title's `text_labels` entry from the YAML file and navigates to the photo that followed it, if one exists.
- The round-trip YAML persistence layer (`yaml_store.py`) gains the ability to insert a new title entry and to locate and delete an existing title entry, alongside its existing text-caption insert/update support.

## Capabilities

### Modified Capabilities
- `text-label-web-editor`: The editor's navigable sequence, routing, and page rendering now include titles (not just photos); adds title text editing, adding a title before a photo, and deleting a title.

## Impact

- **Code**: `webapp/data.py` (`EditorData` grows from a photo list + associations to a merged item sequence), `webapp/app.py` (routes renamed/restructured around merged items; new add/delete title endpoints), `webapp/yaml_store.py` (new insert-title and delete-title operations), `webapp/templates/editor.html` + `webapp/static/editor.js`/`style.css` (title-only page variant, add/delete controls), and their corresponding tests.
- **Reused, unchanged**: `text_labels.parse_title_labels` and `text_labels.merge_titles_with_photos` (already exist, used by the renderer, now reused by the editor for ordering).
- **No impact** on the render pipeline, output formats, theme system, or the `text_labels`/`title-slots` YAML schema itself.
