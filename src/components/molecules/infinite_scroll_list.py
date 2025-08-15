"""
Infinite Scroll List Molecule
A scrollable list that loads items progressively as the user scrolls
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from typing import List, Callable, Any, Optional
import threading


class InfiniteScrollList(BoxLayout):
    """
    Infinite scroll list that loads items as the user scrolls down
    Implements virtual scrolling for performance with large datasets
    """
    
    def __init__(self, 
                 item_loader: Callable[[int, int], List[Any]],  # func(start_index, count) -> items
                 item_renderer: Callable[[Any], Any],           # func(item) -> widget
                 items_per_batch: int = 50,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.orientation = 'vertical'
        self.item_loader = item_loader
        self.item_renderer = item_renderer
        self.items_per_batch = items_per_batch
        
        # State
        self.items = []
        self.rendered_items = []
        self.loading = False
        self.has_more = True
        self.current_batch = 0
        
        # Create UI
        self._build_ui()
        
        # Load initial batch
        Clock.schedule_once(lambda dt: self._load_next_batch(), 0.1)
    
    def _build_ui(self):
        """Build the scrollable list UI"""
        # Create scroll view
        self.scroll_view = ScrollView()
        
        # Create items container
        self.items_container = BoxLayout(
            orientation='vertical',
            spacing=2,
            size_hint_y=None
        )
        self.items_container.bind(minimum_height=self.items_container.setter('height'))
        
        self.scroll_view.add_widget(self.items_container)
        
        # Bind scroll events
        self.scroll_view.bind(scroll_y=self._on_scroll)
        
        self.add_widget(self.scroll_view)
    
    def _on_scroll(self, scroll_view, scroll_y):
        """Handle scroll events to trigger loading more items"""
        # Check if we're near the bottom (within 20% of the bottom)
        if scroll_y <= 0.2 and not self.loading and self.has_more:
            self._load_next_batch()
    
    def _load_next_batch(self):
        """Load the next batch of items"""
        if self.loading or not self.has_more:
            return
        
        self.loading = True
        
        # Show loading indicator
        self._add_loading_indicator()
        
        # Load items in background thread
        def load_items():
            try:
                start_index = self.current_batch * self.items_per_batch
                new_items = self.item_loader(start_index, self.items_per_batch)
                
                # Schedule UI update on main thread
                Clock.schedule_once(lambda dt: self._on_items_loaded(new_items))
                
            except Exception as e:
                print(f"Error loading items: {e}")
                Clock.schedule_once(lambda dt: self._on_load_error(e))
        
        thread = threading.Thread(target=load_items)
        thread.daemon = True
        thread.start()
    
    def _on_items_loaded(self, new_items: List[Any]):
        """Handle successfully loaded items"""
        self.loading = False
        self._remove_loading_indicator()
        
        if not new_items:
            self.has_more = False
            return
        
        # Add new items to our list
        self.items.extend(new_items)
        
        # Render new items
        for item in new_items:
            try:
                widget = self.item_renderer(item)
                self.items_container.add_widget(widget)
                self.rendered_items.append(widget)
            except Exception as e:
                print(f"Error rendering item: {e}")
        
        self.current_batch += 1
        
        # Check if we got fewer items than requested (might be the last batch)
        if len(new_items) < self.items_per_batch:
            self.has_more = False
    
    def _on_load_error(self, error):
        """Handle loading errors"""
        self.loading = False
        self._remove_loading_indicator()
        print(f"Failed to load items: {error}")
    
    def _add_loading_indicator(self):
        """Add loading indicator to the bottom of the list"""
        if not hasattr(self, 'loading_indicator'):
            from ..atoms.labels import CaptionLabel
            self.loading_indicator = CaptionLabel(
                text="Loading more items...",
                size_hint_y=None,
                height=40
            )
        
        if self.loading_indicator not in self.items_container.children:
            self.items_container.add_widget(self.loading_indicator)
    
    def _remove_loading_indicator(self):
        """Remove loading indicator"""
        if hasattr(self, 'loading_indicator') and self.loading_indicator in self.items_container.children:
            self.items_container.remove_widget(self.loading_indicator)
    
    def clear_items(self):
        """Clear all items and reset the list"""
        self.items.clear()
        self.rendered_items.clear()
        self.items_container.clear_widgets()
        self.current_batch = 0
        self.has_more = True
        self.loading = False
    
    def refresh(self):
        """Refresh the list from the beginning"""
        self.clear_items()
        Clock.schedule_once(lambda dt: self._load_next_batch(), 0.1)
    
    def get_all_items(self) -> List[Any]:
        """Get all loaded items"""
        return self.items.copy()

