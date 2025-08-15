"""
Atomic Button Components
Basic button atoms with consistent styling and behavior
"""

from kivy.uix.button import Button
from typing import Optional, Callable


class PrimaryButton(Button):
    """Primary action button with consistent styling"""
    
    def __init__(self, text: str = "", on_click: Optional[Callable] = None, **kwargs):
        # Set default styling
        default_kwargs = {
            'font_size': '16sp',
            'size_hint_y': None,
            'height': 50,
            'background_color': (0.2, 0.6, 1.0, 1.0),  # Blue
        }
        default_kwargs.update(kwargs)
        
        super().__init__(text=text, **default_kwargs)
        
        if on_click:
            self.bind(on_press=on_click)


class SecondaryButton(Button):
    """Secondary action button with muted styling"""
    
    def __init__(self, text: str = "", on_click: Optional[Callable] = None, **kwargs):
        # Set default styling
        default_kwargs = {
            'font_size': '14sp',
            'size_hint_y': None,
            'height': 40,
            'background_color': (0.5, 0.5, 0.5, 1.0),  # Gray
        }
        default_kwargs.update(kwargs)
        
        super().__init__(text=text, **default_kwargs)
        
        if on_click:
            self.bind(on_press=on_click)


class DangerButton(Button):
    """Danger/destructive action button"""
    
    def __init__(self, text: str = "", on_click: Optional[Callable] = None, **kwargs):
        # Set default styling
        default_kwargs = {
            'font_size': '14sp',
            'size_hint_y': None,
            'height': 40,
            'background_color': (0.9, 0.3, 0.3, 1.0),  # Red
        }
        default_kwargs.update(kwargs)
        
        super().__init__(text=text, **default_kwargs)
        
        if on_click:
            self.bind(on_press=on_click)


class IconButton(Button):
    """Button with icon-like styling for compact actions"""
    
    def __init__(self, text: str = "", on_click: Optional[Callable] = None, **kwargs):
        # Set default styling
        default_kwargs = {
            'font_size': '12sp',
            'size_hint': (None, None),
            'size': (40, 40),
            'background_color': (0.3, 0.3, 0.3, 1.0),
        }
        default_kwargs.update(kwargs)
        
        super().__init__(text=text, **default_kwargs)
        
        if on_click:
            self.bind(on_press=on_click)


class NavigationButton(Button):
    """Navigation button for moving between screens/pages"""
    
    def __init__(self, text: str = "", on_click: Optional[Callable] = None, **kwargs):
        # Set default styling
        default_kwargs = {
            'font_size': '14sp',
            'size_hint_y': None,
            'height': 45,
            'background_color': (0.4, 0.4, 0.4, 1.0),
        }
        default_kwargs.update(kwargs)
        
        super().__init__(text=text, **default_kwargs)
        
        if on_click:
            self.bind(on_press=on_click)
