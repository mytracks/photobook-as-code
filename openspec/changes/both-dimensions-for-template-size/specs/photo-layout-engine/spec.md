## ADDED Requirements

### Requirement: Layout calculations with maximum bounds
The layout engine SHALL use both the width and height constraints provided by the template to determine the photo's final rendered size, guaranteeing it does not exceed either bound while maintaining the original aspect ratio.

#### Scenario: Bounding box scale calculation
- **WHEN** fitting a photo within the cell dimensions calculated from the template's max bounds
- **THEN** the layout engine selects the minimum scale factor between the width-ratio and height-ratio to prevent overflow in any dimension.