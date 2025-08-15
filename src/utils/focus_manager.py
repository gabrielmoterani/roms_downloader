"""
Focus Manager for Controller Navigation
Handles which UI element is currently focused and manages navigation between focusable items
"""
from typing import List, Optional, Callable, Any
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.event import EventDispatcher


class FocusableWidget:
    """Wrapper to make any widget focusable"""
    
    def __init__(self, widget: Widget, on_select: Optional[Callable] = None, 
                 data: Any = None, navigation_id: str = None):
        self.widget = widget
        self.on_select = on_select  # Called when select button is pressed
        self.data = data  # Associated data (e.g., system info, game data)
        self.navigation_id = navigation_id or f"widget_{id(widget)}"
        self.is_focused = False
        
        # Visual focus indicators
        self.focus_instruction = None
        self.focus_color = None
        
    def set_focused(self, focused: bool):
        """Set focus state and update visual appearance"""
        self.is_focused = focused
        
        if focused:
            self._add_focus_visual()
        else:
            self._remove_focus_visual()
    
    def _add_focus_visual(self):
        """Add visual focus indicator"""
        if self.focus_instruction is None:
            with self.widget.canvas.after:
                self.focus_color = Color(0.2, 0.6, 1.0, 0.8)  # Blue highlight
                self.focus_instruction = Line(
                    rectangle=[
                        self.widget.x - 2, 
                        self.widget.y - 2, 
                        self.widget.width + 4, 
                        self.widget.height + 4
                    ],
                    width=3
                )
            
            # Bind to update position when widget moves
            self.widget.bind(pos=self._update_focus_visual, size=self._update_focus_visual)
    
    def _remove_focus_visual(self):
        """Remove visual focus indicator"""
        if self.focus_instruction is not None:
            self.widget.canvas.after.remove(self.focus_color)
            self.widget.canvas.after.remove(self.focus_instruction)
            self.focus_instruction = None
            self.focus_color = None
            
            # Unbind position updates
            self.widget.unbind(pos=self._update_focus_visual, size=self._update_focus_visual)
    
    def _update_focus_visual(self, *args):
        """Update focus visual position/size"""
        if self.focus_instruction is not None:
            self.focus_instruction.rectangle = [
                self.widget.x - 2, 
                self.widget.y - 2, 
                self.widget.width + 4, 
                self.widget.height + 4
            ]
    
    def select(self):
        """Handle selection (select button pressed)"""
        if self.on_select:
            self.on_select(self.data)


