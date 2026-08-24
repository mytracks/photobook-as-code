"""
Tests for theme system with text positioning.
"""

import pytest
from src.photobook_as_code.themes import (
    Theme, ThemeError, TextPosition, TextStyle, LayoutPhoto,
    LayoutPosition, LayoutPhotoSize, LayoutTemplate, load_theme, list_builtin_themes
)


class TestTextPosition:
    """Tests for TextPosition data structure."""
    
    def test_text_position_creation(self):
        """Test creating a TextPosition."""
        text_pos = TextPosition(x=10, y=20, width=80, height=15, align='left')
        assert text_pos.x == 10
        assert text_pos.y == 20
        assert text_pos.width == 80
        assert text_pos.height == 15
        assert text_pos.align == 'left'
    
    def test_text_position_defaults(self):
        """Test TextPosition default values."""
        text_pos = TextPosition(x=0, y=0, width=100)
        assert text_pos.align == 'left'
        assert text_pos.height is None


class TestTextStyle:
    """Tests for TextStyle data structure."""
    
    def test_text_style_defaults(self):
        """Test TextStyle default values."""
        style = TextStyle()
        assert style.base_font_size == 14
        assert style.font_family == 'DejaVuSans'
        assert style.text_color == '#000000'
        assert style.line_spacing == 10

    def test_text_style_custom_values(self):
        """Test TextStyle with custom values."""
        style = TextStyle(base_font_size=18, font_family='Arial', text_color='#FF0000', line_spacing=20)
        assert style.base_font_size == 18
        assert style.font_family == 'Arial'
        assert style.text_color == '#FF0000'
        assert style.line_spacing == 20


