## 1. Update Photo Distribution Logic

- [x] 1.1 Add field to `PhotoDistribution` to store photo-to-page assignments for sparse distribution
- [x] 1.2 Update `PhotoDistribution.get_photos_for_page()` to support interval-based sparse distribution
- [x] 1.3 Add helper method to calculate which pages should have photos based on spacing interval
- [x] 1.4 Update `distribute_photos()` to use sparse distribution when pages exceed photos in exact page count mode

## 2. Implement Interval-Based Distribution Algorithm

- [x] 2.1 Calculate spacing interval as `total_pages / total_photos` (floating point)
- [x] 2.2 Generate page assignments by multiplying interval by photo index and rounding
- [x] 2.3 Handle edge cases: ensure first photo on page 0, last photo within page range
- [x] 2.4 Verify each photo is assigned to exactly one page

## 3. Update Tests

- [x] 3.1 Add test for sparse distribution with 8 photos across 15 pages
- [x] 3.2 Add test for sparse distribution with 3 photos across 10 pages
- [x] 3.3 Add test verifying photos are evenly spaced across page range
- [x] 3.4 Add test for edge case: 1 photo across many pages
- [x] 3.5 Verify backward compatibility: behavior unchanged when photos >= pages

## 4. Integration Testing

- [x] 4.1 Test with real configuration: create test fixture with sparse photo distribution
- [x] 4.2 Verify rendered pages have photos at correct intervals
- [x] 4.3 Verify blank pages between photos are truly blank (no photo data)
- [x] 4.4 Test with different photo/page ratios (2:5, 1:10, 8:15, etc.)

## 5. Validation

- [x] 5.1 Run full test suite to ensure no regressions
- [x] 5.2 Test with example-config.yaml and verify output
- [x] 5.3 Verify streaming/generator approach still works efficiently
- [x] 5.4 Check memory usage with sparse distribution (should be unchanged)
