"""
System Selector Component
UI component for selecting gaming systems
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.clock import Clock
from typing import List, Dict, Any, Optional, Callable


class SystemCard(BoxLayout):
    """Individual system card widget"""
    
    def __init__(self, system_data: Dict[str, Any], on_select: Callable = None, **kwargs):
        super().__init__(**kwargs)
        self.system_data = system_data
        self.on_select = on_select
        
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 120
        self.spacing = 5
        self.padding = [10, 10, 10, 10]
        
        # System name
        name_label = Label(
            text=system_data.get('name', 'Unknown System'),
            font_size='16sp',
            text_size=(None, None),
            halign='center',
            valign='middle',
            size_hint_y=0.4
        )
        self.add_widget(name_label)
        
        # System info
        rom_folder = system_data.get('roms_folder', 'N/A')
        file_formats = ', '.join(system_data.get('file_format', []))
        
        info_text = f"Folder: {rom_folder}\nFormats: {file_formats}"
        info_label = Label(
            text=info_text,
            font_size='12sp',
            text_size=(None, None),
            halign='center',
            valign='middle',
            size_hint_y=0.4
        )
        self.add_widget(info_label)
        
        # Select button
        select_btn = Button(
            text='Browse Games',
            size_hint_y=0.2,
            font_size='14sp'
        )
        select_btn.bind(on_press=self._on_select)
        self.add_widget(select_btn)
        
        # Style the card
        self.canvas.before.clear()
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.2, 0.2, 0.2, 1)  # Dark gray background
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, *args):
        """Update the background rectangle when position/size changes"""
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def _on_select(self, button):
        """Handle system selection"""
        if self.on_select:
            self.on_select(self.system_data)


class SystemSelector(BoxLayout):
    """Main system selector component"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = [20, 20, 20, 20]
        
        self.systems_data = []
        self.navigation_callback = None
        self.app_reference = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the user interface"""
        # Title
        title_label = Label(
            text='Select Gaming System',
            font_size='24sp',
            size_hint_y=None,
            height=50,
            color=(1, 1, 1, 1)
        )
        self.add_widget(title_label)
        
        # Instructions
        instructions = Label(
            text='Choose a gaming system to browse available games',
            font_size='14sp',
            size_hint_y=None,
            height=30,
            color=(0.7, 0.7, 0.7, 1)
        )
        self.add_widget(instructions)
        
        # Systems scroll view
        self.scroll_view = ScrollView()
        self.systems_layout = GridLayout(
            cols=2,
            spacing=10,
            size_hint_y=None,
            padding=[0, 10, 0, 10]
        )
        self.systems_layout.bind(minimum_height=self.systems_layout.setter('height'))
        
        self.scroll_view.add_widget(self.systems_layout)
        self.add_widget(self.scroll_view)
        
        # Bottom buttons
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=10
        )
        
        settings_btn = Button(
            text='Settings',
            size_hint_x=0.3,
            font_size='16sp'
        )
        settings_btn.bind(on_press=self._go_to_settings)
        button_layout.add_widget(settings_btn)
        
        # Spacer
        button_layout.add_widget(Label())
        
        refresh_btn = Button(
            text='Refresh',
            size_hint_x=0.3,
            font_size='16sp'
        )
        refresh_btn.bind(on_press=self._refresh_systems)
        button_layout.add_widget(refresh_btn)
        
        self.add_widget(button_layout)
    
    def set_systems_data(self, systems_data: List[Dict[str, Any]]):
        """Set the systems data and refresh the display"""
        self.systems_data = systems_data
        self._populate_systems()
    
    def _populate_systems(self):
        """Populate the systems layout with system cards"""
        self.systems_layout.clear_widgets()
        
        if not self.systems_data:
            no_systems_label = Label(
                text='No gaming systems available.\nCheck your configuration.',
                font_size='16sp',
                halign='center',
                valign='middle',
                color=(1, 0.5, 0.5, 1)
            )
            self.systems_layout.add_widget(no_systems_label)
            return
        
        # Filter out systems marked as list_systems or hidden
        visible_systems = [
            system for system in self.systems_data 
            if not system.get('list_systems', False)
        ]
        
        for system in visible_systems:
            card = SystemCard(
                system_data=system,
                on_select=self._on_system_selected
            )
            self.systems_layout.add_widget(card)
    
    def _on_system_selected(self, system_data: Dict[str, Any]):
        """Handle when a system is selected"""
        print(f"Selected system: {system_data.get('name')}")
        
        if self.navigation_callback:
            # Switch to games screen and pass system data
            self.navigation_callback('games', system_data)
    
    def _go_to_settings(self, button):
        """Navigate to settings screen"""
        if self.navigation_callback:
            self.navigation_callback('settings')
    
    def _refresh_systems(self, button):
        """Refresh the systems list"""
        if self.app_reference:
            # Reload systems data from the app
            self.app_reference.load_systems_data()
            self.set_systems_data(self.app_reference.systems_data)
    
    def setup_navigation(self, screen_manager, app_reference):
        """Setup navigation callback and app reference"""
        self.app_reference = app_reference
        
        def navigate(screen_name, data=None):
            if screen_name == 'games' and data:
                # Pass system data to games screen
                games_screen = screen_manager.get_screen('games')
                games_screen.set_system_data(data)
                screen_manager.current = 'games'
            elif screen_name == 'settings':
                screen_manager.current = 'settings'
        
        self.navigation_callback = navigate