class TestThemeTextPositionParsing:
    """Tests for parsing text positions from theme YAML."""
    
    def test_parse_text_position_valid(self):
        """Test parsing valid text position from theme."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {
                        'x': 10,
                        'y': 20,
                        'width': 80,
                        'height': 15,
                        'align': 'center'
                    }
                }]
            }]
        }
        
        theme = Theme.from_dict(theme_data)
        assert len(theme.layouts) == 1
        assert len(theme.layouts[0].photos) == 1
        
        photo = theme.layouts[0].photos[0]
        assert photo.text is not None
        assert photo.text.x == 10
        assert photo.text.y == 20
        assert photo.text.width == 80
        assert photo.text.height == 15
        assert photo.text.align == 'center'
    
    def test_parse_text_position_defaults(self):
        """Test text position with default values."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {
                        'x': 10,
                        'y': 20,
                        'width': 80
                    }
                }]
            }]
        }
        
        theme = Theme.from_dict(theme_data)
        photo = theme.layouts[0].photos[0]
        assert photo.text.align == 'left'
        assert photo.text.height is None
    
    def test_parse_without_text_position(self):
        """Test photo without text position."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8}
                }]
            }]
        }
        
        theme = Theme.from_dict(theme_data)
        photo = theme.layouts[0].photos[0]
        assert photo.text is None


class TestThemeTextPositionValidation:
    """Tests for text position coordinate validation."""
    
    def test_validate_x_coordinate_negative(self):
        """Test validation rejects negative x coordinate."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': -10, 'y': 20, 'width': 80, 'height': 15}
                }]
            }]
        }
        
        with pytest.raises(ThemeError, match="Text x coordinate must be 0-100"):
            Theme.from_dict(theme_data)
    
    def test_validate_x_coordinate_too_large(self):
        """Test validation rejects x coordinate > 100."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 150, 'y': 20, 'width': 80, 'height': 15}
                }]
            }]
        }
        
        with pytest.raises(ThemeError, match="Text x coordinate must be 0-100"):
            Theme.from_dict(theme_data)
    
    def test_validate_y_coordinate_range(self):
        """Test validation of y coordinate range."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 120, 'width': 80, 'height': 15}
                }]
            }]
        }
        
        with pytest.raises(ThemeError, match="Text y coordinate must be 0-100"):
            Theme.from_dict(theme_data)
    
    def test_validate_width_range(self):
        """Test validation of width range."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 150, 'height': 15}
                }]
            }]
        }
        
        with pytest.raises(ThemeError, match="Text width must be 0-100"):
            Theme.from_dict(theme_data)
    
    def test_validate_height_range(self):
        """Test validation of height range."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': -5}
                }]
            }]
        }
        
        with pytest.raises(ThemeError, match="Text height must be 0-100"):
            Theme.from_dict(theme_data)
    
    def test_validate_boundary_values(self):
        """Test that boundary values (0, 100) are accepted."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 0, 'y': 0, 'width': 100, 'height': 100}
                }]
            }]
        }
        
        theme = Theme.from_dict(theme_data)
        photo = theme.layouts[0].photos[0]
        assert photo.text.x == 0
        assert photo.text.y == 0
        assert photo.text.width == 100
        assert photo.text.height == 100


class TestThemeAlignmentValidation:
    """Tests for text alignment validation."""
    
    def test_validate_horizontal_align_left(self):
        """Test left alignment is accepted."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': 15, 'align': 'left'}
                }]
            }]
        }
        
        theme = Theme.from_dict(theme_data)
        assert theme.layouts[0].photos[0].text.align == 'left'
    
    def test_validate_horizontal_align_center(self):
        """Test center alignment is accepted."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': 15, 'align': 'center'}
                }]
            }]
        }
        
        theme = Theme.from_dict(theme_data)
        assert theme.layouts[0].photos[0].text.align == 'center'
    
    def test_validate_horizontal_align_right(self):
        """Test right alignment is accepted."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': 15, 'align': 'right'}
                }]
            }]
        }
        
        theme = Theme.from_dict(theme_data)
        assert theme.layouts[0].photos[0].text.align == 'right'
    
    def test_validate_horizontal_align_invalid(self):
        """Test invalid horizontal alignment is rejected."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': 15, 'align': 'invalid'}
                }]
            }]
        }
        
        with pytest.raises(ThemeError, match="Text align must be one of"):
            Theme.from_dict(theme_data)


class TestThemeDockValidation:
    """Tests for text dock validation."""

    def test_dock_defaults_to_none(self):
        """Test dock is None when not specified."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': 15}
                }]
            }]
        }

        theme = Theme.from_dict(theme_data)
        assert theme.layouts[0].photos[0].text.dock is None

    def test_validate_dock_left(self):
        """Test dock: left is accepted."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': 15, 'dock': 'left'}
                }]
            }]
        }

        theme = Theme.from_dict(theme_data)
        assert theme.layouts[0].photos[0].text.dock == 'left'

    def test_validate_dock_right(self):
        """Test dock: right is accepted."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': 15, 'dock': 'right'}
                }]
            }]
        }

        theme = Theme.from_dict(theme_data)
        assert theme.layouts[0].photos[0].text.dock == 'right'

    def test_validate_dock_invalid(self):
        """Test invalid dock value is rejected."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': 15, 'dock': 'top'}
                }]
            }]
        }

        with pytest.raises(ThemeError, match="Text dock must be one of"):
            Theme.from_dict(theme_data)


class TestThemeTextStyling:
    """Tests for theme-level text styling properties."""
    
    def test_parse_text_styling_defaults(self):
        """Test default text styling values."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': []
        }
        
        theme = Theme.from_dict(theme_data)
        assert theme.text.base_font_size == 14
        assert theme.text.font_family == 'DejaVuSans'
        assert theme.text.text_color == '#000000'
        assert theme.text.text_background_enabled == True
        assert theme.text.text_background_color == '#FFFFFF'
        assert theme.text.text_background_opacity == 85
        assert theme.text.text_padding == 8
        assert theme.text.line_spacing == 10

    def test_parse_text_styling_custom(self):
        """Test custom text styling values."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'text': {
                'base_font_size': 18,
                'font_family': 'Arial',
                'text_color': '#333333',
                'text_background_enabled': False,
                'text_background_color': '#000000',
                'text_background_opacity': 50,
                'text_padding': 12,
                'line_spacing': 16
            },
            'layouts': []
        }

        theme = Theme.from_dict(theme_data)
        assert theme.text.base_font_size == 18
        assert theme.text.font_family == 'Arial'
        assert theme.text.text_color == '#333333'
        assert theme.text.text_background_enabled == False
        assert theme.text.text_background_color == '#000000'
        assert theme.text.text_background_opacity == 50
        assert theme.text.text_padding == 12
        assert theme.text.line_spacing == 16


class TestThemeTitleStyling:
    """Tests for theme-level title styling properties."""

    def test_parse_title_styling_defaults(self):
        """Test default title styling values when theme omits a title: block."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': []
        }

        theme = Theme.from_dict(theme_data)
        assert theme.title.base_font_size == 28
        assert theme.title.font_family == 'DejaVuSans'
        assert theme.title.text_color == '#000000'
        assert theme.title.align == 'center'
        assert theme.title.text_background_enabled == True
        assert theme.title.line_spacing == 10

    def test_parse_title_styling_custom(self):
        """Test custom title styling values, independent from text styling."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'text': {'base_font_size': 14, 'text_color': '#111111'},
            'title': {
                'base_font_size': 48,
                'font_family': 'DejaVuSansMono',
                'text_color': '#222222',
                'align': 'left',
                'text_background_enabled': False,
                'line_spacing': 24,
            },
            'layouts': []
        }

        theme = Theme.from_dict(theme_data)
        assert theme.title.base_font_size == 48
        assert theme.title.font_family == 'DejaVuSansMono'
        assert theme.title.text_color == '#222222'
        assert theme.title.align == 'left'
        assert theme.title.text_background_enabled == False
        assert theme.title.line_spacing == 24
        # Text styling is unaffected by title styling
        assert theme.text.base_font_size == 14
        assert theme.text.text_color == '#111111'

    def test_invalid_title_align_raises(self):
        """An invalid title.align value raises ThemeError."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'title': {'align': 'justify'},
            'layouts': []
        }
        with pytest.raises(ThemeError, match="Title align must be one of"):
            Theme.from_dict(theme_data)

    def test_invalid_title_base_font_size_raises(self):
        """A non-positive title.base_font_size raises ThemeError."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'title': {'base_font_size': -10},
            'layouts': []
        }
        with pytest.raises(ThemeError, match="Title base_font_size must be a positive number"):
            Theme.from_dict(theme_data)


class TestThemeMaxLayoutCount:
    """Tests for Theme.max_layout_count, used to cap day-aware page density."""

    def test_max_layout_count_from_dict(self):
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [
                {'count': 1, 'photos': [{'orientation': 'landscape', 'size': {'width': 0.8, 'height': 0.8}}]},
                {'count': 3, 'photos': [
                    {'orientation': 'landscape', 'size': {'width': 0.5, 'height': 0.5}},
                    {'orientation': 'landscape', 'size': {'width': 0.5, 'height': 0.5}},
                    {'orientation': 'landscape', 'size': {'width': 0.5, 'height': 0.5}},
                ]},
            ]
        }
        theme = Theme.from_dict(theme_data)
        assert theme.max_layout_count == 3

    def test_max_layout_count_no_layouts(self):
        theme = Theme(
            name='Empty', description='', background=None, borders=None, spacing=None,
        )
        assert theme.max_layout_count == 0

    @pytest.mark.parametrize("theme_name", list_builtin_themes())
    def test_builtin_themes_cap_at_four(self, theme_name):
        """Every shipped theme currently defines layouts up to count 4."""
        theme = load_theme(theme_name)
        assert theme.max_layout_count == 4