class FocusManager(EventDispatcher):
    """Manages focus state and navigation between focusable widgets"""
    
    __events__ = ('on_focus_changed', 'on_item_selected')
    
    def __init__(self):
        super().__init__()
        self.focusable_widgets: List[FocusableWidget] = []
        self.current_focus_index = -1
        self.grid_columns = 1  # For grid-based navigation
        self.navigation_enabled = True
    
    def clear(self):
        """Clear all focusable widgets"""
        # Remove focus from current widget
        if self.current_focus_index >= 0:
            self.focusable_widgets[self.current_focus_index].set_focused(False)
        
        self.focusable_widgets.clear()
        self.current_focus_index = -1
    
    def add_focusable(self, widget: Widget, on_select: Optional[Callable] = None, 
                     data: Any = None, navigation_id: str = None) -> FocusableWidget:
        """Add a focusable widget"""
        focusable = FocusableWidget(widget, on_select, data, navigation_id)
        self.focusable_widgets.append(focusable)
        
        # If this is the first widget, focus it
        if len(self.focusable_widgets) == 1:
            self.set_focus(0)
        
        return focusable
    
    def remove_focusable(self, widget: Widget):
        """Remove a focusable widget"""
        for i, focusable in enumerate(self.focusable_widgets):
            if focusable.widget == widget:
                # Remove focus if this widget was focused
                if i == self.current_focus_index:
                    focusable.set_focused(False)
                    # Move focus to next available widget
                    if len(self.focusable_widgets) > 1:
                        new_index = min(i, len(self.focusable_widgets) - 2)
                        self.set_focus(new_index)
                    else:
                        self.current_focus_index = -1
                
                self.focusable_widgets.pop(i)
                break
    
    def set_grid_columns(self, columns: int):
        """Set number of columns for grid-based navigation"""
        self.grid_columns = max(1, columns)
    
    def set_focus(self, index: int):
        """Set focus to specific index"""
        if not self.navigation_enabled or not self.focusable_widgets:
            return
        
        # Remove focus from current widget
        if 0 <= self.current_focus_index < len(self.focusable_widgets):
            self.focusable_widgets[self.current_focus_index].set_focused(False)
        
        # Set focus to new widget
        if 0 <= index < len(self.focusable_widgets):
            self.current_focus_index = index
            self.focusable_widgets[index].set_focused(True)
            self.dispatch('on_focus_changed', index, self.focusable_widgets[index])
        else:
            self.current_focus_index = -1
    
    def navigate_up(self):
        """Navigate up (previous item or grid row above)"""
        if not self.navigation_enabled or not self.focusable_widgets:
            return
        
        if self.grid_columns == 1:
            # Linear navigation
            new_index = (self.current_focus_index - 1) % len(self.focusable_widgets)
        else:
            # Grid navigation
            new_index = self.current_focus_index - self.grid_columns
            if new_index < 0:
                # Wrap to bottom row
                rows = (len(self.focusable_widgets) + self.grid_columns - 1) // self.grid_columns
                col = self.current_focus_index % self.grid_columns
                new_index = (rows - 1) * self.grid_columns + col
                # Ensure we don't go beyond the last item
                new_index = min(new_index, len(self.focusable_widgets) - 1)
        
        self.set_focus(new_index)
    
    def navigate_down(self):
        """Navigate down (next item or grid row below)"""
        if not self.navigation_enabled or not self.focusable_widgets:
            return
        
        if self.grid_columns == 1:
            # Linear navigation
            new_index = (self.current_focus_index + 1) % len(self.focusable_widgets)
        else:
            # Grid navigation
            new_index = self.current_focus_index + self.grid_columns
            if new_index >= len(self.focusable_widgets):
                # Wrap to top row
                col = self.current_focus_index % self.grid_columns
                new_index = col
        
        self.set_focus(new_index)
    
    def navigate_left(self):
        """Navigate left (in grid layout or circular in linear)"""
        if not self.navigation_enabled or not self.focusable_widgets:
            return
        
        if self.grid_columns == 1:
            # In linear layout, left = up
            self.navigate_up()
        else:
            # Grid navigation
            current_col = self.current_focus_index % self.grid_columns
            if current_col == 0:
                # Wrap to rightmost column of same row
                current_row = self.current_focus_index // self.grid_columns
                new_index = current_row * self.grid_columns + self.grid_columns - 1
                # Ensure we don't go beyond the last item
                new_index = min(new_index, len(self.focusable_widgets) - 1)
            else:
                new_index = self.current_focus_index - 1
            
            self.set_focus(new_index)
    
    def navigate_right(self):
        """Navigate right (in grid layout or circular in linear)"""
        if not self.navigation_enabled or not self.focusable_widgets:
            return
        
        if self.grid_columns == 1:
            # In linear layout, right = down
            self.navigate_down()
        else:
            # Grid navigation
            current_col = self.current_focus_index % self.grid_columns
            current_row = self.current_focus_index // self.grid_columns
            
            if current_col == self.grid_columns - 1 or self.current_focus_index == len(self.focusable_widgets) - 1:
                # Wrap to leftmost column of same row
                new_index = current_row * self.grid_columns
            else:
                new_index = self.current_focus_index + 1
            
            self.set_focus(new_index)
    
    def select_current(self):
        """Select the currently focused item"""
        if (self.navigation_enabled and 
            0 <= self.current_focus_index < len(self.focusable_widgets)):
            
            focusable = self.focusable_widgets[self.current_focus_index]
            focusable.select()
            self.dispatch('on_item_selected', self.current_focus_index, focusable)
    
    def get_current_focused(self) -> Optional[FocusableWidget]:
        """Get the currently focused widget"""
        if 0 <= self.current_focus_index < len(self.focusable_widgets):
            return self.focusable_widgets[self.current_focus_index]
        return None
    
    def set_navigation_enabled(self, enabled: bool):
        """Enable or disable navigation"""
        self.navigation_enabled = enabled
        
        if not enabled and self.current_focus_index >= 0:
            # Remove focus visual when disabled
            self.focusable_widgets[self.current_focus_index].set_focused(False)
    
    def on_focus_changed(self, *args):
        """Event handler for focus changes (override in subclass)"""
        pass
    
    def on_item_selected(self, *args):
        """Event handler for item selection (override in subclass)"""
        pass
