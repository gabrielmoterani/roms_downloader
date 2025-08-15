"""
Search Bar Molecule
Combines search input with optional clear button and search actions
"""

from kivy.uix.boxlayout import BoxLayout
from typing import Callable, Optional
from ..atoms.inputs import SearchInput
from ..atoms.buttons import IconButton


class SearchBar(BoxLayout):
    """
    Search bar molecule combining input field with clear functionality
    """
    
    def __init__(self,
                 placeholder: str = "Search...",
                 on_text_change: Optional[Callable] = None,
                 on_clear: Optional[Callable] = None,
                 show_clear_button: bool = True,
                 **kwargs):
        
        default_kwargs = {
            'orientation': 'horizontal',
            'size_hint_y': None,
            'height': 50,
            'spacing': 10
        }
        default_kwargs.update(kwargs)
        
        super().__init__(**default_kwargs)
        
        self.on_text_change = on_text_change
        self.on_clear = on_clear
        
        self._build_ui(placeholder, show_clear_button)
    
    def _build_ui(self, placeholder: str, show_clear_button: bool):
        """Build the search bar UI"""
        # Search input
        self.search_input = SearchInput(
            placeholder=placeholder,
            on_text_change=self._on_input_change
        )
        self.add_widget(self.search_input)
        
        # Clear button (optional)
        if show_clear_button:
            self.clear_button = IconButton(
                text="✕",
                on_click=self._on_clear_clicked,
                size_hint_x=None,
                width=40
            )
            self.add_widget(self.clear_button)
    
    def _on_input_change(self, text_input, text):
        """Handle text input changes"""
        if self.on_text_change:
            self.on_text_change(text)
    
    def _on_clear_clicked(self, button):
        """Handle clear button click"""
        self.search_input.text = ""
        if self.on_clear:
            self.on_clear()
    
    def get_text(self) -> str:
        """Get current search text"""
        return self.search_input.text
    
    def set_text(self, text: str):
        """Set search text"""
        self.search_input.text = text
    
    def clear(self):
        """Clear the search text"""
        self.search_input.text = ""
    
    def focus(self):
        """Focus the search input"""
        self.search_input.focus = True

