## 1. Fix Photo Distribution Logic

- [x] 1.1 Update `PhotoDistribution.get_photos_for_page()` to use even distribution algorithm for exact page count mode
- [x] 1.2 Calculate base photos per page as `total_photos // total_pages`
- [x] 1.3 Calculate remainder as `total_photos % total_pages`
- [x] 1.4 Return `base + 1` photos for first `remainder` pages, `base` photos for remaining pages
- [x] 1.5 Ensure sparse distribution logic remains unchanged (only fix dense distribution)

## 2. Update Tests

- [x] 2.1 Update test `test_exact_page_count_with_excess_pages` to expect even distribution
- [x] 2.2 Update test `test_very_high_page_count` to expect even distribution
- [x] 2.3 Add test for the reported bug case: 168 photos across 100 pages
- [x] 2.4 Verify all pages receive photos in exact page count mode
- [x] 2.5 Verify backward compatibility: photos_per_page mode unchanged

## 3. Validation

- [x] 3.1 Run full test suite to ensure no regressions
- [x] 3.2 Test with example-config.yaml (168 photos, 100 pages) and verify even distribution
- [x] 3.3 Verify all 100 pages contain photos in output
- [x] 3.4 Test with other page count scenarios (photos < pages, photos = pages, photos > pages)
