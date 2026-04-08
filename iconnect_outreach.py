#!/usr/bin/env python3
"""
iconnect_outreach.py — AI-powered outreach campaign generator
Generates complete B2B outreach campaigns for Bryan Lockhart's AI services business.
Uses OpenAI API (gpt-4o) to create industry-specific positioning, emails, and follow-ups.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_user_inputs():
    """Collect campaign parameters from user."""
    print("\n" + "=" * 60)
    print("ICONNECT OUTREACH CAMPAIGN GENERATOR")
    print("=" * 60)
    print("\nEnter your campaign parameters:\n")

    industry = input("Industry (e.g., sports training, dental offices, gyms): ").strip()
    location = input("Location (e.g., Dallas TX, nationwide, Southeast US): ").strip()
    target_roles = input("Target roles (e.g., Owner, General Manager, Marketing Director): ").strip()
    company_type = input("Company type (e.g., youth sports academies, boutique gyms): ").strip()

    if not all([industry, location, target_roles, company_type]):
        print("\n❌ Error: All fields are required.")
        sys.exit(1)

    return {
        "industry": industry,
        "location": location,
        "target_roles": target_roles,
        "company_type": company_type
    }


def generate_campaign(params):
    """Generate complete outreach campaign using OpenAI API."""
    print("\n→ Generating outreach campaign...")

    prompt = f"""You are an expert B2B sales and marketing strategist for AI services. Generate a complete, professional outreach campaign.

CONTEXT:
- Industry: {params['industry']}
- Location: {params['location']}
- Target Decision Makers: {params['target_roles']}
- Company Type: {params['company_type']}

IMPORTANT: The service being offered is AI automation and workflow solutions for business operations. This includes custom AI agents, workflow automation, and implementation guidance.

Generate exactly these 7 sections:

1. IDEAL CUSTOMER PROFILE
Describe the perfect target prospect: company size, revenue range, team size, current stage, key problems, why they'd buy AI services now.

2. OUTREACH ANGLE
The strategic positioning for reaching out. What value prop to lead with. Why this segment cares about AI. The "why now" urgency.

3. OFFER
What's being offered specifically. Service structure (audit → implementation → ongoing). Value positioning. What makes this different.

4. COLD EMAILS (3 emails)
Email 1: Initial hook + value prop + soft CTA
Email 2: Different angle - case study/social proof
Email 3: Breakup email - urgency, final attempt
Format each as: [SUBJECT] / [BODY]

5. FOLLOW-UPS (2 follow-ups)
Follow-up 1: After no reply to email 1 - new insight
Follow-up 2: After no reply to email 2 - ultra-short
Format each as: [SUBJECT] / [BODY]

6. PERSONALIZATION LINES (3)
One-liners that reference their industry/business. Can open any email. Specific, not generic.

7. HOW AI IS USED IN THE OFFER
What automation is being offered. What AI agents do. What workflows get built. Specific examples tied to {params['industry']}. Make it tangible.

TONE: Real business development copy. Sharp, confident, commercially aware. Not robotic or generic. Written by someone who actually does outbound.

Generate now:"""

    try:
        response = client.messages.create(
            model="gpt-4o",
            max_tokens=3000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.content[0].text

    except Exception as e:
        print(f"\n❌ Error calling OpenAI API: {e}")
        sys.exit(1)


def save_campaign(campaign_text, params):
    """Save campaign to timestamped file and latest output file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    industry_slug = params["industry"].lower().replace(" ", "_")

    # Timestamped file
    timestamped_filename = f"outreach_{industry_slug}_{timestamp}.txt"
    with open(timestamped_filename, "w") as f:
        f.write(f"OUTREACH CAMPAIGN\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Industry: {params['industry']}\n")
        f.write(f"Location: {params['location']}\n")
        f.write(f"Target Roles: {params['target_roles']}\n")
        f.write(f"Company Type: {params['company_type']}\n")
        f.write(f"\n{'=' * 60}\n\n")
        f.write(campaign_text)

    # Latest output file (overwritten each run)
    with open("outreach_output.txt", "w") as f:
        f.write(f"OUTREACH CAMPAIGN\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Industry: {params['industry']}\n")
        f.write(f"Location: {params['location']}\n")
        f.write(f"Target Roles: {params['target_roles']}\n")
        f.write(f"Company Type: {params['company_type']}\n")
        f.write(f"\n{'=' * 60}\n\n")
        f.write(campaign_text)

    return timestamped_filename


def print_campaign(campaign_text):
    """Print campaign to terminal."""
    print("\n" + "=" * 60)
    print("CAMPAIGN OUTPUT")
    print("=" * 60 + "\n")
    print(campaign_text)
    print("\n" + "=" * 60)


def main():
    """Main execution flow."""
    try:
        # Get user inputs
        params = get_user_inputs()

        # Generate campaign
        campaign_text = generate_campaign(params)

        # Print to terminal
        print_campaign(campaign_text)

        # Save to files
        timestamped_file = save_campaign(campaign_text, params)

        # Confirmation
        print(f"\n✅ Campaign saved to:")
        print(f"   → {timestamped_file}")
        print(f"   → outreach_output.txt (latest)")
        print("\nDone.\n")

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
