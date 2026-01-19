"""Cairo-based waveform visualization widget."""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
import cairo
import math
import random


class WaveformWidget(Gtk.DrawingArea):
    """Real-time audio waveform visualization using Cairo."""
    
    def __init__(self, num_bars=20):
        super().__init__()
        self.num_bars = num_bars
        self.amplitudes = [0.0] * num_bars
        self.target_amplitudes = [0.0] * num_bars
        self.smoothing = 0.3  # Lower = smoother transitions
        
        # Colors
        self.bar_color = (0.3, 0.85, 0.6)  # Emerald green
        self.bg_color = (0.1, 0.1, 0.15, 0.0)  # Transparent
        
        self.set_draw_func(self._draw)
        self.set_content_width(260)
        self.set_content_height(40)
        
        # Animation timer
        self._animation_id = None
        
    def start_animation(self):
        """Start the animation loop."""
        if self._animation_id is None:
            self._animation_id = GLib.timeout_add(33, self._animate)  # ~30 FPS
            
    def stop_animation(self):
        """Stop the animation loop."""
        if self._animation_id is not None:
            GLib.source_remove(self._animation_id)
            self._animation_id = None
        # Reset amplitudes
        self.amplitudes = [0.0] * self.num_bars
        self.target_amplitudes = [0.0] * self.num_bars
        self.queue_draw()
    
    def update_amplitude(self, amplitude: float):
        """Update the waveform with a new amplitude value (0.0 to 1.0)."""
        # Generate varied bar heights based on input amplitude
        for i in range(self.num_bars):
            # Create natural variation
            variation = random.uniform(0.5, 1.0)
            center_weight = 1 - abs(i - self.num_bars / 2) / (self.num_bars / 2) * 0.4
            self.target_amplitudes[i] = min(1.0, amplitude * variation * center_weight)
    
    def _animate(self) -> bool:
        """Animation tick - smooth transition to target amplitudes."""
        for i in range(self.num_bars):
            diff = self.target_amplitudes[i] - self.amplitudes[i]
            self.amplitudes[i] += diff * self.smoothing
            
            # Add slight decay when idle
            if self.target_amplitudes[i] < 0.01:
                self.amplitudes[i] *= 0.85
                
        self.queue_draw()
        return True  # Continue animation
    
    def _draw(self, area, cr, width, height):
        """Draw the waveform bars."""
        # Clear with transparent background
        cr.set_source_rgba(*self.bg_color)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        
        # Calculate bar dimensions
        total_gap = self.num_bars * 3
        bar_width = max(3, (width - total_gap) / self.num_bars)
        gap = 3
        
        # Draw bars
        for i, amp in enumerate(self.amplitudes):
            x = i * (bar_width + gap) + gap
            bar_height = max(4, amp * (height - 8))
            y = (height - bar_height) / 2
            
            # Rounded rectangle
            radius = bar_width / 2
            self._draw_rounded_rect(cr, x, y, bar_width, bar_height, radius)
            
            # Gradient fill based on amplitude
            gradient = cairo.LinearGradient(x, y, x, y + bar_height)
            r, g, b = self.bar_color
            gradient.add_color_stop_rgba(0, r, g, b, 0.9)
            gradient.add_color_stop_rgba(1, r * 0.7, g * 0.7, b * 0.7, 0.7)
            cr.set_source(gradient)
            cr.fill()
    
    def _draw_rounded_rect(self, cr, x, y, width, height, radius):
        """Draw a rounded rectangle path."""
        radius = min(radius, width / 2, height / 2)
        cr.new_path()
        cr.arc(x + radius, y + radius, radius, math.pi, 1.5 * math.pi)
        cr.arc(x + width - radius, y + radius, radius, 1.5 * math.pi, 2 * math.pi)
        cr.arc(x + width - radius, y + height - radius, radius, 0, 0.5 * math.pi)
        cr.arc(x + radius, y + height - radius, radius, 0.5 * math.pi, math.pi)
        cr.close_path()
