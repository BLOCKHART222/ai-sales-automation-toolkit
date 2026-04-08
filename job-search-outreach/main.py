"""
Main CLI for the job outreach automation tool.
Orchestrates job analysis, targeting, and message generation.
"""

import json
import sys
from pathlib import Path

from config import (
    ensure_output_dir,
    get_resume_text,
    validate_config,
)
from job_analyzer import analyze_job, display_analysis
from job_input import get_job_input, validate_job_input
from message_generator import (
    display_messages,
    export_messages_json,
    export_messages_text,
    generate_messages,
)
from saleshandy_formatter import export_saleshandy_csv, format_for_saleshandy
from targeting import display_targets, generate_targets
from tracker import log_job
from utils import create_output_dir, print_header, print_step, save_json, save_text


def main() -> None:
    """
    Main entry point for the job outreach automation tool.

    Workflow:
    1. Validate configuration (OpenAI API key, mode, files)
    2. Collect job input (URL and/or description)
    3. Load resume for the selected mode
    4. Analyze the job posting
    5. Generate target contacts
    6. Generate outreach messages
    7. Export results to timestamped output directory
    8. Log campaign to tracker
    9. Display summary
    """
    try:
        # Validate configuration
        print_step("Validating configuration...")
        validate_config()

        # Get job input
        print_step("Collecting job input...")
        job_input = get_job_input()
        validate_job_input(job_input)

        # Determine mode
        mode = job_input["mode"]
        print_header(f"MODE: {mode.upper()}")

        # Load resume
        print_step(f"Loading resume for {mode.upper()} mode...")
        resume_text = get_resume_text(mode)

        # Analyze job
        print_step("Analyzing job posting with OpenAI...")
        analysis = analyze_job(job_input["description"], mode, resume_text)
        analysis["description"] = job_input["description"]  # Store for later use
        display_analysis(analysis)

        # Generate targets
        print_step("Generating target contacts...")
        targets = generate_targets(analysis, mode)
        display_targets(targets)

        # Generate messages
        print_step("Generating outreach messages...")
        messages = generate_messages(analysis, targets, mode, resume_text)
        display_messages(messages)

        # Create output directory
        print_step("Creating output directory...")
        output_dir = create_output_dir()
        print(f"Output directory: {output_dir}\n")

        # Prepare slug for filenames
        company_slug = analysis["company_name"].lower().replace(" ", "_")

        # Export campaign data for Saleshandy
        print_step("Formatting data for Saleshandy...")
        saleshandy_data = format_for_saleshandy(analysis, messages, targets, mode)
        saleshandy_path = export_saleshandy_csv(saleshandy_data, output_dir)
        print(f"Exported Saleshandy CSV: {saleshandy_path}")

        # Export as JSON
        print_step("Exporting JSON results...")
        results = {
            "campaign_name": saleshandy_data["campaign_name"],
            "analysis": analysis,
            "targets": targets,
            "messages": messages,
            "saleshandy_data": saleshandy_data,
        }
        json_path = output_dir / f"{company_slug}_results.json"
        save_json(results, str(json_path))
        print(f"Exported JSON: {json_path}")

        # Export as formatted text summary
        print_step("Exporting text summary...")
        summary_text = _generate_summary_text(analysis, targets, messages, mode)
        summary_path = output_dir / f"{company_slug}_summary.txt"
        save_text(summary_text, str(summary_path))
        print(f"Exported summary: {summary_path}")

        # Log to tracker
        print_step("Logging campaign to tracker...")
        log_entry = log_job(analysis, targets, mode, job_input.get("url"), output_dir)
        print(f"Campaign logged: {log_entry['campaign_name']}")

        # Print final summary
        print_header("CAMPAIGN GENERATION COMPLETE")
        print(f"Company: {analysis['company_name']}")
        print(f"Role: {analysis['job_title']}")
        print(f"Mode: {mode.upper()}")
        print(f"Campaign ID: {saleshandy_data['campaign_name']}")
        print(f"\nOutput files:")
        print(f"  • Summary: {summary_path}")
        print(f"  • Results: {json_path}")
        print(f"  • Saleshandy: {saleshandy_path}")
        print(f"\nNext steps:")
        print(f"  1. Review messages in summary.txt")
        print(f"  2. Personalize for specific contacts")
        print(f"  3. Import Saleshandy CSV into campaign tool")
        print(f"  4. Track follow-ups in job_tracker.csv\n")

    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\nFile Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


