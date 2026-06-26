# OpenSpec

This directory contains the repository's versioned specifications.

## Purpose

OpenSpec is used here to document:

- feature requirements
- behavior of the YAML input format
- the rendering pipeline for PDF, PNG, and JPG outputs
- command line interface expectations

## Layout

- `specs/` stores active specifications for the project
- `templates/` stores reusable templates for future specifications

## Workflow

1. Define or update the relevant spec before implementing a meaningful behavior change.
2. Keep requirements, assumptions, and constraints close to the code in this repository.
3. Update the affected spec whenever CLI behavior, YAML structure, or rendering behavior changes.
