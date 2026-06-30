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
class Theme:
    """Complete theme definition."""
    name: str
    description: str
    background: BackgroundStyle
    borders: BorderStyle
    spacing: SpacingStyle
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Theme':
        """Create Theme from dictionary."""
        return cls(
            name=data.get('name', 'Unnamed'),
            description=data.get('description', ''),
            background=BackgroundStyle(**data.get('background', {})),
            borders=BorderStyle(**data.get('borders', {})),
            spacing=SpacingStyle(**data.get('spacing', {})),
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
