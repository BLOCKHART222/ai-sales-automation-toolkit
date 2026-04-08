"""
Job posting analysis using OpenAI API.
Extracts key hiring intelligence and company needs from job descriptions.
"""

import json
from typing import Optional

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from prompts import format_job_analysis_prompt


def analyze_job(description: str, mode: str, resume_text: str) -> dict:
    """
    Analyze a job posting and extract key hiring intelligence.

    Uses OpenAI to determine:
    - Company name and job title
    - Role type (recruiting, operations, etc.)
    - Summary of responsibilities
    - Employer priorities (what they actually care about)
    - Core requirements (must-have skills)
    - Pain points the hire will solve
    - How to position the candidate's background

    Args:
        description: The job posting text
        mode: Either "ta" (talent acquisition) or "ai" (AI roles)
        resume_text: The candidate's resume summary

    Returns:
        Dictionary with keys:
        - company_name (str)
        - job_title (str)
        - role_type (str)
        - summary (str)
        - employer_priorities (list of str)
        - core_requirements (list of str)
        - pain_points (list of str)
        - positioning_angle (str)

    Raises:
        ValueError: If API response is invalid or parsing fails
        Exception: If OpenAI API call fails
    """
    if not description.strip():
        raise ValueError("Job description cannot be empty")

    if mode not in ("ta", "ai"):
        raise ValueError(f"Invalid mode: {mode}")

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Format the prompt
        prompt = format_job_analysis_prompt(description, resume_text, mode)

        # Call OpenAI with JSON mode for structured output
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        # Extract and parse JSON response
        response_text = response.choices[0].message.content
        analysis = json.loads(response_text)

        # Validate expected fields
        required_fields = [
            "company_name",
            "job_title",
            "role_type",
            "summary",
            "employer_priorities",
            "core_requirements",
            "pain_points",
            "positioning_angle",
        ]

        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"Missing field in analysis: {field}")

        return analysis

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse OpenAI response as JSON: {e}")
    except Exception as e:
        raise Exception(f"Error calling OpenAI API: {e}")


def display_analysis(analysis: dict) -> None:
    """
    Display job analysis in a readable format.

    Args:
        analysis: The job analysis dictionary from analyze_job()
    """
    print("\n=== JOB ANALYSIS ===\n")
    print(f"Company: {analysis['company_name']}")
    print(f"Job Title: {analysis['job_title']}")
    print(f"Role Type: {analysis['role_type']}\n")

    print(f"Summary:\n{analysis['summary']}\n")

    print("Employer Priorities:")
    for priority in analysis["employer_priorities"]:
        print(f"  • {priority}")

    print("\nCore Requirements:")
    for req in analysis["core_requirements"]:
        print(f"  • {req}")

    print("\nPain Points This Hire Solves:")
    for pain in analysis["pain_points"]:
        print(f"  • {pain}")

    print(f"\nPositioning Angle:\n{analysis['positioning_angle']}\n")
