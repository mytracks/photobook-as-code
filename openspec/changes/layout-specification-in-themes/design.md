## Context

The current photobook system uses a uniform grid-based layout where all photos are arranged in equal-sized cells. This approach works well for consistency but severely limits creative expression. Theme designers cannot create sophisticated layouts that leverage the different characteristics of portrait and landscape photos, nor can they create asymmetric or focal-point-based designs.

The system already has:
- Theme YAML loading infrastructure (`themes.py`)
- Photo layout calculation logic (`layout.py`)
- Page rendering with PIL (`renderer.py`)
- Photo metadata detection (`photos.py`)

This design replaces the grid-based approach with explicit layout templates. All themes must be updated to include layout specifications.

## Goals / Non-Goals

**Goals:**
- Enable theme designers to create custom page layouts with precise photo positioning
- Support orientation-aware layouts (portrait vs. landscape)
- Maintain aspect ratios while applying template specifications
- Provide clear error messages when photos don't match available templates
- Replace grid-based layout with more flexible template system

**Non-Goals:**
- Automatic layout optimization or AI-based layout generation
- Support for photo rotation or cropping specifications
- Dynamic layouts that adjust based on photo content
- Text or caption positioning within templates

## Decisions

### 1. Center-point positioning with relative coordinates

**Decision**: Use center-point coordinates (x, y) ranging from 0.0 to 1.0, relative to page dimensions.

**Rationale**: 
- Center-point positioning is more intuitive for designers than corner-based positioning
- Relative coordinates (0.0-1.0) make templates resolution-independent
- Simpler mental model than absolute pixel coordinates

**Alternatives considered**:
- Corner-based positioning: More complex when centering photos
- Absolute pixel coordinates: Would break at different page sizes

### 2. Orientation-specific size percentages

**Decision**: Size percentages are relative to page width for landscape photos and page height for portrait photos.

**Rationale**:
- Aligns with natural dimensions for each orientation
- Landscape photos naturally fill horizontal space
- Portrait photos naturally fill vertical space
- Simplifies template authoring (designers think in primary dimension)

**Alternatives considered**:
- Always relative to width: Awkward for portrait photos
- Separate width/height percentages: More complex template specification

### 3. Template matching with order preference

**Decision**: Match templates by count and orientation sequence, preferring exact order matches when multiple templates qualify.

**Rationale**:
- Gives designers control over layout intent
- A [landscape, portrait, portrait] sequence has different visual weight than [portrait, landscape, portrait]
- Prevents arbitrary template selection when multiple options exist

**Alternatives considered**:
- Match by count only: Loses visual design intent
- Match by count and orientation histogram: Doesn't preserve sequence

### 4. Fail-fast on missing templates

**Decision**: Raise an error when no matching template exists rather than falling back to grid layout.

**Rationale**:
- Makes missing templates immediately visible during testing
- Prevents silent degradation of intended designs
- Forces explicit coverage of expected photo combinations
- Template authors can decide whether to add grid fallback in theme

**Alternatives considered**:
- Auto-fallback to grid: Hides template gaps, inconsistent output
- Skip page: Loses photos, confusing to users

### 5. Theme YAML structure

**Decision**: Add `layouts` section as list of template objects, each with `count`, `orientations`, and `photos` arrays.

```yaml
layouts:
  - count: 2
    photos:
      - orientation: landscape
        position: {x: 0.5, y: 0.2}
        size: 0.6
      - orientation: portrait
        position: {x: 0.5, y: 0.5}
        size: 0.4
      - orientation: portrait
        position: {x: 0.5, y: 0.8}
        size: 0.6
```

**Rationale**:
- Keeps all theme configuration in one place
- `count` enables quick filtering before orientation matching
- Nested `photos` array maintains position-orientation coupling

**Alternatives considered**:
- Separate template files: Fragments theme configuration
- Flat orientation strings (e.g., "LP"): Less readable

## Risks / Trade-offs

**[Risk] Template authoring complexity** → Provide example templates in default themes and clear documentation

**[Risk] Missing template combinations** → Provide helpful error messages listing what orientations were expected vs. found

**[Risk] Coordinate system confusion** → Document with visual diagrams showing (0,0) = top-left, (1,1) = bottom-right, (0.5, 0.5) = center

**[Risk] Photo overlap in templates** → Document as theme author responsibility; rendering engine does not validate overlap

**[Trade-off] Order-preference matching adds complexity** → But provides necessary control for design intent; can be disabled by providing single template per count

**[Trade-off] Breaking change for existing themes** → All themes must be updated with layout specifications; grid-based code will be removed

## Migration Plan

**Phase 1: Implementation**
1. Add `layouts` section as required field in theme YAML schema
2. Add orientation detection to photo loading
3. Implement template matching algorithm
4. Update renderer to use template positioning
5. Remove grid-based layout code

**Phase 2: Theme Updates**
1. Update all default themes (clean, modern, classic) with layout templates
2. Add layout templates covering common photo combinations (1-6 photos)
3. Test each theme with various orientation combinations
4. Document migration guide for custom theme authors

**Phase 3: Validation**
1. Error testing: Verify helpful messages for missing templates
2. Edge case testing: Single photo, all same orientation, complex sequences
3. Test all default themes with real photo sets
4. Verify all existing example configs work with updated themes

**Breaking Change**: Existing themes without `layouts` section will fail with clear error message. Theme authors must add layout specifications.

## Open Questions

**Q: Should square photos match both portrait and landscape templates?**  
A: Treat as landscape for now (simpler matching). Can revisit if users need separate square handling.

**Q: Should we support optional photos (e.g., 2-3 photos matching same template)?**  
A: No in initial version. One template = exact count. Keeps matching logic simple.

**Q: What photo combinations should default themes support?**  
A: Cover 1-6 photos per page with common orientation combinations. For example: 1 photo (landscape/portrait), 2 photos (LL, PP, LP, PL), 3 photos (LLP, LPP, PLL, PPL, etc.). Themes should fail with helpful error for unsupported combinations rather than attempting to handle all possibilities.
