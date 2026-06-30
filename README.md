# Photobook as Code

Create professional photobook layouts programmatically using simple YAML configuration files.

## What is it?

Photobook as Code is a CLI tool that automatically generates print-ready photobook layouts from your photos. Instead of manually arranging photos in desktop software, you describe what you want in a YAML file and let the tool do the layout work.

## Features

- **Declarative Configuration**: Define your photobook in a simple YAML file
- **Automatic Layout**: Smart photo arrangement based on your preferences
- **Print-Ready Output**: Generate PDF or high-resolution images (300 DPI)
- **Theme System**: Choose from built-in themes or create your own
- **Standard Paper Sizes**: Support for A4, Letter, and custom dimensions
- **Offline Operation**: No cloud dependencies, works entirely locally

## Installation

```bash
pip install photobook-as-code
```

Or install from source:

```bash
git clone https://github.com/yourusername/photobook-as-code.git
cd photobook-as-code
pip install -e .
```

## Quick Start

1. Create a configuration file `my-photobook.yaml`:

```yaml
photos: ./my-photos/
output:
  size: A4
  format: pdf
  filename: my-album.pdf
layout:
  photos_per_page: 4
theme: clean
```

2. Generate your photobook:

```bash
photobook --config my-photobook.yaml
```

3. Find your PDF in the current directory!

## Configuration

### Basic Structure

```yaml
# Path to photo directory (relative or absolute)
photos: ./vacation-2024/

# Output settings
output:
  size: A4                    # A4, Letter, or custom dimensions
  format: pdf                 # pdf, png, or jpg
  filename: vacation-book.pdf # output filename
  
# Layout options (choose one)
layout:
  photos_per_page: 4         # Fixed photos per page
  # OR
  pages: 10                  # Fixed number of pages

# Theme selection
theme: clean                 # clean, classic, or modern
```

### Paper Sizes

- **A4**: 210mm × 297mm
- **Letter**: 8.5in × 11in
- **Custom**: Specify width and height

### Themes

- **clean**: Minimalist with white background and thin borders
- **classic**: Traditional with cream background and visible borders  
- **modern**: Contemporary with no borders and tight spacing

## Output Formats

- **PDF**: Single file with all pages (ideal for printing)
- **PNG**: Individual high-quality images per page
- **JPG**: Individual compressed images per page

## Requirements

- Python 3.9 or higher
- Pillow (image processing)
- ReportLab (PDF generation)
- Click (CLI framework)
- PyYAML (configuration parsing)

## Configuration Reference

### Complete Configuration Example

```yaml
# Photo source (required)
photos: ./my-photos/

# Output configuration (required)
output:
  size: A4              # Paper size: A4, Letter, or custom (e.g., "2480x3508")
  format: pdf           # Output format: pdf, png, or jpg
  filename: album.pdf   # Output filename (optional, defaults to config name)
  directory: ./output/  # Output directory (optional, defaults to current dir)
  quality: 95           # JPEG quality 1-100 (only for jpg format)

# Layout configuration
layout:
  photos_per_page: 4    # OR pages: 10 (choose one, not both)
  order: alphabetical   # Photo ordering: alphabetical or date

# Theme (optional, defaults to 'clean')
theme: clean            # Built-in: clean, classic, modern
                        # Or path: ./my-custom-theme.yaml
```

### Photo Ordering

- **alphabetical** (default): Sort by filename
- **date**: Sort by EXIF date taken (falls back to file modification date)

### Custom Paper Sizes

For custom dimensions, specify width and height in pixels at 300 DPI:

```yaml
output:
  size: "2480x3508"  # Custom size in pixels
```

Common sizes at 300 DPI:
- A4: 2480 × 3508 pixels
- Letter: 2550 × 3300 pixels
- A5: 1748 × 2480 pixels

## Theme Customization

### Creating Custom Themes

Create a YAML file with your theme definition:

```yaml
name: My Custom Theme
description: My personalized photobook style

background:
  color: "#F0F0F0"    # Hex color code

borders:
  enabled: true       # true or false
  width: 3            # Border width in pixels
  color: "#333333"    # Border color
  shadow: false       # Drop shadow effect

spacing:
  grid_gap: 12        # Pixels between photos
  page_margin: 25     # Pixels around page edges
```

