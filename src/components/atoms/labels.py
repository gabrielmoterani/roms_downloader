"""
Atomic Label Components
Basic text display atoms with consistent typography
"""

from kivy.uix.label import Label


class HeadingLabel(Label):
    """Main heading text"""
    
    def __init__(self, text: str = "", **kwargs):
        default_kwargs = {
            'font_size': '24sp',
            'color': (1, 1, 1, 1),
            'size_hint_y': None,
            'height': 50,
            'halign': 'left',
            'valign': 'middle',
        }
        default_kwargs.update(kwargs)
        
        super().__init__(text=text, **default_kwargs)


class SubheadingLabel(Label):
    """Secondary heading text"""
    
    def __init__(self, text: str = "", **kwargs):
        default_kwargs = {
            'font_size': '18sp',
            'color': (0.9, 0.9, 0.9, 1),
            'size_hint_y': None,
            'height': 35,
            'halign': 'left',
            'valign': 'middle',
        }
        default_kwargs.update(kwargs)
        
        super().__init__(text=text, **default_kwargs)


class BodyLabel(Label):
    """Regular body text"""
    
    def __init__(self, text: str = "", **kwargs):
        default_kwargs = {
            'font_size': '14sp',
            'color': (1, 1, 1, 1),
            'halign': 'left',
            'valign': 'middle',
            'text_size': (None, None),
        }
        default_kwargs.update(kwargs)
        
        super().__init__(text=text, **default_kwargs)


class CaptionLabel(Label):
    """Small caption/helper text"""
    
    def __init__(self, text: str = "", **kwargs):
        default_kwargs = {
            'font_size': '12sp',
            'color': (0.7, 0.7, 0.7, 1),
            'halign': 'left',
            'valign': 'middle',
            'size_hint_y': None,
            'height': 25,
        }
        default_kwargs.update(kwargs)
        
        super().__init__(text=text, **default_kwargs)


class StatusLabel(Label):
    """Status/info text with semantic colors"""
    
    def __init__(self, text: str = "", status_type: str = "info", **kwargs):
        # Define status colors
        colors = {
            'info': (0.3, 0.6, 1.0, 1),      # Blue
            'success': (0.3, 0.8, 0.3, 1),   # Green
            'warning': (1.0, 0.7, 0.2, 1),   # Orange
            'error': (0.9, 0.3, 0.3, 1),     # Red
        }
        
        default_kwargs = {
            'font_size': '13sp',
            'color': colors.get(status_type, colors['info']),
            'size_hint_y': None,
            'height': 30,
            'halign': 'center',
            'valign': 'middle',
        }
        default_kwargs.update(kwargs)
        
        super().__init__(text=text, **default_kwargs)

