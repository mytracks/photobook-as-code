## Context

Today `PhotobookConfig.photos: str` names one directory, resolved relative to the config file by `resolve_photos_path()` and checked by `validate_photos_path()`. `photos.py`'s `discover_photos`/`collect_photos` take a single `Path` and return one sorted list of `PhotoMetadata`. Nothing downstream of that (layout distribution, rendering, text-label association) is directory-aware — matching is entirely by timestamp — so this change is a boundary-level change: parse a list, discover across each entry, and hand the same kind of flat, ordered `List[PhotoMetadata]` to everything that already consumes it. See proposal.md - Why/What Changes for the field rename and multi-folder behavior itself.

## Goals / Non-Goals

**Goals:**
- Replace the single `photos` path with a `photo_folders` list, validated and resolved per-entry.
- Keep every downstream consumer (layout, rendering, webapp) working against one flat, deduplicated, ordered photo list, unaware of folder boundaries.
- Keep existing single-folder configs working with a mechanical edit (rename key, wrap value in a list) rather than a compatibility shim.

**Non-Goals:**
- No per-folder ordering, grouping, or provenance tracking (e.g. "folder = day" semantics) - folders are purely a photo source, not a display grouping.
- No recursive-search config option - `recursive` stays hardcoded `False` at both call sites, unchanged from today.
- No backward-compatible single-string shorthand for `photo_folders` - decided explicitly in favor of one strict list syntax.

## Decisions

**`photo_folders: List[str]`, list-only, snake_case.** Considered accepting a bare string as shorthand for one folder, to avoid touching every existing config. Rejected: one syntax is simpler to validate and document, and the migration touches at most 5 real files plus fixtures - a one-time mechanical cost. `photo_folders` (not `photoFolders`) matches every other key in the schema (`photos_per_page`, `new_page_per_day`, `text_labels`).

**Flat merge, then apply existing `layout.order`.** Photos from all folders are pooled and sorted exactly as a single-folder config is today (alphabetical by filename, or by EXIF/mtime date) - folder listing order has no effect on output order. Considered folder-sequential ordering (all of folder 1, then all of folder 2) to preserve folder grouping, but that would silently break chronological ordering whenever two folders' date ranges overlap (the primary motivating use case - e.g. two people's cameras from the same trip), and would make `layout.order: date` mean different things depending on folder count. Flat merge keeps `layout.order`'s meaning unchanged regardless of how many folders are configured.

**Per-folder existence check, combined-pool emptiness check.** Each listed folder must exist and be a directory (same strictness as today, so a typo'd path is still caught immediately). But an individual folder is allowed to contribute zero photos - only the combined pool across all folders must be non-empty. Rejected requiring every folder non-empty: that's an arbitrary constraint on how someone organizes source folders and would turn reasonable configs (e.g. a folder reserved for a day that turned out photo-less) into errors.

**Dedupe combined pool by resolved photo path, not by folder path.** If two `photo_folders` entries resolve to the same directory (exact duplicate, or different relative/absolute spellings of the same path), the photos they contribute would be identical `Path` objects after resolution, so deduplicating the final photo list (extending today's `sorted(set(photos))` in `discover_photos`) handles this for free without a separate folder-level uniqueness check.

**Rename, don't shim, the Python surface.** `PhotobookConfig.photos` → `photo_folders: List[str]`; `resolve_photos_path()` → `resolve_photo_folders() -> List[Path]`; `validate_photos_path()` → validates each resolved folder. `discover_photos`/`collect_photos` take `directories: List[Path]`. No deprecated aliases are kept - this is an early-stage, single-consumer tool (the real configs in this repo are the only known users), so a clean rename is cheaper than carrying compatibility code.

**`PhotoDirectoryCache` keys on the resolved folder tuple.** `webapp/data.py`'s cache is keyed `(photos_dir: str, order)` today; it becomes keyed on `(tuple(sorted(str(f) for f in resolved_folders)), order)` so the cache key is stable regardless of the order folders were listed in the config (consistent with the "listing order doesn't affect output" decision) and still misses correctly whenever the folder set or `layout.order` changes.

## Risks / Trade-offs

- **[Breaking change]** Every existing config (5 real files, several test fixtures) stops working until edited → Mitigation: this change's tasks include editing all of them; the edit is mechanical (rename key, wrap in a list) and `load_config` raises a clear `ConfigurationError` naming the missing `photo_folders` field rather than failing silently.
- **[Filename collisions across folders]** Two folders can contain files with the same name (e.g. camera numbering resets); since `PhotoMetadata.path` is the full resolved path, downstream identity is unaffected, but `format_text_label_stubs`' filename-only comments could show the same filename twice for genuinely different photos → Mitigation: none needed for this change - comments already tolerate duplicate filenames within a single folder's collisions were never disambiguated by path either, and disambiguating them is out of scope here.

## Migration Plan

- Update `example-config.yaml`, `hamburg.yaml`, `karwendel.yaml`, `mondsee.yaml`, `sevilla.yaml`, and `tests/fixtures/*.yaml` from `photos: <dir>` to `photo_folders:\n  - <dir>` (single-entry list, preserving current behavior exactly).
- No feature flag or phased rollout - this is a local CLI/webapp tool with no deployed service to sequence around; the rename lands in one change.
- Rollback is a plain revert, since no data is persisted in the new shape outside the YAML files themselves.
