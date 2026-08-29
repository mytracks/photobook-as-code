## Purpose

Output generation for creating print-ready PDF and image files. This capability handles PDF assembly, individual page image generation, print-ready settings, file naming, progress reporting, and output directory management.

## Requirements

### Requirement: Generate output with minimal memory footprint
The system SHALL generate PDF and image output files using a streaming approach that processes pages incrementally rather than loading all pages into memory simultaneously.

#### Scenario: Large photobook PDF generation
- **WHEN** user generates a PDF with 50+ pages
- **THEN** system processes pages one at a time, keeping only the current page in memory

#### Scenario: Memory usage for multi-page output
- **WHEN** generating output with multiple pages
- **THEN** peak memory usage SHALL NOT exceed memory required for a single page plus output file overhead

#### Scenario: Sequential page processing
- **WHEN** pages are rendered for output
- **THEN** system renders each page on-demand during output generation rather than pre-rendering all pages

#### Scenario: Generator-based page iteration
- **WHEN** output generation receives rendered pages
- **THEN** system accepts page iterator that yields pages one at a time

### Requirement: Generate PDF output
The system SHALL generate a single PDF file containing all photobook pages in sequence.

#### Scenario: Multi-page PDF creation
- **WHEN** user requests PDF output
- **THEN** system creates PDF with one page per layout page

#### Scenario: PDF page dimensions
- **WHEN** generating PDF
- **THEN** PDF pages match specified output size from configuration

#### Scenario: High-resolution images
- **WHEN** photos are embedded in PDF
- **THEN** system preserves image quality suitable for printing (minimum 300 DPI)

### Requirement: Generate individual image files
The system SHALL generate separate image files for each photobook page.

#### Scenario: PNG output format
- **WHEN** user requests PNG output
- **THEN** system generates one PNG file per page with lossless compression

#### Scenario: JPG output format
- **WHEN** user requests JPG output
- **THEN** system generates one JPG file per page with specified quality level

#### Scenario: Sequential file naming
- **WHEN** generating multiple page images
- **THEN** system names files sequentially (e.g., page_001.png, page_002.png)

### Requirement: Generate transparent PNG output
The system SHALL support rendering PNG page images with a transparent background instead of an opaque fill, leaving only photo, text, and border pixels opaque.

#### Scenario: Transparent PNG requested
- **WHEN** `output.format` is `png` and `output.transparent` is `true`
- **THEN** system renders each page as an RGBA image where page margins and any gaps between photos are fully transparent (alpha 0)

#### Scenario: Photo content stays opaque
- **WHEN** a photo is placed on a transparent-background page
- **THEN** the pixels covered by that photo are fully opaque, regardless of the photo's own content (including photos containing colors that match the theme's background color)

#### Scenario: Letterboxed photo edges transparent
- **WHEN** a photo's aspect ratio does not match its layout cell and transparent background is enabled
- **THEN** the resulting letterbox gap around the photo is transparent, not filled with the theme's background color

#### Scenario: Text and borders stay opaque
- **WHEN** text labels or photo borders are rendered on a transparent-background page
- **THEN** their pixels remain fully opaque

#### Scenario: Default behavior unchanged
- **WHEN** `output.transparent` is not set
- **THEN** system continues to render an opaque background fill using `theme.background.color`, as before

### Requirement: Composite theme effects correctly on transparent output
The system SHALL render drop shadows and semi-transparent text-background boxes with correct alpha compositing when transparent PNG output is enabled, preserving intended partial transparency rather than corrupting pixel color or opacity.

#### Scenario: Drop shadow on transparent output
- **WHEN** theme specifies `borders.shadow: true` and `output.transparent` is `true`
- **THEN** the shadow renders as a semi-transparent element with correct alpha, rather than being flattened to an opaque color or discarded

#### Scenario: Text background box on transparent output
- **WHEN** theme specifies `text_background_enabled: true` (for text labels or titles) and `output.transparent` is `true`
- **THEN** the background box and the text drawn on top of it render with correct color and alpha at every pixel, including anti-aliased text edges, without color fringing introduced by the transparent backdrop

#### Scenario: Opaque output rendering unchanged
- **WHEN** `output.transparent` is not set
- **THEN** drop shadow and text-background-box rendering remain visually unchanged from prior output

### Requirement: Validate transparent background configuration
The system SHALL restrict `output.transparent` to output formats that support an alpha channel.

#### Scenario: Transparent requested with unsupported format
- **WHEN** `output.transparent` is `true` and `output.format` is `jpg` or `pdf`
- **THEN** system raises a configuration error at load time rather than proceeding to render

#### Scenario: Transparent requested with png format
- **WHEN** `output.transparent` is `true` and `output.format` is `png`
- **THEN** system accepts the configuration and proceeds

### Requirement: Apply print-ready settings
The system SHALL generate output suitable for professional printing.

#### Scenario: Resolution specification
- **WHEN** generating output for print
- **THEN** system uses minimum 300 DPI resolution

#### Scenario: Color space
- **WHEN** configuration specifies color space
- **THEN** system outputs in specified color space (RGB or CMYK)

#### Scenario: Bleed marks
- **WHEN** configuration includes bleed specification
- **THEN** system includes bleed area in output dimensions

### Requirement: Handle output file naming
The system SHALL generate output files with meaningful names based on configuration or defaults.

#### Scenario: Custom output filename
- **WHEN** configuration specifies output filename
- **THEN** system uses specified name for output file(s)

#### Scenario: Default filename
- **WHEN** configuration does not specify output filename
- **THEN** system generates filename from configuration file name

