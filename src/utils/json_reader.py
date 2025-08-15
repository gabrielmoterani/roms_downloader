"""
JSON Reader Utility
Handles reading and parsing JSON configuration files like download.json
"""

import json
import os
from typing import List, Dict, Any, Optional


class JSONReader:
    """Utility class for reading and parsing JSON files"""
    
    def __init__(self):
        self.cached_data = {}
    
    def load_json(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load JSON data from file
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Parsed JSON data as list of dictionaries
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is malformed
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        # Check if we have cached data and file hasn't changed
        if file_path in self.cached_data:
            file_mtime = os.path.getmtime(file_path)
            if self.cached_data[file_path]['mtime'] == file_mtime:
                return self.cached_data[file_path]['data']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cache the data with modification time
            self.cached_data[file_path] = {
                'data': data,
                'mtime': os.path.getmtime(file_path)
            }
            
            return data
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e}")
    
    def get_systems(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get list of gaming systems from download.json
        
        Args:
            file_path: Path to download.json
            
        Returns:
            List of system configurations
        """
        data = self.load_json(file_path)
        
        # Filter out systems that are marked as list_systems
        systems = [system for system in data if not system.get('list_systems', False)]
        
        return systems
    
    def get_system_by_name(self, file_path: str, system_name: str) -> Optional[Dict[str, Any]]:
        """
        Get specific system configuration by name
        
        Args:
            file_path: Path to download.json
            system_name: Name of the system to find
            
        Returns:
            System configuration or None if not found
        """
        systems = self.get_systems(file_path)
        
        for system in systems:
            if system.get('name') == system_name:
                return system
        
        return None
    
    def get_nintendo_switch_config(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get Nintendo Switch specific configuration
        
        Args:
            file_path: Path to download.json
            
        Returns:
            Nintendo Switch system config or None
        """
        return self.get_system_by_name(file_path, "Nintendo Switch")
    
    def get_systems_requiring_nsz(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get systems that require NSZ decompression
        
        Args:
            file_path: Path to download.json
            
        Returns:
            List of systems with should_decompress_nsz flag
        """
        systems = self.get_systems(file_path)
        
        nsz_systems = []
        for system in systems:
            if system.get('should_decompress_nsz', False):
                nsz_systems.append(system)
        
        return nsz_systems
    
    def validate_system_config(self, system: Dict[str, Any]) -> bool:
        """
        Validate that a system configuration has required fields
        
        Args:
            system: System configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['name', 'url', 'file_format', 'roms_folder']
        
        for field in required_fields:
            if field not in system:
                return False
        
        # Validate file_format is a list
        if not isinstance(system['file_format'], list):
            return False
        
        return True
    
    def clear_cache(self):
        """Clear all cached JSON data"""
        self.cached_data.clear()