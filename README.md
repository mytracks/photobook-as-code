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

## Text Labels

Add descriptive text to your photobook pages! Text labels are automatically associated with photos based on timestamps and can include markdown formatting for styling.

### Basic Usage

Add text labels to your configuration:

```yaml
photos: ./my-photos/
output:
  size: A4
  format: pdf
layout:
  photos_per_page: 2
theme: clean
text_labels:
  - timestamp: "2024-06-15T10:30:00"
    text: "# Beach Day\nOur amazing summer vacation!"
  - timestamp: "2024-06-15T14:00:00"
    text: "Beautiful sunset with *stunning* colors"
  - timestamp: "2024-06-16T09:00:00"
    text: "**Best breakfast ever**\nLocal cafe in town"
```

### Timestamp Format

Text labels use timestamps to match with photos. Two formats are supported:

- **ISO 8601**: `"2024-06-15T10:30:00"` (recommended)
- **Unix epoch**: `1718450400` (seconds since 1970-01-01)

The system automatically matches each text label to the photo with the closest timestamp based on EXIF data or file modification time.

### Discovering Photo Timestamps

Writing `text_labels` by hand requires knowing each photo's timestamp. Rather than inspecting EXIF data manually, run the CLI with `--extract-labels` to print an empty stub for every photo timestamp in the configured photo directory:

```bash
photobook --config my-photobook.yaml --extract-labels
```

This prints a ready-to-paste `text_labels` block to stdout, one entry per distinct timestamp, with an empty `text` field and the source filename(s) as a trailing comment:

```yaml
text_labels:
  - timestamp: "2024-06-15T10:30:00"  # IMG_0001.jpg
    text: ""
  - timestamp: "2024-06-15T14:00:00"  # IMG_0002.jpg, IMG_0003.jpg
    text: ""
```

A few things to know about this mode:

- It **ignores** any `text_labels` already in the config - it always prints a stub for every photo, regardless of what's already been written. Merge the output into your config by hand.
- Photos sharing the exact same timestamp collapse into a single stub entry, listing all their filenames, since they'd bind to the same page slot anyway.
- Entries are always printed in chronological order, regardless of the config's `layout.order` setting.
- No photobook is generated in this mode - `--extract-labels` exits immediately after printing, and any `--output` option is ignored.
- An empty `text: ""` entry is safe to leave in your config - it renders nothing (no text, no background) until you fill it in.

### Markdown Formatting

Text labels support a subset of markdown for styling:

- **Headings**: `# Heading 1`, `## Heading 2`, `### Heading 3`
  - H1 = 1.5x base font size
  - H2 = 1.3x base font size
  - H3 = 1.2x base font size
- **Bold**: `**bold text**`
- **Italic**: `*italic text*`
- **Bold + Italic**: `***bold and italic***`
- **Multiple lines**: Use `\n` for line breaks

### Theme Text Positioning

Themes control where text appears on the page. The `clean` theme includes text positioning for some layouts. You can customize text position in your own themes:

```yaml
layouts:
- count: 2
  photos:
  - orientation: landscape
    position: {x: 0.5, y: 0.25}
    size: {width: 1.0, height: 0.5}
    text:
      x: 10          # Left edge (% of page width)
      y: 55          # Top edge (% of page height)
      width: 80      # Text box width (%) - required
      align: left    # left, center, or right
```

**Note**: Text height is automatically calculated based on content. Only width needs to be specified.

### Theme Text Styling

Customize text appearance at the theme level:

```yaml
text:
  base_font_size: 14                # Base font size in points
  font_family: "DejaVuSans"         # Font family name
  text_color: "#000000"             # Text color (hex)
  text_background_enabled: true     # Enable semi-transparent background for readability
  text_background_color: "#FFFFFF"  # Background color (hex)
  text_background_opacity: 85       # Background opacity 0-100 (0=transparent, 100=opaque)
  text_padding: 8                   # Padding around text in pixels
```

**Text Background for Readability**: By default, text is rendered with a semi-transparent white background (85% opacity) to ensure readability when text is positioned over photos. You can customize the background color and opacity, or disable it entirely by setting `text_background_enabled: false`.

