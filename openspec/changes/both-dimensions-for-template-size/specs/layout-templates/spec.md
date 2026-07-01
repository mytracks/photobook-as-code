## MODIFIED Requirements

### Requirement: Photo Sizing
The renderer SHALL size photos on the page based on the `size` object (`{width, height}`) in the selected layout template, applying both dimensions as maximum boundaries and proportionally fitting the photo within them.

#### Scenario: Photo sizing with dual boundaries
- **WHEN** a photo is placed with `size: {width: 0.8, height: 0.5}`
- **THEN** the photo SHALL be scaled proportionally to fit within 80% of the page width and 50% of the page height, using the smaller scaling factor.

## REMOVED Requirements

### Requirement: Old Photo Sizing (Scalar)
**Reason**: Replaced by dual-boundary `{width, height}` object to support better layout flexibility.
**Migration**: Update theme YAML files so that all `size` scalar values (e.g., `size: 0.8`) are converted to `size: {width: 0.8, height: 1.0}` (or equivalent pairs) matching the new schema requirements.