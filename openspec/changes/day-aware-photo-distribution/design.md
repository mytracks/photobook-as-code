## Context

See proposal.md for motivation. Relevant current state:

- `layout.py:distribute_photos` (exact-page-count branch, `layout.py:250-284`) computes `photos_pp = ceil(total/pages)`, then gives the first `total % pages` pages `photos_pp` items and the rest `photos_pp - 1`, purely arithmetic over a bare `int`. It has no access to item order, dates, or orientation.
- `PhotoDistribution.get_photo_indices_for_page` (`layout.py:90-108`) slices a flat index range out of that arithmetic for dense mode, but already has a second, entirely different representation for sparse mode (`pages > items`): an explicit `photo_to_page_map: dict[int, int]` built by `_calculate_sparse_page_assignments`, which spaces items evenly using `round(index * interval)`.
- `renderer.py:render_all_pages` (`renderer.py:641-687`) only depends on `distribution.total_pages` and `distribution.get_photo_indices_for_page(page_num)` — nothing else about `PhotoDistribution`'s internals is a public contract.
- `match_template` (`layout.py:116-158`) matches purely on `(count, orientations)` and already tolerates any item exposing `.orientation`; the shipped themes (`clean`, `classic`, `modern`, `clean2`) define templates for every orientation multiset at counts 1–4, so a theme's cap on items-per-page is its largest defined `count`, not any specific orientation combination.
- `PhotoMetadata.orientation` and `TitleLabel.orientation` already exist; `PhotoMetadata.sort_date` / `TitleLabel.timestamp` give every item a date. Nothing currently groups items by calendar day — `webapp/data.py:EditorData.is_new_day` does this only for the web editor's UI, over the editor's own photo list, and isn't reachable from `layout.py`.
- Today's exact-page-count mode never checks `photos_pp` (or flexible mode's configured `photos_per_page`) against the theme's max `count`. A config whose density exceeds the theme's largest template silently passes distribution and only fails later, inside rendering, with `LayoutError: No layout template found for N photos.` — confusing, since the real problem is upstream in distribution/config.

## Goals / Non-Goals

**Goals:**
- Replace the arithmetic exact-page-count distribution with one algorithm that reasons about the actual item sequence (day, orientation) while keeping `PhotoDistribution`'s public surface (`total_pages`, `get_photo_indices_for_page`) unchanged, so `renderer.py` needs no changes.
- Guarantee the requested `pages` count is always honored exactly; day boundaries are the value that bends under pressure, never the page count.
- Make day-boundary breaks apply to `photos_per_page` (flexible) mode too, by default, since that mode has no fixed budget to protect and the rule is a general readability improvement — but keep it a toggle (`layout.new_page_per_day`, default `true`) since a user may prefer the old dense-fill behavior.
- Full determinism: every choice the algorithm makes (which day boundaries to merge, which pages to split) is a total order over deterministic keys — same config + same photo files always produce byte-identical page assignments.
- Along the way, fix the latent gap where a distribution's per-page density can silently exceed the theme's max template count — surface it as a clear `LayoutError` during distribution instead of a confusing one deep in rendering.

**Non-Goals:**
- Reordering photos. The chronological/alphabetical order from `layout.order` is untouched; this change only decides *where the page breaks fall* within that fixed order.
- Applying orientation-match preference to any page-count reduction other than the final step down to a single item per page (e.g. 4 items → 3 items on a page gets no orientation preference — confirmed product decision).
- Sparse mode (`pages > items`). Each page there already holds at most one item by construction, so the day-per-page rule is a non-issue; sparse assignment (`_calculate_sparse_page_assignments`) is untouched.
- Any change to `match_template` or theme template vocabulary — this change only decides item-to-page grouping, never how a page's items are laid out once assigned.

## Decisions

### 1. Replace arithmetic mode-branching with one explicit item→page mapping
`PhotoDistribution` already has two representations: arithmetic (dense) and an explicit `photo_to_page_map` (sparse). This change drops the arithmetic representation entirely and makes every mode — dense, day-aware, sparse — build an explicit `photo_to_page_map`. `get_photo_indices_for_page` becomes one code path (dict lookup) instead of three. `distribute_photos` changes signature to take the ordered item sequence itself (for date/orientation), not just `total_photos: int`.

**Alternative considered:** keep the arithmetic base/remainder formula and patch day-awareness on top as a post-process that shifts page boundaries. Rejected — the arithmetic formula and the day-block-driven page count are two different ways of arriving at "how many pages does this need," and reconciling them after the fact means solving the same line-breaking problem twice. A single pass that always produces an explicit mapping is simpler and easier to keep deterministic.

### 2. Day-block segmentation
A day is `item.sort_date.date()` for a photo or `item.timestamp.date()` for a title (both give a real `datetime`). Consecutive items sharing a day form a "day-block," computed once over the existing item order — no re-sorting, no grouping across non-adjacent runs (a day that reappears later, e.g. across a multi-day trip loop, is treated as a new block, not merged with its earlier occurrence — page breaks track physical position, not calendar identity).

### 3. Exact-`pages` mode: segment → feasibility/merge → dense-pack → spend slack
Let `M` = the active theme's max defined `count` (`max(t.count for t in theme.layouts)`).

