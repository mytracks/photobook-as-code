## Purpose

Theme system for visual styling of photobook pages. This capability manages theme definitions, background styling, borders, spacing, and provides built-in and custom theme support.

## Requirements

### Requirement: Define theme structure
The system SHALL support theme definitions that specify visual styling properties for photobook pages. Themes SHALL also define layout templates.

#### Scenario: Theme file format
- **WHEN** system loads a theme
- **THEN** theme file contains properties for backgrounds, borders, spacing, colors, and layouts.

#### Scenario: Theme inheritance
- **WHEN** theme omits specific properties
- **THEN** system uses default values for unspecified properties

### Requirement: Layout Specification
The theme SHALL include a `layouts` section that defines page layouts for different photo counts and orientations.

#### Scenario: Valid layouts section
- **WHEN** a theme YAML file has a `layouts` section with valid template definitions
- **THEN** the theme loader SHALL parse it successfully.

#### Scenario: Missing layouts section
- **WHEN** a theme YAML file is missing the `layouts` section
- **THEN** the system SHALL raise an error.

### Requirement: Apply background styling
The system SHALL apply background styling to pages according to theme specifications.

#### Scenario: Solid color background
- **WHEN** theme specifies a solid background color
- **THEN** system fills page background with specified color

#### Scenario: White background default
- **WHEN** theme does not specify background
- **THEN** system uses white as default background color

### Requirement: Apply border styling to photos
The system SHALL apply border styling to photo frames according to theme specifications.

#### Scenario: Border width and color
- **WHEN** theme specifies border properties
- **THEN** system draws borders around photos with specified width and color

#### Scenario: No borders
- **WHEN** theme specifies no borders
- **THEN** system displays photos without frames

#### Scenario: Drop shadow effect
- **WHEN** theme includes shadow properties
- **THEN** system applies drop shadow to photo frames

### Requirement: Apply spacing rules
The system SHALL apply spacing between photo grid cells according to theme specifications.

#### Scenario: Uniform spacing
- **WHEN** theme specifies grid spacing value
- **THEN** system applies equal spacing between all grid cells

#### Scenario: Tight layout
- **WHEN** theme specifies minimal spacing
- **THEN** system places photos with minimal gaps

#### Scenario: Airy layout
- **WHEN** theme specifies generous spacing
- **THEN** system places photos with substantial gaps for breathing room

### Requirement: Provide default themes
The system SHALL include multiple default themes covering common aesthetic preferences.

#### Scenario: Clean theme
- **WHEN** user selects "clean" theme
- **THEN** system applies minimalist style with white background, thin borders, moderate spacing

#### Scenario: Classic theme
- **WHEN** user selects "classic" theme
- **THEN** system applies traditional style with cream background, visible borders, standard spacing

#### Scenario: Modern theme
- **WHEN** user selects "modern" theme
- **THEN** system applies contemporary style with no borders, tight spacing, high contrast

### Requirement: Support custom themes
The system SHALL allow users to define and use custom theme files.

#### Scenario: Custom theme file location
- **WHEN** user specifies path to custom theme file
- **THEN** system loads theme from specified location

#### Scenario: Theme validation
- **WHEN** custom theme file has invalid structure
- **THEN** system reports error indicating which properties are invalid

### Requirement: Maintain theme consistency across pages
The system SHALL apply theme styling consistently across all pages in a photobook.

#### Scenario: Multi-page consistency
- **WHEN** photobook contains multiple pages
- **THEN** all pages use identical theme styling properties

### Requirement: Define text positioning in layout templates
The system SHALL support optional text positioning specifications for each photo slot in layout templates. `x` and `width` are percentages of the associated photo's rendered width: `x` is interpolated by the slack between the photo's width and the label's rendered width (0 means the label's left edge aligns with the photo's left edge, 100 means the label's right edge aligns with the photo's right edge), and `width` sizes the label as a fraction of the photo's width. `y` is a percentage of the associated photo's rendered height: 0 means the text label's top edge aligns with the photo's top edge, and 100 means the text label's bottom edge aligns with the photo's bottom edge, interpolated by the slack between the photo's height and the label's rendered height. If the label's rendered height exceeds the photo's height, the label top-aligns with the photo regardless of `y` (slack floored at 0). An optional `dock` property (`left` or `right`) overrides the horizontal anchor: when set, the label's corresponding edge is pinned to the literal page border instead of interpolating within the photo, ignoring `x` and any page margin.

