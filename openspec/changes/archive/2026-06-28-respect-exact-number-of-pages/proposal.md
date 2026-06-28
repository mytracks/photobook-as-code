## Why

When users specify an exact number of pages in their configuration (e.g., `pages: 100`), the system should generate exactly that many pages in the output, even if it means some pages have fewer photos or are empty. This ensures users can create photobooks with a specific page count for printing requirements or layout preferences.

## What Changes

- Modify photo distribution logic to respect the exact page count specified in configuration
- Ensure pages are generated up to the specified count even if photos run out
- Handle edge cases: more pages than photos, partial page fills, empty trailing pages
- Maintain even distribution of photos across specified pages when possible

## Capabilities

### New Capabilities

None

### Modified Capabilities

- `photo-layout-engine`: Extend photo distribution to strictly respect exact page count from configuration

## Impact

- Photo layout algorithm in layout module
- Page generation logic in renderer module
- Test fixtures for various page count scenarios
