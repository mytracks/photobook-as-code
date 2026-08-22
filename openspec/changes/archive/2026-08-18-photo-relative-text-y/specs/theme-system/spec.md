## MODIFIED Requirements

### Requirement: Define text positioning in layout templates
The system SHALL support optional text positioning specifications for each photo slot in layout templates. `x` and `width` are percentages of the page's usable width. `y` is a percentage of the associated photo's rendered height: 0 means the text label's top edge aligns with the photo's top edge, and 100 means the text label's bottom edge aligns with the photo's bottom edge, interpolated by the slack between the photo's height and the label's rendered height. If the label's rendered height exceeds the photo's height, the label top-aligns with the photo regardless of `y` (slack floored at 0).

#### Scenario: Layout template with text positions
- **WHEN** theme layout template includes text positioning for photo slots
- **THEN** system parses text position properties successfully

#### Scenario: Text position with coordinates
- **WHEN** text position specifies x, y, width, height as percentages
- **THEN** system stores position as bounding box for text rendering, resolving `y` against the associated photo's pixel bounds rather than the page's

#### Scenario: Text position with alignment
- **WHEN** text position specifies horizontal alignment (left, center, right)
- **THEN** system uses alignment for text rendering within bounding box

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
