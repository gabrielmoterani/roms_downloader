"""
Virtual Scroll List Molecule
Efficiently renders only visible items from large datasets
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.metrics import dp
from typing import List, Callable, Any, Optional, Dict
import threading


class VirtualScrollList(BoxLayout):
    """
    Virtual scrolling list that only renders visible items plus a buffer
    This dramatically improves performance with large datasets
    """
    
    def __init__(self, 
                 item_height: float = 60,
                 buffer_size: int = 10,
                 item_loader: Optional[Callable[[int, int], List[Any]]] = None,
                 item_renderer: Optional[Callable[[Any], Any]] = None,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.orientation = 'vertical'
        
        # Configuration
        self.item_height = dp(item_height)
        self.buffer_size = buffer_size  # Items to render above/below viewport
        self.item_loader = item_loader
        self.item_renderer = item_renderer
        
        # State
        self.all_items: List[Any] = []
        self.rendered_widgets: Dict[int, Any] = {}  # index -> widget
        self.visible_start = 0
        self.visible_end = 0
        self.total_items = 0
        self.viewport_height = 0
        self.loading = False
        self.load_batch_size = 100
        self.loaded_batches = set()
        
        # Create UI
        self._build_ui()
        
        # Schedule initial load
        Clock.schedule_once(self._initial_load, 0.1)
    
    def _build_ui(self):
        """Build the virtual scroll UI"""
        # Create scroll view
        self.scroll_view = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            scroll_type=['bars', 'content']
        )
        
        # Create container that represents the full list height
        self.scroll_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None
        )
        
        # Top spacer (represents items above viewport)
        self.top_spacer = Widget(
            size_hint_y=None,
            height=0
        )
        self.scroll_container.add_widget(self.top_spacer)
        
        # Visible items container
        self.visible_container = BoxLayout(
            orientation='vertical',
            spacing=2,
            size_hint_y=None
        )
        self.visible_container.bind(minimum_height=self.visible_container.setter('height'))
        self.scroll_container.add_widget(self.visible_container)
        
        # Bottom spacer (represents items below viewport)
        self.bottom_spacer = Widget(
            size_hint_y=None,
            height=0
        )
        self.scroll_container.add_widget(self.bottom_spacer)
        
        self.scroll_view.add_widget(self.scroll_container)
        
        # Bind scroll events
        self.scroll_view.bind(scroll_y=self._on_scroll)
        self.scroll_view.bind(size=self._on_viewport_size_change)
        
        self.add_widget(self.scroll_view)
    
    def _initial_load(self, dt):
        """Initial load to determine total items and load first batch"""
        if self.item_loader:
            self._load_batch(0)
    
    def _on_viewport_size_change(self, *args):
        """Handle viewport size changes"""
        self.viewport_height = self.scroll_view.height
        self._calculate_visible_range()
        self._update_visible_items()
    
    def _on_scroll(self, scroll_view, scroll_y):
        """Handle scroll events"""
        self._calculate_visible_range()
        self._update_visible_items()
        
        # Check if we need to load more data
        self._check_load_more()
    
    def _calculate_visible_range(self):
        """Calculate which items should be visible based on scroll position"""
        if not self.all_items or self.item_height <= 0:
            return
        
        # Get scroll position (Kivy uses 0-1 range, 1 = top, 0 = bottom)
        scroll_pos = self.scroll_view.scroll_y
        content_height = self.total_items * self.item_height
        viewport_height = self.scroll_view.height
        
        if content_height <= viewport_height:
            # All items fit in viewport
            self.visible_start = 0
            self.visible_end = len(self.all_items)
            return
        
        # Calculate which items are visible
        # scroll_y = 1 means top of content, 0 means bottom
        scroll_offset = (1 - scroll_pos) * (content_height - viewport_height)
        
        # Calculate first and last visible item indices
        first_visible = max(0, int(scroll_offset // self.item_height) - self.buffer_size)
        last_visible = min(
            len(self.all_items),
            int((scroll_offset + viewport_height) // self.item_height) + 1 + self.buffer_size
        )
        
        self.visible_start = first_visible
        self.visible_end = last_visible
    
    def _update_visible_items(self):
        """Update which items are actually rendered"""
        if not self.all_items:
            return
        
        # Clear current visible items
        self.visible_container.clear_widgets()
        
        # Update spacer heights
        self.top_spacer.height = self.visible_start * self.item_height
        items_below = max(0, len(self.all_items) - self.visible_end)
        self.bottom_spacer.height = items_below * self.item_height
        
        # Update total container height
        self.scroll_container.height = len(self.all_items) * self.item_height
        
        # Render visible items
        for i in range(self.visible_start, self.visible_end):
            if i < len(self.all_items):
                widget = self._get_or_create_widget(i)
                if widget:
                    self.visible_container.add_widget(widget)
        
        # Clean up widgets that are no longer visible
        self._cleanup_invisible_widgets()
    
    def _get_or_create_widget(self, index: int):
        """Get existing widget or create new one for item at index"""
        if index in self.rendered_widgets:
            widget = self.rendered_widgets[index]
            # Remove from parent if it has one
            if widget.parent:
                widget.parent.remove_widget(widget)
            return widget
        
        if index >= len(self.all_items):
            return None
        
        # Create new widget
        if self.item_renderer:
            item_data = self.all_items[index]
            widget = self.item_renderer(item_data)
            # Ensure consistent height
            widget.size_hint_y = None
            widget.height = self.item_height
            
            self.rendered_widgets[index] = widget
            return widget
        
        return None
    
    def _cleanup_invisible_widgets(self):
        """Remove widgets that are no longer visible to save memory"""
        visible_indices = set(range(self.visible_start, self.visible_end))
        
        # Find widgets to remove
        to_remove = []
        for index in self.rendered_widgets:
            if index not in visible_indices:
                to_remove.append(index)
        
        # Remove invisible widgets (keep some buffer for performance)
        max_cached_widgets = (self.visible_end - self.visible_start) * 3
        if len(self.rendered_widgets) > max_cached_widgets:
            # Remove oldest widgets first
            for index in to_remove[:len(to_remove)//2]:
                del self.rendered_widgets[index]
    
    def _check_load_more(self):
        """Check if we need to load more data"""
        if not self.item_loader or self.loading:
            return
        
        # Calculate which batch we need
        items_from_end = len(self.all_items) - self.visible_end
        if items_from_end < self.buffer_size * 2:
            # We're close to the end, load more
            next_batch_start = len(self.all_items)
            batch_number = next_batch_start // self.load_batch_size
            
            if batch_number not in self.loaded_batches:
                self._load_batch(next_batch_start)
    
    def _load_batch(self, start_index: int):
        """Load a batch of items starting from start_index"""
        if self.loading or not self.item_loader:
            return
        
        self.loading = True
        batch_number = start_index // self.load_batch_size
        
        def load_items():
            try:
                new_items = self.item_loader(start_index, self.load_batch_size)
                Clock.schedule_once(lambda dt: self._on_batch_loaded(new_items, batch_number))
            except Exception as e:
                print(f"Error loading batch: {e}")
                Clock.schedule_once(lambda dt: self._on_batch_error(e))
        
        thread = threading.Thread(target=load_items)
        thread.daemon = True
        thread.start()
    
    def _on_batch_loaded(self, new_items: List[Any], batch_number: int):
        """Handle successfully loaded batch"""
        self.loading = False
        self.loaded_batches.add(batch_number)
        
        if new_items:
            self.all_items.extend(new_items)
            self.total_items = len(self.all_items)
            
            # Update display
            self._calculate_visible_range()
            self._update_visible_items()
            
            print(f"Loaded batch {batch_number}: {len(new_items)} items (total: {self.total_items})")
    
    def _on_batch_error(self, error):
        """Handle batch loading error"""
        self.loading = False
        print(f"Failed to load batch: {error}")
    
    def set_data_source(self, item_loader: Callable[[int, int], List[Any]]):
        """Set the data source loader function"""
        self.item_loader = item_loader
        self.clear_all()
        Clock.schedule_once(self._initial_load, 0.1)
    
    def set_item_renderer(self, item_renderer: Callable[[Any], Any]):
        """Set the item renderer function"""
        self.item_renderer = item_renderer
        self.clear_widgets_cache()
        self._update_visible_items()
    
    def clear_all(self):
        """Clear all data and widgets"""
        self.all_items.clear()
        self.rendered_widgets.clear()
        self.loaded_batches.clear()
        self.visible_container.clear_widgets()
        self.total_items = 0
        self.visible_start = 0
        self.visible_end = 0
        
        # Reset spacers
        self.top_spacer.height = 0
        self.bottom_spacer.height = 0
        self.scroll_container.height = 0
    
    def clear_widgets_cache(self):
        """Clear only the widget cache, keep data"""
        self.rendered_widgets.clear()
        self.visible_container.clear_widgets()
    
    def refresh(self):
        """Refresh the current view"""
        self.clear_widgets_cache()
        self._calculate_visible_range()
        self._update_visible_items()
    
    def scroll_to_top(self):
        """Scroll to the top of the list"""
        self.scroll_view.scroll_y = 1
    
    def scroll_to_bottom(self):
        """Scroll to the bottom of the list"""
        self.scroll_view.scroll_y = 0
    
    def get_total_items(self) -> int:
        """Get total number of items"""
        return self.total_items
    
    def get_visible_items(self) -> List[Any]:
        """Get currently visible items"""
        return self.all_items[self.visible_start:self.visible_end]
