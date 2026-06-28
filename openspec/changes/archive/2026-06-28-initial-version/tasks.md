## 1. Project Setup

- [x] 1.1 Create Python package structure with src/photobook_as_code/ directory
- [x] 1.2 Create setup.py or pyproject.toml with project metadata and dependencies
- [x] 1.3 Add requirements.txt with Pillow, ReportLab, Click, and PyYAML
- [x] 1.4 Create README.md with project description and basic usage
- [x] 1.5 Create example configuration YAML file for documentation
- [x] 1.6 Set up basic .gitignore for Python projects

## 2. Configuration Module (config.py)

- [x] 2.1 Create configuration schema classes/dataclasses for type safety
- [x] 2.2 Implement YAML file loading with PyYAML
- [x] 2.3 Add validation for required fields (photos path, output size)
- [x] 2.4 Add validation for mutually exclusive fields (photos_per_page vs pages)
- [x] 2.5 Implement path resolution for relative photo paths
- [x] 2.6 Add error messages for missing or invalid configuration
- [x] 2.7 Implement paper size lookup (A4, Letter) and custom dimensions support
- [x] 2.8 Add configuration defaults (theme, output format, etc.)

## 3. Photo Collection Module (photos.py)

- [x] 3.1 Implement photo file discovery in specified directory
- [x] 3.2 Add file extension filtering (jpg, jpeg, png) - case insensitive
- [x] 3.3 Implement alphabetical filename ordering
- [x] 3.4 Add EXIF metadata reading using Pillow
- [x] 3.5 Implement date-based ordering from EXIF data
- [x] 3.6 Add fallback to file modification time when EXIF missing
- [x] 3.7 Validate that photo directory exists and contains photos
- [x] 3.8 Add warning for photos with insufficient resolution

## 4. Theme Module (themes.py)

- [x] 4.1 Create themes/ directory with built-in theme YAML files
- [x] 4.2 Create "clean" theme (white background, thin borders, moderate spacing)
- [x] 4.3 Create "classic" theme (cream background, visible borders, standard spacing)
- [x] 4.4 Create "modern" theme (no borders, tight spacing, high contrast)
- [x] 4.5 Implement theme YAML loading and parsing
- [x] 4.6 Add validation for theme structure and properties
- [x] 4.7 Implement default theme fallback
- [x] 4.8 Add support for custom theme file paths
- [x] 4.9 Create theme property classes (background, borders, spacing)

## 5. Layout Calculator Module (layout.py)

- [x] 5.1 Implement grid dimension calculation from photos-per-page
- [x] 5.2 Implement photos-per-page calculation from total pages
- [x] 5.3 Add logic for uneven photo distribution across pages
- [x] 5.4 Calculate cell dimensions based on page size and grid
- [x] 5.5 Apply page margins from theme to usable area
- [x] 5.6 Create data structures for page layout specifications
- [x] 5.7 Implement aspect ratio preservation logic for photos in cells

## 6. Page Renderer Module (renderer.py)

- [x] 6.1 Create blank page images with correct dimensions and DPI
- [x] 6.2 Implement background color/pattern application
- [x] 6.3 Load and resize photos to fit grid cells
- [x] 6.4 Implement letterbox/pillarbox for aspect ratio preservation
- [x] 6.5 Apply photo positioning within grid cells
- [x] 6.6 Implement border drawing around photos
- [x] 6.7 Add drop shadow support for photo frames
- [x] 6.8 Apply grid spacing between cells
- [x] 6.9 Handle pages with fewer photos than grid capacity (empty cells)

## 7. Output Generation Module (output.py)

- [x] 7.1 Implement PDF output using ReportLab
- [x] 7.2 Set correct PDF page dimensions from configuration
- [x] 7.3 Embed page images into PDF with 300 DPI
- [x] 7.4 Implement PNG output for individual pages
- [x] 7.5 Implement JPG output with configurable quality
- [x] 7.6 Add sequential filename generation for multi-page images
- [x] 7.7 Implement custom output filename from configuration
- [x] 7.8 Add default filename generation from config filename
- [x] 7.9 Implement output directory creation if not exists
- [x] 7.10 Add file overwrite protection with confirmation or timestamp

## 8. CLI Interface (cli.py)

- [x] 8.1 Create Click command for main photobook generation
- [x] 8.2 Add --config/-c argument for configuration file path
- [x] 8.3 Add --output/-o argument for overriding output location
- [x] 8.4 Implement progress reporting between pipeline stages
- [x] 8.5 Add --verbose flag for detailed logging
- [x] 8.6 Implement error handling and user-friendly error messages
- [x] 8.7 Add success message with output file location
- [x] 8.8 Create entry point in setup.py for 'photobook' command

## 9. Pipeline Integration (main processing flow)

- [x] 9.1 Implement main pipeline orchestration function
- [x] 9.2 Connect configuration parser to pipeline
- [x] 9.3 Connect photo collector to layout calculator
- [x] 9.4 Connect theme loader to renderer
- [x] 9.5 Connect layout calculator to page renderer
- [x] 9.6 Connect page renderer to output generator
- [x] 9.7 Add progress tracking between stages
- [x] 9.8 Implement error propagation and cleanup

## 10. Testing and Validation

- [x] 10.1 Create test fixtures (sample photos and configs)
- [x] 10.2 Test configuration parsing with valid and invalid YAML
- [x] 10.3 Test photo discovery and ordering
- [x] 10.4 Test layout calculation with various photo counts
- [x] 10.5 Test theme loading and application
- [x] 10.6 Test PDF generation with multi-page output
- [x] 10.7 Test image output generation
- [x] 10.8 Test end-to-end with complete configuration

## 11. Documentation

- [x] 11.1 Write comprehensive README with installation instructions
- [x] 11.2 Document configuration file format and all options
- [x] 11.3 Document built-in themes and customization
- [x] 11.4 Add example configurations for common use cases
- [x] 11.5 Document print quality recommendations
- [x] 11.6 Add troubleshooting section for common issues
- [x] 11.7 Create CONTRIBUTING.md if planning community contributions