Use your custom theme:

```yaml
theme: ./themes/my-custom-theme.yaml
```

### Built-in Themes

**clean** - Minimalist
- White background (#FFFFFF)
- Thin borders (2px, light gray)
- Moderate spacing (10px gap, 20px margin)

**classic** - Traditional
- Cream background (#F5F5DC)
- Visible borders (4px, brown)
- Generous spacing (15px gap, 30px margin)
- Drop shadows enabled

**modern** - Contemporary
- White background (#FFFFFF)
- No borders
- Tight spacing (5px gap, 10px margin)

## Print Quality Recommendations

For best print quality:

### Photo Resolution

- **Minimum recommended**: 1200 × 1200 pixels per photo
- **Ideal**: 2000 × 1500 pixels or higher
- The tool will warn if photos are below recommended resolution

### Output Settings

- **DPI**: All output is generated at 300 DPI (print standard)
- **Format**: Use PDF for professional printing
- **Color space**: RGB (most print services accept RGB and convert to CMYK)

### Print Services

Common print service requirements:
- **Blurb**: PDF at 300 DPI, RGB color
- **Shutterfly**: Individual JPG pages, high quality
- **Local print shop**: PDF preferred, check with printer

## Example Configurations

### Family Vacation Album

```yaml
photos: ./vacation-2024/
output:
  size: A4
  format: pdf
  filename: family-vacation.pdf
layout:
  photos_per_page: 6
  order: date
theme: classic
```

### Instagram Grid Style

```yaml
photos: ./instagram-exports/
output:
  size: Letter
  format: pdf
  filename: insta-grid.pdf
layout:
  photos_per_page: 9
theme: modern
```

### Wedding Album (Archival Quality)

```yaml
photos: ./wedding-photos/
output:
  size: A4
  format: png
  directory: ./wedding-album-pages/
layout:
  photos_per_page: 4
  order: date
theme: clean
```

### Social Media Preview

```yaml
photos: ./event-photos/
output:
  size: Letter
  format: jpg
  quality: 90
  directory: ./preview-pages/
layout:
  pages: 20
theme: modern
```

## Migration Guide (Breaking Changes)

This update introduces a new, flexible template-based layout system that replaces the old grid-based layout. This is a **BREAKING CHANGE** for custom themes and configurations.

**Key Changes:**

1.  **`layouts` section is now required in all themes**:
    -   Previously, themes implicitly used a grid-based layout.
    -   Now, every theme (built-in or custom) **must** include a `layouts` section in its YAML definition. This section defines how photos are arranged on a page for different photo counts and orientation combinations.
    -   Themes without a `layouts` section will now raise a `"Theme missing 'layouts' section"` error.

2.  **Removal of grid-based layout options**:
    -   The internal grid-based layout calculation code has been removed.
    -   Layouts are now entirely driven by the templates defined in the `layouts` section of your theme.

**Migration Steps for Custom Themes:**

If you have custom themes, you need to update them to include the new `layouts` section.

1.  **Add `layouts` section**:
    -   Add a top-level `layouts:` key to your theme YAML file.
    -   Under `layouts`, define a list of `LayoutTemplate` objects.

2.  **Define Layout Templates**:
    -   For each `LayoutTemplate`, specify:
        -   `count`: The number of photos the template is designed for.
        -   `photos`: A list of `PhotoSpec` objects, one for each photo.
            -   `orientation`: (`landscape` or `portrait`) - used for matching and sizing.
            -   `position`: `{x: 0.0-1.0, y: 0.0-1.0}` - center point of the photo, relative to the page. (0.0,0.0 is top-left, 0.5,0.5 is center).
            -   `size`: `0.0-1.0` - relative size. For landscape photos, this is a percentage of the page width. For portrait photos, it's a percentage of the page height.

**Example of a basic `layouts` section (for 1 photo):**

```yaml
layouts:
  - count: 1
    photos:
      - orientation: landscape
        position: {x: 0.5, y: 0.5}
        size: 0.9 # 90% of page width
  - count: 1
    photos:
      - orientation: portrait
        position: {x: 0.5, y: 0.5}
        size: 0.9 # 90% of page height
```

Refer to the built-in themes (`clean.yaml`, `modern.yaml`, `classic.yaml` in `src/photobook_as_code/themes/`) for more comprehensive examples covering various photo counts and orientation combinations.

## Troubleshooting

### "No supported image files found"

- Check that your photos directory exists and contains JPG or PNG files
- Ensure file extensions are correct (.jpg, .jpeg, .png)
- Check file permissions

### "Photos have resolution below recommended minimum"

- This is a warning, not an error - generation will continue
- For best print quality, use photos of at least 1200×1200 pixels
- Consider using higher resolution source photos

### "Theme not found"

- Check theme name spelling (case-sensitive)
- Available built-in themes: clean, classic, modern
- For custom themes, verify the file path exists

### "Cannot specify both photos_per_page and pages"

- Choose only one layout constraint, not both
- Use `photos_per_page: 4` OR `pages: 10`, but not both

### PDF generation fails

- Ensure you have write permissions in the output directory
- Check that output filename doesn't contain invalid characters
- Try specifying an absolute path for output directory

### Out of memory errors

- Reduce the number of photos per batch
- Use JPG format with lower quality setting
- Close other memory-intensive applications

### EXIF date warnings

- Some photos may lack EXIF date metadata
- Tool falls back to file modification date
- To fix: use photo management software to add EXIF dates

### Layout and Theme Configuration Errors

- **"Theme missing 'layouts' section"**:
  - **Description**: The selected theme (built-in or custom) does not have a required `layouts` section in its YAML definition.
  - **Resolution**: Ensure your theme YAML includes a `layouts` section that defines at least one layout template. Refer to "Theme Customization" for examples.

- **"Layout template at index X is missing required fields: 'count' or 'photos'"**:
  - **Description**: A layout template within the `layouts` section is missing either the `count` or `photos` field.
  - **Resolution**: Each layout template must define `count` (the number of photos for this template) and `photos` (a list of photo specifications).

- **"Photo spec at index X in layout Y is missing required field: 'orientation', 'position', or 'size'"**:
  - **Description**: A photo specification within a layout template is missing a required field.
  - **Resolution**: Each photo specification must include `orientation` (landscape/portrait), `position` (x,y coordinates), and `size` (relative percentage).

- **"Photo spec orientation must be 'landscape' or 'portrait'"**:
  - **Description**: An invalid value was provided for a photo's `orientation`.
  - **Resolution**: Use either `'landscape'` or `'portrait'` for photo orientation.

- **"Photo spec position coordinates must be in 0.0-1.0 range"**:
  - **Description**: The `x` or `y` coordinate for a photo's position is outside the valid range of 0.0 to 1.0.
  - **Resolution**: Ensure position coordinates are between 0.0 (top/left) and 1.0 (bottom/right).

- **"Photo spec size must be in 0.0-1.0 range"**:
  - **Description**: The `size` value for a photo is outside the valid range of 0.0 to 1.0.
  - **Resolution**: Ensure the photo `size` is between 0.0 and 1.0.

- **"No layout templates found for N photos."**:
  - **Description**: The theme does not contain any layout templates designed for the current number of photos on a page (N).
  - **Resolution**: Add a layout template to your theme with `count: N`, or adjust the number of photos on the page.

- **"No layout templates found matching orientation types/counts for [...]"**:
  - **Description**: The theme has templates for the correct photo count, but none match the combination of landscape and portrait photos on the current page.
  - **Resolution**: Ensure your theme includes templates that support the specific mix of landscape and portrait photos for the given photo count.

- **"No exact order-matching template found for orientations: [...]"**:
  - **Description**: The theme has templates that match the photo count and types/counts of orientations, but none match the exact sequence of orientations on the page.
  - **Resolution**: Review your theme's layout templates. If you need a specific order for photos (e.g., [L, P, P] vs. [P, L, P]), ensure there is a template that matches that exact sequence.


## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.
