"""
Job tracking and logging utilities.
Maintains a CSV record of all job outreach campaigns.
"""

import csv
from datetime import datetime
from pathlib import Path


def get_tracker_path() -> Path:
    """
    Get the path to the job tracker CSV file.

    Returns:
        Path object for the tracker CSV
    """
    return Path("job_tracker.csv")


def log_job(
    job_analysis: dict,
    targets: dict,
    mode: str,
    url: str | None,
    output_dir: Path,
) -> dict:
    """
    Log a job outreach campaign to the tracker CSV.

    Creates the CSV with headers if it doesn't exist, then appends a new entry.

    Args:
        job_analysis: The job analysis dictionary from analyze_job()
        targets: The targets dictionary from generate_targets()
        mode: Either "ta" or "ai"
        url: The job posting URL (optional)
        output_dir: The output directory path

    Returns:
        Dictionary with the logged entry data
    """
    tracker_path = get_tracker_path()

    # Prepare the log entry
    target_titles = ", ".join(targets.get("target_titles", []))
    campaign_name = f"{job_analysis['company_name'].replace(' ', '_')}_{mode.upper()}_{datetime.now().strftime('%Y-%m-%d')}"

    entry = {
        "date": datetime.now().isoformat(),
        "company": job_analysis["company_name"],
        "job_title": job_analysis["job_title"],
        "mode": mode,
        "source_url": url or "N/A",
        "target_contact_titles": target_titles,
        "outreach_status": "pending",
        "followup_status": "not_started",
        "notes": f"Campaign ID: {campaign_name}",
        "resume_used": f"resume_{mode}.txt",
        "campaign_name": campaign_name,
    }

    # Check if file exists, create with headers if not
    file_exists = tracker_path.exists()

    with open(tracker_path, "a", newline="", encoding="utf-8") as f:
        fieldnames = [
            "date",
            "company",
            "job_title",
            "mode",
            "source_url",
            "target_contact_titles",
            "outreach_status",
            "followup_status",
            "notes",
            "resume_used",
            "campaign_name",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # Write header if file is new
        if not file_exists:
            writer.writeheader()

        # Write the entry
        writer.writerow(entry)

    return entry
