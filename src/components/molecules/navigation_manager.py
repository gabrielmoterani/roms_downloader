"""
Navigation Manager Molecule
Handles navigation between screens with proper transitions and history
"""

from kivy.uix.screenmanager import ScreenManager
from typing import List, Optional, Callable, Dict, Any
from ..atoms.transitions import AppTransitions


class NavigationManager:
    """
    Manages navigation state, history, and transitions between screens
    """
    
    def __init__(self, screen_manager: ScreenManager):
        self.screen_manager = screen_manager
        self.navigation_history: List[str] = []
        self.navigation_callbacks: Dict[str, List[Callable]] = {}
        
        # Track current screen
        if hasattr(screen_manager, 'current'):
            self.navigation_history.append(screen_manager.current)
    
    def navigate_to(self, screen_name: str, transition_type: str = 'forward', 
                   clear_history: bool = False, callback: Optional[Callable] = None):
        """
        Navigate to a screen with appropriate transition
        
        Args:
            screen_name: Name of the target screen
            transition_type: Type of transition ('forward', 'back', 'modal', 'fade')
            clear_history: Whether to clear navigation history
            callback: Optional callback to execute after navigation
        """
        if not self._screen_exists(screen_name):
            print(f"Warning: Screen '{screen_name}' does not exist")
            return False
        
        # Set appropriate transition
        self._set_transition(transition_type)
        
        # Update history
        if clear_history:
            self.navigation_history.clear()
        
        # Add to history if not going back
        if transition_type != 'back' and screen_name not in self.navigation_history:
            self.navigation_history.append(screen_name)
        
        # Navigate
        current_screen = self.screen_manager.current
        self.screen_manager.current = screen_name
        
        # Execute callback
        if callback:
            callback(current_screen, screen_name)
        
        # Fire navigation event callbacks
        self._fire_navigation_callbacks(current_screen, screen_name)
        
        print(f"Navigated: {current_screen} → {screen_name} (transition: {transition_type})")
        return True
    
    def go_back(self, callback: Optional[Callable] = None) -> bool:
        """
        Navigate back to the previous screen in history
        """
        if len(self.navigation_history) <= 1:
            print("Cannot go back: No previous screen in history")
            return False
        
        # Remove current screen from history
        self.navigation_history.pop()
        
        # Get previous screen
        previous_screen = self.navigation_history[-1]
        
        # Navigate with back transition
        return self.navigate_to(previous_screen, 'back', callback=callback)
    
    def navigate_to_root(self, root_screen: str = 'systems', callback: Optional[Callable] = None):
        """Navigate to root screen and clear history"""
        return self.navigate_to(root_screen, 'fade', clear_history=True, callback=callback)
    
    def can_go_back(self) -> bool:
        """Check if back navigation is possible"""
        return len(self.navigation_history) > 1
    
    def get_current_screen(self) -> str:
        """Get current screen name"""
        return self.screen_manager.current
    
    @property
    def current_screen(self) -> str:
        """Property to access current screen name"""
        return self.screen_manager.current
    
    def get_previous_screen(self) -> Optional[str]:
        """Get previous screen name"""
        if len(self.navigation_history) >= 2:
            return self.navigation_history[-2]
        return None
    
    def get_navigation_history(self) -> List[str]:
        """Get navigation history"""
        return self.navigation_history.copy()
    
    def add_navigation_callback(self, callback: Callable, event_type: str = 'any'):
        """
        Add callback to be executed on navigation events
        
        Args:
            callback: Function to call with (from_screen, to_screen) parameters
            event_type: Type of navigation event ('any', 'forward', 'back')
        """
        if event_type not in self.navigation_callbacks:
            self.navigation_callbacks[event_type] = []
        self.navigation_callbacks[event_type].append(callback)
    
    def remove_navigation_callback(self, callback: Callable, event_type: str = 'any'):
        """Remove navigation callback"""
        if event_type in self.navigation_callbacks:
            if callback in self.navigation_callbacks[event_type]:
                self.navigation_callbacks[event_type].remove(callback)
    
    def _set_transition(self, transition_type: str):
        """Set the appropriate transition based on type"""
        transition_map = {
            'forward': AppTransitions.get_forward_transition(),
            'back': AppTransitions.get_back_transition(),
            'modal': AppTransitions.get_modal_transition(),
            'modal_close': AppTransitions.get_modal_close_transition(),
            'fade': AppTransitions.get_fade_transition()
        }
        
        transition = transition_map.get(transition_type, AppTransitions.get_forward_transition())
        self.screen_manager.transition = transition
    
    def _screen_exists(self, screen_name: str) -> bool:
        """Check if screen exists in screen manager"""
        return any(screen.name == screen_name for screen in self.screen_manager.screens)
    
    def _fire_navigation_callbacks(self, from_screen: str, to_screen: str):
        """Fire navigation event callbacks"""
        # Fire 'any' callbacks
        for callback in self.navigation_callbacks.get('any', []):
            try:
                callback(from_screen, to_screen)
            except Exception as e:
                print(f"Error in navigation callback: {e}")
        
        # Fire specific event callbacks based on navigation direction
        if len(self.navigation_history) >= 2 and self.navigation_history[-2] == to_screen:
            # Going back
            event_type = 'back'
        else:
            # Going forward
            event_type = 'forward'
        
        for callback in self.navigation_callbacks.get(event_type, []):
            try:
                callback(from_screen, to_screen)
            except Exception as e:
                print(f"Error in {event_type} navigation callback: {e}")


class NavigationMixin:
    """
    Mixin class to add navigation capabilities to screens
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.navigation_manager: Optional[NavigationManager] = None
    
    def set_navigation_manager(self, nav_manager: NavigationManager):
        """Set the navigation manager for this screen"""
        self.navigation_manager = nav_manager
    
    def navigate_to(self, screen_name: str, transition_type: str = 'forward'):
        """Navigate to another screen"""
        if self.navigation_manager:
            return self.navigation_manager.navigate_to(screen_name, transition_type)
        else:
            print("Warning: No navigation manager set")
            return False
    
    def go_back(self):
        """Go back to previous screen"""
        if self.navigation_manager:
            return self.navigation_manager.go_back()
        else:
            print("Warning: No navigation manager set")
            return False
    
    def can_go_back(self) -> bool:
        """Check if can go back"""
        if self.navigation_manager:
            return self.navigation_manager.can_go_back()
        return False
