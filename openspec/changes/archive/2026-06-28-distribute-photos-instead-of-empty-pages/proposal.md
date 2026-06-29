## Why

When users specify more pages than needed for their photos (e.g., 8 photos across 15 pages), the current behavior fills consecutive pages then leaves trailing pages empty. This creates an unbalanced photobook with all photos clustered at the beginning. Users would prefer photos distributed throughout the entire photobook, creating a more balanced and aesthetically pleasing result.

## What Changes

- Modify photo distribution algorithm to spread photos across all specified pages instead of clustering them consecutively
- Calculate spacing intervals to distribute photos evenly throughout the page count
- Maintain exact page count generation as currently implemented
- Update distribution logic to interleave photos with blank pages when pages exceed photo count

## Capabilities

### New Capabilities

None

### Modified Capabilities

- `photo-layout-engine`: Change photo distribution algorithm from "fill consecutive then trail empty" to "distribute evenly across all pages" when page count exceeds photos

## Impact

- Photo distribution algorithm in layout module
- Layout calculation logic
- Test fixtures for sparse photo distribution scenarios
- User experience for photobooks with more pages than photos
