"""Pop Shell integration utilities for floating window exceptions."""

import json
from pathlib import Path


# Window identifiers for Pop Shell
# Pop Shell matches on class (WM_CLASS) or title
APP_CLASS = "com.voice.transcription"
APP_TITLE = "Voice Transcription Overlay"


def get_pop_shell_config_path() -> Path:
    """Get the path to Pop Shell's config file."""
    return Path.home() / ".config" / "pop-shell" / "config.json"


def register_floating_exception(app_class: str = None, app_title: str = None) -> bool:
    """
    Register an application as a floating exception in Pop Shell.
    
    Pop Shell can match by class (WM_CLASS) or by title, or both.
    We register multiple variations to ensure compatibility.
    
    Args:
        app_class: The window class name
        app_title: The window title for title-based matching
        
    Returns:
        True if successfully registered, False otherwise
    """
    if app_class is None:
        app_class = APP_CLASS
    if app_title is None:
        app_title = APP_TITLE
        
    config_path = get_pop_shell_config_path()
    
    # Check if Pop Shell config exists
    if not config_path.exists():
        print(f"Pop Shell config not found at {config_path}")
        return False
    
    try:
        # Read existing config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Ensure float array exists
        if 'float' not in config:
            config['float'] = []
        
        float_entries = config['float']
        
        # Entries to add (multiple variations for compatibility)
        entries_to_add = [
            {"class": app_class},                           # Standard class match
            {"class": app_class, "title": app_title},       # Class + title
            {"title": app_title},                           # Title-only match
        ]
        
        # Check existing entries and add missing ones
        added = False
        for new_entry in entries_to_add:
            exists = False
            for entry in float_entries:
                if isinstance(entry, dict):
                    if entry.get('class') == new_entry.get('class') and \
                       entry.get('title') == new_entry.get('title'):
                        exists = True
                        break
            
            if not exists:
                float_entries.append(new_entry)
                added = True
        
        if added:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Registered floating exceptions for '{app_class}' / '{app_title}'")
            print("Note: Restart Pop Shell (Alt+F2 → r → Enter) for changes to take effect")
        else:
            print("Floating exceptions already registered")
            
        return True
        
    except json.JSONDecodeError as e:
        print(f"Error parsing Pop Shell config: {e}")
        return False
    except Exception as e:
        print(f"Error updating Pop Shell config: {e}")
        return False


def is_pop_shell_available() -> bool:
    """Check if Pop Shell is installed and configured."""
    return get_pop_shell_config_path().exists()
