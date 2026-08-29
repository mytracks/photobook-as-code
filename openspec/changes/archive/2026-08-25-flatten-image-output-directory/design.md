## Context

See proposal.md - Why for the root cause. Summary of the current call chain for the config-derived default path (`cli.py` `main()`, no `--output` override):

```
pb_config.get_output_directory()     -> output_dir   (e.g. ./output)
pb_config.get_output_filename(...)   -> filename      (e.g. "mondsee", no extension)
prepare_output_path(output_dir, filename, format)
    -> always appends ".{format}"    -> output_path = ./output/mondsee.jpg
generate_output(pages, format, output_path, ...)
    -> output_dir = output_path.parent if format == 'pdf' else output_path
    -> output_dir.mkdir(...)         -> creates ./output/mondsee.jpg/  (a directory named like a file)
    -> base_name = output_path.stem  -> "mondsee"
    -> generate_jpg_pages(pages, output_dir, base_name, ...)
```

`prepare_output_path` was written for the single-file `pdf` case and reused unmodified for `png`/`jpg`, which need a directory + a base name rather than a single file path. `generate_output` then tries to recover those two pieces by inspecting `.parent` vs. the whole path, which is what materializes the fake-file-looking directory.

The `--output` CLI flag can also override this path directly (`cli.py:165-166`, bypassing `prepare_output_path` entirely) and is documented as accepting "a file path or a directory" - today that's ambiguous for `png`/`jpg` since `generate_output` decides directory-vs-file purely from `output_format`, not from whether the given path looks like a file.

## Goals / Non-Goals

**Goals:**
- For `png`/`jpg`, page files land directly in the resolved output directory - no subfolder named after the base filename/format.
- Keep `pdf` output behavior byte-for-byte unchanged.
- Make the directory-vs-base-filename split explicit in the code, rather than encoding both into one `Path` and re-deriving them later.

**Non-Goals:**
- No change to overwrite/collision behavior for any format (confirmed with user: silent overwrite stays, matching current PDF behavior).
- No change to `output.directory` / `output.filename` config schema or semantics.
- Not fixing `ensure_unique_filename` / timestamp-suffix behavior (currently unused by the CLI - `ensure_unique=False` is hardcoded in `main()`); out of scope for this change.
- Not addressing PDF's own `--output`-as-directory edge cases beyond what's already documented, since that path is unchanged.

## Decisions

### 1. `generate_output()` takes an explicit output directory and base filename, not one overloaded `output_path`

Change the signature so the directory and the base name are two separate parameters for every format, instead of one `Path` that's a real file path for `pdf` and a not-quite-a-directory for `png`/`jpg`:

```python
def generate_output(pages, output_format, output_dir: Path, base_filename: str, ...):
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_format == 'pdf':
        output_path = output_dir / f"{base_filename}.pdf"
        generate_pdf(pages, output_path, ...)
        return [output_path]
    elif output_format == 'png':
        return generate_png_pages(pages, output_dir, base_filename, ...)
    elif output_format == 'jpg':
        return generate_jpg_pages(pages, output_dir, base_filename, quality, ...)
```

`generate_png_pages` / `generate_jpg_pages` are unchanged - they already take `(pages, output_dir, base_filename, total_pages, ...)` and just write `{base_filename}_page_NNN.{ext}` into `output_dir`. They were never the problem; the problem was what got passed in as `output_dir`.

**Alternative considered:** Keep the single-`output_path` signature and just fix the `.mkdir()` call (e.g. special-case stripping the extension for png/jpg before mkdir). Rejected because it patches the symptom, not the underlying "one value, two meanings" design - the same class of bug (inferring directory vs. file from a path's shape/suffix) would remain latent for any future format or refactor. Splitting the parameters makes the contract explicit and matches what `generate_output`'s own docstring already claimed the behavior should be.

### 2. `prepare_output_path()` only appends an extension for `pdf`; for `png`/`jpg` it resolves to a directory + base name

`prepare_output_path` currently always appends `.{format}` to build a path (used by `main()` for the no-`--output` case). Since `generate_output` now wants a directory and a base filename rather than one path, `main()`'s default-path construction changes to call `generate_output` directly with `pb_config.get_output_directory()` and `pb_config.get_output_filename(config.name)` - no extension-appending step for `png`/`jpg` at all. For `pdf`, the existing extension-appending behavior of `prepare_output_path` is kept (still used to build the single output file path passed through, unchanged).

**Alternative considered:** Make `prepare_output_path` format-aware and return either a file path or a directory path depending on format, keeping `generate_output`'s single-`output_path` signature. Rejected: this just moves the "one value, two meanings" ambiguity from `generate_output` into `prepare_output_path` instead of removing it, and callers would still need to know which shape they got back.

### 3. `--output` CLI override: unchanged for `pdf`, directory-only for `png`/`jpg`

Per user decision: for `pdf`, `--output` keeps accepting either an explicit file path (`--output my_book.pdf`) or a directory (current behavior: `output_path.parent` /  `output_path` split based on suffix presence is preserved for this format only). For `png`/`jpg`, `--output <path>` is now always treated as the output directory; the base filename still comes from config (`pb_config.get_output_filename(...)`) exactly as in the no-override case. This is a narrowing of previously-ambiguous behavior, not a new capability - today, passing `--output some/existing/directory` for `png`/`jpg` already partially worked as a directory (via the `output_path.suffix`-empty branch in `generate_output`), just with the base filename wrongly derived from the directory's own name instead of the config. After this change the base filename is always the config-derived one, consistently.

## Risks / Trade-offs

- **[Risk] Existing user output directories already contain a stray `<name>.jpg`/`<name>.png` folder from prior runs of the buggy behavior.** → Mitigation: this change only affects where *new* runs write files; it does not delete or migrate old subfolders. Worth a one-line release/changelog note so users know to clean up the old nested folder by hand if they want to.
- **[Risk] Any external tooling/scripts a user built around the current `output/<name>.<ext>/<name>_page_NNN.<ext>` path shape will break.** → Mitigation: this is exactly the bug being fixed and the behavior was undocumented and untested, so there's no supported contract being broken. Called out explicitly in the proposal as a behavior change.
- **[Trade-off] `--output` semantics now differ by format** (file-or-directory for `pdf`, directory-only for `png`/`jpg`). → Accepted per user decision; alternative (directory-only for all formats) would change existing, presumably-relied-upon `pdf` behavior, which is out of scope.

## Migration Plan

No data migration. This is a CLI/library behavior fix:
1. Implement the signature/logic changes in `output.py` and the call-site changes in `cli.py`.
2. Add test coverage in `tests/test_output.py` for the `png`/`jpg` directory-flattening behavior (currently untested).
3. Update README's output-format documentation if it shows example paths (check during implementation).
4. No rollback concerns beyond a normal revert - no persisted state changes shape.
