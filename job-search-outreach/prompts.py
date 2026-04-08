"""
OpenAI prompt templates for job analysis, targeting, and message generation.
All prompts are designed to produce high-quality, structured output.
"""

JOB_ANALYSIS_PROMPT = """
Analyze this job posting and extract key hiring intelligence. Return valid JSON.

Job Description:
{job_description}

Candidate Background:
{resume_text}

Mode: {mode}

Analyze and return a JSON object with these exact fields:
- company_name: (string) The company name from the posting
- job_title: (string) The specific job title
- role_type: (string) Category like "recruiting", "operations", "talent_strategy", "talent_ops"
- summary: (string) 2-3 sentence summary of the role
- employer_priorities: (array of strings) What the employer actually cares about (3-5 items)
- core_requirements: (array of strings) Must-have skills/experience (3-5 items)
- pain_points: (array of strings) Problems this hire will solve (2-3 items)
- positioning_angle: (string) How to position {mode} candidate's experience as relevant to THIS company's needs

Be specific and insightful. Focus on what this company needs, not generic job posting language.
"""

TARGETING_PROMPT = """
Determine the best contact titles for this job opportunity.

Company: {company_name}
Job Title: {job_title}
Role Type: {role_type}
Mode: {mode}

Job Context:
{job_description}

You are helping someone reach decision-makers who need to solve the problem this job posting indicates.

For TA mode: Return recruiting/talent professionals who would care about this opening or hiring challenges.
For AI mode: Return operators, leaders, or stakeholders who understand workflow pain this AI role will solve.

Return a JSON object with:
- target_titles: (array of 4-6 specific job titles)
- target_departments: (array of 2-3 departments where these people sit)
- rationale: (string) Why these contacts would care about our outreach

Focus on titles of people who actually make decisions, not HR generalists.
"""

MESSAGE_GENERATION_PROMPT = """
Generate compelling outreach messages for this opportunity.

Company: {company_name}
Role Type: {role_type}
Candidate Mode: {mode}

Target Contacts: {target_titles}
Positioning Angle: {positioning_angle}

Candidate Background:
{resume_text}

Generate a JSON object with these exact fields:

1. initial_cold_email: {{
   "subject": "compelling subject line (5-8 words, no generic templates)",
   "body": "concise body (150-200 words, high-conviction, specific to their company)"
}}

2. followup_1: {{
   "subject": "follow-up subject (reference previous conversation)",
   "body": "brief follow-up (100-150 words, adds new insight or value)"
}}

3. followup_2: {{
   "subject": "second follow-up subject",
   "body": "final follow-up (80-120 words, creates urgency or clear next step)"
}}

4. linkedin_connection_request: "connection message (50-80 words, specific to their profile)"

5. linkedin_followup: "follow-up message after connection (100-150 words, provides value)"

TONE REQUIREMENTS:
- Polished, confident, commercially aware
- NOT generic ("I know you're busy", "just checking in", "I'd love to pick your brain")
- NOT desperate or overly formal
- Personalized to the company and their pain points
- Position candidate as experienced professional, not junior/transitioning
- For AI mode: leverage ops/recruiting background as advantage for understanding their workflow
- For TA mode: position as process builder and stakeholder manager who understands hiring challenges
- High signal-to-noise ratio

PROHIBITED PHRASES (absolutely no):
- "I know you're busy"
- "Just checking in"
- "I'd love to pick your brain"
- "I'm passionate about"
- "Quick question"
- "Wanted to reach out"
- Generic "excited about your company"
"""

def format_job_analysis_prompt(
    job_description: str, resume_text: str, mode: str
) -> str:
    """
    Format the job analysis prompt with provided values.

    Args:
        job_description: The job posting text
        resume_text: The candidate's resume
        mode: Either "ta" or "ai"

    Returns:
        Formatted prompt string
    """
    return JOB_ANALYSIS_PROMPT.format(
        job_description=job_description, resume_text=resume_text, mode=mode
    )


def format_targeting_prompt(
    company_name: str,
    job_title: str,
    role_type: str,
    mode: str,
    job_description: str,
) -> str:
    """
    Format the targeting prompt with provided values.

    Args:
        company_name: Name of the target company
        job_title: Title of the open position
        role_type: Type of role (recruiting, ops, etc.)
        mode: Either "ta" or "ai"
        job_description: The job posting text

    Returns:
        Formatted prompt string
    """
    return TARGETING_PROMPT.format(
        company_name=company_name,
        job_title=job_title,
        role_type=role_type,
        mode=mode,
        job_description=job_description,
    )


def format_message_generation_prompt(
    company_name: str,
    role_type: str,
    mode: str,
    target_titles: list[str],
    positioning_angle: str,
    resume_text: str,
) -> str:
    """
    Format the message generation prompt with provided values.

    Args:
        company_name: Name of the target company
        role_type: Type of role
        mode: Either "ta" or "ai"
        target_titles: List of target job titles
        positioning_angle: How to position the candidate
        resume_text: The candidate's resume

    Returns:
        Formatted prompt string
    """
    return MESSAGE_GENERATION_PROMPT.format(
        company_name=company_name,
        role_type=role_type,
        mode=mode,
        target_titles=", ".join(target_titles),
        positioning_angle=positioning_angle,
        resume_text=resume_text,
    )
