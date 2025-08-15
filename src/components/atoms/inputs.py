"""
Atomic Input Components
Basic form input atoms with consistent styling
"""

from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from typing import Optional, Callable


class SearchInput(TextInput):
    """Search text input with consistent styling"""
    
    def __init__(self, placeholder: str = "Search...", on_text_change: Optional[Callable] = None, **kwargs):
        default_kwargs = {
            'hint_text': placeholder,
            'multiline': False,
            'font_size': '14sp',
            'size_hint_y': None,
            'height': 40,
            'background_color': (0.2, 0.2, 0.2, 1),
            'foreground_color': (1, 1, 1, 1),
        }
        default_kwargs.update(kwargs)
        
        super().__init__(**default_kwargs)
        
        if on_text_change:
            self.bind(text=on_text_change)


class FormInput(TextInput):
    """General form input field"""
    
    def __init__(self, placeholder: str = "", multiline: bool = False, **kwargs):
        default_kwargs = {
            'hint_text': placeholder,
            'multiline': multiline,
            'font_size': '14sp',
            'size_hint_y': None,
            'height': 40 if not multiline else 80,
            'background_color': (0.15, 0.15, 0.15, 1),
            'foreground_color': (1, 1, 1, 1),
        }
        default_kwargs.update(kwargs)
        
        super().__init__(**default_kwargs)


class SelectionCheckbox(CheckBox):
    """Checkbox for item selection with consistent styling"""
    
    def __init__(self, is_checked: bool = False, on_toggle: Optional[Callable] = None, **kwargs):
        default_kwargs = {
            'active': is_checked,
            'size_hint': (None, None),
            'size': (30, 30),
        }
        default_kwargs.update(kwargs)
        
        super().__init__(**default_kwargs)
        
        if on_toggle:
            self.bind(active=on_toggle)

