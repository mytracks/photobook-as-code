# Theme Migration Guide: Layout Templates

The photobook-as-code layout engine has been upgraded! We've moved away from a rigid, grid-based layout system to a flexible **Layout Template** system.

This change gives theme designers full control over how photos are arranged, sized, and positioned based on the number of photos per page and their orientation (portrait vs. landscape).

## What's Changed?

- **Old System:** The engine automatically calculated a grid (e.g., 2x2 for 4 photos) and placed photos uniformly.
- **New System:** Themes must now explicitly define templates for how photos are arranged. The renderer uses these templates instead of grid calculations.

## Breaking Change

If you have custom themes, they will now fail to load with a `ThemeError` stating that the `layouts` section is missing.

**To fix this, you must add a `layouts` section to your custom theme YAML files.**

## Adding Layout Templates

A layout template defines a layout for a specific number of photos (`count`). For each photo, it specifies its expected `orientation`, `position` (as a center point in relative coordinates `0.0`-`1.0`), and `size` (as a percentage relative to page width for landscape or page height for portrait).

### Example Layouts Section

Add the following structure to your theme YAML:

```yaml
layouts:
  - count: 1
    photos:
      - orientation: landscape
        position: {x: 0.5, y: 0.5}
        size: 0.8  # 80% of page width
  - count: 1
    photos:
      - orientation: portrait
        position: {x: 0.5, y: 0.5}
        size: 0.8  # 80% of page height
  - count: 2
    photos:
      - orientation: landscape
        position: {x: 0.5, y: 0.25}
        size: 0.7
      - orientation: landscape
        position: {x: 0.5, y: 0.75}
        size: 0.7
```

### Template Matching

1.  **Count:** The engine first looks for templates matching the number of photos on the page.
2.  **Orientation:** It then checks if the orientations (portrait, landscape) match the available templates.
3.  **Exact Order:** If multiple templates exist, it prefers the one where the order of orientations matches exactly (e.g., [landscape, portrait] vs [portrait, landscape]).

If no template matches the given combination of photos, the renderer will log a `LayoutError` and skip the layout for that page. It is highly recommended to provide fallback templates covering combinations of orientations for 1 to 4 photos.

For a full set of default layouts, reference the built-in themes (e.g., `clean.yaml`, `modern.yaml`).

## Title Slots and Layout Templates

Title slots (`text_labels` entries using `title` instead of `text` - see the README's "Title Slots" section) consume a page slot the same way a photo does, and are matched into a layout template exactly like a photo: by count and orientation.

A title always presents as `portrait` orientation for this matching, regardless of the orientations of the real photos sharing its page. This means:

- A title lands in whatever cell a theme's layout template assigns to a portrait photo at that item count - no separate "title" orientation or dedicated title-only template is needed.
- If your theme is missing a portrait-inclusive layout at a given count (for example, only an all-landscape `count: 3` template exists), a page that needs to place a title alongside 2 landscape photos at that count will fail to match with a `LayoutError`, exactly as it would for a missing photo-orientation combination today.
- To use titles freely, make sure your theme defines at least one portrait-inclusive template for every photo count you expect a title to appear at (built-in themes already do this for counts 1-4).

Because a title's box comes directly from the matched slot's `position`/`size` - not from a per-slot `text:` block - no additional per-layout configuration is required to support titles once a portrait-inclusive template exists. Title font, color, and alignment are configured once at the theme level (see the README's "Theme Title Styling" section).
