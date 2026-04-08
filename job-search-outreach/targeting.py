"""
Target contact determination based on job analysis and role mode.
Identifies the right job titles and departments to reach for outreach.
"""

import json

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from prompts import format_targeting_prompt


def generate_targets(job_analysis: dict, mode: str) -> dict:
    """
    Generate target contact titles and departments based on job analysis.

    For TA mode: Suggests recruiting and talent-specific titles.
    For AI mode: Uses OpenAI to infer target titles based on the role's impact.

    Args:
        job_analysis: The job analysis dictionary from analyze_job()
        mode: Either "ta" (talent acquisition) or "ai" (AI roles)

    Returns:
        Dictionary with keys:
        - target_titles (list of str): Job titles to target
        - target_departments (list of str): Departments where targets sit
        - rationale (str): Why these contacts would care about outreach

    Raises:
        ValueError: If analysis is invalid or API response fails
        Exception: If OpenAI API call fails
    """
    if mode not in ("ta", "ai"):
        raise ValueError(f"Invalid mode: {mode}")

    if "company_name" not in job_analysis or "job_title" not in job_analysis:
        raise ValueError("job_analysis missing required fields")

    try:
        if mode == "ta":
            # TA mode: use predefined recruiting-focused titles
            return _generate_ta_targets(job_analysis)
        else:
            # AI mode: use OpenAI to determine targets based on role type
            return _generate_ai_targets(job_analysis)

    except Exception as e:
        raise Exception(f"Error generating targets: {e}")


def _generate_ta_targets(job_analysis: dict) -> dict:
    """
    Generate TA-specific target titles.

    For talent acquisition roles, target other recruiting leaders
    who understand hiring challenges.

    Args:
        job_analysis: The job analysis dictionary

    Returns:
        Dictionary with target_titles, target_departments, rationale
    """
    # Recruiting-focused titles
    recruiting_titles = [
        "VP of Talent Acquisition",
        "Head of Recruiting",
        "Recruiting Director",
        "Recruiting Manager",
        "Talent Acquisition Manager",
        "Head of People Operations",
        "Talent Operations Manager",
        "Recruitment Manager",
        "Staffing Director",
    ]

    departments = [
        "Talent Acquisition",
        "People/HR Operations",
        "Human Resources",
        "Recruiting",
        "Talent/People",
    ]

    rationale = (
        f"These recruiting and talent leaders understand the challenges of hiring for roles "
        f"like '{job_analysis['job_title']}' and would benefit from discussing your experience "
        f"building talent processes and managing stakeholders."
    )

    return {
        "target_titles": recruiting_titles[:6],  # Return top 6
        "target_departments": departments,
        "rationale": rationale,
    }


def _generate_ai_targets(job_analysis: dict) -> dict:
    """
    Use OpenAI to determine target titles for AI mode.

    Analyzes the job to understand who would be impacted by the AI role
    and what departments would benefit from the hire.

    Args:
        job_analysis: The job analysis dictionary

    Returns:
        Dictionary with target_titles, target_departments, rationale
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Format targeting prompt
        prompt = format_targeting_prompt(
            company_name=job_analysis["company_name"],
            job_title=job_analysis["job_title"],
            role_type=job_analysis.get("role_type", "AI/operations"),
            mode="ai",
            job_description=job_analysis.get(
                "description", job_analysis["job_title"]
            ),
        )

        # Call OpenAI
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        # Parse response
        response_text = response.choices[0].message.content
        targets = json.loads(response_text)

        # Validate response
        required_fields = ["target_titles", "target_departments", "rationale"]
        for field in required_fields:
            if field not in targets:
                raise ValueError(f"Missing field in targets response: {field}")

        return targets

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse OpenAI response as JSON: {e}")
    except Exception as e:
        raise Exception(f"Error calling OpenAI API: {e}")


def display_targets(targets: dict) -> None:
    """
    Display target contacts in a readable format.

    Args:
        targets: The targets dictionary from generate_targets()
    """
    print("\n=== TARGET CONTACTS ===\n")

    print("Target Titles:")
    for title in targets["target_titles"]:
        print(f"  • {title}")

    print("\nTarget Departments:")
    for dept in targets["target_departments"]:
        print(f"  • {dept}")

    print(f"\nRationale:\n{targets['rationale']}\n")
