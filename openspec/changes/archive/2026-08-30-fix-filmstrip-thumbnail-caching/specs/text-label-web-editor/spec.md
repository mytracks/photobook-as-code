## MODIFIED Requirements

### Requirement: Serve a small thumbnail image for filmstrip cells
The system SHALL serve each photo's filmstrip thumbnail at a substantially smaller size than the item's main display image, suitable for a strip that may contain hundreds of cells on the same page, without degrading the responsiveness of loading the currently displayed photo. The URL identifying a photo's thumbnail SHALL depend only on that photo's own identity and content, not on its position in the book's merged item order, so that a long-lived browser cache of that URL remains correct regardless of edits that change item positions.

#### Scenario: Thumbnail is smaller than the main image
- **WHEN** the system serves a photo's filmstrip thumbnail
- **THEN** the served image is scaled to a small display size and does not require decoding or transferring the same amount of data as the item's main display image

#### Scenario: Title added before a photo whose thumbnail was already cached
- **WHEN** the user adds a title before a photo whose thumbnail URL a browser has already cached, causing that photo to move to a later position in the merged item order
- **THEN** the photo's thumbnail URL is unchanged by the move, and the browser's cached thumbnail continues to correctly depict that same photo

#### Scenario: Title deleted before photos whose thumbnails were already cached
- **WHEN** the user deletes a title that precedes photos whose thumbnail URLs a browser has already cached, causing those photos to move to earlier positions in the merged item order
- **THEN** each photo's thumbnail URL is unchanged by the move, and the browser's cached thumbnails continue to correctly depict those same photos

#### Scenario: A photo is added to the photo folder before a restart
- **WHEN** a photo is added to the configured photo folder and the editor is restarted, causing existing photos to shift position in the configured order
- **THEN** each existing photo's thumbnail URL is unchanged by the shift, and any thumbnails already cached by the browser continue to correctly depict those same photos

#### Scenario: A photo file is replaced in place under the same filename
- **WHEN** a photo file on disk is replaced with different content under the same filename, and the editor is restarted
- **THEN** the photo's thumbnail URL differs from the one previously served for that filename, so a browser does not reuse a cached thumbnail rendered from the old content
