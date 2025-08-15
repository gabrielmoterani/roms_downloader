"""
Game Browser Organism
Modern game browser using atomic design principles and virtual scroll
"""

from kivy.uix.boxlayout import BoxLayout
from typing import Dict, Any, List, Set, Optional, Callable
import requests
import re
from urllib.parse import unquote

from ..atoms.labels import HeadingLabel, StatusLabel
from ..atoms.buttons import PrimaryButton, SecondaryButton, NavigationButton
from ..molecules.search_bar import SearchBar
from ..molecules.virtual_scroll_list import VirtualScrollList
from ..molecules.game_item import GameItem
from ..loading_widget import task_manager
from utils.focus_manager import FocusManager


class GameBrowser(BoxLayout):
    """
    Modern game browser organism using atomic design and virtual scroll
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 15
        self.padding = [20, 20, 20, 20]
        
        # State
        self.system_data: Optional[Dict[str, Any]] = None
        self.all_games: List[Any] = []
        self.filtered_games: List[Any] = []
        self.selected_games: Set[str] = set()
        self.search_query = ""
        
        # Callbacks
        self.on_back: Optional[Callable] = None
        self.on_download: Optional[Callable] = None
        
        # Focus management for controller navigation
        self.focus_manager = FocusManager()
        self.focus_manager.bind(on_item_selected=self._on_item_selected)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the game browser UI using atomic components"""
        # Header section
        self._build_header()
        
        # Search section
        self._build_search()
        
        # Action controls
        self._build_controls()
        
        # Games list (infinite scroll)
        self._build_games_list()
        
        # Status section
        self._build_status()
    
    def _build_header(self):
        """Build header with title and back button"""
        header_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=60,
            spacing=15
        )
        
        # Back button
        self.back_btn = NavigationButton(
            text="← Back",
            size_hint_x=None,
            width=80,
            on_click=self._on_back_clicked
        )
        header_layout.add_widget(self.back_btn)
        
        # Title
        self.title_label = HeadingLabel(text="Games")
        header_layout.add_widget(self.title_label)
        
        self.add_widget(header_layout)
    
    def _build_search(self):
        """Build search section"""
        self.search_bar = SearchBar(
            placeholder="Search games...",
            on_text_change=self._on_search_change,
            on_clear=self._on_search_clear
        )
        self.add_widget(self.search_bar)
    
    def _build_controls(self):
        """Build action controls"""
        controls_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=10
        )
        
        # Selection controls
        self.select_all_btn = SecondaryButton(
            text="Select All Searched",
            size_hint_x=0.3,
            on_click=self._select_all_searched
        )
        controls_layout.add_widget(self.select_all_btn)
        
        self.clear_btn = SecondaryButton(
            text="Clear Selection",
            size_hint_x=0.3,
            on_click=self._clear_selection
        )
        controls_layout.add_widget(self.clear_btn)
        
        # Selection info
        self.selection_label = StatusLabel(
            text="0 games selected",
            size_hint_x=0.4
        )
        controls_layout.add_widget(self.selection_label)
        
        self.add_widget(controls_layout)
        
        # Download button (separate row for prominence)
        self.download_btn = PrimaryButton(
            text="Download Selected Games",
            on_click=self._on_download_clicked
        )
        self.add_widget(self.download_btn)
        
        # Add buttons to focus manager for controller navigation
        self._setup_focus_manager()
    
    def _setup_focus_manager(self):
        """Setup focus manager with all focusable elements"""
        self.focus_manager.clear()
        
        # Don't add buttons to focus manager - we'll focus on games instead
        # Navigation mode: games = navigate through game list, buttons = navigate through buttons
        self.navigation_mode = "games"  # Start in games mode
        self.current_game_index = 0
    
    def _on_item_selected(self, focus_manager, index: int, focusable_widget):
        """Handle item selection from focus manager"""
        focusable_widget.select()
    
    def navigate_up(self):
        """Handle up navigation - move through games"""
        if self.navigation_mode == "games" and self.filtered_games:
            self.current_game_index = max(0, self.current_game_index - 1)
            self._update_game_selection_visual()
            print(f"Game navigation: up to index {self.current_game_index}")
    
    def navigate_down(self):
        """Handle down navigation - move through games"""
        if self.navigation_mode == "games" and self.filtered_games:
            self.current_game_index = min(len(self.filtered_games) - 1, self.current_game_index + 1)
            self._update_game_selection_visual()
            print(f"Game navigation: down to index {self.current_game_index}")
    
    def navigate_left(self):
        """Handle left navigation - not used in game list"""
        pass
    
    def navigate_right(self):
        """Handle right navigation - not used in game list"""
        pass
    
    def select_current(self):
        """Handle select button press - toggle current game selection"""
        if self.navigation_mode == "games" and self.filtered_games:
            if 0 <= self.current_game_index < len(self.filtered_games):
                current_game = self.filtered_games[self.current_game_index]
                game_key = self._get_game_key(current_game)
                
                # Toggle selection
                if game_key in self.selected_games:
                    self.selected_games.remove(game_key)
                    print(f"Deselected game: {self._extract_game_name(current_game)}")
                else:
                    self.selected_games.add(game_key)
                    print(f"Selected game: {self._extract_game_name(current_game)}")
                
                self._update_selection_display()
                self._update_game_selection_visual()
    
    def start_action(self):
        """Handle start button press - quick download"""
        if self.selected_games:
            print("Start button: Starting download")
            self._on_download_clicked()
        else:
            print("Start button: No games selected")
    
    def _update_game_selection_visual(self):
        """Update visual indicator for currently highlighted game"""
        # TODO: Update virtual scroll list to highlight current game
        # For now, just ensure the current game is visible
        if hasattr(self.games_list, 'ensure_item_visible'):
            self.games_list.ensure_item_visible(self.current_game_index)
        
        print(f"Highlighting game {self.current_game_index + 1} of {len(self.filtered_games)}")
    
    def _build_games_list(self):
        """Build virtual scroll games list"""
        self.games_list = VirtualScrollList(
            item_height=60,  # Height of each game item
            buffer_size=5,   # Items to render above/below viewport
            item_loader=self._load_games_batch,
            item_renderer=self._render_game_item
        )
        self.add_widget(self.games_list)
    
    def _build_status(self):
        """Build status section"""
        self.status_label = StatusLabel(
            text="Ready",
            status_type="info"
        )
        self.add_widget(self.status_label)
    
    def set_system_data(self, system_data: Dict[str, Any]):
        """Set system data and load games"""
        self.system_data = system_data
        system_name = system_data.get('name', 'Unknown')
        self.title_label.text = f"Games: {system_name}"
        
        # Clear previous state
        self.all_games.clear()
        self.filtered_games.clear()
        self.selected_games.clear()
        self._update_selection_display()
        self.games_list.clear_all()
        
        # Load games
        self._load_all_games()
    
    def _load_all_games(self):
        """Load all games for the current system"""
        if not self.system_data:
            return
        
        system_name = self.system_data.get('name', 'Unknown')
        self.status_label.text = "Loading games..."
        
        # Use task manager for async loading with modal
        task_manager.run_task(
            task_func=self._fetch_games_sync,
            callback=self._on_all_games_loaded,
            error_callback=self._on_games_error,
            loading_text=f"Loading games for {system_name}...",
            show_modal=True
        )
    
    def _fetch_games_sync(self):
        """Fetch all games synchronously (runs in background)"""
        url = self.system_data.get('url', '')
        if not url:
            raise ValueError("No URL configured for this system")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse based on system type
        if 'api.ultranx.ru' in url:
            return self._parse_switch_api(response.json())
        else:
            return self._parse_html_directory(response.text)
    
    def _parse_switch_api(self, api_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Nintendo Switch API response"""
        games = []
        for title_id, game_info in api_data.items():
            games.append({
                'title_id': title_id,
                'name': game_info.get('name', 'Unknown Game'),
                'banner_url': game_info.get('banner_url', ''),
                'icon_url': game_info.get('icon_url', '')
            })
        return games
    
    def _parse_html_directory(self, html_content: str) -> List[Dict[str, str]]:
        """Parse HTML directory listing"""
        games = []
        regex_pattern = self.system_data.get('regex', r'<a href="([^"]+)">([^<]+)</a>')
        file_formats = self.system_data.get('file_format', [])
        
        try:
            if 'href' in regex_pattern and 'text' in regex_pattern:
                # Named groups
                matches = re.finditer(regex_pattern, html_content)
                for match in matches:
                    try:
                        href = match.group('href') if 'href' in match.groupdict() else ''
                        filename = match.group('text') if 'text' in match.groupdict() else ''
                        
                        if not filename and href:
                            filename = href
                        
                        if filename and any(filename.lower().endswith(fmt.lower()) for fmt in file_formats):
                            clean_filename = unquote(filename)
                            if clean_filename and clean_filename[0].isascii():
                                games.append({
                                    'filename': clean_filename,
                                    'href': href
                                })
                    except Exception as e:
                        print(f"Error processing match: {e}")
                        continue
            else:
                # Simple positional groups
                matches = re.findall(regex_pattern, html_content)
                for match in matches:
                    if len(match) >= 2:
                        href, filename = match[0], match[1]
                        if any(filename.lower().endswith(fmt.lower()) for fmt in file_formats):
                            clean_filename = unquote(filename)
                            if clean_filename and clean_filename[0].isascii():
                                games.append({
                                    'filename': clean_filename,
                                    'href': href
                                })
        except Exception as e:
            print(f"Error parsing HTML: {e}")
            raise e
        
        # Sort alphabetically
        games.sort(key=lambda x: x.get('filename', '').lower())
        return games
    
    def _on_all_games_loaded(self, games_data: List[Any]):
        """Handle successful games loading"""
        self.all_games = games_data
        self.filtered_games = games_data.copy()
        
        # Reset navigation
        self.current_game_index = 0
        
        # Set up the virtual scroll with the loaded data
        self.games_list.set_data_source(self._load_games_batch)
        
        count = len(self.all_games)
        self.status_label.text = f"Loaded {count} games"
        
        print(f"Successfully loaded {count} games for {self.system_data.get('name', 'Unknown')}")
    
    def _on_games_error(self, error):
        """Handle games loading error"""
        error_msg = str(error)
        self.status_label.text = f"Error loading games: {error_msg}"
        self.status_label.status_type = "error"
        
        self.all_games.clear()
        self.filtered_games.clear()
        self.games_list.clear_all()
    
    def _load_games_batch(self, start_index: int, count: int) -> List[Any]:
        """Load a batch of games for infinite scroll"""
        end_index = min(start_index + count, len(self.filtered_games))
        return self.filtered_games[start_index:end_index]
    
    def _render_game_item(self, game_data: Any) -> GameItem:
        """Render a single game item"""
        game_key = self._get_game_key(game_data)
        is_selected = game_key in self.selected_games
        
        # Create the game item
        game_item = GameItem(
            game_data=game_data,
            is_selected=is_selected,
            on_selection_change=self._on_game_selection_changed
        )
        
        # Ensure the selection state is correct (important for widget reuse)
        game_item.set_selected(is_selected)
        
        return game_item
    
    def _get_game_key(self, game_data: Any) -> str:
        """Get unique key for game data"""
        if isinstance(game_data, dict):
            if 'name' in game_data:
                return game_data['name']
            elif 'filename' in game_data:
                return game_data['filename']
            else:
                return str(game_data)
        else:
            return str(game_data)
    
    def _on_game_selection_changed(self, game_data: Any, is_selected: bool):
        """Handle game selection change"""
        game_key = self._get_game_key(game_data)
        
        if is_selected:
            self.selected_games.add(game_key)
        else:
            self.selected_games.discard(game_key)
        
        self._update_selection_display()
    
    def _update_selection_display(self):
        """Update selection count display"""
        count = len(self.selected_games)
        self.selection_label.text = f"{count} games selected"
        
        # Enable/disable download button
        self.download_btn.disabled = (count == 0)
    
    def _on_search_change(self, search_text: str):
        """Handle search text change"""
        self.search_query = search_text.lower().strip()
        self._apply_search_filter()
    
    def _on_search_clear(self):
        """Handle search clear"""
        self.search_query = ""
        self._apply_search_filter()
    
    def _apply_search_filter(self):
        """Apply search filter and refresh list"""
        if not self.search_query:
            self.filtered_games = self.all_games.copy()
        else:
            self.filtered_games = []
            for game in self.all_games:
                game_name = self._get_game_key(game).lower()
                if self.search_query in game_name:
                    self.filtered_games.append(game)
        
        # Update virtual scroll with new filtered data
        self.games_list.set_data_source(self._load_games_batch)
        print(f"Applied search filter: {len(self.filtered_games)} games match '{self.search_query}'")
    
    def _select_all_searched(self, button=None):
        """Select all games matching current search"""
        for game in self.filtered_games:
            game_key = self._get_game_key(game)
            self.selected_games.add(game_key)
        
        self._update_selection_display()
        # Refresh list to update visual state
        self.games_list.refresh()
    
    def _clear_selection(self, button=None):
        """Clear all selected games"""
        self.selected_games.clear()
        self._update_selection_display()
        # Refresh list to update visual state
        self.games_list.refresh()
    
    def _on_back_clicked(self, button=None):
        """Handle back button click"""
        if self.on_back:
            self.on_back()
    
    def _on_download_clicked(self, button=None):
        """Handle download button click"""
        if self.on_download and self.selected_games:
            # Get selected game data
            selected_game_data = []
            for game in self.filtered_games:
                game_key = self._get_game_key(game)
                if game_key in self.selected_games:
                    selected_game_data.append(game)
            
            self.on_download(selected_game_data, self.system_data)
    
    def set_navigation_callback(self, callback: Callable):
        """Set navigation callback"""
        self.on_back = callback
    
    def set_download_callback(self, callback: Callable):
        """Set download callback"""
        self.on_download = callback

