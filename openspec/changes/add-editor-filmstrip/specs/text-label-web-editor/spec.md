## MODIFIED Requirements

### Requirement: Navigate between items
The system SHALL let the user move forward and backward through the items of the configured photobook - photos and titles, interleaved in the same merged order the photobook renderer would use for that configuration - one item at a time. The system SHALL provide always-visible previous/next controls in the page header and a keyboard shortcut for this navigation, both usable regardless of where the page's focus currently is and regardless of whether the current or adjacent item is a photo or a title. The keyboard shortcut SHALL NOT intercept key combinations that carry native text-editing meaning inside a text field.

#### Scenario: Sequential navigation
- **WHEN** the user requests the next or previous item
- **THEN** the system displays the adjacent item (photo or title) in the configured order

#### Scenario: First and last photo boundaries
- **WHEN** the user is viewing the first or last item in the order
- **THEN** the system does not allow navigating before the first or after the last item

#### Scenario: Order matches final photobook order
- **WHEN** the configuration specifies `layout.order: date` or `layout.order: alphabetical`, with or without `title` entries in `text_labels`
- **THEN** the item sequence shown in the editor matches the order photos and titles would be laid out in the generated photobook

#### Scenario: Titles appear in their merged position
- **WHEN** the configuration's `text_labels` contains one or more `title` entries
- **THEN** each title appears in the editor's sequence immediately before the first photo whose timestamp is at or after the title's own timestamp, matching the renderer's placement, and is appended at the end of the sequence if no such photo exists

#### Scenario: Header navigation controls
- **WHEN** the user views any item
- **THEN** the system displays previous and next navigation controls in the page header, visible without requiring the pointer to hover over the item's display area

#### Scenario: Keyboard shortcut navigates regardless of focus
- **WHEN** the user presses Cmd+Enter or Ctrl+Enter (either modifier accepted on any platform), including while a caption or title text field has focus
- **THEN** the system navigates to the next item, saving any pending text edit first as it does for other navigation actions

#### Scenario: Keyboard shortcut navigates backward with Shift
- **WHEN** the user presses Cmd+Shift+Enter or Ctrl+Shift+Enter, including while a caption or title text field has focus
- **THEN** the system navigates to the previous item, saving any pending text edit first as it does for other navigation actions

#### Scenario: Native text-editing shortcuts are not intercepted
- **WHEN** the user presses Cmd+Left Arrow, Cmd+Right Arrow, Ctrl+Left Arrow, or Ctrl+Right Arrow (with or without Shift held) while a caption or title text field has focus
- **THEN** the system does not navigate to a different item, and the browser's native text-editing behavior for that combination is left to run unmodified

#### Scenario: Smooth transition on navigation
- **WHEN** the user navigates to a different item by any means (previous/next controls, jump-to-number, keyboard shortcut, a filmstrip item, or after adding/deleting a title)
- **THEN** the system transitions to the new item with a smooth visual transition rather than an abrupt, unstyled page reload

## ADDED Requirements

### Requirement: Display a filmstrip of all items for visual navigation
The system SHALL display a persistent, always-visible strip at the bottom of the per-item editor showing every item in the book's merged order (photos and titles), in a fixed-height, horizontally scrollable container, and SHALL let the user click any item in the strip to navigate to it.

#### Scenario: Filmstrip is always visible
- **WHEN** the user views any item in the per-item editor
- **THEN** the system displays the filmstrip below the caption field, with a fixed height that does not change as the user navigates

#### Scenario: Filmstrip contains every item
- **WHEN** the user views the filmstrip
- **THEN** it contains one cell for every item in the book's merged order, matching the same order used for previous/next navigation

#### Scenario: Clicking a filmstrip item navigates to it
- **WHEN** the user clicks a cell in the filmstrip
- **THEN** the system saves any pending text edit first, then navigates to that item, the same way other navigation actions do

#### Scenario: Filmstrip scrolls horizontally
- **WHEN** the book has more items than fit within the filmstrip's width
- **THEN** the user can scroll the filmstrip horizontally to reveal items outside the initially visible range

### Requirement: Filmstrip photo cells show only a thumbnail
The system SHALL render each photo item's filmstrip cell as a small thumbnail image of that photo, with no caption text or date displayed on the cell, other than the small caption-presence overlay described below.

