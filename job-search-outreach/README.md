# AI Job Outreach System

An intelligent job outreach automation tool that analyzes job postings and generates personalized cold email campaigns with follow-ups and LinkedIn messaging.

## What It Does

This system helps job candidates and recruiters identify the right people to reach out to for job opportunities and generates professionally-crafted outreach messages tailored to specific companies and roles.

**Workflow:**
1. Input a job posting (URL and/or description)
2. Select outreach mode (Talent Acquisition or AI Roles)
3. AI analyzes the job and identifies key hiring intelligence
4. System generates target contact titles and departments
5. Creates personalized cold email, follow-ups, and LinkedIn messages
6. Exports results in multiple formats (JSON, CSV, text summary)
7. Logs campaign details to tracker for follow-up management

## Architecture

```
Job Input
    ↓
Job Analysis (OpenAI) → Extract company, role, priorities, pain points
    ↓
Target Generation (OpenAI) → Identify decision-makers to reach
    ↓
Message Generation (OpenAI) → Create personalized outreach
    ↓
Exports
    ├→ summary.txt (formatted text)
    ├→ results.json (complete data)
    ├→ saleshandy_campaign.csv (for Saleshandy import)
    └→ job_tracker.csv (campaign log)
```

## Modes

### TA Mode (Talent Acquisition)
For job seekers targeting Talent Acquisition and Recruiting leadership roles. Generates outreach emphasizing recruiting expertise, process building, and team leadership.

### AI Mode (AI/Operations Roles)
For professionals transitioning into AI operations and workflow automation roles. Generates outreach positioning background in operations combined with AI automation skills.

## Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key
- Mac or Linux environment

### Installation (Mac + VS Code)

1. **Clone or download the project**
   ```bash
   cd /path/to/Job\ Outreach
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add API key**
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=sk-your-actual-key-here
     ```

5. **Add resume files** (if not already present)
   - Create `resume_ta.txt` with your TA-focused resume
   - Create `resume_ai.txt` with your AI-focused resume

6. **Run the tool**
   ```bash
   python main.py
   ```

## Example Commands

### Interactive Mode (Recommended)
```bash
python main.py
# Follow prompts to:
# - Enter job URL (optional)
# - Paste job description (required)
# - Select mode (ta or ai)
```

### Example Inputs
See included example files:
- `input_example_ta.json` - Senior Recruiter position
- `input_example_ai.json` - AI Operations Specialist position

Run with input files:
```bash
# To use example, edit job_input.py to accept file argument, then:
python main.py < input_example_ta.json
```

## Output Structure

Each run creates a timestamped output directory: `outputs/YYYY-MM-DD_HHMMSS/`

**Files generated:**
- `summary.txt` - Human-readable campaign summary and messages
- `results.json` - All data in JSON format
- `saleshandy_campaign.csv` - Import-ready format for Saleshandy
- `job_tracker.csv` - Appended campaign log (global file)

**Example output:**
```
outputs/
└── 2026-04-08_143000/
    ├── company_name_summary.txt
    ├── company_name_results.json
    └── saleshandy_campaign.csv

job_tracker.csv (shared across all campaigns)
```

## Campaign Tracker

`job_tracker.csv` maintains a log of all campaigns with:
- Date, company, job title
- Mode and source URL
- Target contact titles
- Outreach status (pending → sent → followup)
- Campaign ID for reference
- Resume used

Use this to track which companies/roles you've targeted and manage follow-up timing.

## Tech Stack

- **Language:** Python 3.9+
- **AI:** OpenAI GPT-4o for analysis and message generation
- **Data:** JSON, CSV
- **Environment:** .env for configuration
- **Package Manager:** pip

## Project Files

### Core Modules
- `main.py` - CLI entry point and orchestration
- `config.py` - Configuration and environment loading
- `job_input.py` - Job posting input collection
- `job_analyzer.py` - OpenAI-powered job analysis
- `targeting.py` - Target contact generation
- `message_generator.py` - Outreach message creation

### Support Modules
- `utils.py` - File I/O, formatting, console output
- `tracker.py` - Campaign logging and tracking
- `saleshandy_formatter.py` - Saleshandy CSV export
- `prompts.py` - OpenAI prompt templates

### Configuration & Examples
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore rules
- `resume_ta.txt` - TA mode resume
- `resume_ai.txt` - AI mode resume
- `input_example_ta.json` - TA input example
- `input_example_ai.json` - AI input example

## Usage Tips

1. **Be specific with job descriptions** - More detail = better analysis
2. **Target high-signal recipients** - System targets decision-makers, not HR generalists
3. **Personalization matters** - Edit generated messages to add specific details about target
4. **Track your campaigns** - Use job_tracker.csv to manage follow-up timing
5. **Test different modes** - Same job might yield different insights in TA vs AI mode

## Error Handling

- Missing OpenAI API key → Error with setup instructions
- Invalid resume file → FileNotFoundError with path
- Empty job description → ValueError with requirement
- API failures → Exception with OpenAI error details

## Author

**Bryan Lockhart**
- 14 years in Talent Acquisition and Operations
- Now building AI automation workflows and intelligent systems
- GitHub: [AI Job Outreach System](https://github.com/yourusername/job-outreach-system)
