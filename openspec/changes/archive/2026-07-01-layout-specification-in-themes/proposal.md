## Why

The current theme system only supports grid-based layouts where all photos are arranged uniformly. This limits creative freedom and prevents theme designers from creating sophisticated page layouts that accommodate different photo orientations (portrait vs. landscape) with specific positioning and sizing. We need a flexible layout specification system that allows theme designers to define custom page templates for different photo combinations.

## What Changes

- Add layout template specification to theme YAML files
- Each template specifies photo count, orientation sequence (portrait/landscape), and positioning
- Photo positions defined by center point coordinates (x: 0.0-1.0, y: 0.0-1.0) relative to page dimensions
- Photo sizes specified as percentage values (relative to page width for landscape, height for portrait)
- Renderer matches actual photos to templates based on count and orientation sequence
- Renderer prefers templates where the portrait/landscape order matches the photo sequence
- **BREAKING**: Error thrown when no matching template exists for a given photo combination

## Capabilities

### New Capabilities
- `layout-templates`: Template-based page layout system with orientation-aware positioning and sizing

### Modified Capabilities
- `theme-system`: Add layout template configuration section to theme YAML specification
- `photo-layout-engine`: Replace grid-based layout with template matching algorithm based on photo orientations

## Impact

**Code:**
- `themes.py`: Load and parse layout templates from theme YAML
- `layout.py`: Add template matching logic based on photo orientations, remove grid-based layout code
- `renderer.py`: Use template specifications for photo positioning instead of grid calculations
- All theme YAML files: Must be updated with layout specifications

**Breaking Changes:**
- **BREAKING**: All themes must include `layouts` section with template specifications
- **BREAKING**: Grid-based layout code will be removed
- **BREAKING**: Themes without layout templates will fail with clear error message
