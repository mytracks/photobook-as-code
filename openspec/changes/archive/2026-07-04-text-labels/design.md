## Context

The photobook system currently supports only photos without text annotations. Users need to add contextual information (captions, dates, locations, descriptions) to tell richer stories. The challenge is to provide an intuitive way to associate text with photos while giving theme designers control over visual presentation.

Current state:
- YAML configuration defines photos and layout parameters
- Photo-layout-engine associates photos with EXIF timestamps
- Theme system defines visual styling and layout templates
- Renderer places photos on pages according to templates

Constraints:
- Text must be timestamped to enable automatic association with photos
- Theme designers need full control over text positioning and styling
- System must support multi-line text with basic formatting
- Solution must not break existing photobooks without text labels

## Goals / Non-Goals

**Goals:**
- Enable users to define timestamped text labels in YAML configuration
- Automatically match text labels to photos based on chronological proximity
- Allow theme designers to specify text position, size, and alignment per photo slot
- Support markdown-based text formatting (italics, bold, heading levels)
- Maintain backward compatibility with existing configurations

**Non-Goals:**
- Rich text editing UI (YAML-based only)
- Complex text layout algorithms (line wrapping, justification beyond basic alignment)
- Internationalization or text direction beyond left-to-right
- Text overlays on photos (text is positioned in dedicated template areas)
- Dynamic font loading (use system fonts)

## Decisions

### Decision 1: Timestamp-based association rather than explicit photo-text links
**Rationale**: Users naturally think chronologically ("add this caption near photos from that date"). Explicit linking requires knowing photo filenames, which is cumbersome. Timestamp-based matching leverages existing EXIF data and provides intuitive authoring.

**Alternatives considered**: 
- Photo filename references: Too brittle (renames break links)
- Index-based (photo 5, 6, 7): Fragile when photo set changes

**Implementation**: Find photo with timestamp closest to text label timestamp. If multiple labels exist for same page, distribute based on photo count.

### Decision 2: Template-level text positioning rather than global rules
**Rationale**: Different layouts need different text placements (e.g., 1-photo page might have text below, 4-photo grid might have text in corners). Theme designers understand their layouts and should have granular control.

**Alternatives considered**:
- Global text position (e.g., "always bottom"): Too inflexible for varied layouts
- Automatic text fitting: Complex to implement and reduces designer control

**Implementation**: Add optional `text` property to each photo entry in template layouts. Contains position (x, y, width, height as percentages) and alignment (left/center/right, top/middle/bottom).

### Decision 3: Markdown subset for formatting rather than full HTML/CSS
**Rationale**: Markdown is familiar to technical users and simple to parse. Subset keeps implementation simple while supporting common needs (emphasis, headings).

**Supported syntax**:
- `*italic*` → italic text
- `**bold**` → bold text  
- `#`, `##`, `###` at line start → increased font size (1.5x, 1.3x, 1.2x base size)

**Alternatives considered**:
- Plain text only: Too limiting for storytelling
- Full markdown: Overkill (lists, links, images not needed)
- Custom markup: Reinventing the wheel

### Decision 4: Text labels as separate YAML section rather than inline with photos
**Rationale**: Photos are discovered from directories; text is authored content. Keeping them separate maintains clarity and avoids mixing file-system concerns with authored content.

**Implementation**: Add top-level `text_labels` array in YAML. Each entry has `timestamp` (ISO 8601 or Unix epoch) and `text` (multi-line string).

## Risks / Trade-offs

**Risk: Ambiguous timestamp matching when multiple photos have similar times**  
→ Mitigation: Use deterministic tiebreaker (earliest photo wins). Document behavior in specs.

**Risk: Theme doesn't define text positions for a layout**  
→ Mitigation: Text rendering is optional. If template lacks text positions, skip text rendering for that page without error.

**Risk: Text overflow when content exceeds template-defined area**  
→ Mitigation: Initially, clip text at boundary. Future enhancement could add ellipsis or font scaling.

**Risk: Complex markdown parsing edge cases (nested formatting, malformed syntax)**  
→ Mitigation: Use simple regex-based parser. Unsupported syntax renders as-is (graceful degradation).

**Trade-off: Timestamp-based matching vs explicit control**  
Users gain convenience but lose explicit control over text-photo associations. Mitigation: Document timestamp matching behavior clearly. Future enhancement could add optional explicit overrides.

**Trade-off: Template-level positioning vs automatic text flow**  
Theme designers gain full control but must define positions for every layout. Mitigation: Provide sensible examples in default themes.
