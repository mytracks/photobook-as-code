## Context

See proposal.md for motivation. Relevant current state:

- `text_labels.py:TitleLabel.orientation` is a property hardcoded to return `'portrait'`. It exists solely so `layout.py:match_template()` can treat a title exactly like a photo item during count/orientation matching - no other code path reads it differently.
- The original `add-title-slots` change (2026-08-21) made this choice deliberately, explicitly rejecting a distinct `title` orientation value "to avoid multiplying the count × position combinations themes must define." That rationale is unaffected by swapping which single fixed value is used - `landscape` is a substitution of the same mechanism, not the rejected alternative.
- All four built-in themes (`classic`, `modern`, `clean`, `clean2`) already define, for every item count they support (1-4), at least one template containing a `landscape` slot and at least one all-`portrait` template - each theme's YAML comment reads "all orientation combinations." Verified by inspecting each theme's `layouts` list grouped by `count`.

## Goals / Non-Goals

**Goals:**
- Titles consistently render in a wide/banner-shaped slot regardless of which photos happen to share their page.
- No change to title content, chronological placement, or styling - orientation-for-matching is the only value that moves.

**Non-Goals:**
- Not introducing a distinct `title` orientation value or theme-authored title-specific templates (same non-goal the original design carried, for the same reason).
- Not making the reported orientation configurable per-title or per-theme. A single global fixed value keeps the matcher simple; if a future need arises for per-title control, that is a separate change with its own proposal.
- Not auditing or modifying user-authored (non-built-in) themes - only the four themes shipped in this repo are verified here.

## Decisions

### 1. Flip the fixed value from `'portrait'` to `'landscape'`, keep the mechanism unchanged
`TitleLabel.orientation` continues to be a property returning one hardcoded string; only the string changes. `match_template()` requires no code change - it already treats titles as opaque items exposing `.orientation`.

**Alternative considered:** make the value configurable (e.g. a theme- or config-level `title_orientation` setting). Rejected for this change - no user need for `portrait` titles has been identified, the original design already rejected combinatorial title-orientation flexibility, and a fixed default is simpler to reason about. Revisit only if a concrete use case for portrait-shaped titles emerges.

### 2. No fallback/dual-orientation matching
When a theme lacks a landscape-inclusive template at a title-bearing count, matching still fails with the existing `LayoutError` - there is no attempt to fall back to a portrait-shaped slot for that title. This mirrors the original design's own stance on the equivalent gap ("none automatic; document that using titles requires the theme to have \[the newly-required orientation\]-inclusive templates at the relevant counts").

**Alternative considered:** try `landscape` first, fall back to `portrait` if no landscape-inclusive template matches. Rejected - silently changing a title's rendered shape based on unrelated theme gaps produces inconsistent-looking books with no explicit signal to the author; a loud `LayoutError` is more diagnosable than a book where some titles are narrow and others wide for reasons the author can't see from the config.

## Risks / Trade-offs

- **[Risk]** Any theme (built-in or user-authored) lacking a landscape-inclusive template at a count where a title appears now fails with `LayoutError` where it previously succeeded. **Mitigation:** verified all four built-in themes already have landscape-inclusive templates at every count they support (1-4); no built-in theme regresses. Document the new requirement (landscape-inclusive, not portrait-inclusive) in the README and `docs/theme_migration.md`.
- **[Risk]** Symmetric to the above: a theme that previously needed a portrait-inclusive template *only* to support titles (with no portrait photos ever used) may now have that requirement drop, which is a behavior change but not a break - it can only make more configs succeed, never fewer, for that specific case.
- **[Trade-off]** Same trade-off the original design accepted, mirrored onto the other orientation: a title's box shape is whatever geometry the matched template gives a landscape photo at that item count. Themes still can't give titles a distinctly-shaped slot without also reshaping their landscape photo slots at that count.

## Migration Plan

Single-value flip plus documentation updates (README, `docs/theme_migration.md`, this capability's spec) and updates to any existing tests asserting the old `'portrait'` value or portrait-template matching behavior for titles. No data migration. Any existing `<config>.yaml` + theme combination that previously required a portrait-inclusive template purely to place titles must be re-rendered to confirm it still matches (or gains a landscape-inclusive template at that count) - flagged as a task rather than automated, since this repo doesn't enumerate user-authored configs/themes it doesn't ship.
