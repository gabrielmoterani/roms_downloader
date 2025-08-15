"""
Game Item Molecule
A single game item with selection, name display, and actions
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from typing import Any, Callable, Optional
from ..atoms.inputs import SelectionCheckbox
from ..atoms.labels import BodyLabel


class GameItem(BoxLayout):
    """
    A molecule representing a single game item
    Combines checkbox + label + visual styling
    """
    
    def __init__(self, 
                 game_data: Any, 
                 is_selected: bool = False, 
                 on_selection_change: Optional[Callable] = None,
                 **kwargs):
        
        default_kwargs = {
            'orientation': 'horizontal',
            'size_hint_y': None,
            'height': 60,
            'spacing': 15,
            'padding': [15, 5, 15, 5]
        }
        default_kwargs.update(kwargs)
        
        super().__init__(**default_kwargs)
        
        self.game_data = game_data
        self.is_selected = is_selected
        self.on_selection_change = on_selection_change
        
        self._build_ui()
        self._update_visual_style()
        
        # Make the entire item clickable
        self.bind(on_touch_down=self._on_item_click)
    
    def _build_ui(self):
        """Build the game item UI"""
        # Selection checkbox
        self.checkbox = SelectionCheckbox(
            is_checked=self.is_selected,
            on_toggle=self._on_checkbox_toggle
        )
        self.add_widget(self.checkbox)
        
        # Game name label
        game_name = self._extract_game_name(self.game_data)
        self.name_label = BodyLabel(
            text=game_name,
            font_size='16sp'
        )
        self.add_widget(self.name_label)
    
    def _extract_game_name(self, game_data: Any) -> str:
        """Extract display name from game data"""
        if isinstance(game_data, dict):
            if 'name' in game_data:
                # Switch API format
                return game_data['name']
            elif 'filename' in game_data:
                # File listing format - remove extension
                import os
                return os.path.splitext(game_data['filename'])[0]
            else:
                return str(game_data)
        else:
            # Simple string format
            import os
            return os.path.splitext(str(game_data))[0]
    
    def _on_checkbox_toggle(self, checkbox, is_active):
        """Handle checkbox toggle"""
        # Only update if this is a real user interaction
        if self.is_selected != is_active:
            self.is_selected = is_active
            self._update_visual_style()
            
            if self.on_selection_change:
                self.on_selection_change(self.game_data, is_active)
    
    def _on_item_click(self, widget, touch):
        """Handle clicks on the entire item"""
        if self.collide_point(*touch.pos):
            # Toggle the checkbox when the item is clicked
            self.checkbox.active = not self.checkbox.active
            return True
        return False
    
    def _update_visual_style(self):
        """Update visual style based on selection state"""
        self.canvas.before.clear()
        with self.canvas.before:
            if self.is_selected:
                Color(0.2, 0.4, 0.2, 0.8)  # Green tint for selected
            else:
                Color(0.1, 0.1, 0.1, 1.0)  # Dark background
            
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        # Bind to update rectangle when widget moves/resizes
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, *args):
        """Update background rectangle"""
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size
    
    def set_selected(self, selected: bool):
        """Programmatically set selection state without triggering callback"""
        self.is_selected = selected
        # Temporarily unbind to avoid callback during programmatic update
        self.checkbox.unbind(active=self._on_checkbox_toggle)
        self.checkbox.active = selected
        self.checkbox.bind(active=self._on_checkbox_toggle)
        self._update_visual_style()
    
    def get_game_key(self) -> str:
        """Get a unique key for this game"""
        if isinstance(self.game_data, dict):
            if 'name' in self.game_data:
                return self.game_data['name']
            elif 'filename' in self.game_data:
                return self.game_data['filename']
            else:
                return str(self.game_data)
        else:
            return str(self.game_data)

