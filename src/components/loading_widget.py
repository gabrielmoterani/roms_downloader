"""
Loading Widget Compatibility Layer
Provides backward compatibility while using new atomic design components
"""

# Re-export the new atomic components for compatibility
from .molecules.loading_indicators import (
    LoadingIndicator,
    LoadingModal, 
    InlineLoadingIndicator,
    AsyncTaskManager,
    task_manager
)

from .atoms.loading_animations import (
    SpinnerAtom as SpinnerWidget,
    PulseAtom,
    DotsAtom,
    ProgressRingAtom,
    WaveAtom
)

# Backward compatibility exports
__all__ = [
    'LoadingIndicator',
    'LoadingModal', 
    'InlineLoadingIndicator',
    'AsyncTaskManager',
    'task_manager',
    'SpinnerWidget',  # Old name for compatibility
    'PulseAtom',
    'DotsAtom', 
    'ProgressRingAtom',
    'WaveAtom'
]
