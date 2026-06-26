# photobook-as-code
Command line utility to create photobooks (PDF, PNGs, JPGs) using YAML files.

## Working with OpenSpec

This repository now keeps product and implementation specifications in
`/openspec`.

### Structure

- `/home/runner/work/photobook-as-code/photobook-as-code/openspec/README.md` explains how OpenSpec is used here.
- `/home/runner/work/photobook-as-code/photobook-as-code/openspec/specs/photobook-cli.md` contains the initial specification baseline.
- `/home/runner/work/photobook-as-code/photobook-as-code/openspec/templates/spec-template.md` is the template for new specs.

### Usage

1. Add or update specs in `/openspec/specs` before implementing a larger change.
2. Use the template in `/openspec/templates/spec-template.md` for new features or behavior changes.
3. Keep the OpenSpec documents aligned with the YAML contract, rendering flow, and CLI behavior of the project.