1. **Minimum pages under strict day-isolation:** `P_min_days = Σ ceil(len(block) / M)` over all day-blocks.
2. **Feasibility / merge fallback:** if `P_min_days > total_pages`, repeatedly merge the adjacent block pair whose merge frees the most pages — `ceil(len(a)/M) + ceil(len(b)/M) − ceil(len(a+b)/M)` — recomputing after each merge, tie-broken by earliest boundary position (lowest block index first). Stop once `P_min_days ≤ total_pages` or only one block remains. `layout.new_page_per_day = false` short-circuits this whole step by starting from a single block covering the entire sequence — which is exactly today's day-blind behavior, so the flag's "off" state and "day rule doesn't apply" are the same code path.
3. **Still infeasible after full merge?** If `ceil(total_items / M) > total_pages` even as one block, distribution is impossible regardless of day rules (more items than `pages × M` can ever hold) — raise `LayoutError` here, during distribution, instead of the previous silent pass-through that failed later inside `match_template`.
4. **Dense-pack:** pack each (possibly merged) block at `M` items/page; a block's own last page gets the remainder (`len(block) % M`, or `M` if it divides evenly). This uses exactly `P_min` pages (recomputed post-merge). `slack = total_pages − P_min` is guaranteed `≥ 0` by step 2/3.
5. **Spend slack — final splits first, orientation-tiered:** collect every page currently holding exactly 2 items as a split candidate. Rank into three tiers — both items' orientation equals book orientation; exactly one does; neither does. Spend slack starting from the best tier; within a tier, if there are more candidates than slack requires, choose the needed subset spread evenly across page position using the same `round(i * interval)` technique `_calculate_sparse_page_assignments` already uses (`interval = candidates_in_tier / needed_from_tier`). Each applied split turns one page of 2 into two pages of 1, consuming exactly one slack unit.
6. **Spend remaining slack — no preference:** if slack remains after every 2-item page is split (only possible when `M > 2` and blocks rarely land on 2-item remainders), reduce any page holding more than 1 item by 1, again choosing which pages via the same even-spread selection (largest pages first, ties broken by earliest position), until slack reaches 0.

Slack is always fully spendable: since `total_pages ≤ total_items` holds in dense/day mode (`total_pages > total_items` is sparse mode, handled separately) and `P_min ≤ total_pages` (feasibility), `slack ≤ total_items − P_min`, which is exactly the maximum a full cascade down to all-1-item pages can absorb.

**Alternative considered (for step 2's tie-break):** merge the boundary that produces the most *evenly spread* remaining book, rather than the boundary that frees the most pages. Rejected — merges are meant to be rare (only triggered when day count approaches or exceeds the page budget); optimizing for spread here adds complexity for a case that, by design, should barely ever fire. Greedy-most-pages-freed is simpler, fully explainable, and deterministic.

### 4. `photos_per_page` (flexible) mode gains day-breaks, no slack-spending
No fixed budget, so no feasibility/merge/slack machinery applies — that machinery exists purely to hit an exact page count. Segmentation (step 2 above) still applies when `new_page_per_day` is true; each block is independently dense-packed at `min(configured photos_per_page, M)`. The under-full page a day-boundary or a block's own remainder produces is simply the last page of that block — expected and not "spent" from anywhere, since the book is allowed to grow. Add the same upfront `photos_per_page ≤ M` validation as exact mode (see Decision 3, step 3) instead of letting an over-cap config fail later in rendering.

### 5. Book orientation
Derived once per run from the already-computed `page_width, page_height` (`config.py:get_paper_size_pixels`, used at `cli.py:139`): `portrait` if `page_height ≥ page_width`, else `landscape`. No new config field.

### 6. `new_page_per_day` config field
`LayoutConfig.new_page_per_day: bool = True` (`config.py:30`), validated as a boolean when present, following the existing validation pattern for `layout.photos_per_page`/`layout.pages` (`config.py:269-275`).

## Risks / Trade-offs

- **[Risk]** The merge fallback silently changes book structure (two days sharing a page) with no user-facing signal. **Mitigation:** log at WARNING when any day boundary is merged away, matching the existing `logger.warning` usage elsewhere (`photos.py:212`, `photos.py:226`).
- **[Risk]** Every existing fixed-`pages` config produces a different distribution after this change (called out in proposal.md as BREAKING). **Mitigation:** none beyond documentation — this is the intended fix, not a side effect.
- **[Trade-off]** The greedy "most pages freed" merge heuristic isn't proven globally optimal in every pathological day/size distribution. **Accepted** — merges are a rare last resort, and simple + deterministic + explainable outweighs provable optimality here.
- **[Trade-off]** Position-spread selection (`round(i * interval)`) is a heuristic notion of "evenly spread," not formally optimal spacing — the same trade-off `_calculate_sparse_page_assignments` already accepts today.
- **[Risk]** Moving the `photos_per_page`/computed-density-vs-theme-max check earlier (Decision 3 step 3, Decision 4) changes the failure mode for any config that was already silently over the theme's cap, from a late `LayoutError` inside rendering to an early one in distribution. **Mitigation:** strictly a clarity improvement — same failure, earlier and clearer message — called out since it rides along with this change rather than being requested directly.

## Migration Plan

Purely additive on the config surface: `new_page_per_day` defaults to `true`, and setting it `false` reproduces today's day-blind behavior exactly (Decision 3, step 2). No data migration. Existing fixed-`pages` photobooks will distribute differently the next time they're regenerated from source config + photos; nothing regenerates automatically.

## Open Questions

- Sparse mode's `round(index * interval)` placement doesn't formally guarantee at most one item lands on the same page in every edge case. Pre-existing and orthogonal to this change (sparse mode is a declared Non-Goal here); worth a separate look, not blocking.
