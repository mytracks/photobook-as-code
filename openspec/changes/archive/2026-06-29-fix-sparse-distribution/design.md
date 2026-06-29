## Context

The current photo distribution implementation has a bug in exact page count mode. When users specify an exact page count, photos are filled consecutively from page 0 until all photos are placed, leaving trailing pages empty. For example, with 168 photos across 100 pages (photos_per_page=2), pages 0-83 get 2 photos each, and pages 84-99 remain empty.

This contradicts the user expectation that specifying 100 pages means "use all 100 pages." The sparse distribution feature (for pages > photos) works correctly, but dense distribution (photos >= pages) uses consecutive filling.

## Goals / Non-Goals

**Goals:**
- Distribute photos evenly across ALL specified pages in exact page count mode
- Use the standard "distribute items into buckets" algorithm
- Maintain backward compatibility for photos_per_page mode (no exact page count)
- Preserve existing sparse distribution behavior (pages > photos)

**Non-Goals:**
- Changing the sparse distribution algorithm (already works correctly)
- Modifying photos_per_page mode behavior
- Adding new configuration options

## Decisions

### Decision 1: Use standard distribution algorithm for exact page count mode
When exact page count is specified and photos >= pages, calculate:
- Base photos per page: `base = total_photos // total_pages`
- Remainder: `remainder = total_photos % total_pages`
- First `remainder` pages get `base + 1` photos
- Remaining pages get `base` photos

**Rationale**: This is the standard algorithm for distributing items evenly into fixed buckets. It guarantees:
- All pages are used
- Maximum spread across page range
- Deterministic and testable

**Alternative considered**: Keep consecutive filling - rejected because it doesn't meet user expectations of "using all pages."

### Decision 2: Fix get_photos_for_page() logic
Replace the consecutive filling logic in `PhotoDistribution.get_photos_for_page()` for exact_page_count mode.

**Rationale**: The bug is in the page-level calculation, not the high-level distribution logic. Fix at the source.

**Alternative considered**: Change distribute_photos() to pre-calculate all page assignments - rejected because it increases memory usage and complexity.

### Decision 3: Update renderer to handle variable photos per page
The renderer already supports variable photos per page through `get_photo_indices_for_page()`, so no changes needed.

**Rationale**: The renderer is designed to be flexible. The fix is isolated to the distribution logic.

## Risks / Trade-offs

**Risk**: Existing tests expect consecutive filling behavior.
**Mitigation**: Update tests to expect even distribution. This is the correct behavior.

**Risk**: Users may have come to expect consecutive filling.
**Mitigation**: This is a bug fix, not a feature change. The original intent was even distribution (as stated in specs).

**Trade-off**: Pages will have variable photo counts (some pages 2 photos, others 1 photo).
**Trade-off**: This is expected and desirable - it's how even distribution works.

## Open Questions

None - implementation is straightforward.
