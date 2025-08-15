"""
Settings Screen
Screen for application settings and configuration
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from components.settings_panel import SettingsPanel


class SettingsScreen(Screen):
    """Screen for application settings"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'
        
        # Create main layout
        layout = BoxLayout(orientation='vertical')
        
        # Add settings panel component
        self.settings_panel = SettingsPanel()
        layout.add_widget(self.settings_panel)
        
        self.add_widget(layout)
    
    def setup_navigation(self, screen_manager, app_reference):
        """Setup navigation and app reference"""
        self.settings_panel.setup_navigation(screen_manager, app_reference)
    
    def on_enter(self):
        """Called when screen is entered"""
        # Load current settings
        pass
    
    def on_leave(self):
        """Called when screen is left"""
        # Auto-save settings if needed
        pass