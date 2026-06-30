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

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.
