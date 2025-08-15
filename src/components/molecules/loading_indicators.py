"""
Loading Indicator Molecules
Combines loading atoms with labels and containers
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from typing import Optional, Callable
import threading
import uuid

from ..atoms.labels import BodyLabel, CaptionLabel
from ..atoms.loading_animations import SpinnerAtom, PulseAtom, DotsAtom, ProgressRingAtom, WaveAtom


class LoadingIndicator(BoxLayout):
    """
    Complete loading indicator molecule
    Combines loading animation with text
    """
    
    def __init__(self, text: str = "Loading...", 
                 animation_type: str = "spinner",
                 show_progress: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 10
        self.size_hint = (None, None)
        self.size = (250, 120)
        
        self.animation_type = animation_type
        self.show_progress = show_progress
        
        # Create text label first (at top)
        self.label = BodyLabel(
            text=text,
            size_hint_y=None,
            height=30,
            halign='center',
            valign='middle'
        )
        self.add_widget(self.label)
        
        # Create animation widget
        self._create_animation_widget()
        
        # Optional progress indicator
        if show_progress:
            self.progress_ring = ProgressRingAtom()
            progress_container = BoxLayout(size_hint_y=None, height=60)
            progress_container.add_widget(BoxLayout())  # Left spacer
            progress_container.add_widget(self.progress_ring)
            progress_container.add_widget(BoxLayout())  # Right spacer
            self.add_widget(progress_container)
    
    def _create_animation_widget(self):
        """Create the appropriate animation widget"""
        # Container for animation
        animation_container = BoxLayout(size_hint_y=None, height=50)
        
        # Create animation based on type
        if self.animation_type == "spinner":
            self.animation_widget = SpinnerAtom()
        elif self.animation_type == "pulse":
            self.animation_widget = PulseAtom()
        elif self.animation_type == "dots":
            self.animation_widget = DotsAtom()
        elif self.animation_type == "wave":
            self.animation_widget = WaveAtom()
        else:
            self.animation_widget = SpinnerAtom()  # Default
        
        # Center the animation
        animation_container.add_widget(BoxLayout())  # Left spacer
        animation_container.add_widget(self.animation_widget)
        animation_container.add_widget(BoxLayout())  # Right spacer
        
        self.add_widget(animation_container)
    
    def start_loading(self, text: Optional[str] = None):
        """Start the loading animation"""
        if text:
            self.label.text = text
        
        # Start appropriate animation
        if hasattr(self.animation_widget, 'start_spinning'):
            self.animation_widget.start_spinning()
        elif hasattr(self.animation_widget, 'start_pulsing'):
            self.animation_widget.start_pulsing()
        elif hasattr(self.animation_widget, 'start_animating'):
            self.animation_widget.start_animating()
        elif hasattr(self.animation_widget, 'start_wave'):
            self.animation_widget.start_wave()
    
    def stop_loading(self):
        """Stop the loading animation"""
        # Stop appropriate animation
        if hasattr(self.animation_widget, 'stop_spinning'):
            self.animation_widget.stop_spinning()
        elif hasattr(self.animation_widget, 'stop_pulsing'):
            self.animation_widget.stop_pulsing()
        elif hasattr(self.animation_widget, 'stop_animating'):
            self.animation_widget.stop_animating()
        elif hasattr(self.animation_widget, 'stop_wave'):
            self.animation_widget.stop_wave()
    
    def update_text(self, text: str):
        """Update the loading text"""
        self.label.text = text
    
    def update_progress(self, value: float):
        """Update progress (0.0 to 1.0)"""
        if hasattr(self, 'progress_ring'):
            self.progress_ring.set_progress(value)


class LoadingModal(Popup):
    """
    Modal loading dialog molecule
    Combines popup with loading indicator
    """
    
    def __init__(self, title: str = "Loading", text: str = "Please wait...", 
                 animation_type: str = "dots", show_progress: bool = False, **kwargs):
        
        # Create loading indicator
        self.loading_indicator = LoadingIndicator(
            text=text,
            animation_type=animation_type,
            show_progress=show_progress
        )
        
        # Initialize popup with better styling
        super().__init__(
            title=title,
            title_color=(1, 1, 1, 1),
            title_size='16sp',
            content=self.loading_indicator,
            size_hint=(None, None),
            size=(320, 220),
            auto_dismiss=False,
            separator_color=(0.3, 0.6, 1.0, 1),
            separator_height='2dp',
            **kwargs
        )
    
    def start_loading(self, text: Optional[str] = None):
        """Start loading and show modal"""
        self.loading_indicator.start_loading(text)
        self.open()
    
    def stop_loading(self):
        """Stop loading and hide modal"""
        self.loading_indicator.stop_loading()
        self.dismiss()
    
    def update_text(self, text: str):
        """Update loading text"""
        self.loading_indicator.update_text(text)
    
    def update_progress(self, value: float):
        """Update progress value"""
        self.loading_indicator.update_progress(value)


class InlineLoadingIndicator(BoxLayout):
    """
    Inline loading indicator molecule
    For embedding in other components without modal
    """
    
    def __init__(self, text: str = "Loading...", 
                 animation_type: str = "dots", compact: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 10
        self.size_hint_y = None
        self.height = 30 if compact else 50
        
        # Create compact animation
        if animation_type == "dots":
            self.animation_widget = DotsAtom()
            self.animation_widget.size = (60, 15) if compact else (80, 20)
        elif animation_type == "spinner":
            self.animation_widget = SpinnerAtom()
            self.animation_widget.size = (20, 20) if compact else (30, 30)
        else:
            self.animation_widget = SpinnerAtom()
            self.animation_widget.size = (20, 20) if compact else (30, 30)
        
        self.add_widget(self.animation_widget)
        
        # Create text label
        self.label = CaptionLabel(text=text) if compact else BodyLabel(text=text)
        self.add_widget(self.label)
    
    def start_loading(self, text: Optional[str] = None):
        """Start the loading animation"""
        if text:
            self.label.text = text
        
        if hasattr(self.animation_widget, 'start_spinning'):
            self.animation_widget.start_spinning()
        elif hasattr(self.animation_widget, 'start_animating'):
            self.animation_widget.start_animating()
    
    def stop_loading(self):
        """Stop the loading animation"""
        if hasattr(self.animation_widget, 'stop_spinning'):
            self.animation_widget.stop_spinning()
        elif hasattr(self.animation_widget, 'stop_animating'):
            self.animation_widget.stop_animating()
    
    def update_text(self, text: str):
        """Update the loading text"""
        self.label.text = text


class AsyncTaskManager:
    """
    Manages asynchronous tasks with loading indicators
    Uses the new atomic loading components
    """
    
    def __init__(self):
        self.active_tasks = {}
    
    def run_task(
        self,
        task_func: Callable,
        callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
        loading_text: str = "Loading...",
        show_modal: bool = True,
        animation_type: str = "dots",
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Run an asynchronous task with loading indicator
        
        Args:
            task_func: Function to run asynchronously
            callback: Function to call on success
            error_callback: Function to call on error
            loading_text: Text to show during loading
            show_modal: Whether to show loading modal
            animation_type: Type of animation ("spinner", "pulse", "dots", "wave")
            progress_callback: Callback for progress updates
            
        Returns:
            Task ID for tracking
        """
        task_id = str(uuid.uuid4())
        
        # Create loading modal if needed
        modal = None
        if show_modal:
            modal = LoadingModal(
                text=loading_text,
                animation_type=animation_type,
                show_progress=progress_callback is not None
            )
            modal.start_loading()
            self.active_tasks[task_id] = modal
        
        def task_wrapper():
            try:
                # Run the task
                if progress_callback:
                    result = task_func(progress_callback)
                else:
                    result = task_func()
                
                # Schedule callback on main thread
                Clock.schedule_once(lambda dt: self._handle_success(task_id, result, callback, modal))
                
            except Exception as e:
                # Schedule error callback on main thread
                Clock.schedule_once(lambda dt: self._handle_error(task_id, e, error_callback, modal))
        
        # Start task in background thread
        thread = threading.Thread(target=task_wrapper)
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _handle_success(self, task_id: str, result, callback: Optional[Callable], modal: Optional[LoadingModal]):
        """Handle successful task completion"""
        if modal:
            modal.stop_loading()
            self.active_tasks.pop(task_id, None)
        
        if callback:
            callback(result)
    
    def _handle_error(self, task_id: str, error: Exception, error_callback: Optional[Callable], modal: Optional[LoadingModal]):
        """Handle task error"""
        if modal:
            modal.stop_loading()
            self.active_tasks.pop(task_id, None)
        
        if error_callback:
            error_callback(error)
    
    def cancel_task(self, task_id: str):
        """Cancel a task by ID"""
        if task_id in self.active_tasks:
            modal = self.active_tasks.pop(task_id)
            if modal:
                modal.stop_loading()
    
    def cancel_all_tasks(self):
        """Cancel all active tasks"""
        for modal in self.active_tasks.values():
            if modal:
                modal.stop_loading()
        self.active_tasks.clear()


# Global task manager instance
task_manager = AsyncTaskManager()
