## Why

Creating physical photobooks currently requires manual layout work in proprietary desktop software or expensive online services. This project enables developers and automation enthusiasts to generate professional photobook layouts programmatically using simple YAML configuration files, making photobook creation reproducible, version-controlled, and automatable.

## What Changes

- Add CLI tool for generating photobook layouts from YAML configuration
- Support standard paper sizes (DIN A4, Letter, etc.) and custom dimensions
- Implement automatic photo layout generation with configurable photos-per-page
- Add theme system for consistent styling across pages
- Generate output as single PDF or individual page images (PNG/JPG)
- Support common photo formats (JPG, PNG)

## Capabilities

### New Capabilities

- `yaml-configuration`: Parse and validate YAML config files that specify photo sources, page dimensions, layout preferences, and theme selection
- `photo-layout-engine`: Automatically arrange photos on pages based on user-specified constraints (photos per page or total pages), handling different aspect ratios and orientations
- `theme-system`: Apply predefined visual themes controlling borders, spacing, backgrounds, and overall aesthetic
- `output-generation`: Render final layouts to PDF or individual page images with print-ready quality

### Modified Capabilities

<!-- No existing capabilities to modify -->

## Impact

- New CLI tool as main entry point
- Dependencies on image processing library (e.g., Pillow/PIL or ImageMagick)
- Dependencies on PDF generation library (e.g., ReportLab or similar)
- YAML parsing library
- New project structure with theme definitions, layout algorithms, and rendering pipeline
