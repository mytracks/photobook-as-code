## 1. `output.py` core changes

- [x] 1.1 Change `generate_output()` to accept an explicit `output_dir: Path` and `base_filename: str` instead of a single `output_path`, and build the final `pdf` file path internally as `output_dir / f"{base_filename}.pdf"`; verify by reading the diff that no branch still infers a directory from `.parent` vs. the path itself
- [x] 1.2 Update `prepare_output_path()` so it only appends the format extension when building a `pdf` path; for `png`/`jpg` it should no longer be used to produce an extension-bearing directory path (adjust or narrow its docstring/usage accordingly)
- [x] 1.3 Verify `generate_png_pages()` / `generate_jpg_pages()` need no changes (they already take `output_dir` + `base_filename` and write `{base_filename}_page_NNN.{ext}` directly into `output_dir`)

## 2. `cli.py` call-site changes

- [x] 2.1 Update the no-`--output` default-path construction in `main()` to call the new `generate_output()` signature: for `pdf`, keep using `prepare_output_path()` to get the file path's directory/base; for `png`/`jpg`, pass `pb_config.get_output_directory()` and `pb_config.get_output_filename(config.name)` (stripped of any extension) directly, with no extension-appending step
- [x] 2.2 Update `--output` override handling: for `pdf`, preserve current behavior (accepts a file path or a directory); for `png`/`jpg`, always treat the given `--output` path as the output directory and derive the base filename from `pb_config.get_output_filename(config.name)`, not from the directory's own name
- [x] 2.3 Verify `click.echo` of "Output files:" after generation still prints the correct final paths (page files inside the flattened directory, not the old nested subfolder) by running the CLI manually against a small fixture config for each format (`pdf`, `png`, `jpg`)

## 3. Test coverage

- [x] 3.1 Add a test in `tests/test_output.py` asserting `generate_output()` with `output_format='jpg'` writes `{base_filename}_page_NNN.jpg` files directly into the given `output_dir`, with no subdirectory created
- [x] 3.2 Add the equivalent test for `output_format='png'`
- [x] 3.3 Add/extend a `tests/test_cli.py` test that runs the CLI end-to-end with `output.format: jpg` (or `png`) in the config and asserts the generated page files exist directly under the configured `output.directory`, with no `<base_filename>.<ext>`-named subfolder present
- [x] 3.4 Add a `tests/test_cli.py` test for the `--output <dir>` override with `png`/`jpg` format, asserting files land directly in `<dir>` using the config-derived base filename (not the directory's own name)
- [x] 3.5 Run the full test suite (`pytest`) and confirm existing `pdf`-format tests still pass unchanged, verifying no regression to `generate_pdf` behavior

## 4. Documentation

- [x] 4.1 Check README.md's output-format section for any example paths implying the old nested-subfolder shape; update if present - none found (README shows config examples only, no example generated output paths)
