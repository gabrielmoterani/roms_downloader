"""
Controller mapping and input handling utilities for Kivy implementation
"""
import json
import os
from typing import Dict, Any, Optional, Tuple, Callable
from kivy.event import EventDispatcher
from kivy.clock import Clock


class ControllerManager(EventDispatcher):
    """Manages controller mapping and input handling"""
    
    __events__ = ('on_button_press', 'on_navigation', 'on_action')
    
    def __init__(self, config_dir: str = None):
        super().__init__()
        
        # Default config directory
        if config_dir is None:
            config_dir = os.path.expanduser("~/.config/simple_rom_downloader")
        
        self.config_dir = config_dir
        self.mapping_file = os.path.join(config_dir, "controller_mapping.json")
        
        # Controller mapping storage
        self.controller_mapping: Dict[str, Any] = {}
        
        # Essential buttons that must be mapped
        self.essential_buttons = [
            ("up", "D-pad UP"),
            ("down", "D-pad DOWN"), 
            ("left", "D-pad LEFT"),
            ("right", "D-pad RIGHT"),
            ("select", "SELECT/CONFIRM button (usually A)"),
            ("back", "BACK/CANCEL button (usually B)"),
            ("start", "START/MENU button"),
            ("detail", "DETAIL/SECONDARY button (usually Y)"),
            ("search", "SEARCH button (for game search)"),
            ("left_shoulder", "Left Shoulder button (L/LB)"),
            ("right_shoulder", "Right Shoulder button (R/RB)")
        ]
        
        # Input debouncing
        self.last_input_time = 0
        self.debounce_delay = 0.3  # 300ms debounce
        
        # Load existing mapping
        self.load_mapping()
    
    def load_mapping(self) -> bool:
        """Load controller mapping from file"""
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r') as f:
                    self.controller_mapping = json.load(f)
                print("Controller mapping loaded from file")
                return True
            else:
                print("No controller mapping found, will need to create new mapping")
                self.controller_mapping = {}
                return False
        except Exception as e:
            print(f"Failed to load controller mapping: {e}")
            self.controller_mapping = {}
            return False
    
    def save_mapping(self) -> bool:
        """Save controller mapping to file"""
        try:
            os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
            with open(self.mapping_file, 'w') as f:
                json.dump(self.controller_mapping, f, indent=2)
            print("Controller mapping saved")
            return True
        except Exception as e:
            print(f"Failed to save controller mapping: {e}")
            return False
    
    def needs_mapping(self) -> bool:
        """Check if controller mapping is needed"""
        essential_keys = [button[0] for button in self.essential_buttons]
        return not self.controller_mapping or not all(key in self.controller_mapping for key in essential_keys)
    
    def get_button_info(self, action: str) -> Optional[Any]:
        """Get button info for action"""
        return self.controller_mapping.get(action)
    
    def map_button(self, action: str, button_info: Any) -> None:
        """Map a button to an action"""
        current_time = Clock.get_time()
        
        # Debounce input
        if current_time - self.last_input_time < self.debounce_delay:
            return
            
        self.controller_mapping[action] = button_info
        self.last_input_time = current_time
        print(f"Mapped {action} to {button_info}")
    
    def input_matches_action(self, event_type: str, event_data: Dict[str, Any], action: str) -> bool:
        """Check if input event matches the mapped action"""
        button_info = self.get_button_info(action)
        if button_info is None:
            return False
        
        if event_type == 'joybuttondown':
            # Check regular button press
            return isinstance(button_info, int) and event_data.get('button') == button_info
        elif event_type == 'joyhatmotion':
            # Check D-pad/hat input
            if (isinstance(button_info, (tuple, list)) and 
                len(button_info) >= 3 and button_info[0] == "hat"):
                _, expected_x, expected_y = button_info[0:3]
                hat_value = event_data.get('value', (0, 0))
                return hat_value == (expected_x, expected_y)
        
        return False
    
    def process_input_event(self, event_type: str, event_data: Dict[str, Any]) -> Optional[str]:
        """Process input event and return matched action"""
        for action, _ in self.essential_buttons:
            if self.input_matches_action(event_type, event_data, action):
                self.dispatch('on_action', action, event_data)
                return action
        return None
    
    def on_button_press(self, *args):
        """Event handler for button press (override in subclass)"""
        pass
    
    def on_navigation(self, *args):
        """Event handler for navigation (override in subclass)"""
        pass
    
    def on_action(self, *args):
        """Event handler for action (override in subclass)"""
        pass