#### Scenario: Prevent overwriting
- **WHEN** output file already exists
- **THEN** system either prompts for confirmation or appends timestamp to avoid overwriting

#### Scenario: Base filename used as page file prefix for image formats
- **WHEN** output format is `png` or `jpg` and the base filename is derived (e.g. `mondsee`)
- **THEN** system uses that base filename only as the prefix of each page's filename (e.g. `mondsee_page_001.jpg`), never as a directory name, and any extension implied by the output format is not appended to the directory path

### Requirement: Report generation progress
The system SHALL provide progress feedback during output generation process using pre-calculated page count rather than batch size.

#### Scenario: Page rendering progress
- **WHEN** system is rendering pages
- **THEN** system displays progress indicator showing current page being processed

#### Scenario: Progress with streaming generation
- **WHEN** pages are generated via streaming
- **THEN** progress indicator shows "Page X of Y" where Y is the expected total from layout calculation

#### Scenario: Completion notification
- **WHEN** output generation completes successfully
- **THEN** system displays success message with output file location

#### Scenario: Generation failure
- **WHEN** output generation fails
- **THEN** system reports error message with specific failure reason

### Requirement: Optimize file size
The system SHALL generate output files with reasonable file sizes while maintaining quality.

#### Scenario: Image compression
- **WHEN** generating output
- **THEN** system applies appropriate compression to embedded images

#### Scenario: Quality vs size balance
- **WHEN** user specifies quality level
- **THEN** system adjusts compression accordingly

#### Scenario: PDF page image compression
- **WHEN** a rendered page is embedded into PDF output
- **THEN** system encodes the page as JPEG at the configured output quality level (`output.quality`, default 95) rather than embedding it losslessly

### Requirement: Support output directory specification
The system SHALL allow users to specify where output files are saved.

#### Scenario: Custom output directory
- **WHEN** configuration specifies output directory
- **THEN** system saves generated files to specified location

#### Scenario: Default output location
- **WHEN** configuration does not specify output directory
- **THEN** system saves output to current working directory

#### Scenario: Create missing directories
- **WHEN** specified output directory does not exist
- **THEN** system creates necessary directory structure

#### Scenario: Image page files land directly in the output directory
- **WHEN** output format is `png` or `jpg`
- **THEN** system writes each page's image file directly into the resolved output directory, without creating an intermediate per-run subfolder named after the base filename

### Requirement: Render text labels on pages
The system SHALL render text labels on photobook pages according to template positioning and formatting specifications.

#### Scenario: Text label with position
- **WHEN** page has text label associated with photo and template defines text position
- **THEN** system renders text at specified position with proper formatting

#### Scenario: Multi-line text rendering
- **WHEN** text label contains multiple lines, whether from literal line breaks in the source text or from word-wrapping a line that exceeds the bounding box's width
- **THEN** system renders each line with proper line spacing

#### Scenario: Text with italic formatting
- **WHEN** text segment is marked as italic
- **THEN** system renders text in italic font style

#### Scenario: Text with bold formatting
- **WHEN** text segment is marked as bold
- **THEN** system renders text in bold font weight

#### Scenario: Text with heading format
- **WHEN** text line is marked as heading with size multiplier
- **THEN** system renders text at increased font size according to multiplier

#### Scenario: Combined bold and italic
- **WHEN** text segment has both bold and italic formatting
- **THEN** system renders text with both styles applied

#### Scenario: Text alignment left
- **WHEN** template specifies left text alignment
- **THEN** system aligns text to left edge of bounding box

#### Scenario: Text alignment center
- **WHEN** template specifies center text alignment
- **THEN** system centers text horizontally within bounding box

#### Scenario: Text alignment right
- **WHEN** template specifies right text alignment
- **THEN** system aligns text to right edge of bounding box

#### Scenario: Vertical alignment top
- **WHEN** template specifies top vertical alignment
- **THEN** system aligns text to top of bounding box

#### Scenario: Vertical alignment middle
- **WHEN** template specifies middle vertical alignment
- **THEN** system centers text vertically within bounding box

#### Scenario: Vertical alignment bottom
- **WHEN** template specifies bottom vertical alignment
- **THEN** system aligns text to bottom of bounding box

#### Scenario: Text exceeds bounding box
- **WHEN** a line of text is wider than the bounding box's width
- **THEN** system wraps the line onto additional display lines at word boundaries instead of omitting it, growing the box's height to fit when `height` is not explicitly set

#### Scenario: Wrapped line preserves word styling
- **WHEN** a line containing bold, italic, or heading-styled segments is wrapped onto multiple display lines
- **THEN** each word retains the style of the segment it came from, on whichever display line it lands on

#### Scenario: Single word wider than bounding box
- **WHEN** a single word's rendered width alone exceeds the bounding box's width
- **THEN** system still draws the word rather than omitting it, even though it extends past the box's width

#### Scenario: Wrapped content exceeds a fixed height
- **WHEN** template specifies an explicit `height` and word-wrapped content still exceeds it
- **THEN** system clips the remaining display lines at the height boundary, same as today's per-line clipping behavior

#### Scenario: Theme text color
- **WHEN** theme specifies text_color property
- **THEN** system renders text in specified color

#### Scenario: Custom font family
- **WHEN** theme specifies font_family property
- **THEN** system uses specified font for rendering (if available on system)

#### Scenario: Font not available
- **WHEN** theme specifies font that is not available on system
- **THEN** system falls back to default sans-serif font

#### Scenario: Photo without text label
- **WHEN** photo has no associated text label
- **THEN** system renders photo normally without text

#### Scenario: Template without text position
- **WHEN** template does not define text position for photo
- **THEN** system renders photo without text (even if text label exists)
