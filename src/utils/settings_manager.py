"""
Settings Manager
Handles loading, saving, and managing application settings
"""

import os
import json
from typing import Dict, Any, Optional


class SettingsManager:
    """Manages application settings with file persistence"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize settings manager
        
        Args:
            config_dir: Directory to store config files. If None, auto-detect.
        """
        # Auto-detect environment and set paths
        self.dev_mode = os.getenv('DEV_MODE', 'false').lower() == 'true'
        
        if config_dir:
            self.config_dir = config_dir
        elif self.dev_mode:
            # Development mode - use project root
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            self.config_dir = script_dir
        else:
            # Production mode - use script directory
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.config_dir = script_dir
        
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.controller_mapping_file = os.path.join(self.config_dir, "controller_mapping.json")
        
        # Initialize default settings
        self._default_settings = self._get_default_settings()
        self._settings = self._default_settings.copy()
        
        # Load settings on initialization
        self.load_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings based on environment"""
        # Default paths based on environment
        if self.dev_mode:
            # Development mode - use local directories
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            default_work_dir = os.path.join(script_dir, "py_downloads")
            default_roms_dir = os.path.join(script_dir, "roms")
        elif os.path.exists("/userdata") and os.access("/userdata", os.W_OK):
            # Console environment with writable /userdata
            default_work_dir = "/userdata/py_downloads"
            default_roms_dir = "/userdata/roms"
        else:
            # Other environments - use home directory
            home_dir = os.path.expanduser("~")
            default_work_dir = os.path.join(home_dir, "Downloads", "py_downloads")
            default_roms_dir = os.path.join(home_dir, "Downloads", "roms")
        
        return {
            "enable_boxart": True,
            "view_type": "list",  # "list" or "grid"
            "usa_only": False,
            "work_dir": default_work_dir,
            "roms_dir": default_roms_dir,
            "downloads_directory": default_roms_dir,  # Main downloads directory
            "switch_keys_path": "",
            "should_unzip": True,  # Extract ZIP files after download
            "should_decompress_nsz": True,  # Decompress NSZ files to NSP
            "keep_archives": False,  # Keep original ZIP/NSZ files after extraction
            "system_settings": {}  # Per-system configuration
        }
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to handle new settings
                    self._settings = self._default_settings.copy()
                    self._settings.update(loaded_settings)
            else:
                # Create config file with defaults
                self.save_settings()
        except Exception as e:
            print(f"Failed to load settings, using defaults: {e}")
            self._settings = self._default_settings.copy()
        
        return self._settings
    
    def save_settings(self) -> bool:
        """Save current settings to config file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save settings: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        return self._settings.get(key, default)
    
    def set_setting(self, key: str, value: Any, save: bool = True) -> bool:
        """Set a specific setting value"""
        self._settings[key] = value
        if save:
            return self.save_settings()
        return True
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all current settings"""
        return self._settings.copy()
    
    def reset_to_defaults(self, save: bool = True) -> bool:
        """Reset all settings to default values"""
        self._settings = self._default_settings.copy()
        if save:
            return self.save_settings()
        return True
    
    def get_system_setting(self, system_name: str, setting_key: str, default: Any = None) -> Any:
        """Get a per-system setting"""
        system_settings = self._settings.get("system_settings", {})
        return system_settings.get(system_name, {}).get(setting_key, default)
    
    def set_system_setting(self, system_name: str, setting_key: str, value: Any, save: bool = True) -> bool:
        """Set a per-system setting"""
        if "system_settings" not in self._settings:
            self._settings["system_settings"] = {}
        if system_name not in self._settings["system_settings"]:
            self._settings["system_settings"][system_name] = {}
        
        self._settings["system_settings"][system_name][setting_key] = value
        
        if save:
            return self.save_settings()
        return True
    
    def is_system_hidden(self, system_name: str) -> bool:
        """Check if a system is hidden from main menu"""
        return self.get_system_setting(system_name, 'hidden', False)
    
    def set_system_hidden(self, system_name: str, hidden: bool, save: bool = True) -> bool:
        """Set whether a system is hidden from main menu"""
        return self.set_system_setting(system_name, 'hidden', hidden, save)
    
    def get_system_custom_folder(self, system_name: str) -> str:
        """Get custom ROM folder for a system"""
        return self.get_system_setting(system_name, 'custom_folder', '')
    
    def set_system_custom_folder(self, system_name: str, folder_path: str, save: bool = True) -> bool:
        """Set custom ROM folder for a system"""
        return self.set_system_setting(system_name, 'custom_folder', folder_path, save)
    
    def validate_paths(self) -> Dict[str, bool]:
        """Validate that configured paths exist and are accessible"""
        results = {}
        
        # Check work directory
        work_dir = self.get_setting("work_dir")
        try:
            if work_dir:
                os.makedirs(work_dir, exist_ok=True)
                results["work_dir"] = os.path.exists(work_dir) and os.access(work_dir, os.W_OK)
            else:
                results["work_dir"] = False
        except Exception:
            results["work_dir"] = False
        
        # Check ROMs directory
        roms_dir = self.get_setting("roms_dir")
        try:
            if roms_dir:
                os.makedirs(roms_dir, exist_ok=True)
                results["roms_dir"] = os.path.exists(roms_dir) and os.access(roms_dir, os.W_OK)
            else:
                results["roms_dir"] = False
        except Exception:
            results["roms_dir"] = False
        
        # Check Nintendo Switch keys path
        switch_keys = self.get_setting("switch_keys_path")
        if switch_keys:
            results["switch_keys_path"] = os.path.exists(switch_keys)
        else:
            results["switch_keys_path"] = True  # Optional setting
        
        return results
    
    def get_settings_display_list(self) -> list:
        """Get list of settings for display in UI"""
        settings_list = [
            {
                "name": "Enable Box-art Display",
                "key": "enable_boxart",
                "type": "boolean",
                "value": self.get_setting("enable_boxart")
            },
            {
                "name": "View Type",
                "key": "view_type",
                "type": "choice",
                "value": self.get_setting("view_type"),
                "choices": ["list", "grid"]
            },
            {
                "name": "USA Games Only",
                "key": "usa_only",
                "type": "boolean",
                "value": self.get_setting("usa_only")
            },
            {
                "name": "Work Directory",
                "key": "work_dir",
                "type": "path",
                "value": self.get_setting("work_dir")
            },
            {
                "name": "ROMs Directory",
                "key": "roms_dir",
                "type": "path",
                "value": self.get_setting("roms_dir")
            },
            {
                "name": "Nintendo Switch Keys",
                "key": "switch_keys_path",
                "type": "path",
                "value": self.get_setting("switch_keys_path")
            }
        ]
        return settings_list
