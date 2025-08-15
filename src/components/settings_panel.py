"""
Settings Panel Component
UI component for application settings management
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
import json
import os
from typing import Dict, Any, Callable


class SettingItem(BoxLayout):
    """Individual setting item widget"""
    
    def __init__(self, title: str, setting_type: str, value: Any = None, 
                 on_change: Callable = None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.setting_type = setting_type
        self.value = value
        self.on_change = on_change
        
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 60
        self.spacing = 10
        self.padding = [10, 10, 10, 10]
        
        # Title label
        title_label = Label(
            text=title,
            text_size=(None, None),
            halign='left',
            valign='middle',
            font_size='14sp',
            size_hint_x=0.6
        )
        self.add_widget(title_label)
        
        # Control widget based on type
        if setting_type == 'boolean':
            self.control = Switch(active=bool(value))
            self.control.bind(active=self._on_switch_change)
        elif setting_type == 'text':
            self.control = TextInput(
                text=str(value) if value else '',
                multiline=False,
                font_size='12sp'
            )
            self.control.bind(text=self._on_text_change)
        elif setting_type == 'file':
            # File path with browse button
            file_layout = BoxLayout(orientation='horizontal', spacing=5)
            
            self.control = TextInput(
                text=str(value) if value else '',
                multiline=False,
                font_size='12sp',
                size_hint_x=0.8
            )
            self.control.bind(text=self._on_text_change)
            file_layout.add_widget(self.control)
            
            browse_btn = Button(
                text='Browse',
                size_hint_x=0.2,
                font_size='12sp'
            )
            browse_btn.bind(on_press=self._browse_file)
            file_layout.add_widget(browse_btn)
            
            self.control = file_layout
        elif setting_type == 'directory':
            # Directory path with browse button
            dir_layout = BoxLayout(orientation='horizontal', spacing=5)
            
            self.text_input = TextInput(
                text=str(value) if value else '',
                multiline=False,
                font_size='12sp',
                size_hint_x=0.8
            )
            self.text_input.bind(text=self._on_text_change)
            dir_layout.add_widget(self.text_input)
            
            browse_btn = Button(
                text='Browse',
                size_hint_x=0.2,
                font_size='12sp'
            )
            browse_btn.bind(on_press=self._browse_directory)
            dir_layout.add_widget(browse_btn)
            
            self.control = dir_layout
        elif setting_type == 'action':
            self.control = Button(
                text=str(value) if value else 'Execute',
                font_size='12sp'
            )
            self.control.bind(on_press=self._on_action)
        else:
            # Default to label
            self.control = Label(
                text=str(value) if value else '',
                font_size='12sp'
            )
        
        self.control.size_hint_x = 0.4
        self.add_widget(self.control)
        
        # Style the item
        self.canvas.before.clear()
        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.15, 0.15, 0.15, 1)  # Dark background
            self.rect = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, *args):
        """Update the background rectangle"""
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def _on_switch_change(self, switch, active):
        """Handle switch toggle"""
        self.value = active
        if self.on_change:
            self.on_change(self.title, active)
    
    def _on_text_change(self, text_input, text):
        """Handle text input change"""
        self.value = text
        if self.on_change:
            self.on_change(self.title, text)
    
    def _on_action(self, button):
        """Handle action button press"""
        if self.on_change:
            self.on_change(self.title, "action")
    
    def _browse_file(self, button):
        """Open file browser"""
        content = BoxLayout(orientation='vertical')
        
        filechooser = FileChooserListView(
            path=os.path.expanduser('~'),
            filters=['*.keys', '*.*']
        )
        content.add_widget(filechooser)
        
        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        select_btn = Button(text='Select')
        cancel_btn = Button(text='Cancel')
        
        button_layout.add_widget(select_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='Select File',
            content=content,
            size_hint=(0.8, 0.8)
        )
        
        def on_select(btn):
            if filechooser.selection:
                if self.setting_type == 'file':
                    self.control.children[1].text = filechooser.selection[0]  # TextInput
                    self._on_text_change(None, filechooser.selection[0])
                elif self.setting_type == 'directory':
                    self.text_input.text = filechooser.selection[0]
                    self._on_text_change(None, filechooser.selection[0])
            popup.dismiss()
        
        def on_cancel(btn):
            popup.dismiss()
        
        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=on_cancel)
        
        popup.open()
    
    def _browse_directory(self, button):
        """Open directory browser"""
        self._browse_file(button)  # Reuse file browser for now
    
    def set_value(self, value):
        """Set the value programmatically"""
        self.value = value
        
        if self.setting_type == 'boolean' and hasattr(self.control, 'active'):
            self.control.active = bool(value)
        elif self.setting_type in ['text', 'file', 'directory']:
            if self.setting_type == 'file':
                self.control.children[1].text = str(value) if value else ''
            elif self.setting_type == 'directory':
                self.text_input.text = str(value) if value else ''
            else:
                self.control.text = str(value) if value else ''


class SettingsPanel(BoxLayout):
    """Main settings panel component"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = [20, 20, 20, 20]
        
        self.settings_data = {}
        self.navigation_callback = None
        self.app_reference = None
        self.settings_items = {}
        
        self._build_ui()
        self._load_default_settings()
    
    def _build_ui(self):
        """Build the user interface"""
        # Header
        header_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=10
        )
        
        back_btn = Button(
            text='← Back',
            size_hint_x=None,
            width=100,
            font_size='16sp'
        )
        back_btn.bind(on_press=self._go_back)
        header_layout.add_widget(back_btn)
        
        title_label = Label(
            text='Settings',
            font_size='20sp',
            halign='left',
            valign='middle'
        )
        header_layout.add_widget(title_label)
        
        self.add_widget(header_layout)
        
        # Settings scroll view
        self.scroll_view = ScrollView()
        self.settings_layout = GridLayout(
            cols=1,
            spacing=5,
            size_hint_y=None,
            padding=[0, 10, 0, 10]
        )
        self.settings_layout.bind(minimum_height=self.settings_layout.setter('height'))
        
        self.scroll_view.add_widget(self.settings_layout)
        self.add_widget(self.scroll_view)
        
        # Bottom buttons
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=10
        )
        
        save_btn = Button(
            text='Save Settings',
            size_hint_x=0.3,
            font_size='16sp'
        )
        save_btn.bind(on_press=self._save_settings)
        button_layout.add_widget(save_btn)
        
        # Spacer
        button_layout.add_widget(Label())
        
        reset_btn = Button(
            text='Reset to Defaults',
            size_hint_x=0.3,
            font_size='16sp'
        )
        reset_btn.bind(on_press=self._reset_settings)
        button_layout.add_widget(reset_btn)
        
        self.add_widget(button_layout)
        
        # Status label
        self.status_label = Label(
            text='Ready',
            size_hint_y=None,
            height=30,
            font_size='12sp',
            color=(0.7, 0.7, 0.7, 1)
        )
        self.add_widget(self.status_label)
    
    def _load_default_settings(self):
        """Load default settings configuration"""
        self.settings_data = {
            'enable_boxart': True,
            'view_type': 'list',
            'usa_only': False,
            'work_dir': os.path.expanduser('~/Downloads/rom_work'),
            'roms_dir': os.path.expanduser('~/Downloads/roms'),
            'switch_keys_path': '',
            'max_concurrent_downloads': 3,
            'auto_extract_zip': True,
            'auto_decompress_nsz': True
        }
        
        self._populate_settings()
    
    def _populate_settings(self):
        """Populate the settings UI"""
        self.settings_layout.clear_widgets()
        self.settings_items.clear()
        
        # Define settings configuration
        settings_config = [
            {
                'title': 'Enable Box Art Display',
                'key': 'enable_boxart',
                'type': 'boolean',
                'description': 'Show game thumbnails and box art'
            },
            {
                'title': 'View Type',
                'key': 'view_type', 
                'type': 'text',
                'description': 'Display mode: list or grid'
            },
            {
                'title': 'USA Games Only',
                'key': 'usa_only',
                'type': 'boolean',
                'description': 'Filter to show only USA region games'
            },
            {
                'title': 'Work Directory',
                'key': 'work_dir',
                'type': 'directory',
                'description': 'Temporary directory for downloads'
            },
            {
                'title': 'ROMs Directory',
                'key': 'roms_dir',
                'type': 'directory',
                'description': 'Final destination for ROM files'
            },
            {
                'title': 'Nintendo Switch Keys',
                'key': 'switch_keys_path',
                'type': 'file',
                'description': 'Path to Nintendo Switch prod.keys file'
            },
            {
                'title': 'Max Concurrent Downloads',
                'key': 'max_concurrent_downloads',
                'type': 'text',
                'description': 'Maximum number of simultaneous downloads'
            },
            {
                'title': 'Auto Extract ZIP Files',
                'key': 'auto_extract_zip',
                'type': 'boolean',
                'description': 'Automatically extract downloaded ZIP files'
            },
            {
                'title': 'Auto Decompress NSZ Files',
                'key': 'auto_decompress_nsz',
                'type': 'boolean',
                'description': 'Automatically decompress Nintendo Switch NSZ files'
            },
            {
                'title': 'Update from GitHub',
                'key': 'update_action',
                'type': 'action',
                'description': 'Download latest configuration from GitHub'
            }
        ]
        
        for setting_config in settings_config:
            key = setting_config['key']
            value = self.settings_data.get(key, '')
            
            if setting_config['type'] == 'action':
                value = 'Update Now'
            
            setting_item = SettingItem(
                title=setting_config['title'],
                setting_type=setting_config['type'],
                value=value,
                on_change=self._on_setting_change
            )
            
            self.settings_items[key] = setting_item
            self.settings_layout.add_widget(setting_item)
            
            # Add description label
            desc_label = Label(
                text=setting_config['description'],
                font_size='10sp',
                size_hint_y=None,
                height=20,
                color=(0.6, 0.6, 0.6, 1),
                halign='left',
                valign='middle'
            )
            self.settings_layout.add_widget(desc_label)
    
    def _on_setting_change(self, setting_name: str, value: Any):
        """Handle setting value change"""
        # Map display names to keys
        setting_key_map = {
            'Enable Box Art Display': 'enable_boxart',
            'View Type': 'view_type',
            'USA Games Only': 'usa_only',
            'Work Directory': 'work_dir',
            'ROMs Directory': 'roms_dir',
            'Nintendo Switch Keys': 'switch_keys_path',
            'Max Concurrent Downloads': 'max_concurrent_downloads',
            'Auto Extract ZIP Files': 'auto_extract_zip',
            'Auto Decompress NSZ Files': 'auto_decompress_nsz',
            'Update from GitHub': 'update_action'
        }
        
        key = setting_key_map.get(setting_name, setting_name)
        
        if key == 'update_action' and value == 'action':
            self._update_from_github()
        elif key == 'max_concurrent_downloads':
            try:
                value = int(value)
                if value < 1:
                    value = 1
                elif value > 10:
                    value = 10
            except ValueError:
                value = 3
            self.settings_data[key] = value
        else:
            self.settings_data[key] = value
        
        self.status_label.text = f"Changed: {setting_name}"
    
    def _save_settings(self, button):
        """Save settings to file"""
        try:
            config_path = os.path.join(os.path.expanduser('~'), '.rom_downloader_config.json')
            
            with open(config_path, 'w') as f:
                json.dump(self.settings_data, f, indent=2)
            
            self.status_label.text = "Settings saved successfully"
            
            # Apply settings to services
            if self.app_reference:
                download_service = self.app_reference.get_service('download_service')
                if download_service:
                    download_service.max_concurrent_downloads = self.settings_data.get('max_concurrent_downloads', 3)
                
                nsz_service = self.app_reference.get_service('nsz_service')
                if nsz_service:
                    keys_path = self.settings_data.get('switch_keys_path', '')
                    if keys_path:
                        nsz_service.set_keys_path(keys_path)
            
        except Exception as e:
            self.status_label.text = f"Error saving settings: {str(e)}"
    
    def _reset_settings(self, button):
        """Reset settings to defaults"""
        self._load_default_settings()
        self.status_label.text = "Settings reset to defaults"
    
    def _update_from_github(self):
        """Update configuration from GitHub"""
        self.status_label.text = "Updating from GitHub..."
        # This would implement the GitHub update functionality
        # For now, just show a placeholder message
        self.status_label.text = "GitHub update not implemented yet"
    
    def _go_back(self, button):
        """Go back to systems screen"""
        if self.navigation_callback:
            self.navigation_callback('systems')
    
    def setup_navigation(self, screen_manager, app_reference):
        """Setup navigation callback and app reference"""
        self.app_reference = app_reference
        
        def navigate(screen_name):
            screen_manager.current = screen_name
        
        self.navigation_callback = navigate
    
    def load_settings_from_file(self, config_path: str):
        """Load settings from configuration file"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings_data.update(saved_settings)
                    
                # Update UI
                for key, value in self.settings_data.items():
                    if key in self.settings_items:
                        self.settings_items[key].set_value(value)
                        
                self.status_label.text = "Settings loaded from file"
                
        except Exception as e:
            self.status_label.text = f"Error loading settings: {str(e)}"