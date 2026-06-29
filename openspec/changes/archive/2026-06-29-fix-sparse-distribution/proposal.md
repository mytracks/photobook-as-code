## Why

When users specify an exact page count, photos are not distributed evenly across all pages. Instead, pages are filled consecutively with trailing empty pages. For example, with 168 photos and 100 pages, the first 84 pages get 2 photos each and the remaining 16 pages are empty. Users expect photos to be distributed across all requested pages to create a balanced photobook.

## What Changes

- Fix photo distribution logic to spread photos across ALL pages when exact page count is specified
- Ensure the last pages get photos too (not just early pages)
- Change distribution from "consecutive fill + empty trail" to "even spread across all pages"
- Preserve sparse distribution behavior for cases where pages > photos

## Capabilities

### New Capabilities

None

### Modified Capabilities

- `photo-layout-engine`: Fix photo distribution to use all specified pages evenly, not just fill consecutive pages

## Impact

- Photo distribution calculation in layout module
- Page rendering logic to support uneven photo distribution across page range
- Existing tests may need updates to reflect corrected behavior
- Users with exact page counts will see photos distributed throughout the photobook instead of clustered at the beginning
