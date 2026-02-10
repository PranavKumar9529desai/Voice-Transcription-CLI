# Voice Transcription CLI - Project Context

## Project Overview

A high-performance, low-latency **Voice-to-Text CLI tool** for Linux that provides seamless Push-to-Talk (PTT) transcription with automatic keyboard injection. Built with GPU acceleration and a modern GTK4 floating UI.

**Key Capabilities:**
- Push-to-Talk recording with configurable hotkey (default: F8)
- GPU-accelerated Whisper transcription using CTranslate2
- Automatic text injection into any active window
- Real-time waveform visualization with floating UI
- Voice Activity Detection (VAD) for intelligent silence filtering
- Single-instance enforcement to prevent conflicts

## Technology Stack

- **Language:** Python 3.12+
- **Transcription:** faster-whisper (CTranslate2 backend) with OpenAI Whisper models
- **GPU Acceleration:** CUDA, cuBLAS, cuDNN (NVIDIA GPUs)
- **Audio Processing:** sounddevice, numpy, scipy
- **Keyboard Control:** pynput (hotkey listening + text injection)
- **UI Framework:** GTK4 (PyGObject) with Cairo rendering
- **Display Servers:** Supports both X11 and Wayland
- **Package Manager:** uv for fast dependency management

## Architecture

### Core Components

1. **main.py** - Application entry point and orchestrator
   - Single-instance enforcement (file locking at `/tmp/voice-transcription.lock`)
   - CUDA library path bootstrapping (auto-restart with correct LD_LIBRARY_PATH)
   - Hotkey listener and event coordination
   - Threading for async transcription processing

2. **recorder.py** - Audio capture module
   - Records audio at 16kHz mono using sounddevice
   - Real-time RMS amplitude calculation for UI feedback
   - Callback-based architecture for amplitude updates

3. **transcriber.py** - Whisper transcription engine
   - Auto-detects CUDA availability (falls back to CPU)
   - Uses distil-large-v3 model by default
   - Integrated Silero VAD with 500ms min silence duration
   - Beam search with size=5 for quality

4. **typer.py** - Keyboard injection handler
   - Detects display server type (X11/Wayland)
   - X11: Uses xclip + xdotool for clipboard-based pasting
   - Wayland: Uses wl-copy + ydotool
   - Fallback to pynput Ctrl+V if tools unavailable

5. **feedback.py** - User feedback system
   - Desktop notifications via notify-send
   - Audio beep generation (880Hz sine wave at /tmp/transcription_beep.wav)
   - Non-blocking subprocess calls

