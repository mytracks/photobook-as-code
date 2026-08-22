## ADDED Requirements

### Requirement: Render text labels on pages
The system SHALL render text labels on photobook pages according to template positioning and formatting specifications.

#### Scenario: Text label with position
- **WHEN** page has text label associated with photo and template defines text position
- **THEN** system renders text at specified position with proper formatting

#### Scenario: Multi-line text rendering
- **WHEN** text label contains multiple lines
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
- **WHEN** rendered text exceeds template-defined bounding box dimensions
- **THEN** system clips text at boundary

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
