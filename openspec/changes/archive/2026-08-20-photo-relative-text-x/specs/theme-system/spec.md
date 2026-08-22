## MODIFIED Requirements

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
