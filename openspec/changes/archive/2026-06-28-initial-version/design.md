## Context

This is a greenfield project to create an automated photobook layout generator. No existing codebase exists. The tool will be used by automation enthusiasts who want to generate photobooks programmatically rather than using manual desktop software.

**Key Constraints:**
- Must be usable as a CLI tool
- Must work offline without cloud dependencies
- Must generate print-ready output
- Must be simple to install and run

**Target Users:**
- Power users comfortable with YAML and command-line tools

## Goals / Non-Goals

**Goals:**
- Create a working CLI tool that generates photobooks from YAML configuration
- Support common use cases with minimal configuration
- Provide good defaults and opinionated layouts
- Generate professional, print-ready output

**Non-Goals:**
- GUI or web interface (CLI only)
- Advanced photo editing capabilities (cropping, filters, adjustments)
- Online printing service integration
- Real-time preview or interactive layout editing
- Support for video or other media types

## Decisions

### Technology Stack: Python

**Decision:** Use Python 3.9+ as the implementation language.

**Rationale:**
- Excellent image processing libraries (Pillow)
- Strong PDF generation libraries (ReportLab)
- YAML parsing built into standard ecosystem (PyYAML)
- Easy distribution via pip
- Good CLI frameworks (Click or Typer)

**Alternatives Considered:**
- **Node.js**: Good ecosystem but image processing is less mature
- **Go**: Fast but fewer image/PDF libraries, harder for end users to extend with custom themes

### Image Processing: Pillow (PIL Fork)

**Decision:** Use Pillow for all image manipulation operations.

**Rationale:**
- Pure Python, easy to install via pip
- Comprehensive image format support (JPEG, PNG, etc.)
- Good performance for typical photobook use cases
- Extensive documentation and community support
- Built-in support for EXIF data reading

**Alternatives Considered:**
- **ImageMagick (via wand)**: More powerful but requires external binary installation
- **OpenCV**: Overkill for this use case, larger dependency

### PDF Generation: ReportLab

**Decision:** Use ReportLab for PDF output generation.

**Rationale:**
- Industry-standard Python PDF library
- Precise control over page layout and dimensions
- Good support for high-resolution images
- Can embed images efficiently
- Commercial-grade output quality

**Alternatives Considered:**
- **PyPDF2/pypdf**: More for PDF manipulation than creation
- **pdfkit/WeasyPrint**: HTML-to-PDF approach adds unnecessary complexity

### CLI Framework: Click

**Decision:** Use Click for command-line interface.

**Rationale:**
- Clean, decorator-based API
- Excellent documentation
- Built-in support for progress bars and colored output
- Easy testing
- Industry standard (used by Flask, etc.)

**Alternatives Considered:**
- **argparse**: More verbose, less user-friendly
- **Typer**: Great but adds type complexity; Click is sufficient for v1

### Configuration Format: YAML

**Decision:** Use YAML for configuration files.

**Rationale:**
- Human-readable and editable
- Supports comments for documentation
- Better for nested structures than JSON
- Familiar to developers (used in Docker, Kubernetes, CI/CD)

**Implementation:**
```yaml
# Example structure
photos: ./vacation/2024/
output:
  size: A4
  format: pdf
  filename: vacation-album.pdf
layout:
  photos_per_page: 4
  # OR: pages: 10
theme: clean
```

### Theme Storage: YAML Files

**Decision:** Store themes as YAML files in a themes/ directory.

**Rationale:**
- Consistent with main configuration format
- Users can easily create custom themes by copying/editing
- Version controllable
- No code execution required (safer than Python modules)

**Theme Structure:**
```yaml
name: Clean
description: Minimalist style with white background
background:
  color: "#FFFFFF"
borders:
  enabled: true
  width: 2
  color: "#CCCCCC"
spacing:
  grid_gap: 10  # pixels
  page_margin: 20  # pixels
```

### Project Architecture: Pipeline Pattern

**Decision:** Implement as a pipeline of independent stages.

**Architecture:**
```
┌─────────────────────────────────────────────────────┐
│                   CLI Entry Point                   │
│                  (click command)                    │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              Configuration Parser                   │
│         (validate YAML, resolve paths)              │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│               Photo Collector                       │
│     (find photos, read EXIF, determine order)       │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│               Layout Calculator                     │
│  (determine pages, photos per page, grid layout)    │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│                Theme Applicator                     │
│         (load theme, prepare styling)               │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│                 Page Renderer                       │
│    (create page images with photos and styling)     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│               Output Generator                      │
│          (PDF assembly or image export)             │
└─────────────────────────────────────────────────────┘
```

