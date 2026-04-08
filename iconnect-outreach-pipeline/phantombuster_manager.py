#!/usr/bin/env python3
"""
iConnect Sports — PhantomBuster LinkedIn Auto Connect Manager
=============================================================
Manage, launch, monitor, and update the LinkedIn Auto Connect phantom
entirely from the command line. No UI needed.

Usage:
    python phantombuster_manager.py status       # Check phantom status & last run
    python phantombuster_manager.py launch       # Trigger an immediate launch
    python phantombuster_manager.py results      # Fetch latest run results/output
    python phantombuster_manager.py pause        # Pause repeated launches
    python phantombuster_manager.py resume       # Resume repeated launches
    python phantombuster_manager.py update-leads <csv_path>  # Upload new lead list
"""

import sys
import json
import csv
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY = "s7QxrPmrzcngLLWmhkS3ekKabrSxJ6U0E4uMptXowfU"
AGENT_ID = "7987172913724230"
ORG_ID = "7754371388487037"
LEAD_LIST_ID = "2047763977126447"
BASE_URL = "https://api.phantombuster.com/api/v2"

HEADERS = {
    "X-Phantombuster-Key": API_KEY,
    "Content-Type": "application/json",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def api_request(method, endpoint, data=None):
    """Make an API request to PhantomBuster."""
    url = f"{BASE_URL}/{endpoint}"
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        error_body = e.read().decode()
        print(f"[ERROR] {e.code}: {error_body}")
        sys.exit(1)


def api_get(endpoint):
    return api_request("GET", endpoint)


def api_post(endpoint, data=None):
    return api_request("POST", endpoint, data)


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  iConnect Sports — {title}")
    print(f"{'='*60}\n")


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_status():
    """Show current phantom status and configuration."""
    print_header("Phantom Status")
    agent = api_get(f"agents/fetch?id={AGENT_ID}")

    print(f"  Name:         {agent.get('name', 'N/A')}")
    print(f"  Launch Type:  {agent.get('launchType', 'N/A')}")
    print(f"  Last Status:  {agent.get('lastEndMessage', 'N/A')}")

    last_end = agent.get("lastEndedAt")
    if last_end:
        print(f"  Last Run:     {last_end}")

    # Check if currently running
    container_id = agent.get("containerId")
    if container_id:
        print(f"  Running Now:  YES (container {container_id})")
    else:
        print(f"  Running Now:  No")

    # Parse argument for config details
    arg = agent.get("argument", "{}")
    if isinstance(arg, str):
        try:
            arg = json.loads(arg)
        except json.JSONDecodeError:
            arg = {}

    print(f"\n  Config:")
    print(f"    Invites/launch:  {arg.get('numberOfAddsPerLaunch', '?')}")
    print(f"    Input type:      {arg.get('inputType', '?')}")
    print(f"    Dwell time:      {arg.get('dwellTime', '?')}")
    print()


def cmd_launch():
    """Trigger an immediate phantom launch."""
    print_header("Launching Phantom")
    result = api_post("agents/launch", {"id": AGENT_ID})
    container_id = result.get("containerId")
    print(f"  Launched! Container ID: {container_id}")
    print(f"  The phantom will process up to 10 connection requests.")
    print(f"  Run 'python phantombuster_manager.py results' to check output.\n")


def cmd_results():
    """Fetch the latest run output/results."""
    print_header("Latest Run Results")

    # Get agent output
    agent = api_get(f"agents/fetch?id={AGENT_ID}")
    output = api_get(f"agents/fetch-output?id={AGENT_ID}")

    last_status = agent.get("lastEndMessage", "N/A")
    last_end = agent.get("lastEndedAt", "N/A")

    print(f"  Last Status: {last_status}")
    print(f"  Last Ended:  {last_end}")

    # Check for result object
    result_object = output.get("resultObject")
    if result_object:
        if isinstance(result_object, str):
            try:
                result_object = json.loads(result_object)
            except json.JSONDecodeError:
                pass

        if isinstance(result_object, list):
            print(f"\n  Connections processed: {len(result_object)}")
            for i, item in enumerate(result_object[:10], 1):
                name = item.get("name", item.get("firstName", "Unknown"))
                status = item.get("status", item.get("message", "N/A"))
                print(f"    {i}. {name} — {status}")
            if len(result_object) > 10:
                print(f"    ... and {len(result_object) - 10} more")
        else:
            print(f"\n  Result: {json.dumps(result_object, indent=2)[:500]}")
    else:
        output_text = output.get("output", "")
        if output_text:
            # Show last 20 lines of console output
            lines = output_text.strip().split("\n")
            print(f"\n  Console output (last 20 lines):")
            for line in lines[-20:]:
                print(f"    {line}")
        else:
            print("  No output available yet. Phantom may still be running.")
    print()


def cmd_pause():
    """Pause repeated launches (set to manual only)."""
    print_header("Pausing Phantom")
    # Abort any running container first
    agent = api_get(f"agents/fetch?id={AGENT_ID}")
    api_post("agents/abort", {"id": AGENT_ID})

    # The API doesn't have a direct pause — we delete the launch schedule
    # by updating launchType. We'll use the v1 endpoint for this.
    url = "https://api.phantombuster.com/api/v1/agent/save"
    data = json.dumps({
        "id": AGENT_ID,
        "launchType": "manually"
    }).encode()
    req = Request(url, data=data, headers=HEADERS, method="POST")
    try:
        with urlopen(req) as resp:
            result = json.loads(resp.read().decode())
        print("  Phantom paused. It will no longer auto-launch daily.")
        print("  Use 'resume' to re-enable daily launches.\n")
    except HTTPError as e:
        print(f"  Could not pause via v1 API: {e.code}")
        print("  You may need to pause it from the PhantomBuster UI.\n")


def cmd_resume():
    """Resume repeated daily launches."""
    print_header("Resuming Phantom")
    url = "https://api.phantombuster.com/api/v1/agent/save"
    data = json.dumps({
        "id": AGENT_ID,
        "launchType": "repeatedly",
        "repeatedLaunchTimes": {"simplePreset": "Once per day"}
    }).encode()
    req = Request(url, data=data, headers=HEADERS, method="POST")
    try:
        with urlopen(req) as resp:
            result = json.loads(resp.read().decode())
        print("  Phantom resumed! It will now launch once per day.")
        print("  Use 'launch' to also trigger an immediate run.\n")
    except HTTPError as e:
        print(f"  Could not resume via v1 API: {e.code}")
        print("  You may need to resume it from the PhantomBuster UI.\n")


def cmd_update_leads(csv_path):
    """Upload a new CSV of LinkedIn leads to the phantom's lead list."""
    print_header("Updating Lead List")

    if not os.path.exists(csv_path):
        print(f"  [ERROR] File not found: {csv_path}")
        sys.exit(1)

    # Read the CSV and extract LinkedIn URLs
    leads = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            linkedin_url = row.get("LinkedIn URL") or row.get("linkedInUrl") or row.get("linkedin_url", "")
            if linkedin_url and linkedin_url.strip():
                lead = {
                    "linkedInUrl": linkedin_url.strip(),
                    "firstName": row.get("First Name", row.get("firstName", "")),
                    "lastName": row.get("Last Name", row.get("lastName", "")),
                    "company": row.get("Company", row.get("company", "")),
                    "title": row.get("Title", row.get("title", "")),
                }
                leads.append(lead)

    print(f"  Found {len(leads)} leads with LinkedIn URLs in {csv_path}")

    if not leads:
        print("  [ERROR] No valid LinkedIn URLs found in CSV.")
        sys.exit(1)

    # Write processed CSV for PhantomBuster format
    output_path = os.path.join(os.path.dirname(csv_path), "phantombuster_linkedin_upload.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["linkedInUrl", "firstName", "lastName", "company", "title"])
        writer.writeheader()
        writer.writerows(leads)

    print(f"  Wrote PhantomBuster-formatted CSV: {output_path}")
    print(f"  Upload this file to the PhantomBuster lead list via the UI,")
    print(f"  or use the PhantomBuster lead list API if available.\n")

    # Note: PhantomBuster's lead list upload is typically done via the UI
    # or their internal API. The public API doesn't have a direct CSV upload
    # endpoint for lead lists. The formatted CSV is ready to drag-and-drop.


def cmd_help():
    print_header("Help")
    print("  Commands:")
    print("    status         Show phantom status and config")
    print("    launch         Trigger immediate launch")
    print("    results        Show latest run results")
    print("    pause          Pause daily auto-launches")
    print("    resume         Resume daily auto-launches")
    print("    update-leads   Format a new CSV for PhantomBuster upload")
    print("    help           Show this help message")
    print()
    print("  Examples:")
    print("    python phantombuster_manager.py status")
    print("    python phantombuster_manager.py launch")
    print("    python phantombuster_manager.py update-leads iconnect_leads.csv")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        cmd_help()
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "status":
        cmd_status()
    elif command == "launch":
        cmd_launch()
    elif command == "results":
        cmd_results()
    elif command == "pause":
        cmd_pause()
    elif command == "resume":
        cmd_resume()
    elif command == "update-leads":
        if len(sys.argv) < 3:
            print("[ERROR] Provide CSV path: python phantombuster_manager.py update-leads <path>")
            sys.exit(1)
        cmd_update_leads(sys.argv[2])
    elif command == "help":
        cmd_help()
    else:
        print(f"[ERROR] Unknown command: {command}")
        cmd_help()
        sys.exit(1)
