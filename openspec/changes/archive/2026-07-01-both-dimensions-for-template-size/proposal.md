## Why

Currently, in a theme template, the size of a photo is specified by a single numeric value (acting as width for landscape and height for portrait). This approach is not flexible enough. Introducing a maximum bounds pair (`{width, height}`) allows better control over the rendering size of photos within the templates, regardless of the aspect ratio.

## What Changes

- Update the theme template schema to expect `size` as an object containing `{width, height}` (e.g. `{width: 0.8, height: 0.5}`) instead of a single scalar value.
- Update the layout engine to compute the scaled size based on both width and height constraints of the photo's aspect ratio, and select the smaller one to fit the boundaries.
- **BREAKING**: Remove support for the old format (single number size). Theme templates will be expected to use the new object structure.

## Capabilities

### New Capabilities
<!-- No new capabilities, we are modifying existing ones -->

### Modified Capabilities
- `layout-templates`: Update photo size specification from a scalar value to a `{width, height}` object.
- `photo-layout-engine`: Update layout calculations to use maximum bounds and calculate the minimum fitting scale for both dimensions.

## Impact

- All existing theme templates using a single number for `size` will break and must be updated to the new structure.
- The configuration parser for templates must be updated.
- The core layout algorithms in the `photo-layout-engine` must be updated to handle aspect ratio calculations restricted by a bounding box.