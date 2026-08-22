## Context

`text_labels.py::parse_markdown_text` splits `text`/`title` content on `\n` into `(segments, heading_level)` tuples, one per source line. `renderer.py::_wrap_markdown_lines` (shared by `render_text_label` and `render_title_slot`) turns those into measured, word-wrapped display lines and sums their heights plus a fixed `line_spacing = 4`.

A blank source line already produces a `(segments=[TextSegment(text="")], heading_level=0)` tuple, and `_wrap_markdown_lines` already special-cases it (no words tokenized, so `current_words` stays empty) — but `current_height` for that line stays at its initial value `0`. The blank display line therefore contributes only `line_spacing` (4px) to `total_text_height`, which is imperceptible against 42-108px text. See proposal.md - Why.

Separately, YAML's `|` block scalar uses "clip" chomping by default: it keeps exactly one trailing `\n`. Splitting `"...\n"` on `\n` yields a trailing empty string, so every multi-line `text: |`/`title: |` value already carries one unintended trailing blank line into the parsed line list, today masked by the same near-zero blank-line height.

## Goals / Non-Goals

**Goals:**
- Give blank lines real, visible vertical spacing when authored deliberately between content lines.
- Prevent YAML formatting artifacts (the clip-chomping trailing newline, an accidental blank line after `title: |`) from being mistaken for authored spacing.

**Non-Goals:**
- No new config syntax for blank lines - a blank line in the YAML string is already the trigger.
- No theme-level control over blank-line height in this change; it's fixed at "one normal line" (see Decisions).
- No change to `TextLabel`/`TitleLabel` dataclasses or `parse_markdown_line`'s per-line return shape.

## Decisions

**Blank-line height = regular font's line height at `base_font_size`, not the previous or next line's heading size.**
A blank source line has no markdown of its own (`parse_markdown_line("")` always returns `heading_level=0`), so there's no heading context to inherit. Using the plain-text line height keeps the behavior predictable regardless of what surrounds the blank line (matches "one blank line in the editor = one line of vertical space" intuition). Alternative considered: inherit the *previous* display line's height (so a blank line after an `h1` reads as heading-sized) - rejected as surprising and harder to reason about from the source text alone, and it would make consecutive-blank-line stacking height-dependent on position.

**Trim leading/trailing blank lines in `parse_markdown_text`, not in config validation or at the YAML layer.**
`parse_markdown_text` is the single place both `render_text_label` and `render_title_slot` already go through, and it's where the line list is constructed - trimming there (e.g., stripping blank entries off both ends of the split-line list before building tuples) fixes both call sites at once without touching `config.py` validation (which only checks presence/type of `text`/`title`, not content) or requiring authors to know about YAML chomping indicators (`|-`). Interior blank lines are left untouched.

**Stack consecutive blank lines additively; don't collapse runs to a single gap.**
Each blank source line becomes its own display line with one line-height of height, same as today's structural (if invisible) handling. This is the simplest rule, requires no run-length detection, and matches plain-text-editor semantics rather than Markdown-source semantics (where blank-line count is normally insignificant) - appropriate here since this content is closer to "formatted caption text" than prose Markdown meant for an HTML renderer.

## Risks / Trade-offs

- **Existing configs with a leading/trailing blank line change layout.** Any config relying on the current near-zero blank-line gap (unlikely, since it's imperceptible) would see a visible reflow. Mitigated by this being the intended fix; `example-config.yaml` itself is the motivating case, and its `title:` block scalar has a leading-none / trailing-one blank line, both handled by the trim rule.
- **Interior blank lines in a `text` (not `title`) caption grow the caption's auto-computed box height** (`render_text_label` computes `box_height` from `total_text_height` when `text_pos.height` is unset), which shifts vertical position on its associated photo. This is expected - it's the same mechanism that already sizes multi-line captions - but worth calling out since it wasn't previously observable for blank lines.

## Migration Plan

No migration needed - this is a rendering behavior fix with no config schema change. Existing configs continue to load; only the rendered pixel output of multi-line `text`/`title` values with leading/trailing/interior blank lines changes.
