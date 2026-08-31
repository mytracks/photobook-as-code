## MODIFIED Requirements

### Requirement: Present title slots as landscape orientation for layout matching
A title slot SHALL report `landscape` as its orientation when participating in layout template matching, so it can occupy any template slot a theme already defines for a landscape photo at that item count, without requiring dedicated title layout templates.

#### Scenario: Title matched into an existing landscape-capable template
- **WHEN** a page's items are, in order, one portrait photo and one title
- **THEN** the system selects a layout template whose orientations are `[portrait, landscape]`, exactly as it would for one portrait and one landscape photo

#### Scenario: No dedicated title template required
- **WHEN** a theme defines no layout template referencing a `title`-specific orientation
- **THEN** the system still renders title slots successfully, provided the theme has a template matching the page's item count with a landscape-shaped slot at the title's position