**Rationale:**
- Clear separation of concerns
- Easy to test each stage independently
- Easy to add new stages later (e.g., text overlays)
- Progress reporting between stages
- Easy to debug by inspecting intermediate state

**Module Structure:**
```
photobook_as_code/
├── cli.py              # Click commands
├── config.py           # Configuration parsing and validation
├── photos.py           # Photo discovery and metadata
├── layout.py           # Layout calculation algorithms
├── themes.py           # Theme loading and management
├── renderer.py         # Page rendering with Pillow
├── output.py           # PDF/image output generation
└── utils.py            # Shared utilities
```

### Layout Algorithm: Simple Grid with Equal Cells

**Decision:** Use equal-sized grid cells for initial version.

**Rationale:**
- Predictable, consistent results
- Simpler implementation
- Easier to reason about spacing
- Photos maintain aspect ratio within cells

**Implementation Details:**
- Calculate grid dimensions from photos-per-page (e.g., 4 → 2x2, 6 → 2x3)
- All cells have equal dimensions
- Photos fit within cells preserving aspect ratio (letterbox/pillarbox as needed)
- Background color fills unused cell space

**Future Enhancement:** Could add "flexible" layouts with variable cell sizes for featured photos.

### Photo Ordering: Alphabetical with EXIF Date Option

**Decision:** Default to alphabetical filename ordering, with optional EXIF date sorting.

**Rationale:**
- Alphabetical is predictable and reproducible
- EXIF date is natural for chronological photobooks
- Explicit ordering via filename numbering (IMG_001, IMG_002) works well

**Configuration:**
```yaml
photos:
  path: ./photos/
  order: alphabetical  # or 'date'
```

## Risks / Trade-offs

### Risk: Large Image Memory Usage
**Description:** Loading many high-resolution photos into memory simultaneously could cause out-of-memory issues.

**Mitigation:**
- Process pages one at a time
- Load only photos needed for current page
- Optionally resize/downsample photos to target DPI before processing
- Add --max-resolution flag for memory-constrained environments

### Risk: EXIF Data Inconsistency
**Description:** Not all photos have EXIF data; different cameras use different formats.

**Mitigation:**
- Fall back to file modification time if EXIF missing
- Use robust EXIF parsing (Pillow handles most formats)
- Document EXIF requirements clearly
- Provide warning if EXIF data missing when date ordering requested

### Risk: Print Quality Expectations
**Description:** Users may have varying expectations for print quality and professional output.

**Mitigation:**
- Default to 300 DPI for all output
- Document recommended image resolution (e.g., minimum 2000x1500 for A4)
- Add validation warning if source photos are below recommended resolution
- Include example configurations for common print services

### Trade-off: Opinionated vs Flexible Layouts
**Decision:** Start opinionated (equal grid cells) rather than flexible complex layouts.

**Impact:**
- **Pro:** Faster to implement, easier to use, more predictable
- **Con:** Less creative freedom, may not suit all aesthetic preferences
- **Future:** Can add layout variations as additional themes or modes

### Trade-off: CLI Only vs GUI
**Decision:** No GUI for initial version.

**Impact:**
- **Pro:** Faster development, better for automation, version-controllable configs
- **Con:** Higher barrier for non-technical users
- **Future:** Could add web preview or GUI wrapper later

### Trade-off: RGB vs CMYK Color Space
**Decision:** Default to RGB output; optional CMYK for professional printing.

**Impact:**
- **Pro:** RGB is simpler and more widely supported
- **Con:** Professional print shops prefer CMYK; color conversion may be needed
- **Mitigation:** Document color space considerations; add CMYK option in future version

## Open Questions

### Question: How to handle photos with insufficient resolution?
**Options:**
1. Reject generation with error
2. Generate with warning
3. Upscale with interpolation (quality loss)

**Recommendation:** Generate with prominent warning; add strict mode flag for error.

### Question: Should themes support custom fonts?
**Implications:** No text in v1, but themes might eventually include title/caption styling.

**Recommendation:** Defer until text support is added; keep theme structure extensible.

### Question: Subdirectory handling for photo paths
**Options:**
1. Always recursive (include all subdirectories)
2. Single level only
3. Configurable

**Recommendation:** Start with single-level; add recursive option based on user feedback.