#### Scenario: Layout template with text positions
- **WHEN** theme layout template includes text positioning for photo slots
- **THEN** system parses text position properties successfully

#### Scenario: Text position with coordinates
- **WHEN** text position specifies x, y, width, height as percentages
- **THEN** system stores position as bounding box for text rendering, resolving both `x` and `y` against the associated photo's pixel bounds rather than the page's

#### Scenario: Text position with alignment
- **WHEN** text position specifies horizontal alignment (left, center, right)
- **THEN** system uses alignment for text rendering within bounding box

#### Scenario: x at 0 percent aligns label left with photo left
- **WHEN** text position specifies `x: 0`
- **THEN** system renders the text label's left edge at the same horizontal pixel position as the associated photo's left edge

#### Scenario: x at 100 percent aligns label right with photo right
- **WHEN** text position specifies `x: 100`
- **THEN** system renders the text label's right edge at the same horizontal pixel position as the associated photo's right edge

#### Scenario: x between 0 and 100 interpolates within the photo
- **WHEN** text position specifies an `x` value between 0 and 100
- **THEN** system positions the label's left edge at `photo_left + (x / 100) * (photo_width - label_width)`; `x: 50` centers the label within the photo's width

#### Scenario: y at 0 percent aligns label top with photo top
- **WHEN** text position specifies `y: 0`
- **THEN** system renders the text label's top edge at the same vertical pixel position as the associated photo's top edge

#### Scenario: y at 100 percent aligns label bottom with photo bottom
- **WHEN** text position specifies `y: 100`
- **THEN** system renders the text label's bottom edge at the same vertical pixel position as the associated photo's bottom edge

#### Scenario: Text position with vertical alignment
- **WHEN** text position specifies a `y` value between 0 and 100
- **THEN** system positions the label's top edge at `photo_top + (y / 100) * (photo_height - label_height)`; `y: 50` centers the label within the photo's height (there is no separate `valign` property — vertical alignment is expressed entirely through `y`)

#### Scenario: Label taller than photo clamps to top alignment
- **WHEN** the text label's rendered height exceeds the associated photo's height
- **THEN** system aligns the label's top edge with the photo's top edge regardless of the configured `y` value

#### Scenario: Dock to left page border
- **WHEN** text position specifies `dock: left`
- **THEN** system renders the text label's left edge at the page's left border (pixel 0), ignoring `x` and any page margin, and sizes the label's width from the associated photo's width as usual

#### Scenario: Dock to right page border
- **WHEN** text position specifies `dock: right`
- **THEN** system renders the text label's right edge at the page's right border, ignoring `x` and any page margin, and sizes the label's width from the associated photo's width as usual

#### Scenario: No dock specified
- **WHEN** text position does not specify `dock`
- **THEN** system resolves `x` relative to the associated photo as usual (no change in behavior)

#### Scenario: Invalid dock value
- **WHEN** text position specifies a `dock` value other than `left` or `right`
- **THEN** system reports validation error indicating invalid dock value

#### Scenario: Photo slot without text position
- **WHEN** photo slot in template does not include text position
- **THEN** system renders photo without text (no error)

#### Scenario: Template without any text positions
- **WHEN** layout template has no text position specifications
- **THEN** system renders all photos without text (backward compatible)

#### Scenario: Invalid text position coordinates
- **WHEN** text position coordinates are not numbers or are outside 0-100 range
- **THEN** system reports validation error indicating invalid coordinates

#### Scenario: Invalid text alignment value
- **WHEN** text alignment is not one of allowed values (left/center/right)
- **THEN** system reports validation error indicating invalid alignment

### Requirement: Support text styling properties in themes
The system SHALL support optional text styling properties at the theme level for text rendering.

#### Scenario: Theme with base font size
- **WHEN** theme specifies base_font_size property
- **THEN** system uses specified size for rendering text

#### Scenario: Theme with font family
- **WHEN** theme specifies font_family property
- **THEN** system uses specified font for rendering text

#### Scenario: Theme with text color
- **WHEN** theme specifies text_color property
- **THEN** system uses specified color for rendering text

