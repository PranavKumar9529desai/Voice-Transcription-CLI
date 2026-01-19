"""GTK4 UI components for voice transcription CLI."""

from .floating_window import FloatingWindow
from .waveform import WaveformWidget
from .pop_shell import register_floating_exception, is_pop_shell_available

__all__ = ["FloatingWindow", "WaveformWidget", "register_floating_exception", "is_pop_shell_available"]