### Title Slots

For a large, prominent section title (e.g. a chapter heading), use `title` instead of `text`:

```yaml
text_labels:
  - timestamp: "2024-06-15T08:00:00"
    title: "# Day 1: Arrival"
  - timestamp: "2024-06-15T10:30:00"
    text: "Checked into our hotel"
```

A `title` entry is different from a `text` caption in one important way: instead of being overlaid on the nearest photo, it **consumes its own page slot**, just like a photo would. This means:

- The number of page slots is `photos + titles`, so a configured `pages` or `photos_per_page` accounts for titles automatically - adding titles can increase the total page count.
- Titles are placed chronologically among your photos (by timestamp, same as photos are ordered by date), landing between whichever two photos its timestamp falls between. If a title's timestamp exactly matches a photo's, the title comes first.
- Each `text_labels` entry must have exactly one of `text` or `title` - not both, not neither.
- Titles support the same Markdown formatting and multi-line content as `text` captions (headings, `**bold**`, `*italic*`/`_italic_`).

Because a title takes a photo's place in the page's layout template, themes need at least one layout at each relevant photo count that includes a **portrait**-shaped slot - a title always renders into a portrait-shaped cell, reusing whichever layout your theme already uses for a portrait photo at that count. No dedicated "title layout" needs to be authored.

#### Theme Title Styling

Title text styling is configured independently from caption (`text`) styling, at the theme level:

```yaml
title:
  base_font_size: 28                # Base font size in points (titles default larger than captions)
  font_family: "DejaVuSans"         # Font family name
  text_color: "#000000"             # Text color (hex)
  align: center                     # left, center, or right - alignment within the title's slot
  text_background_enabled: true     # Enable semi-transparent background for readability
  text_background_color: "#FFFFFF"  # Background color (hex)
  text_background_opacity: 85       # Background opacity 0-100 (0=transparent, 100=opaque)
  text_padding: 8                   # Padding around text in pixels
```

Unlike captions (which are positioned per-layout-slot via each template's `text:` block), a title's box is simply its matched layout slot's full `position`/`size`, and the text is vertically centered within it.

### Example with Multiple Labels

```yaml
photos: ./vacation-photos/
output:
  size: A4
  format: pdf
  filename: vacation-with-captions.pdf
layout:
  photos_per_page: 2
theme: clean
text_labels:
  - timestamp: "2024-06-15T08:00:00"
    text: "# Day 1: Arrival\nChecked into our hotel"
  - timestamp: "2024-06-15T12:30:00"
    text: "Lunch at the *best* local restaurant"
  - timestamp: "2024-06-15T18:00:00"
    text: "**Sunset view** from the beach"
  - timestamp: "2024-06-16T10:00:00"
    text: "## Day 2\nExploring the old town"
```

## Web Editor

Writing `text_labels` captions by hand means cross-referencing timestamps and filename comments against a separate photo viewer. `photobook-edit-labels` gives you a small local web app instead: it shows one photo at a time next to a plain text field for that photo's caption, and saves your edits directly into the configuration file as you navigate.

```bash
photobook-edit-labels --config my-photobook.yaml
```

Then open the printed URL (`http://127.0.0.1:5000/` by default) in your browser.

- Photos are shown in the same order (`layout.order`) the generated photobook would use, with Previous/Next navigation (also available via the left/right arrow keys).
- The text field holds raw Markdown - there's no rich-text toolbar or live preview, just what you type.
- Edits are saved automatically when you leave the text field (e.g. by clicking Next), with a small status indicator confirming the save.
- If a photo has no `text_labels` entry yet, one is created the first time you save text for it - you don't need to run `--extract-labels` first.
- The editor only ever writes to the one configuration file it was started with. Photos themselves are never modified, moved, or deleted.
- Editing `title` entries isn't supported yet - only `text` entries are shown for editing.

Options:

```bash
photobook-edit-labels --config my-photobook.yaml --host 0.0.0.0 --port 8080
```

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
  page_margin: 25     # Pixels around page edges
  photo_margin: 10    # Pixels to shrink each photo on each edge
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
