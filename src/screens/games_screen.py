"""
Games Screen
Modern games screen using atomic design principles and virtual scroll
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from components.organisms.game_browser import GameBrowser
from services.download_service import DownloadService
from utils.focus_manager import FocusManager
from typing import Dict, Any, List
import os


class GamesScreen(Screen):
    """Modern games screen using atomic design and virtual scroll"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'games'
        
        # Create main layout
        layout = BoxLayout(orientation='vertical')
        
        # Add modern game browser organism
        self.game_browser = GameBrowser()
        layout.add_widget(self.game_browser)
        
        self.add_widget(layout)
        
        # References
        self.screen_manager = None
        self.app_reference = None
        
        # Focus management - delegate to game browser
        self.focus_manager = None
        
        # Initialize download service
        self.download_service = DownloadService()
        self._setup_download_callbacks()
    
    def setup_navigation(self, screen_manager, app_reference):
        """Setup navigation and app reference"""
        self.screen_manager = screen_manager
        self.app_reference = app_reference
        
        # Set up callbacks
        self.game_browser.set_navigation_callback(self._navigate_back)
        self.game_browser.set_download_callback(self._handle_download)
    
    def set_system_data(self, system_data: Dict[str, Any]):
        """Set the system data for the browser"""
        self.game_browser.set_system_data(system_data)
    
    def navigate_up(self):
        """Handle up navigation - delegate to game browser"""
        if hasattr(self.game_browser, 'navigate_up'):
            self.game_browser.navigate_up()
    
    def navigate_down(self):
        """Handle down navigation - delegate to game browser"""
        if hasattr(self.game_browser, 'navigate_down'):
            self.game_browser.navigate_down()
    
    def navigate_left(self):
        """Handle left navigation - delegate to game browser"""
        if hasattr(self.game_browser, 'navigate_left'):
            self.game_browser.navigate_left()
    
    def navigate_right(self):
        """Handle right navigation - delegate to game browser"""
        if hasattr(self.game_browser, 'navigate_right'):
            self.game_browser.navigate_right()
    
    def select_current(self):
        """Handle select button - delegate to game browser"""
        if hasattr(self.game_browser, 'select_current'):
            self.game_browser.select_current()
    
    def _navigate_back(self):
        """Navigate back to systems screen"""
        if self.app_reference and hasattr(self.app_reference, 'navigation_manager'):
            self.app_reference.navigation_manager.go_back()
        elif self.screen_manager:
            self.screen_manager.current = 'systems'
    
    def _setup_download_callbacks(self):
        """Setup download service callbacks"""
        self.download_service.add_progress_callback(self._on_download_progress)
        self.download_service.add_status_callback(self._on_download_status)
    
    def _on_download_progress(self, task_id: str, task):
        """Handle download progress updates"""
        print(f"Download progress: {task.filename} - {task.progress:.1f}% ({task.speed/1024:.1f} KB/s)")
    
    def _on_download_status(self, task_id: str, status: str, message: str):
        """Handle download status updates"""
        print(f"Download status: {status} - {message}")
        
        if status == "completed":
            print(f"Download completed: {task_id}")
        elif status == "failed":
            print(f"Download failed: {task_id} - {message}")
        elif status == "decompressed":
            print(f"NSZ decompressed: {task_id} - {message}")
    
    def _handle_download(self, selected_games: List[Dict], system_data: Dict):
        """Handle download request"""
        print(f"Download requested for {len(selected_games)} games from {system_data.get('name', 'Unknown')}")
        
        # Get downloads directory from settings or use default
        downloads_dir = self._get_downloads_directory()
        
        try:
            # Add all selected games to download service
            task_ids = self.download_service.add_game_downloads(
                selected_games, 
                system_data, 
                downloads_dir
            )
            
            if task_ids:
                print(f"Added {len(task_ids)} downloads to queue")
                
                # Start all downloads
                started = self.download_service.start_all_downloads()
                print(f"Started {started} downloads")
                
                # Show download manager or status notification
                self._show_download_notification(len(task_ids))
                
            else:
                print("No downloads were added")
                
        except Exception as e:
            print(f"Error setting up downloads: {e}")
    
    def _get_downloads_directory(self) -> str:
        """Get the downloads directory from settings or use default"""
        # Try to get from app settings
        if (self.app_reference and 
            hasattr(self.app_reference, 'settings_manager') and
            self.app_reference.settings_manager):
            
            downloads_dir = self.app_reference.settings_manager.get_setting('downloads_directory')
            if downloads_dir and os.path.isdir(downloads_dir):
                return downloads_dir
        
        # Use default downloads directory
        default_downloads = os.path.join(os.path.expanduser("~"), "Downloads", "ROMs")
        os.makedirs(default_downloads, exist_ok=True)
        return default_downloads
    
    def _show_download_notification(self, count: int):
        """Show a notification about started downloads"""
        # This could show a popup or status message
        print(f"Started downloading {count} games. Check console for progress updates.")
    
    def on_enter(self):
        """Called when screen is entered"""
        # Could refresh games list if needed
        pass
    
    def on_leave(self):
        """Called when screen is left"""
        # Clear any ongoing downloads or operations
        pass