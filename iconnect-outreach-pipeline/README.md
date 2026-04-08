# iConnect Sports — Automated Outbound Lead Pipeline

End-to-end Python automation for B2B outbound sales lead generation. Built to power athlete partnership outreach at iConnect Sports.

## What It Does

This pipeline automates the full outbound prospecting workflow:

1. **Prospecting** — Searches Apollo.io for marketing and partnership contacts at target companies, using a tiered seniority strategy (80% managers, 20% directors)
2. **Enrichment** — Enriches LinkedIn profiles through Apollo to get verified work emails
3. **Email Sequencing** — Imports leads with emails into Saleshandy for automated cold email campaigns
4. **LinkedIn Outreach** — Feeds LinkedIn URLs to PhantomBuster for automated connection requests
5. **Deduplication** — Tracks all leads in a master CSV and prevents double-outreach
6. **Logging** — Writes daily pipeline logs with lead counts, shortfalls, and actionable flags

## Architecture

```
Target Companies (txt)
        │
        ▼
   Apollo Search ──────── Seniority tiers: manager → director
        │
        ├── Email found? ──→ Saleshandy (cold email sequence)
        │
        ├── LinkedIn URL? ──→ PhantomBuster (auto-connect)
        │
        ├── < 5 leads? ──→ Flag for manual LinkedIn search
        │
        └── All leads ──→ Master CSV (dedup tracking)
```

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/iconnect-outreach-automation.git
cd iconnect-outreach-automation

# 2. Set your API keys
cp .env.example .env
# Edit .env with your Apollo, Saleshandy, and PhantomBuster keys

# 3. Search specific companies
python iconnect_pipeline.py run "FanDuel" "State Farm" "Novig"

# 4. Or run the full daily pipeline
python iconnect_pipeline.py daily

# 5. Enrich LinkedIn URLs manually found
python iconnect_pipeline.py enrich --linkedin "https://linkedin.com/in/someone"

# 6. Check pipeline status
python iconnect_pipeline.py status
```

## Commands

| Command | Description |
|---------|-------------|
| `run "Company1" "Company2"` | Search Apollo for leads at specific companies |
| `run --file companies.txt` | Search from a file of companies |
| `enrich --linkedin URL1 URL2` | Enrich LinkedIn profiles via Apollo |
| `enrich --file urls.txt` | Enrich from a file of LinkedIn URLs |
| `daily` | Run full pipeline from `target_companies.txt` |
| `status` | Show lead counts, API key status, config |

## PhantomBuster Manager

Separate tool for managing the LinkedIn auto-connect phantom:

```bash
python phantombuster_manager.py status        # Check phantom status
python phantombuster_manager.py launch        # Trigger immediate launch
python phantombuster_manager.py results       # View latest run results
python phantombuster_manager.py pause         # Pause daily launches
python phantombuster_manager.py resume        # Resume daily launches
python phantombuster_manager.py update-leads leads.csv  # Update lead list
```

## Configuration

Edit the config section at the top of `iconnect_pipeline.py` or use environment variables:

- **API Keys**: `APOLLO_API_KEY`, `SALESHANDY_API_KEY`, `PB_API_KEY`
- **Saleshandy Sequence**: `SH_SEQUENCE_ID`, `SH_STEP_ID`
- **Exclusions**: Companies to never target (e.g., competitors, past clients)
- **Seniority Split**: 80% marketing managers / 20% directors
- **Min Leads**: 5 per company (flags shortfalls for manual search)

## File Structure

```
├── iconnect_pipeline.py            # Main pipeline script
├── phantombuster_manager.py        # PhantomBuster LinkedIn agent manager
├── target_companies.txt            # Daily target company list
├── iconnect_leads.csv              # Master lead tracking (gitignored)
├── phantombuster_linkedin_upload.csv  # PhantomBuster feed (gitignored)
├── iconnect_daily_log_*.txt        # Daily pipeline logs
├── .env.example                    # API key template
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## APIs Used

- [Apollo.io](https://apolloio.github.io/apollo-api-docs/) — Lead prospecting and email enrichment
- [Saleshandy](https://api.saleshandy.com/) — Cold email sequence automation
- [PhantomBuster](https://phantombuster.com/) — LinkedIn auto-connect automation

## Built With

- Python 3.8+ (stdlib only — no external dependencies)
- Apollo.io API for B2B lead data
- Saleshandy API for email sequences
- PhantomBuster API for LinkedIn automation

## Author

Bryan Lockhart — iConnect Sports