def _generate_summary_text(
    analysis: dict, targets: dict, messages: dict, mode: str
) -> str:
    """
    Generate a formatted text summary of the entire campaign.

    Args:
        analysis: Job analysis dictionary
        targets: Target contacts dictionary
        messages: Generated messages dictionary
        mode: The outreach mode (ta/ai)

    Returns:
        Formatted text summary
    """
    lines = []

    # Header
    lines.append("=" * 70)
    lines.append("JOB OUTREACH CAMPAIGN SUMMARY")
    lines.append("=" * 70)
    lines.append("")

    # Campaign info
    lines.append("CAMPAIGN INFORMATION")
    lines.append("-" * 70)
    lines.append(f"Company: {analysis['company_name']}")
    lines.append(f"Job Title: {analysis['job_title']}")
    lines.append(f"Mode: {mode.upper()}")
    lines.append(f"Role Type: {analysis['role_type']}")
    lines.append("")

    # Job analysis summary
    lines.append("JOB ANALYSIS")
    lines.append("-" * 70)
    lines.append(f"Summary: {analysis['summary']}")
    lines.append("")
    lines.append("Employer Priorities:")
    for priority in analysis["employer_priorities"]:
        lines.append(f"  • {priority}")
    lines.append("")
    lines.append("Core Requirements:")
    for req in analysis["core_requirements"]:
        lines.append(f"  • {req}")
    lines.append("")
    lines.append("Pain Points This Hire Solves:")
    for pain in analysis["pain_points"]:
        lines.append(f"  • {pain}")
    lines.append("")
    lines.append(f"Positioning Angle:\n{analysis['positioning_angle']}")
    lines.append("")

    # Target contacts
    lines.append("TARGET CONTACTS")
    lines.append("-" * 70)
    lines.append("Target Titles:")
    for title in targets["target_titles"]:
        lines.append(f"  • {title}")
    lines.append("")
    lines.append("Target Departments:")
    for dept in targets["target_departments"]:
        lines.append(f"  • {dept}")
    lines.append("")
    lines.append(f"Rationale:\n{targets['rationale']}")
    lines.append("")

    # Outreach messages
    lines.append("OUTREACH MESSAGES")
    lines.append("=" * 70)
    lines.append("")

    # Initial cold email
    lines.append("INITIAL COLD EMAIL")
    lines.append("-" * 70)
    lines.append(f"Subject: {messages['initial_cold_email']['subject']}")
    lines.append("")
    lines.append(f"Body:\n{messages['initial_cold_email']['body']}")
    lines.append("")

    # Follow-up 1
    lines.append("FOLLOW-UP 1 (After 3-5 days)")
    lines.append("-" * 70)
    lines.append(f"Subject: {messages['followup_1']['subject']}")
    lines.append("")
    lines.append(f"Body:\n{messages['followup_1']['body']}")
    lines.append("")

    # Follow-up 2
    lines.append("FOLLOW-UP 2 (After 7-10 days)")
    lines.append("-" * 70)
    lines.append(f"Subject: {messages['followup_2']['subject']}")
    lines.append("")
    lines.append(f"Body:\n{messages['followup_2']['body']}")
    lines.append("")

    # LinkedIn messages
    lines.append("LINKEDIN OUTREACH")
    lines.append("=" * 70)
    lines.append("")
    lines.append("CONNECTION REQUEST:")
    lines.append("-" * 70)
    lines.append(f"{messages['linkedin_connection_request']}")
    lines.append("")
    lines.append("FOLLOW-UP MESSAGE (After connection accepted):")
    lines.append("-" * 70)
    lines.append(f"{messages['linkedin_followup']}")
    lines.append("")

    # Usage notes
    lines.append("USAGE NOTES")
    lines.append("=" * 70)
    lines.append("1. Review all messages for accuracy and relevance")
    lines.append("2. Personalize with specific contact names and details")
    lines.append("3. For email: Consider timing between follow-ups (3-5 days, then 7-10 days)")
    lines.append("4. For LinkedIn: Use connection message as-is, customize if needed")
    lines.append("5. Track responses in job_tracker.csv")
    lines.append("6. Use Saleshandy CSV for batch email campaign setup")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
