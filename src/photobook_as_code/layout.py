"""
Layout calculation for photo grid arrangements.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Union, Dict
import math
import logging
from photobook_as_code.themes import LayoutTemplate
from photobook_as_code.photos import PhotoMetadata
from photobook_as_code.text_labels import TitleLabel

logger = logging.getLogger(__name__)

# A page item is either a real photo or a title slot; the distribution and
# matching logic below only ever needs `.orientation` (both expose it) and,
# for day-boundary purposes, a calendar date (see `_item_date`).
PageItem = Union[PhotoMetadata, TitleLabel]


class LayoutError(Exception):
    """Raised when layout calculation fails."""
    pass


def _item_date(item: PageItem):
    """The calendar date an item belongs to, for day-boundary grouping."""
    if isinstance(item, TitleLabel):
        return item.timestamp.date()
    return item.sort_date.date()


@dataclass
class PhotoDistribution:
    """
    Distribution of page items (photos and/or title slots) across pages.

    The single source of truth is `photo_to_page_map` (item index -> page
    number, 0-indexed); every distribution mode - dense, day-aware, sparse -
    builds this same explicit mapping rather than each having its own way of
    answering "what's on page N".

    `photos_per_page` and `photos_on_last_page` are informational summaries
    of the distribution (the configured/computed cap and the actual count on
    the final page) - meaningful as a single number for the arithmetic and
    flexible modes, best-effort for the day-aware mode where per-page counts
    vary.
    """
    total_photos: int
    total_pages: int
    photo_to_page_map: Dict[int, int]
    photos_per_page: int = 0
    photos_on_last_page: int = 0
    exact_page_count: bool = False  # Whether page count is enforced exactly
    sparse_distribution: bool = False  # Whether using interval-based sparse distribution

    def __post_init__(self):
        page_to_indices: Dict[int, List[int]] = {}
        for idx, page in self.photo_to_page_map.items():
            page_to_indices.setdefault(page, []).append(idx)
        for indices in page_to_indices.values():
            indices.sort()
        self._page_to_indices = page_to_indices

    def get_photos_for_page(self, page_num: int) -> int:
        """Get number of photos for a specific page (0-indexed)."""
        return len(self._page_to_indices.get(page_num, []))

    def get_photo_indices_for_page(self, page_num: int) -> list:
        """
        Get the photo indices (into all_photos list) for a specific page.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            List of photo indices that should appear on this page, in their
            original sequence order.
        """
        return list(self._page_to_indices.get(page_num, []))


def match_template(templates: List[LayoutTemplate], photos: List[PageItem]) -> LayoutTemplate:
    """
    Match page items to a layout template based on count and orientation.
    Prefers exact orientation order match. Items may be photos or title slots -
    both expose `.orientation` (a title slot always reports 'landscape').

    Args:
        templates: Available layout templates from theme
        photos: Page items (photos and/or title slots) for a specific page

    Returns:
        Matched LayoutTemplate

    Raises:
        LayoutError: If no matching template is found
    """
    photo_count = len(photos)
    orientations = [p.orientation for p in photos]

    # Filter by count
    matching_count = [t for t in templates if t.count == photo_count]

    if not matching_count:
        raise LayoutError(f"No layout template found for {photo_count} photos.")

    # Filter by orientations (independent of order first)
    valid_templates = []
    for t in matching_count:
        if sorted(t.orientations) == sorted(orientations):
            valid_templates.append(t)

    if not valid_templates:
        raise LayoutError(
            f"No layout template found for {photo_count} photos with orientations: {orientations}."
        )

    # Prefer exact order match
    for t in valid_templates:
        if t.orientations == orientations:
            return t

    # Fallback to any template with correct orientations
    return valid_templates[0]


def calculate_photos_per_page(total_photos: int, total_pages: int) -> int:
    """
    Calculate photos per page for even distribution.

    Args:
        total_photos: Total number of photos
        total_pages: Desired number of pages

    Returns:
        Photos per page (ceiling division)

    Raises:
        LayoutError: If values are invalid
    """
    if total_photos < 1:
        raise LayoutError("total_photos must be at least 1")

    if total_pages < 1:
        raise LayoutError("total_pages must be at least 1")

    # Use ceiling division to ensure all photos fit
    return math.ceil(total_photos / total_pages)


def _calculate_sparse_page_assignments(total_photos: int, total_pages: int) -> Dict[int, int]:
    """
    Calculate which page each photo should appear on for sparse distribution
    (more pages than photos). Uses interval-based spacing to distribute
    photos evenly across all pages.

    Returns:
        Dictionary mapping photo index to page number
    """
    if total_photos == 0:
        return {}

    interval = total_pages / total_photos

    assignments: Dict[int, int] = {}
    for photo_idx in range(total_photos):
        page_num = round(photo_idx * interval)

        if photo_idx == 0:
            page_num = 0

        if page_num >= total_pages:
            page_num = total_pages - 1

        assignments[photo_idx] = page_num

    return assignments


def _day_blocks(items: List[PageItem]) -> List[List[int]]:
    """
    Partition an ordered item sequence into day-blocks: lists of item
    indices, each a maximal run of consecutive items sharing a calendar day.
    A day that reappears later in the sequence (non-adjacent) forms a
    separate block - page breaks track physical position, not calendar
    identity.
    """
    blocks: List[List[int]] = []
    current: List[int] = []
    current_day = None
    for idx, item in enumerate(items):
        day = _item_date(item)
        if current and day != current_day:
            blocks.append(current)
            current = []
        current.append(idx)
        current_day = day
    if current:
        blocks.append(current)
    return blocks


def _pages_needed(count: int, max_per_page: int) -> int:
    """Minimum pages needed to hold `count` items at `max_per_page` items/page."""
    return math.ceil(count / max_per_page) if count > 0 else 0


def _merge_blocks_to_fit(
    blocks: List[List[int]], items: List[PageItem], max_per_page: int, total_pages: int
) -> Tuple[List[List[int]], List[str]]:
    """
    Last-resort feasibility fallback: while giving every day-block its own
    page(s) would need more pages than `total_pages` allows, repeatedly merge
    the adjacent block pair whose merge frees the most pages, tie-broken by
    earliest boundary position, so two days end up sharing a page only where
    unavoidable.

    Returns the (possibly merged) blocks and a human-readable log entry per
    merge performed, for a caller to warn about.
    """
    blocks = [list(b) for b in blocks]
    merge_log: List[str] = []

    def pages_needed_total(block_list: List[List[int]]) -> int:
        return sum(_pages_needed(len(b), max_per_page) for b in block_list)

    while len(blocks) > 1 and pages_needed_total(blocks) > total_pages:
        best_index = 0
        best_savings = -1
        for i in range(len(blocks) - 1):
            a, b = blocks[i], blocks[i + 1]
            savings = (
                _pages_needed(len(a), max_per_page)
                + _pages_needed(len(b), max_per_page)
                - _pages_needed(len(a) + len(b), max_per_page)
            )
            if savings > best_savings:
                best_savings = savings
                best_index = i

        a, b = blocks[best_index], blocks[best_index + 1]
        merge_log.append(f"{_item_date(items[a[0]])} and {_item_date(items[b[0]])}")
        blocks[best_index:best_index + 2] = [a + b]

    return blocks, merge_log


def _pack_block_into_pages(block: List[int], page_count: int) -> List[List[int]]:
    """
    Distribute a block's item indices across exactly `page_count` pages as
    evenly as possible (the first `len(block) % page_count` pages get one
    extra item) - the same base/remainder split `_distribute_exact_arithmetic`
    uses globally, applied per block. Not by greedily filling each page to a
    cap and stranding whatever is left on a final, possibly much smaller
    page: a 37-item day split across 13 pages, for example, gives eleven
    3-item pages and two 2-item pages this way, versus twelve 3-item pages
    plus one isolated 1-item page from greedy chunking.
    """
    total = len(block)
    if total == 0 or page_count <= 0:
        return []

    base = total // page_count
    remainder = total % page_count

    pages: List[List[int]] = []
    cursor = 0
    for page_num in range(page_count):
        count = (base + 1) if page_num < remainder else base
        pages.append(block[cursor:cursor + count])
        cursor += count
    return pages


def _dense_pack_block(block: List[int], max_per_page: int) -> List[List[int]]:
    """Pack a block into the minimum page count at `max_per_page` items/page, evenly distributed."""
    return _pack_block_into_pages(block, _pages_needed(len(block), max_per_page))


def _select_evenly(candidates: List[int], needed: int) -> List[int]:
    """
    Deterministically choose `needed` values out of an ascending list of
    candidates, spread evenly across the candidate range (same
    round(i * interval) idea used for sparse-mode page assignment).
    """
    n = len(candidates)
    if needed >= n:
        return list(candidates)
    if needed <= 0:
        return []

    interval = n / needed
    chosen: List[int] = []
    last = -1
    for i in range(needed):
        target = round(i * interval)
        if target <= last:
            target = last + 1
        if target >= n:
            target = n - 1
        chosen.append(target)
        last = target

    return [candidates[i] for i in chosen]


def _peel(pages: List[List[int]], page_positions: List[int]) -> None:
    """
    Reduce each named page's item count by 1: the last item moves to a new
    page inserted immediately after it. Applied in descending position order
    so earlier insertions don't invalidate the positions still to be applied.
    """
    for p in sorted(page_positions, reverse=True):
        item_indices = pages[p]
        kept, moved = item_indices[:-1], item_indices[-1:]
        pages[p:p + 1] = [kept, moved]


def _spend_slack(
    pages: List[List[int]], slack: int, items: List[PageItem], book_orientation: Optional[str]
) -> None:
    """
    Spend `slack` extra pages (beyond the day-isolated dense-pack minimum) by
    splitting two-item pages into two full-bleed single-item pages, ranked by
    how many of their two items match `book_orientation` (both > one >
    neither). Only once no two-item page remains does a pass fall back to
    reducing any page with more than one item, with no orientation
    preference. Re-evaluating every pass lets a page peeled down to exactly
    two items become eligible for orientation-ranked splitting later.

    Only valid when the dense-pack cap is 2: splitting a single page in two
    can never keep both halves within {cap-1, cap} unless cap == 2 (the two
    new page sizes must sum to the cap, and the only way both can be in
    {cap-1, cap} is if cap == 2*(cap-1)). For any larger cap,
    `_grow_blocks_to_spend_slack` must be used instead - see its docstring.
    """
    while slack > 0:
        two_item_positions = [p for p, page in enumerate(pages) if len(page) == 2]

        if two_item_positions:
            tiers: Dict[int, List[int]] = {2: [], 1: [], 0: []}
            for p in two_item_positions:
                if book_orientation is None:
                    matches = 0
                else:
                    matches = sum(
                        1 for idx in pages[p] if items[idx].orientation == book_orientation
                    )
                tiers[matches].append(p)

            for tier_key in (2, 1, 0):
                candidates = tiers[tier_key]
                if not candidates:
                    continue
                take = min(slack, len(candidates))
                chosen = _select_evenly(candidates, take)
                _peel(pages, chosen)
                slack -= len(chosen)
                break
        else:
            candidates = [p for p, page in enumerate(pages) if len(page) > 1]
            if not candidates:
                raise LayoutError(
                    "Internal error: no page available to absorb the remaining page-count slack."
                )
            take = min(slack, len(candidates))
            chosen = _select_evenly(candidates, take)
            _peel(pages, chosen)
            slack -= len(chosen)


def _grow_blocks_to_spend_slack(
    blocks: List[List[int]], block_pages: List[List[List[int]]], slack: int, max_per_page: int
) -> None:
    """
    Spend `slack` extra pages, for a dense-pack cap greater than 2, by giving
    a whole day-block one additional page and re-distributing that block's
    own items evenly across its new page count - never letting any of that
    block's pages drop below `max_per_page - 1`. Splitting a single existing
    page cannot achieve this (see `_spend_slack`'s docstring), so growth
    always re-packs an entire block via `_pack_block_into_pages`.

    No orientation preference applies here (a confirmed product decision):
    unlike the cap-2 case, growing a block never produces a full-bleed
    single-item page, so there is no aesthetic reason to prefer one block's
    orientation mix over another's. Blocks are chosen for growth via the same
    even-spread selection used elsewhere, in rounds - a block may need more
    than one extra page, and each round only grows blocks that still have
    headroom (their next page wouldn't drop any page below `max_per_page -
    1`), so a block that's used up its headroom drops out of later rounds.
    """
    floor_size = max_per_page - 1

    while slack > 0:
        headroom = [
            i for i, b in enumerate(blocks)
            if floor_size > 0 and len(block_pages[i]) < len(b) // floor_size
        ]

        if not headroom:
            # Every block has already been grown as far as it can go without
            # dropping a page below max_per_page - 1: an extremely rare
            # situation for realistic day-block sizes. Fall back to peeling a
            # single page as a last resort, so the requested page count is
            # still always honored exactly.
            candidates = [
                (bi, pi) for bi, pages in enumerate(block_pages)
                for pi, page in enumerate(pages) if len(page) > 1
            ]
            if not candidates:
                raise LayoutError(
                    "Internal error: no page available to absorb the remaining page-count slack."
                )
            bi, pi = candidates[0]
            item_indices = block_pages[bi][pi]
            kept, moved = item_indices[:-1], item_indices[-1:]
            block_pages[bi][pi:pi + 1] = [kept, moved]
            slack -= 1
            continue

        chosen = _select_evenly(headroom, min(slack, len(headroom)))
        for bi in chosen:
            block_pages[bi] = _pack_block_into_pages(blocks[bi], len(block_pages[bi]) + 1)
        slack -= len(chosen)


def _distribute_exact_arithmetic(total_items: int, total_pages: int) -> List[List[int]]:
    """
    The original, day-blind exact-page-count distribution: the first
    `total_items % total_pages` pages get one extra item, the rest get one
    fewer - used when `new_page_per_day` is disabled.
    """
    base = total_items // total_pages
    remainder = total_items % total_pages
    pages: List[List[int]] = []
    cursor = 0
    for page_num in range(total_pages):
        count = (base + 1) if page_num < remainder else base
        pages.append(list(range(cursor, cursor + count)))
        cursor += count
    return pages


def _distribute_flexible_arithmetic(total_items: int, photos_per_page: int) -> List[List[int]]:
    """The original, day-blind photos_per_page distribution: sequential chunking."""
    return [
        list(range(i, min(i + photos_per_page, total_items)))
        for i in range(0, total_items, photos_per_page)
    ]


def _distribute_exact_day_aware(
    items: List[PageItem],
    total_pages: int,
    max_per_page: int,
    book_orientation: Optional[str],
) -> Tuple[List[List[int]], List[str]]:
    """
    Day-aware exact-page-count distribution: day-block segmentation, the
    last-resort merge fallback when the page budget can't give every day its
    own page, dense-packing each block at `max_per_page` items/page, then
    spending any remaining page-count slack - by splitting two-item pages
    into full-bleed singles, orientation-tiered, when `max_per_page` is 2;
    otherwise by growing whole blocks (see `_grow_blocks_to_spend_slack`),
    since splitting a single page can't keep both halves within
    {max_per_page - 1, max_per_page} for any larger cap.

    `max_per_page` is the natural per-page density for this photo/page ratio
    (`ceil(total_items / total_pages)`, i.e. what `calculate_photos_per_page`
    returns) - the same cap the original arithmetic distribution used. It is
    NOT the theme's rendering capacity: that is only ever a validation
    ceiling on this computed value (see `distribute_photos`), never the pack
    size itself - a book with 150 photos across 100 pages must still cap
    every page at 2 items, even if the active theme could render up to 4.
    """
    total_items = len(items)
    blocks = _day_blocks(items)
    merge_log: List[str] = []

    if len(blocks) > 1:
        p_min = sum(_pages_needed(len(b), max_per_page) for b in blocks)
        if p_min > total_pages:
            blocks, merge_log = _merge_blocks_to_fit(blocks, items, max_per_page, total_pages)

    p_min = sum(_pages_needed(len(b), max_per_page) for b in blocks)
    if p_min > total_pages:
        raise LayoutError(
            f"{total_items} items cannot fit into {total_pages} pages with at most "
            f"{max_per_page} items per page (needs at least {p_min} pages)."
        )

    block_pages = [_dense_pack_block(block, max_per_page) for block in blocks]
    slack = total_pages - sum(len(bp) for bp in block_pages)

    if slack > 0:
        if max_per_page <= 2:
            flat_pages = [page for bp in block_pages for page in bp]
            _spend_slack(flat_pages, slack, items, book_orientation)
            return flat_pages, merge_log
        _grow_blocks_to_spend_slack(blocks, block_pages, slack, max_per_page)

    pages = [page for bp in block_pages for page in bp]
    return pages, merge_log


def _distribute_flexible_day_aware(
    items: List[PageItem], photos_per_page: int
) -> List[List[int]]:
    """
    Day-aware photos_per_page distribution: no fixed page budget, so no
    merge/slack machinery is needed - each day-block is simply dense-packed
    on its own, growing the book as needed.
    """
    blocks = _day_blocks(items)
    pages: List[List[int]] = []
    for block in blocks:
        pages.extend(_dense_pack_block(block, photos_per_page))
    return pages


def distribute_photos(
    items: Optional[List[PageItem]] = None,
    photos_per_page: Optional[int] = None,
    total_pages: Optional[int] = None,
    max_items_per_page: Optional[int] = None,
    book_orientation: Optional[str] = None,
    new_page_per_day: bool = False,
) -> PhotoDistribution:
    """
    Calculate photo/title distribution across pages.

    Args:
        items: Ordered page items (photos and/or title slots) to distribute
        photos_per_page: Photos per page (mutually exclusive with total_pages)
        total_pages: Total pages desired (takes precedence if both specified)
        max_items_per_page: The active theme's max defined layout template
            item count - a validation ceiling only. In exact-page-count mode
            the actual per-page cap is always `ceil(total_items /
            total_pages)` (the same density the original arithmetic used);
            this parameter just makes sure that density (or, in
            photos_per_page mode, the configured value itself) doesn't
            exceed what the theme can render. When omitted, no such
            validation is performed.
        book_orientation: 'portrait' or 'landscape', the book's own page
            orientation - used only to rank orientation-matched splits in
            day-aware exact-page-count mode.
        new_page_per_day: When True, a calendar-day change always starts a
            new page (see module-level day-aware helpers); when False
            (default), distribution is the original day-blind arithmetic.

    Returns:
        PhotoDistribution instance

    Raises:
        LayoutError: If parameters are invalid or inconsistent, or the
            requested page count cannot hold the items within
            `max_items_per_page`.
    """
    if items is None:
        items = []

    # If both specified, total_pages takes precedence
    if photos_per_page is not None and total_pages is not None:
        photos_per_page = None

    if photos_per_page is None and total_pages is None:
        raise LayoutError("Must specify either photos_per_page or total_pages")

    total_items = len(items)

    # Handle edge case: zero items
    if total_items == 0:
        if total_pages is not None:
            return PhotoDistribution(
                total_photos=0,
                total_pages=total_pages,
                photo_to_page_map={},
                photos_per_page=0,
                photos_on_last_page=0,
                exact_page_count=True,
            )
        else:
            return PhotoDistribution(
                total_photos=0,
                total_pages=0,
                photo_to_page_map={},
                photos_per_page=photos_per_page or 0,
                photos_on_last_page=0,
                exact_page_count=False,
            )

    if photos_per_page is not None:
        if photos_per_page < 1:
            raise LayoutError("photos_per_page must be at least 1")

        if max_items_per_page is not None and photos_per_page > max_items_per_page:
            raise LayoutError(
                f"photos_per_page ({photos_per_page}) exceeds the active theme's "
                f"maximum items per page ({max_items_per_page})."
            )

        if new_page_per_day:
            pages = _distribute_flexible_day_aware(items, photos_per_page)
        else:
            pages = _distribute_flexible_arithmetic(total_items, photos_per_page)

        photo_to_page_map = {idx: p for p, page in enumerate(pages) for idx in page}

        return PhotoDistribution(
            total_photos=total_items,
            total_pages=len(pages),
            photo_to_page_map=photo_to_page_map,
            photos_per_page=photos_per_page,
            photos_on_last_page=len(pages[-1]) if pages else 0,
            exact_page_count=False,
        )

    else:  # total_pages specified - exact page count mode
        if total_pages < 1:
            raise LayoutError("total_pages must be at least 1")

        # Check if we need sparse distribution (more pages than items)
        if total_pages > total_items:
            sparse_map = _calculate_sparse_page_assignments(total_items, total_pages)
            return PhotoDistribution(
                total_photos=total_items,
                total_pages=total_pages,
                photo_to_page_map=sparse_map,
                photos_per_page=1,
                photos_on_last_page=1,
                exact_page_count=True,
                sparse_distribution=True,
            )

        photos_pp = calculate_photos_per_page(total_items, total_pages)

        if max_items_per_page is not None and photos_pp > max_items_per_page:
            raise LayoutError(
                f"{total_items} items across {total_pages} pages needs {photos_pp} items on "
                f"some pages, exceeding the active theme's maximum of {max_items_per_page}."
            )

        merge_log: List[str] = []
        if new_page_per_day:
            pages, merge_log = _distribute_exact_day_aware(
                items, total_pages, photos_pp, book_orientation
            )
        else:
            pages = _distribute_exact_arithmetic(total_items, total_pages)

        if merge_log:
            logger.warning(
                "Requested page count (%d) is too small to give every day its own page; "
                "merged day boundaries between: %s",
                total_pages,
                "; ".join(merge_log),
            )

        photo_to_page_map = {idx: p for p, page in enumerate(pages) for idx in page}

        return PhotoDistribution(
            total_photos=total_items,
            total_pages=total_pages,
            photo_to_page_map=photo_to_page_map,
            photos_per_page=photos_pp,
            photos_on_last_page=len(pages[-1]) if pages else 0,
            exact_page_count=True,
        )


def fit_photo_in_cell(photo_width: int, photo_height: int,
                      cell_width: int, cell_height: int) -> Tuple[int, int, int, int]:
    """
    Calculate dimensions and position to fit photo in cell preserving aspect ratio.

    Args:
        photo_width: Original photo width
        photo_height: Original photo height
        cell_width: Cell width
        cell_height: Cell height

    Returns:
        Tuple of (fitted_width, fitted_height, x_offset, y_offset)
        Photo is centered in cell with letterboxing/pillarboxing as needed
    """
    # Calculate aspect ratios
    photo_aspect = photo_width / photo_height
    cell_aspect = cell_width / cell_height

    if photo_aspect > cell_aspect:
        # Photo is wider - fit to width
        fitted_width = cell_width
        fitted_height = int(cell_width / photo_aspect)
    else:
        # Photo is taller - fit to height
        fitted_height = cell_height
        fitted_width = int(cell_height * photo_aspect)

    # Center in cell
    x_offset = (cell_width - fitted_width) // 2
    y_offset = (cell_height - fitted_height) // 2

    return (fitted_width, fitted_height, x_offset, y_offset)
