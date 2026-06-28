## Context

The photobook generator currently calculates the number of pages based on total photos and photos-per-page settings. When users specify an exact page count in the configuration (`layout.pages`), the system treats this as a target but may generate fewer pages if there aren't enough photos to fill them all. Users need the ability to generate exactly the specified number of pages for printing requirements (e.g., photobook printing services require multiples of 4 or 8 pages) or layout preferences.

The photo distribution logic currently operates in photo-first mode: it distributes all available photos across the minimum number of pages needed. We need to extend this to support page-first mode: generate exactly the specified number of pages and distribute photos across them.

## Goals / Non-Goals

**Goals:**
- Generate exactly the number of pages specified in configuration when `layout.pages` is set
- Distribute photos evenly across all specified pages
- Handle edge cases: more pages than photos, partial fills, trailing empty pages
- Maintain backward compatibility with existing configurations
- Preserve streaming/generator-based rendering approach

**Non-Goals:**
- Adding photos from other sources to fill empty pages
- Changing the behavior when `photos_per_page` is specified instead of `pages`
- Validating whether the page count is suitable for printing
- Smart reordering of photos to optimize page distribution

## Decisions

### Decision 1: Page count enforcement mode
When `layout.pages` is specified in configuration, the system will generate exactly that many pages, even if it means:
- Some pages have fewer photos than others
- Some pages are completely empty (if pages > ceil(photos / average_per_page))

**Rationale**: Users explicitly requesting a page count have specific requirements (printing constraints, layout preferences). The system should respect this exactly rather than making assumptions.

**Alternative considered**: Generate only as many pages as needed for all photos, ignoring excess page count. Rejected because it defeats the purpose of specifying an exact count.

### Decision 2: Photo distribution algorithm
Use a "fill evenly then trail empty" approach:
1. Calculate photos_per_page = ceil(total_photos / specified_pages)
2. Distribute photos at this rate across pages
3. If all photos are consumed before reaching specified page count, generate remaining pages as empty

**Rationale**: This ensures photos are distributed as evenly as possible across the available pages while guaranteeing the exact page count.

**Alternative considered**: "Fill densely then sparse" - pack photos tightly on early pages, leave later pages empty. Rejected because it creates an unbalanced photobook appearance.

### Decision 3: Implementation location
Modify the `calculate_layout()` function in `layout.py` to accept an exact page count parameter and adjust its distribution logic accordingly.

**Rationale**: This function already handles the page-to-photo distribution calculations. Centralizing the logic here keeps the change localized.

**Alternative considered**: Add logic in the renderer to pad empty pages. Rejected because it separates calculation from distribution logic, making the code harder to maintain.

## Risks / Trade-offs

**Risk**: Users accidentally specify very high page counts (e.g., `pages: 1000` when they have 10 photos) and wonder why generation is slow or output is large.
**Mitigation**: Consider adding a warning (not an error) when page count significantly exceeds what's needed for the photos.

**Risk**: Backward compatibility - existing configurations might rely on current behavior.
**Mitigation**: The behavior only changes for configurations that explicitly set `layout.pages`. Configurations using `photos_per_page` remain unchanged.

**Trade-off**: Empty pages consume memory and storage even though they contain no photos.
**Trade-off**: This aligns with user intent for exact page counts. The streaming architecture minimizes memory impact.
