## Why

The filmstrip's thumbnail endpoint (`/items/<index>/thumbnail`) was given a long-lived, `immutable` browser cache header for performance. That header's promise - "this URL's content never changes" - is false: the URL is keyed by the item's position in the merged photo+title sequence, and both adding/deleting a title and adding a photo to the folder (picked up on the next server restart) shift every subsequent item's position by one. After either edit, the browser keeps confidently serving stale, wrongly-shifted thumbnails for previously-viewed positions - silently and indefinitely, since `immutable` tells it never to even revalidate. A user captioning a book can end up looking at the wrong photo's thumbnail without any indication something is wrong.

## What Changes

- Stop keying the filmstrip thumbnail's cache identity to the item's position in any ordering (merged item+title index, or photo-list index). Address it by the photo's own identity (filename/resolved path) plus its file-modification time instead, so the URL a browser caches only ever refers to one specific version of one specific file.
- This makes the existing long-lived `Cache-Control: public, immutable, max-age=...` policy actually true, rather than removing or weakening it: a given URL's bytes genuinely never change once served, across title add/delete, across `layout.order`, and across photos added to the folder between server restarts.
- **BREAKING** (internal only, not user-facing): the thumbnail route's URL shape changes from `/items/<index>/thumbnail` to an identity-based path. No stored data, config format, or user-visible behavior is affected - this is a route/caching-key change only.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `text-label-web-editor`: adds an explicit correctness requirement that a filmstrip thumbnail always corresponds to the item currently at that position, surviving title add/delete and photo-folder changes across a restart - closing the gap the current "serve a small thumbnail" requirement left unstated, which let this regression through unnoticed by the spec.

## Impact

- `webapp/app.py`: thumbnail route re-keyed from merged-item `index` to a stable photo identity; `webapp/templates/editor.html`'s filmstrip `<img src>` updated to match.
- `webapp/data.py`: `ThumbnailCache` and `FilmstripItem` adjusted to expose/use the new stable key (photo identity + `file_modified`) instead of the merged-item index.
- No changes to the YAML config format, CLI, or batch operation. No changes to the main per-item display image route (`/items/<index>/image`), which has no caching today and is therefore not affected by this bug - though the same trap would apply if it were ever cached the same way; noted in design.md as a related risk to watch, not fixed here.
