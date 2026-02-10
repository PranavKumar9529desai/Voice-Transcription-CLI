import json
import re
from pathlib import Path


class Corrector:
    """Corrects common transcription errors using pattern matching and exact replacements."""

    def __init__(self, corrections_file="corrections.json"):
        self.corrections_file = Path(corrections_file)
        self.exact_matches = {}
        self.patterns = []
        self._load_corrections()

    def _load_corrections(self):
        """Load corrections from JSON file."""
        if not self.corrections_file.exists():
            print(
                f"Corrections file not found: {self.corrections_file}. Using no corrections."
            )
            return

        try:
            with open(self.corrections_file, "r") as f:
                data = json.load(f)

            # Load exact matches
            self.exact_matches = data.get("exact_matches", {})

            # Load and compile regex patterns
            patterns_data = data.get("patterns", [])
            for pattern_info in patterns_data:
                try:
                    pattern = pattern_info["pattern"]
                    replacement = pattern_info["replacement"]
                    case_sensitive = pattern_info.get("case_sensitive", False)

                    flags = 0 if case_sensitive else re.IGNORECASE
                    compiled = re.compile(pattern, flags)

                    self.patterns.append(
                        {"regex": compiled, "replacement": replacement}
                    )
                except (KeyError, re.error) as e:
                    print(f"Warning: Invalid pattern in corrections file: {e}")
                    continue

        except json.JSONDecodeError as e:
            print(f"Warning: Malformed corrections file: {e}. Using no corrections.")
        except Exception as e:
            print(f"Warning: Error loading corrections: {e}. Using no corrections.")

    def correct(self, text: str) -> str:
        """Apply all corrections to the input text."""
        if not text:
            return text

        corrected = text

        # Apply exact matches first (case-insensitive)
        for mistake, correction in self.exact_matches.items():
            # Use word boundaries and case-insensitive matching
            pattern = re.compile(r"\b" + re.escape(mistake) + r"\b", re.IGNORECASE)
            corrected = pattern.sub(correction, corrected)

        # Apply regex patterns
        for pattern_info in self.patterns:
            corrected = pattern_info["regex"].sub(
                pattern_info["replacement"], corrected
            )

        return corrected

    def add_correction(self, mistake: str, correction: str, is_regex: bool = False):
        """Add a new correction and save to file."""
        if is_regex:
            # Add to patterns
            try:
                compiled = re.compile(mistake, re.IGNORECASE)
                self.patterns.append({"regex": compiled, "replacement": correction})
            except re.error as e:
                print(f"Invalid regex pattern: {e}")
                return False
        else:
            # Add to exact matches
            self.exact_matches[mistake] = correction

        self._save_corrections()
        return True

    def _save_corrections(self):
        """Save corrections back to JSON file."""
        try:
            # Reconstruct the data structure
            data = {
                "exact_matches": self.exact_matches,
                "patterns": [
                    {
                        "pattern": p["regex"].pattern,
                        "replacement": p["replacement"],
                        "case_sensitive": False,
                    }
                    for p in self.patterns
                ],
            }

            with open(self.corrections_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving corrections: {e}")

    def reload(self):
        """Reload corrections from file without restarting."""
        self.exact_matches = {}
        self.patterns = []
        self._load_corrections()
