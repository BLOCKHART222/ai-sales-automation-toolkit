#!/usr/bin/env python3
"""
AI Sales System Tool for Small/Mid-Sized Businesses
Generates comprehensive AI opportunity analysis and sales toolkit
Outputs professional .docx file with 6 sections
"""

import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not found in .env file")
    sys.exit(1)

MODEL = "gpt-4o"
TEMPERATURE = 0.7


def sanitize_filename(company_name: str) -> str:
    """Remove special characters from company name for filename."""
    sanitized = re.sub(r'[^a-zA-Z0-9_\-]', '', company_name.replace(' ', '_'))
    return sanitized[:50]  # Cap at 50 chars


def call_openai(prompt: str) -> str:
    """Call OpenAI API and return response text."""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            temperature=TEMPERATURE,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"ERROR: OpenAI API call failed: {e}")
        sys.exit(1)


def generate_company_analysis(company_name: str, website: str = None) -> str:
    """Generate Section 1: Company Analysis"""
    print("→ Generating company analysis...")
    
    website_info = f"Website: {website}" if website else "No website provided"
    
    prompt = f"""You are an elite AI consultant and sales strategist. Analyze this company:

Company: {company_name}
{website_info}

Generate a professional, concise SECTION 1: COMPANY ANALYSIS covering:
1. What the business likely does (be specific based on name/website)
2. How it likely gets customers (primary channels)
3. Where revenue is likely won or lost (critical revenue dynamics)
4. Where inefficiencies and blind spots likely exist (gaps in their operations/tech)

Write in bullet points. Be commercial and practical. No fluff. Focus on SMB context (not enterprise).
Keep it under 500 words. Assume they're running lean with limited tech staff."""

    return call_openai(prompt)


def generate_pain_points(company_name: str, analysis: str) -> str:
    """Generate Section 2: Industry Pain Points & Blind Spots"""
    print("→ Generating pain points and blind spots...")
    
    prompt = f"""Based on this company analysis:

{analysis}

Generate SECTION 2: INDUSTRY PAIN POINTS & BLIND SPOTS

For 4-5 realistic pain points affecting {company_name}, cover each with:
- The problem (concrete, specific)
- Why it exists (root cause)
- What it costs (time, money, lost revenue — be realistic)
- How AI fixes it (applied AI solution, not research)
- Expected outcome (measurable improvement)

Use bullet points. Be commercially sharp. Focus on SMB-scale problems.
Total: 600-800 words."""

    return call_openai(prompt)


def generate_ai_opportunities(company_name: str, analysis: str, pain_points: str) -> str:
    """Generate Section 3: AI Opportunities by Business Area"""
    print("→ Generating AI opportunities by business area...")
    
    prompt = f"""Based on this company:

Company: {company_name}
Analysis: {analysis}
Pain Points: {pain_points}

Generate SECTION 3: AI OPPORTUNITIES BY BUSINESS AREA

Cover these 5 areas (only if relevant to {company_name}):
1. Customer Acquisition
2. Sales
3. Marketing
4. Customer Service / Retention
5. Operations / Admin

For each relevant area, structure as:
- Current State (how they do it now)
- AI Solution (specific automation/tool)
- Expected Impact (timeline, measurable results)

Use headings and bullets. Be practical. No enterprise-scale tools.
Focus on solutions a solo AI operator can implement.
Total: 700-900 words."""

    return call_openai(prompt)


def generate_automation_workflows(company_name: str, opportunities: str) -> str:
    """Generate Section 4: Advanced Automation / Workflow Systems"""
    print("→ Generating automation workflows...")
    
    prompt = f"""Based on these AI opportunities for {company_name}:

{opportunities}

Generate SECTION 4: ADVANCED AUTOMATION / WORKFLOW SYSTEMS

Design 3-4 specific, implementable workflows:

For each workflow, structure as:
- Workflow name
- Trigger (what starts it)
- Steps (sequential automation steps)
- Where AI is used (which step uses AI/LLM)
- What gets automated (manual tasks eliminated)
- Business result (what improves)

Use Zapier/Make logic. Be concrete and implementable by a solo operator.
Include realistic triggers and outputs.
Total: 600-800 words."""

    return call_openai(prompt)


def generate_sales_toolkit(company_name: str, analysis: str) -> str:
    """Generate Section 5: Sales Toolkit"""
    print("→ Generating sales toolkit...")
    
    prompt = f"""You're selling AI services to {company_name}. Based on the analysis:

{analysis}

Generate SECTION 5: SALES TOOLKIT

Include:

1. What to Sell First
   - Your primary offer (most impactful, easiest to implement)
   - Why it matters to them specifically

2. Pitch Angle
   - 2-3 sentence hook addressing their actual business pain
   - Why AI solves it for them (not generic AI benefits)

3. Objections & Responses
   - 3-4 realistic objections (cost, implementation, complexity)
   - Sharp, professional responses (not dismissive)

4. Personal Text Message Template
   - One text to reach out (casual but professional)
   - Should reference something specific about their business

5. Cold Email Sequence
   - Email 1: Hook (problem + curiosity)
   - Email 2: Proof (case example + credibility)
   - Email 3: Call-to-action (low-friction offer)
   - Each email: subject line + 50-100 word body

6. Reusable Industry Angle
   - 2-3 sentence narrative you can use for similar companies in their space

Write for a solo operator. Commercial tone. No fluff.
Total: 800-1000 words."""

    return call_openai(prompt)


