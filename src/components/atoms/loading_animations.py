"""
Loading Animation Atoms
Basic animated loading components using Kivy animations
"""

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, PushMatrix, PopMatrix, Rotate
from typing import Optional


class SpinnerAtom(Widget):
    """
    Atomic spinning circle loader
    Uses the moving line technique from Kivy animation article
    """
    
    def __init__(self, size_hint=(None, None), size=(40, 40), color=(0.3, 0.6, 1.0, 1.0), **kwargs):
        super().__init__(**kwargs)
        self.size_hint = size_hint
        self.size = size
        self.color = color
        
        self.animation_event = None
        self.is_spinning = False
        self.spinner_offset = 0
        
        # Create graphics - simple moving arc
        with self.canvas:
            Color(*self.color)
            self.spinner_line = Line(width=4)
        
        self.bind(pos=self._update_graphics, size=self._update_graphics)
        # Trigger initial graphics update
        Clock.schedule_once(lambda dt: self._update_graphics(), 0.1)
    
    def _update_graphics(self, *args):
        """Update graphics when position/size changes"""
        if not self.canvas:
            return
            
        # Create spinning arc that moves around the circle
        radius = min(self.width, self.height) / 2 - 5
        center_x, center_y = self.center_x, self.center_y
        
        # Create arc from spinner_offset to spinner_offset + 120 degrees
        start_angle = self.spinner_offset
        end_angle = self.spinner_offset + 120
        
        self.spinner_line.circle = (center_x, center_y, radius, start_angle, end_angle)
    
    def start_spinning(self):
        """Start continuous spinning animation"""
        if self.is_spinning:
            return
        
        self.is_spinning = True
        # Use Clock.schedule_interval for smooth animation
        self.animation_event = Clock.schedule_interval(self._update_rotation, 1/60.0)  # 60 FPS
    
    def stop_spinning(self):
        """Stop spinning animation"""
        if self.animation_event:
            Clock.unschedule(self.animation_event)
            self.animation_event = None
        self.is_spinning = False
        self.spinner_offset = 0
        self._update_graphics()
    
    def _update_rotation(self, dt):
        """Update rotation angle during animation"""
        self.spinner_offset += 360 * dt * 2  # 2 rotations per second
        if self.spinner_offset >= 360:
            self.spinner_offset -= 360
        self._update_graphics()


class PulseAtom(Widget):
    """
    Atomic pulsing circle loader
    Uses scaling animation for breathing effect
    """
    
    def __init__(self, size_hint=(None, None), size=(30, 30), color=(0.3, 0.6, 1.0, 0.8), **kwargs):
        super().__init__(**kwargs)
        self.size_hint = size_hint
        self.size = size
        self.color = color
        
        self.animation = None
        self.is_pulsing = False
        self.scale = 1.0
        self.pulse_time = 0
        
        # Create graphics
        with self.canvas:
            Color(*self.color)
            self.circle = Ellipse(
                pos=(self.x + self.width/4, self.y + self.height/4),
                size=(self.width/2, self.height/2)
            )
        
        self.bind(pos=self._update_graphics, size=self._update_graphics)
    
    def _update_graphics(self, *args):
        """Update graphics when position/size changes"""
        size = min(self.width, self.height) * self.scale
        self.circle.pos = (
            self.center_x - size/2,
            self.center_y - size/2
        )
        self.circle.size = (size, size)
    
    def start_pulsing(self):
        """Start pulsing animation using Clock scheduling"""
        if self.is_pulsing:
            return
        
        self.is_pulsing = True
        self.pulse_time = 0
        # Use Clock.schedule_interval for smooth animation
        self.animation = Clock.schedule_interval(self._update_pulse, 1/60.0)  # 60 FPS
    
    def stop_pulsing(self):
        """Stop pulsing animation"""
        if self.animation:
            Clock.unschedule(self.animation)
            self.animation = None
        self.is_pulsing = False
        self.scale = 1.0
        self._update_graphics()
    
    def _update_pulse(self, dt):
        """Update pulse scale during animation"""
        self.pulse_time += dt * 2  # Speed factor
        import math
        # Create smooth pulsing using sine wave
        self.scale = 0.8 + 0.4 * (math.sin(self.pulse_time) + 1) / 2  # Scale between 0.8 and 1.2
        self._update_graphics()


