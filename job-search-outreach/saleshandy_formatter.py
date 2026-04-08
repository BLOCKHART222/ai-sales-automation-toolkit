"""
Saleshandy campaign formatter.
Converts job analysis and messages into Saleshandy campaign export format.
"""

import csv
from datetime import datetime
from pathlib import Path


def format_for_saleshandy(
    job_analysis: dict, messages: dict, targets: dict, mode: str
) -> dict:
    """
    Format job analysis and messages for Saleshandy campaign import.

    Creates a dictionary with all fields required for Saleshandy CSV export.

    Args:
        job_analysis: The job analysis dictionary from analyze_job()
        messages: The messages dictionary from generate_messages()
        targets: The targets dictionary from generate_targets()
        mode: Either "ta" or "ai"

    Returns:
        Dictionary with campaign data formatted for Saleshandy:
        - campaign_name: Unique campaign identifier
        - company_name: Target company
        - job_title: Job position
        - job_mode: The mode (ta/ai)
        - target_contact_titles: Comma-separated list of target titles
        - email_1_subject: Initial cold email subject
        - email_1_body: Initial cold email body
        - followup_1_subject: First follow-up subject
        - followup_1_body: First follow-up body
        - followup_2_subject: Second follow-up subject
        - followup_2_body: Second follow-up body
        - personalization_notes: Notes for personalization
    """
    campaign_name = f"{job_analysis['company_name'].replace(' ', '_')}_{mode.upper()}_{datetime.now().strftime('%Y-%m-%d')}"
    target_titles = ", ".join(targets.get("target_titles", []))

    return {
        "campaign_name": campaign_name,
        "company_name": job_analysis["company_name"],
        "job_title": job_analysis["job_title"],
        "job_mode": mode.upper(),
        "target_contact_titles": target_titles,
        "email_1_subject": messages["initial_cold_email"]["subject"],
        "email_1_body": messages["initial_cold_email"]["body"],
        "followup_1_subject": messages["followup_1"]["subject"],
        "followup_1_body": messages["followup_1"]["body"],
        "followup_2_subject": messages["followup_2"]["subject"],
        "followup_2_body": messages["followup_2"]["body"],
        "personalization_notes": f"Target departments: {', '.join(targets.get('target_departments', []))}. "
        f"Rationale: {targets.get('rationale', '')}",
    }


def export_saleshandy_csv(data: dict, output_dir: Path | str) -> str:
    """
    Export campaign data to Saleshandy CSV format.

    Creates a CSV file with a single row of campaign data.

    Args:
        data: The campaign data dictionary from format_for_saleshandy()
        output_dir: Directory where to save the CSV file

    Returns:
        The path to the created CSV file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "saleshandy_campaign.csv"

    fieldnames = [
        "campaign_name",
        "company_name",
        "job_title",
        "job_mode",
        "target_contact_titles",
        "email_1_subject",
        "email_1_body",
        "followup_1_subject",
        "followup_1_body",
        "followup_2_subject",
        "followup_2_body",
        "personalization_notes",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(data)

    return str(csv_path)
