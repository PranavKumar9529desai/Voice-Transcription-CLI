# Voice Transcription CLI

A high-performance, low-latency Voice-to-Text CLI tool designed for Linux. This tool allows for seamless Push-to-Talk (PTT) transcription that automatically types the results directly at your cursor.

## 🚀 Key Features

- **Push-to-Talk (PTT):** Simple hotkey-based recording (Default: `F8`). Hold to record, release to transcribe.
- **Auto-Typing:** Integrated keyboard emulation automatically types transcribed text into any active window.
- **GPU Accelerated:** Optimized for NVIDIA GPUs using `CUDA`, `cuBLAS`, and `cuDNN` for near-instant processing.
- **Smart Audio Processing:**
  - **Voice Activity Detection (VAD):** Intelligently filters out silence using `Silero VAD`.
  - **Model Flexibility:** Supports multiple Whisper models (Defaults to `distil-large-v3`).
- **Feedback System:** Provides visual (notifications) and auditory (beeps) feedback for recording states.
- **Single Instance Enforcement:** Prevents multiple instances from conflicting using file locking.

## 🛠️ Technical Stack

- **Transcription Engine:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (re-implementation of OpenAI's Whisper using CTranslate2).
- **Runtime:** [CTranslate2](https://github.com/OpenNMT/CTranslate2) for efficient transformer inference.
- **Audio:** `sounddevice`, `scipy`, `numpy`.
- **Keyboard Control:** `pynput` for hotkey listening and text injection.
- **Environment:** Managed via `uv` for fast, reproducible Python environments.

## 📦 Installation

Requirements: Python 3.12+, NVIDIA GPU (Recommended for speed).

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd voice-transcription-cli
   ```

2. **Install dependencies:**
   Using [uv](https://github.com/astral-sh/uv):
   ```bash
   uv sync
   ```

## ⌨️ Usage

Run the tool using the default settings:
```bash
python main.py
```

### Custom Configurations

| Argument | Description | Default |
|----------|-------------|---------|
| `--model` | Whisper model size (e.g., `base`, `medium`, `distil-large-v3`) | `distil-large-v3` |
| `--key` | Hotkey for Push-to-Talk (e.g., `f8`, `f9`, `cmd_l`) | `f8` |

Example with custom model and key:
```bash
python main.py --model distil-medium.en --key f9
```

## 🖥️ Background & Autostart

For Linux users, a `voice-transcription.desktop` file is included to allow the tool to start automatically upon login.

1. Edit the `Exec` path in `voice-transcription.desktop` to point to your project directory.
2. Copy it to your autostart directory:
   ```bash
   cp voice-transcription.desktop ~/.config/autostart/
   ```

## 📝 License

MIT

This is the new random file writing examination. So let's see if it's able to write in the school as well.
Hello, hello, hello, this is the new output checking status.