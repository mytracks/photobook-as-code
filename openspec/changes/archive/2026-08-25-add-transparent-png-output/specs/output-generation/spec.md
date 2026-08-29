## ADDED Requirements

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
