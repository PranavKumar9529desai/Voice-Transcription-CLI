# Installation Guide for Voice Transcription CLI

This guide covers the complete setup process for the Voice Transcription CLI on Linux.

## 📋 System Requirements

- **Operating System:** Linux (Ubuntu 22.04+, Fedora 38+, Arch Linux)
- **Display Server:** X11 (Recommended) or Wayland
- **GPU:** NVIDIA GPU with CUDA support (Highly Recommended for low latency)
- **Python:** Version 3.12 or higher
- **Audio:** A working microphone

## 1. Install System Dependencies

Before installing the Python packages, you need to install the required system libraries for audio, GUI, and clipboard management.

### Ubuntu / Debian
```bash
sudo apt update
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    libgirepository1.0-dev \
    libcairo2-dev \
    gir1.2-gtk-4.0 \
    libportaudio2 \
    libnotify-bin
```

### Fedora
```bash
sudo dnf install \
    python3-pip \
    git \
    gobject-introspection-devel \
    cairo-gobject-devel \
    gtk4 \
    portaudio \
    libnotify
```

### Arch Linux
```bash
sudo pacman -S \
    python-pip \
    git \
    gobject-introspection \
    cairo \
    gtk4 \
    portaudio \
    libnotify
```

## 2. Install Clipboard Tools

The application requires specific tools to inject text into other windows. Install the tools matching your display server.

**Check your display server:**
```bash
echo $XDG_SESSION_TYPE
```

### For X11 (Default/Most Common)
```bash
sudo apt install xclip xdotool
```

### For Wayland
```bash
sudo apt install wl-clipboard ydotool
```
*Note: Wayland support requires `ydotoold` to be running. You may need to configure permissions for `ydotool`.*

## 3. Install `uv` (Package Manager)

This project uses `uv` for ultra-fast dependency management and environment isolation.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your shell to ensure 'uv' is in your path
exec $SHELL
```

## 4. Clone and Install Project

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/voice-transcription-cli.git
   cd voice-transcription-cli
   ```

2. **Install Python dependencies:**
   This command will create a virtual environment and install all required packages (including CUDA libraries).
   ```bash
   uv sync
   ```

## 5. Verifying Installation

To check if everything is set up correctly, run the application:

```bash
# Activate the environment and run
uv run main.py --no-ui
```

If you see `Listening... (Press F8 to record)`, the installation was successful!

## 6. Desktop Integration (Optional)

To start the application automatically when you log in:

1. Locate the `voice-transcription.desktop` file in the project folder.
2. Edit the file to match your path:
   ```bash
   nano voice-transcription.desktop
   ```
   *Change `Exec=` and `Path=` to point to your installation directory.*
   
   Example `Exec` line using `uv`:
   ```ini
   Exec=/home/youruser/.cargo/bin/uv run /home/youruser/voice-transcription-cli/main.py
   ```

3. Copy to your autostart folder:
   ```bash
   mkdir -p ~/.config/autostart
   cp voice-transcription.desktop ~/.config/autostart/
   ```

## ⚠️ Troubleshooting

### CUDA / GPU Issues
If the transcription is slow, ensure your NVIDIA drivers are installed.
```bash
nvidia-smi
```
The application automatically downloads required CUDA libraries (`nvidia-cublas`, `nvidia-cudnn`) via pip, so you don't need to install the full CUDA Toolkit system-wide.

### "PyGObject" or "Cairo" Errors
If you encounter errors related to `gi` or `cairo`, you are missing system headers. Run the **System Dependencies** step again for your OS.

### Wayland Issues
If text isn't pasting on Wayland:
1. Ensure `ydotoold` is running: `sudo ydotoold &`
2. Or switch to X11 on your login screen for better compatibility.

### Zed Editor / Terminal Pasting
If text pastes incorrectly in terminals:
- The app auto-detects `gnome-terminal` and `zed`.
- You can manually force "Terminal Mode" (Ctrl+Shift+V) by holding **Shift** when you release the recording key.
