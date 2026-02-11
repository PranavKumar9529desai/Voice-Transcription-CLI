"""GTK4 floating window for voice transcription visualization."""

import gi

gi.require_version("Gtk", "4.0")
import threading

from gi.repository import Gdk, GLib, Gtk

from .waveform import WaveformWidget

CSS = b"""
window.floating-window {
    background-color: rgba(20, 20, 30, 0.85);
    border-radius: 16px;
}

.recording-container {
    padding: 12px 16px;
}

.mic-icon {
    font-size: 18px;
    margin-right: 8px;
}

.status-label {
    color: rgba(255, 255, 255, 0.9);
    font-size: 12px;
    font-weight: 500;
}
"""


class FloatingWindow:
    """
    SuperWhisper-style floating window with waveform visualization.

    Features:
    - Frameless, transparent window
    - Always-on-top
    - Positioned at bottom-center of screen
    - Slide-in/out animations
    """

    def __init__(self):
        self._app = None
        self._window = None
        self._waveform = None
        self._is_visible = False
        self._gtk_thread = None
        self._ready_event = threading.Event()

    def start(self):
        """Start the GTK application in a separate thread."""
        # Auto-register with Pop Shell if available
        try:
            from .pop_shell import is_pop_shell_available, register_floating_exception

            if is_pop_shell_available():
                register_floating_exception("com.voice.transcription")
        except Exception as e:
            pass  # Silently continue if Pop Shell registration fails

        self._gtk_thread = threading.Thread(target=self._run_gtk, daemon=True)
        self._gtk_thread.start()
        # Wait for GTK to be ready
        self._ready_event.wait(timeout=5.0)

    def _run_gtk(self):
        """Run the GTK main loop."""
        self._app = Gtk.Application(application_id="com.voice.transcription")
        self._app.connect("activate", self._on_activate)
        self._app.run(None)

    def _on_activate(self, app):
        """Initialize the window when GTK is ready."""
        # Load CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # Create window
        self._window = Gtk.Window(application=app)
        self._window.set_decorated(False)
        self._window.set_resizable(False)
        self._window.add_css_class("floating-window")

        # Set window title for WM identification
        self._window.set_title("Voice Transcription Overlay")

        # CRITICAL: Settings to make Pop Shell and Mutter treat this as floating
        self._window.set_deletable(False)
        self._window.set_focus_on_click(False)

        # Make it a modal-like window - GNOME floats modals by default
        self._window.set_modal(True)

        # Set a small default size - tiling WMs often float small windows
        self._window.set_default_size(320, 60)

        # Explicitly set size request to prevent expansion
        self._window.set_size_request(320, 60)

        # Make window transparent
        self._window.set_opacity(0.95)

        # Main container
        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        container.add_css_class("recording-container")

        # Mic icon
        mic_label = Gtk.Label(label="🎙️")
        mic_label.add_css_class("mic-icon")
        container.append(mic_label)

        # Waveform widget
        self._waveform = WaveformWidget(num_bars=20)
        container.append(self._waveform)

        self._window.set_child(container)

        # Position window at bottom-center after it's realized
        self._window.connect("realize", self._position_window)

        # Signal that GTK is ready
        self._ready_event.set()

    def _position_window(self, widget):
        """Position window at bottom-center of the screen."""
        surface = self._window.get_surface()
        if surface:
            display = Gdk.Display.get_default()
            monitor = display.get_monitors()[0]
            geometry = monitor.get_geometry()

            # Window size
            width = 320
            height = 60

            # Calculate position
            x = (geometry.width - width) // 2
            y = geometry.height - height - 50  # 50px from bottom

            # For Wayland, we need to use layer-shell or accept default positioning
            # GTK4 on Wayland doesn't allow arbitrary window positioning
            # The window will appear but may not be at exact position

    def show(self):
        """Show the floating window with animation."""
        if self._window and not self._is_visible:
            GLib.idle_add(self._show_window)

    def _show_window(self):
        """Internal show (must be called from GTK thread)."""
        self._window.present()
        self._waveform.start_animation()
        self._is_visible = True
        return False

    def hide(self):
        """Hide the floating window with animation."""
        if self._window and self._is_visible:
            GLib.idle_add(self._hide_window)

    def _hide_window(self):
        """Internal hide (must be called from GTK thread)."""
        self._waveform.stop_animation()
        self._window.hide()
        self._is_visible = False
        return False

    def update_amplitude(self, amplitude: float):
        """Update the waveform amplitude (thread-safe)."""
        if self._waveform and self._is_visible:
            GLib.idle_add(self._waveform.update_amplitude, amplitude)

    def stop(self):
        """Stop the GTK application."""
        if self._app:
            GLib.idle_add(self._app.quit)
