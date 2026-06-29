## Context

The photobook generator currently uses a "fill consecutive then trail empty" algorithm for photo distribution when page count exceeds photos. This was implemented in the exact-page-count feature to respect user-specified page counts. However, this creates photobooks where all photos are clustered at the beginning, followed by empty pages at the end. Users find this visually unbalanced and prefer photos distributed throughout the photobook.

Current behavior: 8 photos, 15 pages → photos on pages 1-8, pages 9-15 empty
Desired behavior: 8 photos, 15 pages → photos distributed across the range (e.g., pages 1, 3, 5, 7, 9, 11, 13, 15)

## Goals / Non-Goals

**Goals:**
- Distribute photos evenly across all specified pages when page count exceeds photo count
- Maintain exact page count generation (no change to that feature)
- Create visually balanced photobooks with photos spread throughout
- Use a simple, predictable spacing algorithm

**Non-Goals:**
- Changing behavior when photos exceed or equal page count (photos_per_page mode)
- Smart clustering or grouping of photos by content/date
- User-configurable distribution patterns
- Changing the streaming/generator rendering architecture

## Decisions

### Decision 1: Spacing algorithm
Use a simple interval-based distribution: `interval = total_pages / total_photos` (floating point).

Place photos at positions: 0, interval, 2*interval, 3*interval, etc. (rounded to nearest integer).

**Rationale**: Simple, predictable, creates even spacing. Easy to understand and test.

**Alternative considered**: Random distribution - rejected because it's unpredictable and may cluster photos unevenly.

**Alternative considered**: Alternate pages (photo, blank, photo, blank) - rejected because it doesn't adapt to different photo/page ratios.

### Decision 2: Implementation location
Modify `PhotoDistribution.get_photos_for_page()` to calculate which pages should have photos based on spacing intervals.

**Rationale**: Keeps the logic centralized in the distribution dataclass. The renderer doesn't need to change - it already handles pages with 0 or 1 photo correctly.

**Alternative considered**: Pre-calculate page assignments in `distribute_photos()` - rejected because it would require storing a list of page assignments, increasing memory usage.

### Decision 3: Photos per page remains 1
When distributing sparsely, each page with a photo will have exactly 1 photo (photos_per_page=1).

**Rationale**: Simplifies the grid layout. Pages either have 1 photo (centered) or 0 photos (blank). No need to change grid calculations.

**Alternative considered**: Allow variable photos per page - rejected because it complicates the algorithm and may not meet user expectations.

## Risks / Trade-offs

**Risk**: Users may prefer consecutive placement over sparse distribution.
**Mitigation**: This behavior only applies when pages > photos. Users can adjust page count to get consecutive placement.

**Risk**: Spacing algorithm may not distribute photos exactly as users envision.
**Mitigation**: The interval-based approach is deterministic and produces intuitive results for most ratios.

**Trade-off**: Pages with photos will always have exactly 1 photo, which may look sparse.
**Trade-off**: This is the intended behavior for sparse distribution and matches user expectations for "spreading photos throughout the book."

**Trade-off**: Backward compatibility - existing configurations will behave differently.
**Trade-off**: This is an improvement to the recently-added exact-page-count feature, so impact is minimal. Users requesting exact page counts likely prefer this new behavior.
