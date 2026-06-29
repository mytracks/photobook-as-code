## 1. Update Layout Calculation Logic

- [x] 1.1 Modify `PhotoDistribution` dataclass to support exact page count mode
- [x] 1.2 Update `PhotoDistribution.get_photos_for_page()` to handle uneven distribution across exact page count
- [x] 1.3 Create new function to calculate photos-per-page when exact page count is specified
- [x] 1.4 Update layout calculation to prioritize page count over photos-per-page when both are specified

## 2. Update Photo Distribution Algorithm

- [x] 2.1 Implement "fill evenly then trail empty" distribution algorithm
- [x] 2.2 Handle case where specified pages exceed what's needed for all photos
- [x] 2.3 Ensure page count is respected exactly, generating empty pages if necessary
- [x] 2.4 Update `calculate_layout()` to accept and use exact page count parameter

## 3. Update Renderer for Exact Page Counts

- [x] 3.1 Verify renderer handles pages with fewer photos correctly
- [x] 3.2 Ensure renderer generates exactly the specified number of pages
- [x] 3.3 Test that empty pages are rendered correctly (with theme/margins but no photos)
- [x] 3.4 Confirm streaming/generator approach works with exact page count

## 4. Add Test Coverage

- [x] 4.1 Test exact page count with sufficient photos (evenly distributed)
- [x] 4.2 Test exact page count with excess pages (some pages empty/partial)
- [x] 4.3 Test page count takes precedence over photos_per_page
- [x] 4.4 Test backward compatibility with existing configurations
- [x] 4.5 Test edge cases: single page, zero photos, very high page count

## 5. Validation and Edge Cases

- [x] 5.1 Verify configuration parsing correctly handles layout.pages setting
- [x] 5.2 Test with example-config.yaml (pages: 100)
- [x] 5.3 Validate output with different photo counts and page specifications
- [x] 5.4 Run existing test suite to ensure no regressions
