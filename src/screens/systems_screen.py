"""
Systems Screen
Main screen for selecting gaming systems
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from components.system_selector import SystemSelector
from typing import List, Dict, Any


class SystemsScreen(Screen):
    """Screen for selecting gaming systems"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'systems'
        
        # Create main layout
        layout = BoxLayout(orientation='vertical')
        
        # Add system selector component
        self.system_selector = SystemSelector()
        layout.add_widget(self.system_selector)
        
        self.add_widget(layout)
    
    def setup_navigation(self, screen_manager, app_reference):
        """Setup navigation and app reference"""
        self.system_selector.setup_navigation(screen_manager, app_reference)
    
    def set_systems_data(self, systems_data: List[Dict[str, Any]]):
        """Set the systems data for the selector"""
        self.system_selector.set_systems_data(systems_data)
    
    def on_enter(self):
        """Called when screen is entered"""
        # Refresh systems data if needed
        pass
    
    def on_leave(self):
        """Called when screen is left"""
        pass