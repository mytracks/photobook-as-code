"""
Configuration parsing and validation for photobook generation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union, Literal
import yaml


# Paper size definitions in pixels at 300 DPI
PAPER_SIZES = {
    "A4": (2480, 3508),  # 210mm x 297mm at 300 DPI
    "Letter": (2550, 3300),  # 8.5in x 11in at 300 DPI
}


@dataclass
class OutputConfig:
    """Output configuration settings."""
    size: str = "A4"
    format: Literal["pdf", "png", "jpg"] = "pdf"
    filename: Optional[str] = None
    directory: Optional[str] = None
    quality: int = 95  # For JPG output
    

@dataclass
class LayoutConfig:
    """Layout configuration settings."""
    photos_per_page: Optional[int] = None
    pages: Optional[int] = None
    order: Literal["alphabetical", "date"] = "alphabetical"
    

@dataclass
class PhotobookConfig:
    """Main photobook configuration."""
    photos: str
    output: OutputConfig
    layout: LayoutConfig
    theme: str = "clean"
    config_file_path: Optional[Path] = field(default=None, repr=False)
    
    def resolve_photos_path(self) -> Path:
        """Resolve photos path relative to config file location."""
        photos_path = Path(self.photos)
        
        if photos_path.is_absolute():
            return photos_path
            
        # If relative, resolve from config file directory
        if self.config_file_path:
            return (self.config_file_path.parent / photos_path).resolve()
        else:
            return photos_path.resolve()
    
    def get_paper_size_pixels(self) -> tuple[int, int]:
        """Get paper size in pixels at 300 DPI."""
        if self.output.size in PAPER_SIZES:
            return PAPER_SIZES[self.output.size]
        else:
            # For custom sizes, expect format like "2480x3508"
            try:
                width, height = self.output.size.split("x")
                return (int(width), int(height))
            except (ValueError, AttributeError):
                raise ConfigurationError(
                    f"Invalid paper size: {self.output.size}. "
                    f"Use A4, Letter, or custom format like '2480x3508'"
                )
    
    def get_output_filename(self, config_filename: str) -> str:
        """Get output filename, using default if not specified."""
        if self.output.filename:
            return self.output.filename
        
        # Generate from config filename
        config_stem = Path(config_filename).stem
        extension = self.output.format
        return f"{config_stem}.{extension}"
    
    def get_output_directory(self) -> Path:
        """Get output directory path."""
        if self.output.directory:
            return Path(self.output.directory)
        return Path.cwd()


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


def load_config(config_path: Union[str, Path]) -> PhotobookConfig:
    """
    Load and validate photobook configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Validated PhotobookConfig instance
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    
    # Load YAML
    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML syntax: {e}")
    
    if not isinstance(data, dict):
        raise ConfigurationError("Configuration must be a YAML dictionary")
    
    # Validate required fields
    if 'photos' not in data:
        raise ConfigurationError("Missing required field: 'photos'")
    
    if 'output' not in data or not isinstance(data['output'], dict):
        raise ConfigurationError("Missing or invalid 'output' section")
    
    if 'size' not in data['output']:
        raise ConfigurationError("Missing required field: 'output.size'")
    
    # Validate layout constraints
    layout_data = data.get('layout', {})
    if not isinstance(layout_data, dict):
        raise ConfigurationError("'layout' must be a dictionary")
    
    photos_per_page = layout_data.get('photos_per_page')
    pages = layout_data.get('pages')
    
    if photos_per_page is not None and pages is not None:
        raise ConfigurationError(
            "Cannot specify both 'photos_per_page' and 'pages'. Choose one."
        )
    
    if photos_per_page is None and pages is None:
        # Default to 4 photos per page
        layout_data['photos_per_page'] = 4
    
    # Build configuration objects
    try:
        output_config = OutputConfig(
            size=data['output'].get('size', 'A4'),
            format=data['output'].get('format', 'pdf'),
            filename=data['output'].get('filename'),
            directory=data['output'].get('directory'),
            quality=data['output'].get('quality', 95),
        )
        
        layout_config = LayoutConfig(
            photos_per_page=layout_data.get('photos_per_page'),
            pages=layout_data.get('pages'),
            order=layout_data.get('order', 'alphabetical'),
        )
        
        config = PhotobookConfig(
            photos=data['photos'],
            output=output_config,
            layout=layout_config,
            theme=data.get('theme', 'clean'),
            config_file_path=config_path,
        )
        
    except (TypeError, ValueError) as e:
        raise ConfigurationError(f"Invalid configuration values: {e}")
    
    # Validate output format
    if config.output.format not in ('pdf', 'png', 'jpg'):
        raise ConfigurationError(
            f"Invalid output format: {config.output.format}. "
            f"Must be 'pdf', 'png', or 'jpg'"
        )
    
    # Validate layout values
    if config.layout.photos_per_page is not None:
        if config.layout.photos_per_page < 1:
            raise ConfigurationError("photos_per_page must be at least 1")
    
    if config.layout.pages is not None:
        if config.layout.pages < 1:
            raise ConfigurationError("pages must be at least 1")
    
    # Validate order
    if config.layout.order not in ('alphabetical', 'date'):
        raise ConfigurationError(
            f"Invalid order: {config.layout.order}. "
            f"Must be 'alphabetical' or 'date'"
        )
    
    return config


def validate_photos_path(config: PhotobookConfig) -> None:
    """
    Validate that photos path exists and is accessible.
    
    Args:
        config: PhotobookConfig instance
        
    Raises:
        ConfigurationError: If path is invalid or inaccessible
    """
    photos_path = config.resolve_photos_path()
    
    if not photos_path.exists():
        raise ConfigurationError(
            f"Photos path does not exist: {photos_path}"
        )
    
    if not photos_path.is_dir():
        raise ConfigurationError(
            f"Photos path is not a directory: {photos_path}"
        )
