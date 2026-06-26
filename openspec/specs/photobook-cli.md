# Photobook CLI Specification

## Status

Initial baseline.

## Scope

This specification describes the expected behavior of the photobook command
line utility that generates photobooks from YAML definitions.

## YAML Input

- The application accepts YAML files as the primary input format.
- YAML documents describe the photobook structure, page content, and output
  configuration.
- Invalid or incomplete YAML must be rejected with clear error reporting.

## Rendering Pipeline

- The system transforms YAML input into an internal photobook representation.
- The rendering flow must support generating PDF, PNG, and JPG outputs.
- Rendering behavior should remain deterministic for the same input assets and
  configuration.

## CLI Behavior

- The CLI must expose a clear entry point for generating photobooks from YAML.
- Users must be able to select or request supported output formats.
- Failures must be surfaced through non-zero exit behavior and understandable
  diagnostics.

## Future Extensions

Future specs can refine:

- YAML schema details
- asset discovery and validation
- layout and pagination rules
- renderer-specific options
- automation and release workflows