#### Scenario: Photo cell shows a thumbnail
- **WHEN** a photo item appears in the filmstrip
- **THEN** its cell displays a thumbnail image of that photo and no caption or date text

### Requirement: Filmstrip photo cells indicate whether they have a caption
The system SHALL display a small "T" overlay badge on a photo's filmstrip cell when that photo has non-empty caption text, and SHALL NOT display it when the photo's caption is empty or absent. The badge SHALL NOT display the caption's own text content.

#### Scenario: Photo has a non-empty caption
- **WHEN** a photo item with non-empty caption text appears in the filmstrip
- **THEN** its cell displays a small "T" overlay badge over the thumbnail

#### Scenario: Photo has no caption or an empty caption
- **WHEN** a photo item with no associated caption, or an associated caption whose text is empty, appears in the filmstrip
- **THEN** its cell does not display the overlay badge

#### Scenario: Badge does not leak caption content
- **WHEN** a photo's filmstrip cell displays the caption-presence badge
- **THEN** the badge shows only the "T" glyph, never the caption's own text

### Requirement: Filmstrip title cells show a placeholder, not the title's text
The system SHALL render each title item's filmstrip cell as a bounded placeholder cell containing only a "T" glyph, visually distinct from a photo cell, without displaying the title's own text content.

#### Scenario: Title cell shows a placeholder
- **WHEN** a title item appears in the filmstrip
- **THEN** its cell displays a bounded placeholder containing the letter "T" and does not display the title's text content

### Requirement: Filmstrip indicates day boundaries
The system SHALL display a compact, date-labeled divider between two consecutive filmstrip cells whenever the later item's date differs from the earlier item's date, determined the same way as the per-item editor's own new-day indicator (considering photos and titles together as one sequence).

#### Scenario: Date changes between consecutive items
- **WHEN** two consecutive items in the filmstrip have different dates
- **THEN** the system displays a divider with a compact date label between their cells

#### Scenario: Date matches between consecutive items
- **WHEN** two consecutive items in the filmstrip have the same date
- **THEN** the system does not display a divider between their cells

### Requirement: Filmstrip highlights and tracks the current item
The system SHALL visually highlight the filmstrip cell for the item currently displayed in the per-item editor, and SHALL keep that highlight correct across every navigation trigger - filmstrip clicks, previous/next controls, keyboard shortcuts, jump-to-number, and adding or deleting a title.

#### Scenario: Current item is highlighted
- **WHEN** the user views any item
- **THEN** the filmstrip cell corresponding to that item is visually highlighted, distinguishing it from every other cell

#### Scenario: Highlight follows non-filmstrip navigation
- **WHEN** the user navigates using the header's previous/next controls, a keyboard shortcut, jump-to-number, or by adding or deleting a title
- **THEN** the filmstrip's highlighted cell updates to match the newly displayed item

#### Scenario: Current cell scrolls into view
- **WHEN** the editor loads a new item, by any navigation trigger
- **THEN** the system scrolls the filmstrip so the current item's cell is visible without requiring the user to scroll manually

### Requirement: Serve a small thumbnail image for filmstrip cells
The system SHALL serve each photo's filmstrip thumbnail at a substantially smaller size than the item's main display image, suitable for a strip that may contain hundreds of cells on the same page, without degrading the responsiveness of loading the currently displayed photo.

#### Scenario: Thumbnail is smaller than the main image
- **WHEN** the system serves a photo's filmstrip thumbnail
- **THEN** the served image is scaled to a small display size and does not require decoding or transferring the same amount of data as the item's main display image

### Requirement: Filmstrip cells are accessible to assistive technology
The system SHALL give each filmstrip cell an accessible name that identifies its item without relying on the visual thumbnail or "T" glyph alone.

#### Scenario: Photo cell accessible name
- **WHEN** a screen reader user reaches a photo's filmstrip cell
- **THEN** it announces an accessible name identifying it as that photo (for example, its filename or position), not merely an unlabeled image

#### Scenario: Title cell accessible name
- **WHEN** a screen reader user reaches a title's filmstrip cell
- **THEN** it announces an accessible name identifying it as a title item, not merely the letter "T"
