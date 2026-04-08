"""
Configuration management for the job outreach automation tool.
Loads environment variables and resume files based on selected mode.
"""

import os
from pathlib import Path
from typing import Optional


def load_env_file(filepath: str = ".env") -> None:
    """
    Load environment variables from a .env file without external dependencies.

    Args:
        filepath: Path to the .env file
    """
    env_path = Path(filepath)
    if not env_path.exists():
        return

    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse key=value pairs
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                os.environ[key] = value


# Load environment variables
load_env_file(".env")

# OpenAI Configuration
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

# Mode Configuration
MODE_CHOICES: tuple[str, ...] = ("ta", "ai")
MODE: str = os.getenv("MODE", "ta").lower()

# Path Configuration
RESUME_TA_PATH: str = "resume_ta.txt"
RESUME_AI_PATH: str = "resume_ai.txt"
OUTPUT_DIR: str = "outputs"
TRACKER_CSV: str = "job_tracker.csv"


def get_resume_text(mode: str) -> str:
    """
    Load and return the resume text based on the selected mode.

    Args:
        mode: Either "ta" for talent acquisition or "ai" for AI roles

    Returns:
        The resume text content

    Raises:
        FileNotFoundError: If resume file is not found
        ValueError: If mode is invalid
    """
    if mode not in MODE_CHOICES:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of {MODE_CHOICES}")

    resume_path = RESUME_TA_PATH if mode == "ta" else RESUME_AI_PATH
    path = Path(resume_path)

    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {resume_path}")

    return path.read_text(encoding="utf-8")


def ensure_output_dir() -> Path:
    """
    Ensure the output directory exists.

    Returns:
        Path object for the output directory
    """
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)
    return output_path


def validate_config() -> bool:
    """
    Validate that all required configuration is present.

    Returns:
        True if configuration is valid

    Raises:
        ValueError: If configuration is invalid
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    if MODE not in MODE_CHOICES:
        raise ValueError(f"Invalid MODE '{MODE}'. Must be one of {MODE_CHOICES}")

    return True
