"""No-LLM orchestrator: fetch from Jira REST API, compute worklogs, confirm, post.

Usage:
    python3 run_track_time.py                       # prints proposal, asks to confirm, then posts
    python3 run_track_time.py --dry-run              # prints proposal only, never posts, never prompts
    python3 run_track_time.py --yes                  # skip interactive confirmation, post everything postable
    python3 run_track_time.py --yes --exclude A-1,A-2  # post everything postable except the listed keys
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from compute_worklog import ExistingWorklog, IssueInput, Transition, compute_all, parse_iso
from jira_client import JiraClient, get_token
from normalize import build_jql, extract_existing_worklogs, extract_status_transitions

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def fetch_issue_inputs(client: JiraClient, config: dict) -> list[IssueInput]:
    jql = build_jql(config)
    raw_issues = client.search_issues(jql, fields=["status"])
    issues = []
    for raw in raw_issues:
        key = raw["key"]
        current_status = raw["fields"]["status"]["name"]
        histories = client.get_status_changelog(key)
        worklogs = client.get_worklogs(key)
        transitions = [
            Transition(parse_iso(t["timestamp"]), t["to_status"])
            for t in extract_status_transitions(histories)
        ]
        existing_worklogs = [
            ExistingWorklog(seconds=w["seconds"], tag=w["tag"])
            for w in extract_existing_worklogs(worklogs)
        ]
        issues.append(
            IssueInput(
                key=key,
                current_status=current_status,
                transitions=transitions,
                existing_worklogs=existing_worklogs,
            )
        )
    return issues


def print_proposal(results) -> None:
    print(f"{'Ticket':<12} {'Delta':>10}  Tag / Skip reason")
    print("-" * 50)
    for r in results:
        if r.skip_reason:
            print(f"{r.key:<12} {'--':>10}  skipped: {r.skip_reason}")
        else:
            h, rem = divmod(r.delta_seconds, 3600)
            m = rem // 60
            print(f"{r.key:<12} {f'{h}h{m}m':>10}  tag={r.tag}")


def filter_excluded(results, exclude_keys: set[str]):
    return [r for r in results if not r.skip_reason and r.key not in exclude_keys]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="skip interactive confirmation")
    parser.add_argument("--dry-run", action="store_true", help="print proposal only, never post, never prompt")
    parser.add_argument("--exclude", default="", help="comma-separated ticket keys to skip posting")
    args = parser.parse_args()

    config = load_config()
    email = config["jira_email"]
    token = get_token(email)
    client = JiraClient(base_url=config["jira_base_url"], email=email, token=token)

    issues = fetch_issue_inputs(client, config)
    now = datetime.now(timezone.utc)
    results = compute_all(
        issues,
        now=now,
        review_cap_seconds=config["review_cap_seconds"],
        in_progress_status=config["status_in_progress"],
        review_status=config["status_review"],
        done_status=config["status_done"],
    )

    print_proposal(results)

    if args.dry_run:
        return 0

    exclude_keys = {k.strip() for k in args.exclude.split(",") if k.strip()}
    postable = filter_excluded(results, exclude_keys)
    if not postable:
        print("\nNothing to post.")
        return 0

    if not args.yes:
        answer = input(f"\nPost {len(postable)} worklog(s) to Jira? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted, nothing posted.")
            return 0

    for r in postable:
        client.add_worklog(r.key, r.delta_seconds, r.tag)
        print(f"Posted {r.key}: {r.delta_seconds}s ({r.tag})")

    return 0


if __name__ == "__main__":
    sys.exit(main())