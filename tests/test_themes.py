"""
Tests for theme system with text positioning.
"""

import pytest
from src.photobook_as_code.themes import (
    Theme, ThemeError, TextPosition, TextStyle, LayoutPhoto,
    LayoutPosition, LayoutPhotoSize
)


class TestTextPosition:
    """Tests for TextPosition data structure."""
    
    def test_text_position_creation(self):
        """Test creating a TextPosition."""
        text_pos = TextPosition(x=10, y=20, width=80, height=15, align='left', valign='top')
        assert text_pos.x == 10
        assert text_pos.y == 20
        assert text_pos.width == 80
        assert text_pos.height == 15
        assert text_pos.align == 'left'
        assert text_pos.valign == 'top'
    
    def test_text_position_defaults(self):
        """Test TextPosition default values."""
        text_pos = TextPosition(x=0, y=0, width=100, height=100)
        assert text_pos.align == 'left'
        assert text_pos.valign == 'top'


class TestTextStyle:
    """Tests for TextStyle data structure."""
    
    def test_text_style_defaults(self):
        """Test TextStyle default values."""
        style = TextStyle()
        assert style.base_font_size == 14
        assert style.font_family == 'DejaVuSans'
        assert style.text_color == '#000000'
    
    def test_text_style_custom_values(self):
        """Test TextStyle with custom values."""
        style = TextStyle(base_font_size=18, font_family='Arial', text_color='#FF0000')
        assert style.base_font_size == 18
        assert style.font_family == 'Arial'
        assert style.text_color == '#FF0000'


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
                        'align': 'center',
                        'valign': 'middle'
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
        assert photo.text.valign == 'middle'
    
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
                        'width': 80,
                        'height': 15
                    }
                }]
            }]
        }
        
        theme = Theme.from_dict(theme_data)
        photo = theme.layouts[0].photos[0]
        assert photo.text.align == 'left'
        assert photo.text.valign == 'top'
    
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
    
    def test_validate_vertical_align_top(self):
        """Test top vertical alignment is accepted."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': 15, 'valign': 'top'}
                }]
            }]
        }
        
        theme = Theme.from_dict(theme_data)
        assert theme.layouts[0].photos[0].text.valign == 'top'
    
    def test_validate_vertical_align_middle(self):
        """Test middle vertical alignment is accepted."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': 15, 'valign': 'middle'}
                }]
            }]
        }
        
        theme = Theme.from_dict(theme_data)
        assert theme.layouts[0].photos[0].text.valign == 'middle'
    
    def test_validate_vertical_align_bottom(self):
        """Test bottom vertical alignment is accepted."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': 15, 'valign': 'bottom'}
                }]
            }]
        }
        
        theme = Theme.from_dict(theme_data)
        assert theme.layouts[0].photos[0].text.valign == 'bottom'
    
    def test_validate_vertical_align_invalid(self):
        """Test invalid vertical alignment is rejected."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'layouts': [{
                'count': 1,
                'photos': [{
                    'orientation': 'landscape',
                    'position': {'x': 0.5, 'y': 0.5},
                    'size': {'width': 0.8, 'height': 0.8},
                    'text': {'x': 10, 'y': 20, 'width': 80, 'height': 15, 'valign': 'invalid'}
                }]
            }]
        }
        
        with pytest.raises(ThemeError, match="Text valign must be one of"):
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
    
    def test_parse_text_styling_custom(self):
        """Test custom text styling values."""
        theme_data = {
            'name': 'Test',
            'description': 'Test theme',
            'text': {
                'base_font_size': 18,
                'font_family': 'Arial',
                'text_color': '#333333'
            },
            'layouts': []
        }
        
        theme = Theme.from_dict(theme_data)
        assert theme.text.base_font_size == 18
        assert theme.text.font_family == 'Arial'
        assert theme.text.text_color == '#333333'
