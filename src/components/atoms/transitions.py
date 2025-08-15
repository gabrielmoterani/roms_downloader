"""
Transition Atoms
Screen transition effects and animations
"""

from kivy.uix.screenmanager import SlideTransition, FadeTransition, SwapTransition, WipeTransition


class AppTransitions:
    """
    Centralized transition management for consistent app navigation
    """
    
    # Define transition types
    SLIDE_LEFT = SlideTransition(direction='left')
    SLIDE_RIGHT = SlideTransition(direction='right')
    SLIDE_UP = SlideTransition(direction='up')
    SLIDE_DOWN = SlideTransition(direction='down')
    
    FADE = FadeTransition()
    SWAP = SwapTransition()
    WIPE = WipeTransition()  # WipeTransition doesn't support direction parameter
    
    @staticmethod
    def get_forward_transition():
        """Get transition for forward navigation (deeper into app)"""
        return AppTransitions.SLIDE_LEFT
    
    @staticmethod
    def get_back_transition():
        """Get transition for back navigation (towards main menu)"""
        return AppTransitions.SLIDE_RIGHT
    
    @staticmethod
    def get_modal_transition():
        """Get transition for modal/settings screens"""
        return AppTransitions.SLIDE_UP
    
    @staticmethod
    def get_modal_close_transition():
        """Get transition for closing modal screens"""
        return AppTransitions.SLIDE_DOWN
    
    @staticmethod
    def get_fade_transition():
        """Get fade transition for subtle changes"""
        return AppTransitions.FADE