class DotsAtom(BoxLayout):
    """
    Atomic three-dot loading animation
    Each dot animates in sequence using Clock scheduling
    """
    
    def __init__(self, color=(0.3, 0.6, 1.0, 1.0), **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 8
        self.size_hint = (None, None)
        self.size = (70, 20)
        self.color = color
        
        self.dots = []
        self.animation_event = None
        self.is_animating = False
        self.animation_time = 0
        self.original_y = 0
        
        # Create three dots
        for i in range(3):
            dot = Widget(size_hint=(None, None), size=(12, 12))
            
            with dot.canvas:
                Color(*self.color)
                ellipse = Ellipse(pos=dot.pos, size=dot.size)
                dot.ellipse = ellipse
                dot.original_y = 0  # Will be set when positioned
            
            dot.bind(pos=self._update_dot_graphics, size=self._update_dot_graphics)
            self.dots.append(dot)
            self.add_widget(dot)
        
        # Store original positions after layout
        Clock.schedule_once(self._store_original_positions, 0.1)
    
    def _store_original_positions(self, dt):
        """Store original Y positions for animation"""
        for dot in self.dots:
            dot.original_y = dot.y
    
    def _update_dot_graphics(self, dot, *args):
        """Update dot graphics when position changes"""
        dot.ellipse.pos = dot.pos
        dot.ellipse.size = dot.size
    
    def start_animating(self):
        """Start sequential dot animation using Clock"""
        if self.is_animating:
            return
        
        self.is_animating = True
        self.animation_time = 0
        # Use Clock.schedule_interval for smooth animation
        self.animation_event = Clock.schedule_interval(self._update_dots_animation, 1/60.0)
    
    def stop_animating(self):
        """Stop dot animations"""
        if not self.is_animating:
            return
        
        self.is_animating = False
        
        if self.animation_event:
            Clock.unschedule(self.animation_event)
            self.animation_event = None
        
        # Reset dot positions
        for dot in self.dots:
            if hasattr(dot, 'original_y'):
                dot.y = dot.original_y
    
    def _update_dots_animation(self, dt):
        """Update dot positions during animation"""
        self.animation_time += dt * 3  # Speed factor
        
        import math
        for i, dot in enumerate(self.dots):
            if hasattr(dot, 'original_y'):
                # Each dot bounces with a phase offset
                phase = self.animation_time + i * (math.pi / 3)  # 60 degree offset
                bounce_height = 8 * abs(math.sin(phase))
                dot.y = dot.original_y + bounce_height


class ProgressRingAtom(Widget):
    """
    Atomic progress ring that fills as progress increases
    Combines animation with progress indication
    """
    
    def __init__(self, size_hint=(None, None), size=(50, 50), 
                 color=(0.3, 0.6, 1.0, 1.0), bg_color=(0.2, 0.2, 0.2, 1.0), **kwargs):
        super().__init__(**kwargs)
        self.size_hint = size_hint
        self.size = size
        self.color = color
        self.bg_color = bg_color
        
        self.progress = 0.0  # 0.0 to 1.0
        self.animation = None
        
        # Create graphics
        with self.canvas:
            # Background ring
            Color(*self.bg_color)
            self.bg_ring = Line(
                circle=(self.center_x, self.center_y, min(self.width, self.height) / 2 - 3),
                width=6
            )
            
            # Progress ring
            Color(*self.color)
            self.progress_ring = Line(
                circle=(self.center_x, self.center_y, min(self.width, self.height) / 2 - 3, 0, 0),
                width=6
            )
        
        self.bind(pos=self._update_graphics, size=self._update_graphics)
    
    def _update_graphics(self, *args):
        """Update graphics when position/size changes"""
        radius = min(self.width, self.height) / 2 - 3
        center_x, center_y = self.center_x, self.center_y
        
        # Update background ring
        self.bg_ring.circle = (center_x, center_y, radius)
        
        # Update progress ring based on current progress
        end_angle = self.progress * 360
        self.progress_ring.circle = (center_x, center_y, radius, 0, end_angle)
    
    def set_progress(self, progress: float, animate: bool = True):
        """
        Set progress value (0.0 to 1.0)
        
        Args:
            progress: Progress value between 0.0 and 1.0
            animate: Whether to animate the change
        """
        progress = max(0.0, min(1.0, progress))
        
        if animate:
            if self.animation:
                self.animation.stop(self)
            
            self.animation = Animation(progress=progress, duration=0.5)
            self.animation.bind(on_progress=self._update_progress_animation)
            self.animation.start(self)
        else:
            self.progress = progress
            self._update_graphics()
    
    def _update_progress_animation(self, animation, widget, progression):
        """Update progress during animation"""
        if hasattr(animation, 'animated_properties'):
            self.progress = animation.animated_properties.get('progress', self.progress)
        self._update_graphics()
    
    def reset(self):
        """Reset progress to 0"""
        if self.animation:
            self.animation.stop(self)
        self.progress = 0.0
        self._update_graphics()


class WaveAtom(Widget):
    """
    Atomic wave loading animation
    Creates moving wave effect using line animation
    """
    
    def __init__(self, size_hint=(None, None), size=(100, 20), 
                 color=(0.3, 0.6, 1.0, 1.0), **kwargs):
        super().__init__(**kwargs)
        self.size_hint = size_hint
        self.size = size
        self.color = color
        
        self.wave_offset = 0
        self.animation = None
        self.is_animating = False
        
        # Create graphics
        with self.canvas:
            Color(*self.color)
            self.wave_line = Line(width=3)
        
        self.bind(pos=self._update_graphics, size=self._update_graphics)
        self._update_graphics()
    
    def _update_graphics(self, *args):
        """Update wave graphics"""
        if not self.canvas:
            return
        
        # Create wave points
        points = []
        wave_width = self.width
        wave_height = self.height / 2
        segments = 20
        
        for i in range(segments + 1):
            x = self.x + (i / segments) * wave_width
            # Create sine wave with offset for animation
            import math
            y = self.center_y + math.sin((i / segments) * 4 * math.pi + self.wave_offset) * wave_height * 0.3
            points.extend([x, y])
        
        self.wave_line.points = points
    
    def start_wave(self):
        """Start wave animation"""
        if self.is_animating:
            return
        
        self.is_animating = True
        import math
        
        # Create continuous wave movement
        self.animation = Animation(wave_offset=2 * math.pi, duration=2.0)
        self.animation.repeat = True
        self.animation.bind(on_progress=self._update_wave_animation)
        self.animation.start(self)
    
    def stop_wave(self):
        """Stop wave animation"""
        if self.animation:
            self.animation.stop(self)
            self.animation = None
        self.is_animating = False
        self.wave_offset = 0
        self._update_graphics()
    
    def _update_wave_animation(self, animation, widget, progression):
        """Update wave during animation"""
        if hasattr(animation, 'animated_properties'):
            self.wave_offset = animation.animated_properties.get('wave_offset', 0)
        self._update_graphics()
