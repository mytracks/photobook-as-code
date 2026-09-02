## Purpose

Generates a single self-contained HTML file that plays a photobook as an endless, autoplaying slideshow, reusing the same photo ordering, titles, captions, and theme as the other output formats, viewable directly from the filesystem or a web server.

## ADDED Requirements

### Requirement: Generate a self-contained HTML slideshow file
The system SHALL generate a single `.html` file, with all styling and scripting inlined in that one file, containing one slide per page item (photo or title) in the same order the other output formats use.

#### Scenario: Single file output
- **WHEN** `output.format` is `html`
- **THEN** system produces exactly one `.html` file, with no other generated files alongside it

#### Scenario: One slide per page item
- **WHEN** the photobook's merged photo/title sequence contains N items
- **THEN** the generated file contains N slides, in the same order as that sequence

#### Scenario: No external CSS/JS/font files
- **WHEN** the generated file is opened
- **THEN** it requires no other file except the referenced photos to render and run correctly

#### Scenario: Opens directly from the filesystem
- **WHEN** the generated file is opened directly from disk (not via a web server)
- **THEN** the slideshow plays correctly, including photo display and autoplay

#### Scenario: Pagination configuration has no effect
- **WHEN** `layout.photos_per_page` or `layout.pages` is set and `output.format` is `html`
- **THEN** system ignores it — every page item always occupies exactly one slide, regardless of those values

### Requirement: Slide sequence follows the configured photo and title order
The system SHALL order slides using the same chronological photo ordering and title-merging rules that apply to other output formats, without introducing a separate ordering mechanism.

#### Scenario: Photo ordering respected
- **WHEN** `layout.order` is `alphabetical` or `date`
- **THEN** slides appear in that same order

#### Scenario: Titles placed chronologically among photo slides
- **WHEN** the configuration defines `title` entries alongside photos
- **THEN** each title appears as its own slide at the same chronological position it would occupy as a page item in other output formats

### Requirement: Play as an endless, autoplaying slideshow
The system SHALL autoplay the generated slideshow on open, advancing slides at a configurable interval and looping back to the first slide after the last, with controls to pause and step manually.

#### Scenario: Autoplay starts on open
- **WHEN** the generated file is opened
- **THEN** the slideshow begins advancing automatically, without requiring the viewer to start it

#### Scenario: Configurable interval
- **WHEN** `output.interval_seconds` is set in configuration
- **THEN** each slide is displayed for that many seconds before advancing

#### Scenario: Default interval
- **WHEN** `output.interval_seconds` is not set
- **THEN** system uses a default interval of 5 seconds

#### Scenario: Loops endlessly
- **WHEN** the last slide's interval elapses
- **THEN** the slideshow advances back to the first slide and continues, indefinitely

#### Scenario: Pause and resume
- **WHEN** the viewer clicks the slideshow or presses the spacebar
- **THEN** autoplay toggles between paused and playing

#### Scenario: Manual navigation
- **WHEN** the viewer presses the left or right arrow key
- **THEN** the slideshow steps to the previous or next slide immediately, independent of the autoplay timer

### Requirement: Display titles and text-label captions
The system SHALL render title entries as their own full slide and text-label captions as an overlay on their associated photo's slide, styled using the active theme, with the same Markdown formatting semantics (bold, italic, headings) used by other output formats.

#### Scenario: Title slide
- **WHEN** a page item is a title entry
- **THEN** system renders it as its own slide with no photo, styled using the active theme's title styling, centered in the slide

#### Scenario: Photo with an associated caption
- **WHEN** a photo has an associated text label
- **THEN** system renders that photo's slide with the caption text overlaid on it, styled using the active theme's text styling

#### Scenario: Photo without a caption
- **WHEN** a photo has no associated text label
- **THEN** system renders that photo's slide with no caption overlay

#### Scenario: Markdown formatting preserved
- **WHEN** a caption or title contains Markdown bold, italic, or heading markers
- **THEN** system renders the corresponding text in bold, italic, or a larger heading size, matching the formatting semantics used for PDF/image output

### Requirement: Reference photos via relative paths, not copies
The system SHALL reference each photo from its slide using a relative path from the generated file's location, and SHALL NOT copy, move, embed, or resize the photo files.

#### Scenario: Photos not duplicated
- **WHEN** the html file is generated
- **THEN** no photo file is copied, embedded, or otherwise duplicated — the file only references the existing photo files by relative path

#### Scenario: Relative path within the first photo folder
- **WHEN** a photo is located in the first entry of `photo_folders`
- **THEN** its slide references it with a relative path from the generated file's own location

#### Scenario: Relative path across multiple photo folders
- **WHEN** `photo_folders` lists more than one directory and a photo is located in a folder other than the first
- **THEN** its slide references it with a relative path that correctly resolves from the generated file's location to that photo, regardless of which folder it's in

#### Scenario: Paths with spaces or non-ASCII characters
- **WHEN** a photo's file name or containing folder name contains spaces or non-ASCII characters
- **THEN** the referenced path resolves correctly when the file is opened, both from the filesystem and from a web server

### Requirement: Bound memory and bandwidth regardless of collection size
The system SHALL limit how many full-resolution photos are loaded by the browser at any one time, independent of how many photos the photobook contains or how long the slideshow has been running.

#### Scenario: Only nearby slides are loaded
- **WHEN** the slideshow is displaying a given slide
- **THEN** only that slide's photo and the next slide's photo (if it has one) are loaded; photos for slides further away are not requested

#### Scenario: Passed photos are released
- **WHEN** the slideshow advances past a slide
- **THEN** that slide's previously loaded photo is released rather than being kept loaded, so memory use does not grow as the slideshow continues to run

#### Scenario: Large collections don't delay playback start
- **WHEN** the photobook contains many photos or large photo files
- **THEN** the slideshow begins autoplaying without first loading every photo in the collection

### Requirement: HTML output location resolves to the first photo folder
The system SHALL always write the generated `.html` file into the first entry of `photo_folders`, ignoring any configured or command-line output directory, while still honoring a filename override.

#### Scenario: Directory override ignored
- **WHEN** `output.format` is `html` and `output.directory` is set, or `--output` specifies a directory
- **THEN** system writes the file into the first resolved `photo_folders` entry instead, and prints an informational note that the directory override was ignored

#### Scenario: Filename override still honored
- **WHEN** `output.format` is `html` and `output.filename` or `--output` specifies a filename (with or without a directory component)
- **THEN** system uses that filename for the generated file, written into the first resolved `photo_folders` entry, discarding only the directory portion of the override

#### Scenario: Default filename
- **WHEN** `output.format` is `html` and no filename override is given
- **THEN** system derives the filename from the configuration file's name, with a `.html` extension

#### Scenario: First photo folder not writable
- **WHEN** `output.format` is `html` and the first resolved `photo_folders` entry cannot be written to
- **THEN** system reports a clear error naming that path, rather than attempting to write elsewhere

### Requirement: Visual styling consistent with the active theme
The system SHALL style slide backgrounds, captions, and titles using the active theme's colors and fonts, embedding whatever is needed for that styling to render correctly without relying on fonts installed on the viewer's system.

#### Scenario: Theme colors and fonts applied
- **WHEN** a slide includes a caption or a title
- **THEN** its text color, font, and background styling match the active theme's corresponding settings

#### Scenario: Fonts render without installation
- **WHEN** the generated file is opened on a system that does not have the theme's font installed
- **THEN** the caption/title text still renders in that font

#### Scenario: Font fallback
- **WHEN** the active theme's configured font cannot be resolved at generation time
- **THEN** system falls back to a generic font for the slideshow's text, rather than failing generation
