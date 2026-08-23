## MODIFIED Requirements

### Requirement: Distribute photos across pages
The system SHALL distribute all page items — photos and title slots combined — across the specified or calculated number of pages according to layout constraints, always honoring an explicit `pages` count exactly. Distribution SHALL additionally respect calendar-day boundaries between items (see the day-boundary requirement) and, when an explicit page count leaves pages of slack after day-isolated packing, SHALL spend that slack by preferentially splitting two-item pages into full-page single-item pages, ranked by how well their items' orientations match the book's own page orientation (see the orientation-matched splitting requirement). Title slots count toward `photos_per_page` and `pages` calculations identically to photos. For the same configuration and photo set, the system SHALL always produce the identical page-by-page item assignment.

#### Scenario: Exact division
- **WHEN** total photos divide evenly by photos-per-page
- **THEN** all pages contain exactly the specified number of photos

#### Scenario: Remainder photos
- **WHEN** total photos don't divide evenly
- **THEN** final page contains remaining photos

#### Scenario: Empty cells
- **WHEN** final page has fewer photos than grid capacity
- **THEN** system leaves remaining grid cells empty

#### Scenario: Exact page count with sufficient photos
- **WHEN** configuration specifies exact page count (layout.pages) with enough photos to distribute
- **THEN** system generates exactly that many pages with photos distributed as evenly as possible, subject to day-boundary and orientation-matched-splitting rules

#### Scenario: Exact page count distributes across full range
- **WHEN** configuration specifies exact page count with photos exceeding page count (e.g. 168 photos, 100 pages)
- **THEN** system distributes photos across all 100 pages with no pages left empty, and pages holding fewer items than others are spread across the book's page range rather than clustered together at either end

#### Scenario: Exact page count with excess pages - sparse distribution
- **WHEN** configuration specifies more pages than available photos (e.g., 8 photos, 15 pages)
- **THEN** system distributes photos evenly across all pages using interval-based spacing, with blank pages interspersed

#### Scenario: Sparse distribution spacing
- **WHEN** photos are distributed sparsely across pages (pages > photos)
- **THEN** system calculates spacing interval as total_pages / total_photos and places photos at evenly-spaced intervals

#### Scenario: Exact page count takes precedence
- **WHEN** configuration specifies both pages and photos_per_page
- **THEN** system uses the page count and calculates photos_per_page accordingly

#### Scenario: Titles increase total slot count
- **WHEN** a photobook configuration defines N photos and M title entries
- **THEN** the system calculates page distribution using N + M as the total item count, not N alone

#### Scenario: Title slot placed within a page's item budget
- **WHEN** a title's chronological position falls within a page that would otherwise hold `photos_per_page` photos
- **THEN** the system counts the title as one of that page's items, reducing the number of photos placed on that page so the page's total item count still respects the configured budget

#### Scenario: Deterministic distribution
- **WHEN** distribution is calculated twice for the same photo directory, configuration, and theme
- **THEN** both runs produce an identical mapping of items to pages, with no dependency on set/dict iteration order, randomness, or filesystem enumeration order

## ADDED Requirements

### Requirement: Respect day boundaries when distributing pages
The system SHALL treat each item's calendar day — a photo's `sort_date.date()` or a title's `timestamp.date()` — as a page-break boundary: by default, no page holds items from two different calendar days, so a new day always starts on a new page. This rule applies whenever pages are distributed, whether an exact `pages` count or a `photos_per_page` cap is configured, and can be disabled via the `layout.new_page_per_day` configuration field.

#### Scenario: New day starts a new page
- **WHEN** the next item in chronological order falls on a different calendar day than the previous item on the current page
- **THEN** the system starts a new page for that item, even if the current page has room for more items

#### Scenario: Title counts as its own day's item
- **WHEN** a title slot's timestamp falls on a different calendar day than the item immediately before it
- **THEN** the system starts a new page for the title, the same as it would for a photo

#### Scenario: Day rule applies without a fixed page count
- **WHEN** `layout.photos_per_page` is configured instead of `layout.pages`
- **THEN** the system still starts a new page at each day boundary, growing the total page count as needed since no fixed budget applies

#### Scenario: Day rule disabled
- **WHEN** `layout.new_page_per_day` is set to `false`
- **THEN** the system distributes items without regard to day boundaries, filling pages purely by item count as it did before this rule existed

### Requirement: Prioritize orientation-matched pages when splitting for an exact page count
When an exact `pages` count leaves pages of slack unused after packing every day's items at the theme's maximum items-per-page, the system SHALL spend that slack by turning two-item pages into two full-page single-item pages, preferring pages whose two items' orientations both match the book's own page orientation, then pages where exactly one item matches, then pages where neither matches. The system SHALL NOT apply this orientation preference when reducing a page's item count to more than one item (e.g. four items to three).

#### Scenario: Both-orientation-match pages split first
- **WHEN** slack is available and at least one two-item page exists whose items are both the same orientation as the book
- **THEN** the system splits that page before any two-item page with a different orientation combination

#### Scenario: Partial-match pages split next
- **WHEN** no fully-matching two-item pages remain to split and slack is still available
- **THEN** the system splits a two-item page with exactly one item matching the book's orientation before one with no matching items

#### Scenario: Splits spread across the book
- **WHEN** more pages qualify for splitting within a priority tier than the available slack requires
- **THEN** the system chooses which of those pages to split so the resulting single-item pages are spread across the book's page range rather than clustered together

#### Scenario: No orientation preference for non-final reductions
- **WHEN** slack requires reducing a page's item count from more than two down to more than one item
- **THEN** the system does not apply the orientation-match preference to choose which such pages are reduced

### Requirement: Relax day boundaries when the page budget cannot accommodate them
The exact `pages` count configured by the user SHALL always be honored. When giving every calendar day its own page(s) would require more pages than the configured `pages` count allows, the system SHALL instead merge the fewest, least-costly day boundaries — chosen deterministically — so that two days share a page only where unavoidable.

#### Scenario: Insufficient page budget merges day boundaries
- **WHEN** the number of pages needed to give every day its own page(s) exceeds the configured `pages` count
- **THEN** the system merges adjacent days across a page boundary, starting with the merge that reduces the required page count the most, until the distribution fits within the configured page count

#### Scenario: Exact page count still honored after merging
- **WHEN** day boundaries have been merged to fit the configured page count
- **THEN** the system still generates exactly the configured number of pages

#### Scenario: Deterministic merge selection
- **WHEN** more than one pair of adjacent days would free the same number of pages if merged
- **THEN** the system selects the pair appearing earliest in the book, so the same input always merges the same boundaries

### Requirement: Validate page density against theme capacity
The system SHALL verify that the number of items to be placed on any page does not exceed the active theme's maximum defined layout template item count, and SHALL raise a clear error during distribution — before rendering begins — when it does.

#### Scenario: Exact page count too small for the theme's capacity
- **WHEN** an exact `pages` count is configured that would require more items on a page than any layout template in the active theme supports
- **THEN** the system raises a layout error identifying the page count and the theme's maximum supported item count, instead of proceeding to rendering

#### Scenario: photos_per_page exceeds theme capacity
- **WHEN** `layout.photos_per_page` is configured higher than the active theme's maximum defined layout template item count
- **THEN** the system raises a layout error identifying the configured value and the theme's maximum, instead of proceeding to rendering
