"""
Theme loading and management.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict
import yaml

@dataclass
class LayoutPosition:
    """Position coordinates for a photo (center point, 0.0-1.0)."""
    x: float
    y: float

@dataclass
class LayoutPhotoSize:
    """Maximum size bounds for a photo (0.0-1.0 percentage of page dimensions)."""
    width: float
    height: float

@dataclass
class TextPosition:
    """Text position and alignment specification."""
    x: float  # percentage 0-100 of the associated photo's width; ignored when dock is set
    y: float  # percentage 0-100 of the associated photo's height
    width: float  # percentage 0-100 of the associated photo's width
    height: Optional[float] = None  # percentage 0-100, calculated automatically if not specified
    align: str = "left"  # left, center, right
    dock: Optional[str] = None  # left, right: pin to the page's literal border instead of the photo

@dataclass
class LayoutPhoto:
    """Specification for a single photo in a layout template."""
    orientation: str  # 'portrait' or 'landscape'
    position: LayoutPosition
    size: LayoutPhotoSize  # Maximum bounds for rendering
    text: Optional[TextPosition] = None  # Optional text positioning

@dataclass
class LayoutTemplate:
    """Layout template definition."""
    count: int
    photos: List[LayoutPhoto]

    @property
    def orientations(self) -> List[str]:
        return [p.orientation for p in self.photos]

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
    page_margin: int = 20
    photo_margin: int = 0


@dataclass
class TextStyle:
    """Text styling properties for text labels."""
    base_font_size: int = 14
    font_family: str = "DejaVuSans"
    text_color: str = "#000000"
    text_background_enabled: bool = True
    text_background_color: str = "#FFFFFF"
    text_background_opacity: int = 85  # 0-100, where 100 is fully opaque
    text_padding: int = 8  # Padding in pixels around text


@dataclass
class TitleStyle:
    """Title styling properties for title slots (independent from caption `text` styling)."""
    base_font_size: int = 28
    font_family: str = "DejaVuSans"
    text_color: str = "#000000"
    text_background_enabled: bool = True
    text_background_color: str = "#FFFFFF"
    text_background_opacity: int = 85  # 0-100, where 100 is fully opaque
    text_padding: int = 8  # Padding in pixels around text
    align: str = "center"  # left, center, right


@dataclass
class Theme:
    """Complete theme definition."""
    name: str
    description: str
    background: BackgroundStyle
    borders: BorderStyle
    spacing: SpacingStyle
    text: TextStyle = field(default_factory=TextStyle)
    title: TitleStyle = field(default_factory=TitleStyle)
    layouts: List[LayoutTemplate] = field(default_factory=list)

    @property
    def max_layout_count(self) -> int:
        """Largest item count any layout template in this theme defines - the
        most photos/titles that can ever be placed on a single page."""
        return max((t.count for t in self.layouts), default=0)

    @classmethod
    def from_dict(cls, data: dict) -> 'Theme':
        """Create Theme from dictionary."""
        layouts_data = data.get('layouts', [])
        layouts = []
        for layout_dict in layouts_data:
            photos = []
            for photo_dict in layout_dict.get('photos', []):
                pos = photo_dict.get('position', {})
                size_data = photo_dict.get('size')
                if not isinstance(size_data, dict) or 'width' not in size_data or 'height' not in size_data:
                    raise ThemeError(f"Photo size must be an object with 'width' and 'height'. Got: {size_data}")

                # Parse optional text position
                text_pos = None
                text_data = photo_dict.get('text')
                if text_data and isinstance(text_data, dict):
                    # Validate required width field
                    if 'width' not in text_data:
                        raise ThemeError(f"Text specification must include 'width' field")
                    
                    # Validate coordinates (percentages of the associated photo's dimensions)
                    x = float(text_data.get('x', 0))
                    y = float(text_data.get('y', 0))
                    width = float(text_data.get('width'))
                    height = float(text_data['height']) if 'height' in text_data else None

                    if not (0 <= x <= 100):
                        raise ThemeError(f"Text x coordinate must be 0-100, got: {x}")
                    if not (0 <= y <= 100):
                        raise ThemeError(f"Text y coordinate must be 0-100, got: {y}")
                    if not (0 <= width <= 100):
                        raise ThemeError(f"Text width must be 0-100, got: {width}")
                    if height is not None and not (0 <= height <= 100):
                        raise ThemeError(f"Text height must be 0-100, got: {height}")

                    # Validate alignment
                    align = text_data.get('align', 'left')

                    valid_align = ['left', 'center', 'right']

                    if align not in valid_align:
                        raise ThemeError(f"Text align must be one of {valid_align}, got: {align}")

                    # Validate dock: overrides the horizontal anchor to the page's literal border
                    dock = text_data.get('dock')

                    valid_dock = ['left', 'right']

                    if dock is not None and dock not in valid_dock:
                        raise ThemeError(f"Text dock must be one of {valid_dock}, got: {dock}")

                    text_pos = TextPosition(
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        align=align,
                        dock=dock
                    )

                photos.append(LayoutPhoto(
                    orientation=photo_dict.get('orientation', 'landscape'),
                    position=LayoutPosition(x=pos.get('x', 0.5), y=pos.get('y', 0.5)),
                    size=LayoutPhotoSize(
                        width=float(size_data['width']),
                        height=float(size_data['height'])
                    ),
                    text=text_pos
                ))
            layouts.append(LayoutTemplate(
                count=layout_dict.get('count', len(photos)),
                photos=photos
            ))

        title_style = TitleStyle(**data.get('title', {}))

        valid_title_align = ['left', 'center', 'right']
        if title_style.align not in valid_title_align:
            raise ThemeError(f"Title align must be one of {valid_title_align}, got: {title_style.align}")

        if not isinstance(title_style.base_font_size, (int, float)) or isinstance(title_style.base_font_size, bool) or title_style.base_font_size <= 0:
            raise ThemeError(f"Title base_font_size must be a positive number, got: {title_style.base_font_size}")

        return cls(
            name=data.get('name', 'Unnamed'),
            description=data.get('description', ''),
            background=BackgroundStyle(**data.get('background', {})),
            borders=BorderStyle(**data.get('borders', {})),
            spacing=SpacingStyle(**data.get('spacing', {})),
            text=TextStyle(**data.get('text', {})),
            title=title_style,
            layouts=layouts,
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
    
    if theme.spacing.page_margin < 0:
        raise ThemeError("Page margin cannot be negative")
    
    if theme.spacing.photo_margin < 0:
        raise ThemeError("Photo margin cannot be negative")


def get_default_theme() -> Theme:
    """Get the default theme (clean)."""
    return load_theme("clean")