#### Scenario: Theme without text styling
- **WHEN** theme does not specify text styling properties
- **THEN** system uses default text styling (black, 12pt, sans-serif)

#### Scenario: Invalid font size
- **WHEN** theme specifies non-numeric or negative font size
- **THEN** system reports validation error indicating invalid font size

#### Scenario: Invalid color format
- **WHEN** theme specifies text_color that is not a valid color (hex, rgb, or name)
- **THEN** system reports validation error indicating invalid color

#### Scenario: Theme with text line spacing
- **WHEN** theme specifies `text.line_spacing` (pixels)
- **THEN** system uses the specified gap between consecutive rendered lines of caption (`text`) content

#### Scenario: Theme without text line spacing
- **WHEN** theme does not specify `text.line_spacing`
- **THEN** system uses a default gap of 10 pixels between consecutive rendered lines of caption content

### Requirement: Support title styling properties in themes
The system SHALL support an optional theme-level `title` style block for title-slot rendering, independent from the `text` style block used for photo captions.

#### Scenario: Theme with title base font size
- **WHEN** theme specifies `title.base_font_size`
- **THEN** system uses the specified size for rendering title-slot text

#### Scenario: Theme with title font family
- **WHEN** theme specifies `title.font_family`
- **THEN** system uses the specified font for rendering title-slot text

#### Scenario: Theme with title text color
- **WHEN** theme specifies `title.text_color`
- **THEN** system uses the specified color for rendering title-slot text

#### Scenario: Theme with title alignment
- **WHEN** theme specifies `title.align` as one of `left`, `center`, or `right`
- **THEN** system aligns title-slot text accordingly within its slot

#### Scenario: Theme without title styling
- **WHEN** theme does not specify a `title` style block
- **THEN** system uses default title styling (centered alignment, larger base font size than the default caption style)

#### Scenario: Invalid title alignment
- **WHEN** theme specifies a `title.align` value other than `left`, `center`, or `right`
- **THEN** system reports validation error indicating invalid alignment

#### Scenario: Invalid title font size
- **WHEN** theme specifies a non-numeric or negative `title.base_font_size`
- **THEN** system reports validation error indicating invalid font size

#### Scenario: Title styling independent from text styling
- **WHEN** a theme defines both `text` and `title` style blocks with different font sizes or colors
- **THEN** system renders photo captions using the `text` block and title slots using the `title` block, without either affecting the other

#### Scenario: Theme with title line spacing
- **WHEN** theme specifies `title.line_spacing` (pixels)
- **THEN** system uses the specified gap between consecutive rendered lines of title-slot content, independently of `text.line_spacing`

#### Scenario: Theme without title line spacing
- **WHEN** theme does not specify `title.line_spacing`
- **THEN** system uses a default gap of 10 pixels between consecutive rendered lines of title-slot content

### Requirement: Support text background overlay for readability
The system SHALL support optional text background overlay properties to ensure text remains readable when rendered over photos.

#### Scenario: Theme with text background
- **WHEN** theme specifies text_background_enabled as true
- **THEN** system renders semi-transparent background behind text

#### Scenario: Theme with text background color
- **WHEN** theme specifies text_background_color property
- **THEN** system uses specified color for text background overlay

#### Scenario: Theme with text background opacity
- **WHEN** theme specifies text_background_opacity (0-100)
- **THEN** system uses specified opacity for text background (0=transparent, 100=opaque)

#### Scenario: Theme with text padding
- **WHEN** theme specifies text_padding property
- **THEN** system adds specified padding around text within background overlay

#### Scenario: Theme without text background
- **WHEN** theme does not enable text_background or uses default
- **THEN** system renders text with semi-transparent background (default enabled for readability)

#### Scenario: Text background covers entire bounding box
- **WHEN** text is rendered with background enabled
- **THEN** background overlay is drawn first, then text is drawn on top

#### Scenario: Text labels rendered on top of all photos
- **WHEN** page contains multiple photos with text labels
- **THEN** system renders all photos first, then all text labels on top

#### Scenario: Text not obscured by other photos
- **WHEN** text label is positioned over first photo and second photo is rendered
- **THEN** text from first photo remains visible (not covered by second photo)

#### Scenario: Invalid text background opacity
- **WHEN** theme specifies text_background_opacity outside 0-100 range
- **THEN** system reports validation error indicating invalid opacity value
