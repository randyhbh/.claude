"""Deterministic core for the /track-time slash command.

Computes how many seconds of trackable work each Jira ticket accrued,
based on its status-transition history, applying the review-time cap,
cross-ticket overlap splitting, and idempotent-rerun rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


STATUS_IN_PROGRESS = "IN PROGRESS"
STATUS_IN_REVIEW = "IN-REVIEW"
STATUS_DONE = "DONE"

# No square brackets: Jira's wiki-markup renderer treats "[text]" as link syntax and
# fails to parse it, rendering an error span that some views (e.g. the activity feed)
# show as blank instead of the actual text.
TAG_PARTIAL = "auto-tracked:partial"
TAG_FINAL = "auto-tracked:final"

DEFAULT_REVIEW_CAP_SECONDS = 3600

JIRA_MIN_LOGGABLE_SECONDS = 60


def parse_iso(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


@dataclass
class Transition:
    timestamp: datetime
    to_status: str


@dataclass
class Segment:
    start: datetime
    end: datetime
    status: str


def build_segments(transitions: list[Transition], now: datetime) -> list[Segment]:
    ordered = sorted(transitions, key=lambda t: t.timestamp)
    segments = []
    for i, t in enumerate(ordered):
        end = ordered[i + 1].timestamp if i + 1 < len(ordered) else now
        segments.append(Segment(start=t.timestamp, end=end, status=t.to_status))
    return segments


def _sum_status_seconds(segments: list[Segment], status: str) -> float:
    return sum((s.end - s.start).total_seconds() for s in segments if s.status == status)


def raw_in_progress_seconds(segments: list[Segment], status: str = STATUS_IN_PROGRESS) -> float:
    return _sum_status_seconds(segments, status)


def last_in_progress_seconds(segments: list[Segment], status: str = STATUS_IN_PROGRESS) -> float:
    matching = [s for s in segments if s.status == status]
    if not matching:
        return 0
    last = matching[-1]
    return (last.end - last.start).total_seconds()


def capped_review_seconds(
    segments: list[Segment],
    cap_seconds: int = DEFAULT_REVIEW_CAP_SECONDS,
    status: str = STATUS_IN_REVIEW,
) -> float:
    return min(_sum_status_seconds(segments, status), cap_seconds)


def split_overlapping_in_progress(segments_by_key: dict[str, list["Segment"]]) -> dict[str, float]:
    result = {key: 0.0 for key in segments_by_key}

    points = set()
    for segs in segments_by_key.values():
        for s in segs:
            points.add(s.start)
            points.add(s.end)
    ordered_points = sorted(points)

    for i in range(len(ordered_points) - 1):
        a, b = ordered_points[i], ordered_points[i + 1]
        if a >= b:
            continue
        duration = (b - a).total_seconds()
        active_keys = [
            key
            for key, segs in segments_by_key.items()
            if any(s.start <= a and s.end >= b for s in segs)
        ]
        if not active_keys:
            continue
        share = duration / len(active_keys)
        for key in active_keys:
            result[key] += share

    return result


@dataclass
class ExistingWorklog:
    seconds: int
    tag: str | None = None


@dataclass
class IssueInput:
    key: str
    current_status: str
    transitions: list[Transition]
    existing_worklogs: list[ExistingWorklog] = field(default_factory=list)


@dataclass
class WorklogResult:
    key: str
    total_trackable_seconds: int
    already_logged_seconds: int
    delta_seconds: int
    tag: str | None
    skip_reason: str | None


def compute_all(
    issues: list[IssueInput],
    now: datetime,
    review_cap_seconds: int = DEFAULT_REVIEW_CAP_SECONDS,
    in_progress_status: str = STATUS_IN_PROGRESS,
    review_status: str = STATUS_IN_REVIEW,
    done_status: str = STATUS_DONE,
) -> list[WorklogResult]:
    segments_by_key: dict[str, list[Segment]] = {}
    in_progress_by_key: dict[str, list[Segment]] = {}
    review_seconds_by_key: dict[str, float] = {}

    for issue in issues:
        segments = build_segments(issue.transitions, now)
        segments_by_key[issue.key] = segments
        matching_in_progress = [s for s in segments if s.status == in_progress_status]
        in_progress_by_key[issue.key] = matching_in_progress[-1:] if matching_in_progress else []
        review_seconds_by_key[issue.key] = capped_review_seconds(
            segments, review_cap_seconds, status=review_status
        )

    adjusted_in_progress = split_overlapping_in_progress(in_progress_by_key)

    results = []
    for issue in issues:
        total = round(adjusted_in_progress[issue.key] + review_seconds_by_key[issue.key])
        already_logged = sum(
            w.seconds for w in issue.existing_worklogs if w.tag in (TAG_PARTIAL, TAG_FINAL)
        )
        has_final = any(w.tag == TAG_FINAL for w in issue.existing_worklogs)

        if issue.current_status == done_status and has_final:
            results.append(
                WorklogResult(issue.key, total, already_logged, 0, None, "already finalized")
            )
            continue

        delta = total - already_logged
        is_finalizing = issue.current_status == done_status

        if delta <= 0:
            if is_finalizing:
                results.append(
                    WorklogResult(
                        issue.key, total, already_logged, JIRA_MIN_LOGGABLE_SECONDS, TAG_FINAL, None
                    )
                )
            else:
                results.append(
                    WorklogResult(issue.key, total, already_logged, 0, None, "no new time to log")
                )
            continue
        if delta < JIRA_MIN_LOGGABLE_SECONDS:
            if is_finalizing:
                results.append(
                    WorklogResult(
                        issue.key, total, already_logged, JIRA_MIN_LOGGABLE_SECONDS, TAG_FINAL, None
                    )
                )
            else:
                results.append(
                    WorklogResult(
                        issue.key,
                        total,
                        already_logged,
                        0,
                        None,
                        "delta below 60s Jira minimum, will accumulate next run",
                    )
                )
            continue

        tag = TAG_FINAL if is_finalizing else TAG_PARTIAL
        results.append(WorklogResult(issue.key, total, already_logged, delta, tag, None))

    return results


import argparse
import json
import sys
from dataclasses import asdict


def issues_from_json(data: dict) -> list[IssueInput]:
    issues = []
    for raw in data["issues"]:
        transitions = [
            Transition(parse_iso(t["timestamp"]), t["to_status"]) for t in raw["transitions"]
        ]
        existing_worklogs = [
            ExistingWorklog(seconds=w["seconds"], tag=w.get("tag"))
            for w in raw.get("existing_worklogs", [])
        ]
        issues.append(
            IssueInput(
                key=raw["key"],
                current_status=raw["current_status"],
                transitions=transitions,
                existing_worklogs=existing_worklogs,
            )
        )
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute Jira worklog deltas from status history")
    parser.add_argument("input_file", help="Path to normalized issues JSON file")
    parser.add_argument("--now", required=True, help="ISO-8601 timestamp for the current moment")
    parser.add_argument(
        "--review-cap-seconds", type=int, default=DEFAULT_REVIEW_CAP_SECONDS
    )
    parser.add_argument("--in-progress-status", default=STATUS_IN_PROGRESS)
    parser.add_argument("--review-status", default=STATUS_IN_REVIEW)
    parser.add_argument("--done-status", default=STATUS_DONE)
    args = parser.parse_args(argv)

    with open(args.input_file) as f:
        data = json.load(f)

    issues = issues_from_json(data)
    now = parse_iso(args.now)
    results = compute_all(
        issues,
        now,
        args.review_cap_seconds,
        in_progress_status=args.in_progress_status,
        review_status=args.review_status,
        done_status=args.done_status,
    )
    print(json.dumps([asdict(r) for r in results], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
