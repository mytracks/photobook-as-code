"""
Theme loading and management.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class BackgroundStyle:
    """Background styling properties."""
    color: str = "#FFFFFF"


@dataclass
class BorderStyle:
    """Border styling properties."""
    enabled: bool = True
    width: int = 2
    color: str = "#CCCCCC"
    shadow: bool = False


@dataclass
class SpacingStyle:
    """Spacing properties."""
    grid_gap: int = 10
    page_margin: int = 20


@dataclass
class PhotoPosition:
    """Coordinates for photo center point."""
    x: float
    y: float


@dataclass
class PhotoSpec:
    """Specification for a single photo in a layout template."""
    orientation: str
    position: PhotoPosition
    size: float


@dataclass
class LayoutTemplate:
    """Layout template definition."""
    count: int
    photos: list[PhotoSpec]


@dataclass
class Theme:
    """Complete theme definition."""
    name: str
    description: str
    background: BackgroundStyle
    borders: BorderStyle
    spacing: SpacingStyle
    layouts: list[LayoutTemplate]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Theme':
        """Create Theme from dictionary."""
        if 'layouts' not in data:
            raise ThemeError("Theme missing 'layouts' section")
        
        layouts_data = data.get('layouts', [])
        if not isinstance(layouts_data, list):
            raise ThemeError("Theme 'layouts' section must be a list of templates")
        
        parsed_layouts = []
        for idx, l_data in enumerate(layouts_data):
            if not isinstance(l_data, dict):
                raise ThemeError(f"Layout template at index {idx} must be a dictionary")
            if 'count' not in l_data or 'photos' not in l_data:
                raise ThemeError(f"Layout template at index {idx} is missing required fields: 'count' or 'photos'")
            
            count = l_data['count']
            if not isinstance(count, int) or count < 1:
                raise ThemeError(f"Layout template at index {idx} 'count' must be a positive integer")
            
            photos_data = l_data['photos']
            if not isinstance(photos_data, list):
                raise ThemeError(f"Layout template at index {idx} 'photos' must be a list")
            
            if len(photos_data) != count:
                raise ThemeError(f"Layout template at index {idx} 'photos' length must match 'count' ({count})")
            
            parsed_photos = []
            for p_idx, p_data in enumerate(photos_data):
                if not isinstance(p_data, dict):
                    raise ThemeError(f"Photo spec at index {p_idx} in layout {idx} must be a dictionary")
                
                # required fields: orientation, position, size
                for field in ('orientation', 'position', 'size'):
                    if field not in p_data:
                        raise ThemeError(f"Photo spec at index {p_idx} in layout {idx} is missing required field: '{field}'")
                
                orientation = p_data['orientation']
                if orientation not in ('landscape', 'portrait'):
                    raise ThemeError(f"Photo spec orientation must be 'landscape' or 'portrait', got '{orientation}'")
                
                pos_data = p_data['position']
                if not isinstance(pos_data, dict) or 'x' not in pos_data or 'y' not in pos_data:
                    raise ThemeError(f"Photo spec position must be a dictionary with 'x' and 'y' keys")
                
                try:
                    x = float(pos_data['x'])
                    y = float(pos_data['y'])
                except (ValueError, TypeError):
                    raise ThemeError(f"Photo spec position coordinates must be numeric")
                
                if not (0.0 <= x <= 1.0) or not (0.0 <= y <= 1.0):
                    raise ThemeError(f"Photo spec position coordinates must be in 0.0-1.0 range, got ({x}, {y})")
                
                try:
                    size = float(p_data['size'])
                except (ValueError, TypeError):
                    raise ThemeError(f"Photo spec size must be numeric")
                
                if not (0.0 <= size <= 1.0):
                    raise ThemeError(f"Photo spec size must be in 0.0-1.0 range, got {size}")
                
                parsed_photos.append(PhotoSpec(
                    orientation=orientation,
                    position=PhotoPosition(x=x, y=y),
                    size=size
                ))
            
            parsed_layouts.append(LayoutTemplate(
                count=count,
                photos=parsed_photos
            ))
            
        return cls(
            name=data.get('name', 'Unnamed'),
            description=data.get('description', ''),
            background=BackgroundStyle(**data.get('background', {})),
            borders=BorderStyle(**data.get('borders', {})),
            spacing=SpacingStyle(**data.get('spacing', {})),
            layouts=parsed_layouts,
        )


class ThemeError(Exception):
    """Raised when theme loading or validation fails."""
    pass


def get_builtin_themes_dir() -> Path:
    """Get path to built-in themes directory."""
    return Path(__file__).parent / "themes"


def list_builtin_themes() -> list[str]:
    """List available built-in theme names."""
    themes_dir = get_builtin_themes_dir()
    theme_files = themes_dir.glob("*.yaml")
    return sorted(f.stem for f in theme_files)


def load_theme(theme_name_or_path: str) -> Theme:
    """
    Load a theme by name or path.
    
    Args:
        theme_name_or_path: Built-in theme name or path to custom theme file
        
    Returns:
        Theme instance
        
    Raises:
        ThemeError: If theme cannot be loaded or is invalid
    """
    # Check if it's a path to a custom theme file
    theme_path = Path(theme_name_or_path)
    
    if theme_path.exists() and theme_path.is_file():
        # Load custom theme
        return load_theme_file(theme_path)
    
    # Try as built-in theme name
    builtin_path = get_builtin_themes_dir() / f"{theme_name_or_path}.yaml"
    
    if builtin_path.exists():
        return load_theme_file(builtin_path)
    
    # Theme not found
    available = list_builtin_themes()
    raise ThemeError(
        f"Theme not found: {theme_name_or_path}\n"
        f"Available built-in themes: {', '.join(available)}\n"
        f"Or provide path to custom theme file."
    )


def load_theme_file(theme_path: Path) -> Theme:
    """
    Load theme from YAML file.
    
    Args:
        theme_path: Path to theme YAML file
        
    Returns:
        Theme instance
        
    Raises:
        ThemeError: If file is invalid
    """
    try:
        with open(theme_path, 'r') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ThemeError(f"Invalid YAML in theme file: {e}")
    except IOError as e:
        raise ThemeError(f"Could not read theme file: {e}")
    
    if not isinstance(data, dict):
        raise ThemeError("Theme file must contain a YAML dictionary")
    
    # Validate required sections
    if 'background' not in data:
        raise ThemeError("Theme missing 'background' section")
    
    if 'borders' not in data:
        raise ThemeError("Theme missing 'borders' section")
    
    if 'spacing' not in data:
        raise ThemeError("Theme missing 'spacing' section")
        
    if 'layouts' not in data:
        raise ThemeError("Theme missing 'layouts' section")
    
    try:
        theme = Theme.from_dict(data)
        validate_theme(theme)
        return theme
    except (TypeError, ValueError) as e:
        raise ThemeError(f"Invalid theme data: {e}")


def validate_theme(theme: Theme) -> None:
    """
    Validate theme properties.
    
    Args:
        theme: Theme to validate
        
    Raises:
        ThemeError: If theme is invalid
    """
    # Validate color format (basic check for hex colors)
    if not theme.background.color.startswith('#'):
        raise ThemeError(f"Invalid background color: {theme.background.color}")
    
    if theme.borders.enabled and not theme.borders.color.startswith('#'):
        raise ThemeError(f"Invalid border color: {theme.borders.color}")
    
    # Validate numeric values
    if theme.borders.width < 0:
        raise ThemeError("Border width cannot be negative")
    
    if theme.spacing.grid_gap < 0:
        raise ThemeError("Grid gap cannot be negative")
    
    if theme.spacing.page_margin < 0:
        raise ThemeError("Page margin cannot be negative")


def get_default_theme() -> Theme:
    """Get the default theme (clean)."""
    return load_theme("clean")