6. **ui/** - GTK4 floating window interface
   - **floating_window.py**: Frameless overlay with transparency
   - **waveform.py**: Cairo-based real-time waveform visualization (20 bars, 30 FPS)
   - **pop_shell.py**: GNOME Pop Shell integration for floating window exceptions

### Data Flow

```
User holds hotkey (F8)
  → recorder.start() begins audio capture
  → Audio chunks → amplitude callback → UI waveform update
  
User releases hotkey
  → recorder.stop() returns audio data
  → Transcription thread spawned
  → Whisper model processes with VAD
  → Text typed via clipboard + paste
  → Notification + beep feedback
```

## Project Structure

```
voice-transcription-cli/
├── main.py                    # Entry point and main app logic
├── recorder.py                # Audio recording with amplitude tracking
├── transcriber.py             # Whisper model wrapper
├── typer.py                   # Keyboard injection (X11/Wayland)
├── feedback.py                # Notifications and audio feedback
├── ui/
│   ├── __init__.py
│   ├── floating_window.py     # GTK4 overlay window
│   ├── waveform.py            # Cairo waveform widget
│   └── pop_shell.py           # Pop Shell window exception manager
├── proto_hotkey.py            # Early hotkey prototype
├── proto_test.py              # Audio + Whisper test script
├── pyproject.toml             # uv project configuration
├── README.md                  # User documentation
└── voice-transcription.desktop # Autostart desktop entry

Generated at runtime:
├── /tmp/voice-transcription.lock  # Single-instance lock file
└── /tmp/transcription_beep.wav    # Audio feedback file
```

## Configuration & Usage

### CLI Arguments

```bash
python main.py [OPTIONS]

Options:
  --model MODEL    Whisper model (default: distil-large-v3)
                   Options: tiny, base, small, medium, large-v2, large-v3,
                           distil-medium.en, distil-large-v3
  --key KEY        PTT hotkey (default: f8)
                   Examples: f8, f9, cmd_l, ctrl_l
  --no-ui          Disable floating UI window
```

### Environment Setup

**Dependencies Installation:**
```bash
uv sync  # Installs all dependencies from pyproject.toml
```

**System Requirements:**
- NVIDIA GPU with CUDA support (recommended)
- X11/Wayland display server
- For X11: xclip, xdotool (`sudo apt install xclip xdotool`)
- For Wayland: wl-clipboard, ydotool (`sudo apt install wl-clipboard ydotool`)
- For notifications: libnotify (`sudo apt install libnotify-bin`)

**Autostart Setup:**
Edit `voice-transcription.desktop` paths and copy to `~/.config/autostart/`

## Development Guidelines

### Adding New Features

1. **New Audio Processing:**
   - Modify `recorder.py` for capture logic
   - Update amplitude callback signature if needed
   - Consider impact on UI updates

2. **Transcription Model Changes:**
   - Update `transcriber.py` with new model parameters
   - Test memory usage (large models may cause OOM)
   - Update default in `main.py` and README.md

3. **UI Enhancements:**
   - GTK4 widgets go in `ui/` directory
   - Use GLib.idle_add() for thread-safe UI updates
   - Maintain 30 FPS animation budget (33ms intervals)
   - Test on both GNOME and KDE

4. **Display Server Support:**
   - Add new methods to `typer.py`
   - Detect via `XDG_SESSION_TYPE` environment variable
   - Provide graceful fallbacks

### Code Patterns

**Threading:**
- UI updates MUST use `GLib.idle_add()` from worker threads
- Transcription runs in daemon thread to avoid blocking
- Use `threading.Lock()` to protect shared state (e.g., `is_recording`)

**Error Handling:**
- Silent failures for optional features (UI, beeps, notifications)
- Loud failures for critical components (model loading, recording)
- Provide fallback mechanisms where possible

**GPU Management:**
- CUDA libraries injected via LD_LIBRARY_PATH in bootstrap()
- Process restarts itself if libraries not in path
- Graceful CPU fallback if CUDA unavailable

### Testing

**Manual Tests:**
1. Test with different models: `python main.py --model tiny`
2. Test without UI: `python main.py --no-ui`
3. Test on Wayland vs X11
4. Check memory usage with large models
5. Verify single-instance enforcement

**Prototype Scripts:**
- `proto_test.py`: Test audio recording + Whisper transcription
- `proto_hotkey.py`: Test pynput hotkey detection

## Known Issues & Limitations

1. **Wayland Window Positioning:**
   - GTK4 on Wayland doesn't support arbitrary window positioning
   - Window appears but may not be at exact bottom-center coordinates

2. **Pop Shell Integration:**
   - Requires manual Pop Shell restart (Alt+F2 → r) after first registration
   - Floating exception config saved to `~/.config/pop-shell/config.json`

3. **CUDA Out of Memory:**
   - Large models (large-v3) may cause OOM on GPUs with <8GB VRAM
   - Use distil models or smaller variants
   - Consider int8 quantization for compute_type

4. **Clipboard Conflicts:**
   - Typing uses clipboard (may overwrite user's clipboard content)
   - Brief delay between copy and paste (50ms)

5. **ydotool on Wayland:**
   - Requires ydotoold daemon running in background
   - May need sudo permissions depending on setup

## Security Considerations

- **Lock File:** `/tmp/voice-transcription.lock` is world-readable
- **Audio Beep:** `/tmp/transcription_beep.wav` stored in shared /tmp
- **Clipboard Access:** Application reads/writes system clipboard
- **Hotkey Listener:** Has global keyboard access (necessary for PTT)
- **File Permissions:** No elevated privileges required

## Future Improvements

**Potential Enhancements:**
- [ ] Configurable VAD parameters
- [ ] Multiple language support
- [ ] Text correction/editing UI
- [ ] History of transcriptions
- [ ] Custom keybinding configuration UI
- [ ] Tray icon for status indication
- [ ] Audio preprocessing (noise reduction)
- [ ] Streaming transcription (real-time)
- [ ] Model auto-download with progress bar
- [ ] System-wide text expansion shortcuts

## Dependencies (from pyproject.toml)

```toml
faster-whisper >= 1.2.1       # Whisper transcription engine
numpy >= 2.4.1                # Array processing
nvidia-cublas-cu12 >= 12.9.1.4  # CUDA linear algebra
nvidia-cudnn-cu12 >= 9.17.1.4   # CUDA deep learning
PyGObject >= 3.50.0           # GTK4 bindings
pynput >= 1.8.1               # Keyboard control
scipy >= 1.17.0               # Signal processing
sounddevice >= 0.5.3          # Audio I/O
```

## Git Workflow

**Main Branch:** `master`  
**Current Branch:** `ui` (floating window development)

**Recent Development:**
- UI implementation with GTK4
- Pop Shell integration
- Amplitude visualization
- CUDA library bootstrapping
- Prevention of OOM errors

## Helpful Commands

```bash
# Run with default settings
python main.py

# Run with custom model and key
python main.py --model base --key f9

# Run without UI
python main.py --no-ui

# Install/update dependencies
uv sync

# Check CUDA availability
python -c "import ctranslate2; print(ctranslate2.get_cuda_device_count())"

# List available Whisper models
python -c "from faster_whisper import available_models; print(available_models())"

# Test audio recording
python proto_test.py

# Remove lock file if stuck
rm /tmp/voice-transcription.lock
```

## Contact & Support

For issues or feature requests, check the README.md for test outputs and usage examples.
