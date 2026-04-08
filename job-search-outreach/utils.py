"""
Utility functions for file handling, formatting, and console output.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def sanitize_filename(text: str) -> str:
    """
    Make text safe for use in filenames.

    Removes or replaces characters that are problematic in filenames.

    Args:
        text: The text to sanitize

    Returns:
        A sanitized filename-safe string
    """
    # Replace spaces with underscores
    text = text.replace(" ", "_")
    # Remove or replace special characters
    text = re.sub(r"[^\w\-.]", "", text)
    # Remove leading/trailing dots and dashes
    text = text.strip(".-")
    return text


def create_output_dir() -> Path:
    """
    Create a timestamped output directory.

    Creates a directory with format: outputs/YYYY-MM-DD_HHMMSS/

    Returns:
        Path object for the new output directory
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = Path("outputs") / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_json(data: dict | list, filepath: str) -> None:
    """
    Save data to a JSON file.

    Args:
        data: Dictionary or list to save
        filepath: Path where to save the JSON file
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_text(text: str, filepath: str) -> None:
    """
    Save text to a file.

    Args:
        text: The text to save
        filepath: Path where to save the text file
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def print_header(title: str) -> None:
    """
    Print a formatted console header.

    Args:
        title: The title to display
    """
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def print_step(message: str) -> None:
    """
    Print a formatted step indicator.

    Args:
        message: The step message to display
    """
    print(f"→ {message}")
