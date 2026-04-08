"""
Job input collection and loading utilities.
Handles both interactive input and file-based import of job postings.
"""

import json
from pathlib import Path
from typing import Optional


def get_job_input() -> dict:
    """
    Interactively collect job posting information from the user.

    Prompts for:
    - Job URL (optional)
    - Job description text (required if URL alone is insufficient)
    - Mode selection (ta or ai)

    Returns:
        Dictionary with keys: url, description, mode
    """
    print("\n=== Job Outreach Tool ===\n")

    # Get job URL
    url = input("Job URL (optional, press Enter to skip): ").strip()

    # Get job description
    print("\nPaste the job description below (type END on a new line to finish):")
    description_lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        description_lines.append(line)

    description = "\n".join(description_lines).strip()

    if not description:
        raise ValueError("Job description is required")

    # Get mode
    while True:
        mode = input("\nSelect mode (ta/ai): ").strip().lower()
        if mode in ("ta", "ai"):
            break
        print("Invalid mode. Please enter 'ta' or 'ai'")

    return {
        "url": url if url else None,
        "description": description,
        "mode": mode,
    }


def load_from_file(filepath: str) -> dict:
    """
    Load job input from a JSON file.

    Expected file format:
    {
        "url": "https://...",
        "description": "Job posting text...",
        "mode": "ta" or "ai"
    }

    Args:
        filepath: Path to the JSON input file

    Returns:
        Dictionary with keys: url, description, mode

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid or required fields are missing
        json.JSONDecodeError: If JSON is invalid
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate required fields
    if "description" not in data:
        raise ValueError("Missing required field: 'description'")

    if "mode" not in data:
        raise ValueError("Missing required field: 'mode'")

    # Validate mode
    mode = data["mode"].lower()
    if mode not in ("ta", "ai"):
        raise ValueError(f"Invalid mode '{mode}'. Must be 'ta' or 'ai'")

    return {
        "url": data.get("url"),
        "description": data["description"],
        "mode": mode,
    }


def validate_job_input(job_input: dict) -> bool:
    """
    Validate job input dictionary.

    Args:
        job_input: Dictionary to validate

    Returns:
        True if valid

    Raises:
        ValueError: If validation fails
    """
    required_fields = ["description", "mode"]
    for field in required_fields:
        if field not in job_input:
            raise ValueError(f"Missing required field: {field}")

    if not isinstance(job_input["description"], str):
        raise ValueError("description must be a string")

    if not job_input["description"].strip():
        raise ValueError("description cannot be empty")

    if job_input["mode"] not in ("ta", "ai"):
        raise ValueError(f"Invalid mode: {job_input['mode']}")

    return True
