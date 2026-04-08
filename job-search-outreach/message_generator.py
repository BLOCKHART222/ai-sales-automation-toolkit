"""
Message generation for job outreach campaigns.
Creates personalized cold emails, follow-ups, and LinkedIn messages.
"""

import json
from typing import Optional

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from prompts import format_message_generation_prompt


def generate_messages(
    job_analysis: dict, targets: dict, mode: str, resume_text: str
) -> dict:
    """
    Generate personalized outreach messages for a job opportunity.

    Creates:
    - Initial cold email (subject + body)
    - Two follow-up emails (subject + body)
    - LinkedIn connection request message
    - LinkedIn follow-up message

    All messages are:
    - Concise, confident, high-conviction
    - Commercially aware and personalized
    - NOT generic (no "I know you're busy", "just checking in", etc.)
    - Positioned according to the candidate's mode (TA or AI)

    Args:
        job_analysis: The job analysis dictionary from analyze_job()
        targets: The targets dictionary from generate_targets()
        mode: Either "ta" (talent acquisition) or "ai" (AI roles)
        resume_text: The candidate's resume summary

    Returns:
        Dictionary with keys:
        - initial_cold_email: dict with "subject" and "body"
        - followup_1: dict with "subject" and "body"
        - followup_2: dict with "subject" and "body"
        - linkedin_connection_request: str
        - linkedin_followup: str

    Raises:
        ValueError: If API response is invalid or parsing fails
        Exception: If OpenAI API call fails
    """
    if mode not in ("ta", "ai"):
        raise ValueError(f"Invalid mode: {mode}")

    if "company_name" not in job_analysis:
        raise ValueError("job_analysis missing company_name")

    if "target_titles" not in targets:
        raise ValueError("targets missing target_titles")

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Format the prompt
        prompt = format_message_generation_prompt(
            company_name=job_analysis["company_name"],
            role_type=job_analysis.get("role_type", ""),
            mode=mode,
            target_titles=targets["target_titles"],
            positioning_angle=job_analysis["positioning_angle"],
            resume_text=resume_text,
        )

        # Call OpenAI with JSON mode
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        # Extract and parse JSON response
        response_text = response.choices[0].message.content
        messages = json.loads(response_text)

        # Validate expected fields
        required_fields = [
            "initial_cold_email",
            "followup_1",
            "followup_2",
            "linkedin_connection_request",
            "linkedin_followup",
        ]

        for field in required_fields:
            if field not in messages:
                raise ValueError(f"Missing field in messages: {field}")

        # Validate email format
        for email_key in ["initial_cold_email", "followup_1", "followup_2"]:
            if not isinstance(messages[email_key], dict):
                raise ValueError(f"{email_key} must be a dict")
            if "subject" not in messages[email_key] or "body" not in messages[email_key]:
                raise ValueError(f"{email_key} missing subject or body")

        return messages

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse OpenAI response as JSON: {e}")
    except Exception as e:
        raise Exception(f"Error calling OpenAI API: {e}")


def display_messages(messages: dict) -> None:
    """
    Display generated messages in a readable format.

    Args:
        messages: The messages dictionary from generate_messages()
    """
    print("\n=== OUTREACH MESSAGES ===\n")

    # Initial cold email
    print("--- INITIAL COLD EMAIL ---")
    print(f"Subject: {messages['initial_cold_email']['subject']}")
    print(f"\n{messages['initial_cold_email']['body']}\n")

    # Follow-up 1
    print("--- FOLLOW-UP 1 ---")
    print(f"Subject: {messages['followup_1']['subject']}")
    print(f"\n{messages['followup_1']['body']}\n")

    # Follow-up 2
    print("--- FOLLOW-UP 2 ---")
    print(f"Subject: {messages['followup_2']['subject']}")
    print(f"\n{messages['followup_2']['body']}\n")

    # LinkedIn messages
    print("--- LINKEDIN CONNECTION REQUEST ---")
    print(f"{messages['linkedin_connection_request']}\n")

    print("--- LINKEDIN FOLLOW-UP ---")
    print(f"{messages['linkedin_followup']}\n")


def export_messages_json(messages: dict, filepath: str) -> None:
    """
    Export generated messages to a JSON file.

    Args:
        messages: The messages dictionary from generate_messages()
        filepath: Path where to save the JSON file
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)


def export_messages_text(
    messages: dict, job_analysis: dict, filepath: str
) -> None:
    """
    Export generated messages to a formatted text file.

    Args:
        messages: The messages dictionary from generate_messages()
        job_analysis: The job analysis dictionary
        filepath: Path where to save the text file
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Job Outreach Campaign\n")
        f.write(f"{'='*50}\n\n")

        f.write(f"Company: {job_analysis['company_name']}\n")
        f.write(f"Role: {job_analysis['job_title']}\n")
        f.write(f"Generated: {filepath}\n\n")

        f.write("INITIAL COLD EMAIL\n")
        f.write(f"{'-'*50}\n")
        f.write(f"Subject: {messages['initial_cold_email']['subject']}\n\n")
        f.write(f"{messages['initial_cold_email']['body']}\n\n")

        f.write("FOLLOW-UP 1\n")
        f.write(f"{'-'*50}\n")
        f.write(f"Subject: {messages['followup_1']['subject']}\n\n")
        f.write(f"{messages['followup_1']['body']}\n\n")

        f.write("FOLLOW-UP 2\n")
        f.write(f"{'-'*50}\n")
        f.write(f"Subject: {messages['followup_2']['subject']}\n\n")
        f.write(f"{messages['followup_2']['body']}\n\n")

        f.write("LINKEDIN CONNECTION REQUEST\n")
        f.write(f"{'-'*50}\n")
        f.write(f"{messages['linkedin_connection_request']}\n\n")

        f.write("LINKEDIN FOLLOW-UP\n")
        f.write(f"{'-'*50}\n")
        f.write(f"{messages['linkedin_followup']}\n")