def generate_similar_companies(company_name: str, analysis: str) -> str:
    """Generate Section 6: Similar Target Companies"""
    print("→ Generating similar target companies...")
    
    prompt = f"""Based on {company_name}:

{analysis}

Generate SECTION 6: SIMILAR TARGET COMPANIES

List 7-10 realistic small/mid-sized companies in the same or similar industry.

For each, include:
- Company name (realistic, searchable)
- What they do (one sentence)
- Realistic decision-maker titles (who buys AI services)
- Why they're a good fit (same pain points, similar business model)

Requirements:
- SMB only, no enterprise (under 500 employees ideally)
- Same geographic region or industry
- Real business types (use actual company examples where possible)
- Include realistic titles: Operations Manager, Sales Manager, CEO, etc.

Format as a bulleted list. Keep it scannable.
Total: 400-600 words."""

    return call_openai(prompt)


def create_docx(company_name: str, sections: dict) -> str:
    """Create professional .docx document with all sections."""
    print("→ Creating Word document...")
    
    doc = Document()
    
    # Title
    title = doc.add_paragraph()
    title_run = title.add_run(f"AI Sales System: {company_name}")
    title_run.font.size = Pt(24)
    title_run.font.bold = True
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    subtitle = doc.add_paragraph(f"Comprehensive AI Opportunity Analysis & Sales Toolkit")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_run = subtitle.runs[0]
    subtitle_run.font.size = Pt(12)
    subtitle_run.font.italic = True
    subtitle_run.font.color.rgb = RGBColor(100, 100, 100)
    
    doc.add_paragraph()  # Spacing
    
    # Add sections
    for section_title, section_content in sections.items():
        # Section heading
        heading = doc.add_heading(section_title, level=1)
        heading_format = heading.paragraph_format
        heading_format.space_before = Pt(12)
        heading_format.space_after = Pt(6)
        
        # Section content (preserve formatting from API response)
        for line in section_content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Bold section subheadings (lines ending with colon)
            if line.endswith(':') and len(line) < 100:
                p = doc.add_paragraph(line, style='Heading 2')
            # Bullet points (lines starting with dash or bullet)
            elif line.startswith('-') or line.startswith('•'):
                doc.add_paragraph(line[1:].strip(), style='List Bullet')
            # Regular paragraph
            else:
                doc.add_paragraph(line)
    
    # Save document
    filename = f"{sanitize_filename(company_name)}_ai_sales_system.docx"
    doc.save(filename)
    
    return filename


def main():
    """Main pipeline: gather input, call APIs, generate document."""
    print("\n" + "="*60)
    print("AI SALES SYSTEM TOOL - Small/Mid-Sized Business Analysis")
    print("="*60 + "\n")
    
    # Get company name
    company_name = input("Enter company name: ").strip()
    if not company_name:
        print("ERROR: Company name is required")
        sys.exit(1)
    
    # Get optional website
    website = input("Enter company website (optional, press Enter to skip): ").strip()
    
    print("\n" + "="*60)
    print("Generating comprehensive AI opportunity analysis...")
    print("="*60 + "\n")
    
    # Generate all sections
    analysis = generate_company_analysis(company_name, website)
    pain_points = generate_pain_points(company_name, analysis)
    opportunities = generate_ai_opportunities(company_name, analysis, pain_points)
    workflows = generate_automation_workflows(company_name, opportunities)
    toolkit = generate_sales_toolkit(company_name, analysis)
    targets = generate_similar_companies(company_name, analysis)
    
    # Organize sections in order
    sections = {
        "SECTION 1: COMPANY ANALYSIS": analysis,
        "SECTION 2: INDUSTRY PAIN POINTS & BLIND SPOTS": pain_points,
        "SECTION 3: AI OPPORTUNITIES BY BUSINESS AREA": opportunities,
        "SECTION 4: ADVANCED AUTOMATION / WORKFLOW SYSTEMS": workflows,
        "SECTION 5: SALES TOOLKIT": toolkit,
        "SECTION 6: SIMILAR TARGET COMPANIES": targets,
    }
    
    # Create Word document
    filename = create_docx(company_name, sections)
    
    # Print summary
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print(f"\nDocument saved: {filename}")
    print(f"Company: {company_name}")
    print(f"Sections generated: 6")
    print(f"Total content: ~4000-5000 words")
    print("\nReady to use as:")
    print("  • Sales toolkit for outreach")
    print("  • Pitch deck foundation")
    print("  • Internal strategy document")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
