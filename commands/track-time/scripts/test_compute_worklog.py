import unittest
from datetime import datetime, timezone

from compute_worklog import parse_iso, Transition, Segment, build_segments, raw_in_progress_seconds, last_in_progress_seconds, capped_review_seconds, split_overlapping_in_progress


def dt(s):
    return parse_iso(s)


class TestParseIso(unittest.TestCase):
    def test_parses_z_suffix(self):
        result = parse_iso("2026-07-01T09:00:00Z")
        self.assertEqual(result, datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc))

    def test_parses_explicit_offset(self):
        result = parse_iso("2026-07-01T09:00:00+00:00")
        self.assertEqual(result, datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc))


class TestBuildSegments(unittest.TestCase):
    def test_single_transition_open_ended_ends_at_now(self):
        now = dt("2026-07-01T12:00:00Z")
        transitions = [Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS")]
        segments = build_segments(transitions, now)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].start, dt("2026-07-01T09:00:00Z"))
        self.assertEqual(segments[0].end, now)
        self.assertEqual(segments[0].status, "IN PROGRESS")

    def test_multiple_transitions_chain_end_to_next_start(self):
        now = dt("2026-07-01T15:00:00Z")
        transitions = [
            Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS"),
            Transition(dt("2026-07-01T11:00:00Z"), "IN-REVIEW"),
            Transition(dt("2026-07-01T11:20:00Z"), "DONE"),
        ]
        segments = build_segments(transitions, now)
        self.assertEqual(len(segments), 3)
        self.assertEqual(
            [(s.status, s.start, s.end) for s in segments],
            [
                ("IN PROGRESS", dt("2026-07-01T09:00:00Z"), dt("2026-07-01T11:00:00Z")),
                ("IN-REVIEW", dt("2026-07-01T11:00:00Z"), dt("2026-07-01T11:20:00Z")),
                ("DONE", dt("2026-07-01T11:20:00Z"), now),
            ],
        )


class TestRawInProgressSeconds(unittest.TestCase):
    def test_sums_only_in_progress_segments(self):
        segments = [
            Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T11:00:00Z"), "IN PROGRESS"),
            Segment(dt("2026-07-01T11:00:00Z"), dt("2026-07-01T11:20:00Z"), "IN-REVIEW"),
            Segment(dt("2026-07-01T11:20:00Z"), dt("2026-07-01T12:00:00Z"), "DONE"),
        ]
        self.assertEqual(raw_in_progress_seconds(segments), 2 * 3600)

    def test_sums_across_reopened_cycles(self):
        segments = [
            Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T10:00:00Z"), "IN PROGRESS"),
            Segment(dt("2026-07-01T10:00:00Z"), dt("2026-07-01T10:05:00Z"), "DONE"),
            Segment(dt("2026-07-02T09:00:00Z"), dt("2026-07-02T09:30:00Z"), "IN PROGRESS"),
            Segment(dt("2026-07-02T09:30:00Z"), dt("2026-07-02T09:35:00Z"), "DONE"),
        ]
        self.assertEqual(raw_in_progress_seconds(segments), 3600 + 1800)


class TestLastInProgressSeconds(unittest.TestCase):
    def test_no_matching_segments_returns_zero(self):
        segments = [Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T10:00:00Z"), "DONE")]
        self.assertEqual(last_in_progress_seconds(segments), 0)

    def test_single_stint_returns_its_duration(self):
        segments = [
            Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T11:00:00Z"), "IN PROGRESS"),
            Segment(dt("2026-07-01T11:00:00Z"), dt("2026-07-01T11:20:00Z"), "IN-REVIEW"),
        ]
        self.assertEqual(last_in_progress_seconds(segments), 2 * 3600)

    def test_multiple_stints_only_counts_the_last_one(self):
        segments = [
            Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T10:00:00Z"), "IN PROGRESS"),
            Segment(dt("2026-07-01T10:00:00Z"), dt("2026-07-01T10:05:00Z"), "DONE"),
            Segment(dt("2026-07-02T09:00:00Z"), dt("2026-07-02T09:30:00Z"), "IN PROGRESS"),
            Segment(dt("2026-07-02T09:30:00Z"), dt("2026-07-02T09:35:00Z"), "DONE"),
        ]
        self.assertEqual(last_in_progress_seconds(segments), 1800)

    def test_last_stint_still_open_ended_counts_up_to_now(self):
        segments = [
            Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T10:00:00Z"), "IN PROGRESS"),
            Segment(dt("2026-07-01T10:00:00Z"), dt("2026-07-01T10:05:00Z"), "ON HOLD"),
            Segment(dt("2026-07-01T10:05:00Z"), dt("2026-07-01T12:05:00Z"), "IN PROGRESS"),
        ]
        self.assertEqual(last_in_progress_seconds(segments), 2 * 3600)


class TestCappedReviewSeconds(unittest.TestCase):
    def test_under_cap_counts_in_full(self):
        segments = [Segment(dt("2026-07-01T11:00:00Z"), dt("2026-07-01T11:20:00Z"), "IN-REVIEW")]
        self.assertEqual(capped_review_seconds(segments), 20 * 60)

    def test_over_cap_is_capped_at_one_hour(self):
        segments = [Segment(dt("2026-07-01T11:00:00Z"), dt("2026-07-01T15:00:00Z"), "IN-REVIEW")]
        self.assertEqual(capped_review_seconds(segments), 3600)

    def test_cap_applies_to_sum_across_multiple_review_segments(self):
        segments = [
            Segment(dt("2026-07-01T11:00:00Z"), dt("2026-07-01T11:45:00Z"), "IN-REVIEW"),
            Segment(dt("2026-07-02T09:00:00Z"), dt("2026-07-02T09:45:00Z"), "IN-REVIEW"),
        ]
        self.assertEqual(capped_review_seconds(segments), 3600)


class TestCustomStatusNames(unittest.TestCase):
    def test_raw_in_progress_seconds_uses_custom_status_name(self):
        segments = [Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T10:00:00Z"), "Doing")]
        self.assertEqual(raw_in_progress_seconds(segments, status="Doing"), 3600)
        self.assertEqual(raw_in_progress_seconds(segments), 0)

    def test_capped_review_seconds_uses_custom_status_name(self):
        segments = [Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T11:00:00Z"), "Peer Review")]
        self.assertEqual(capped_review_seconds(segments, status="Peer Review"), 3600)
        self.assertEqual(capped_review_seconds(segments), 0)


class TestSplitOverlappingInProgress(unittest.TestCase):
    def test_no_overlap_keeps_full_duration(self):
        segments_by_key = {
            "A": [Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T11:00:00Z"), "IN PROGRESS")],
            "B": [Segment(dt("2026-07-01T11:00:00Z"), dt("2026-07-01T15:00:00Z"), "IN PROGRESS")],
        }
        result = split_overlapping_in_progress(segments_by_key)
        self.assertEqual(result["A"], 2 * 3600)
        self.assertEqual(result["B"], 4 * 3600)

    def test_full_overlap_splits_evenly_between_two(self):
        segments_by_key = {
            "A": [Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T11:00:00Z"), "IN PROGRESS")],
            "B": [Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T11:00:00Z"), "IN PROGRESS")],
        }
        result = split_overlapping_in_progress(segments_by_key)
        self.assertEqual(result["A"], 3600)
        self.assertEqual(result["B"], 3600)

    def test_partial_overlap_splits_only_the_overlapping_window(self):
        # A: 09:00-11:00, B: 10:00-12:00 -> overlap 10:00-11:00 (1h) split evenly
        segments_by_key = {
            "A": [Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T11:00:00Z"), "IN PROGRESS")],
            "B": [Segment(dt("2026-07-01T10:00:00Z"), dt("2026-07-01T12:00:00Z"), "IN PROGRESS")],
        }
        result = split_overlapping_in_progress(segments_by_key)
        # A: 1h solo (09-10) + 0.5h shared (10-11) = 1.5h
        self.assertEqual(result["A"], 1.5 * 3600)
        # B: 0.5h shared (10-11) + 1h solo (11-12) = 1.5h
        self.assertEqual(result["B"], 1.5 * 3600)

    def test_three_way_overlap_splits_three_ways(self):
        segments_by_key = {
            "A": [Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T10:00:00Z"), "IN PROGRESS")],
            "B": [Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T10:00:00Z"), "IN PROGRESS")],
            "C": [Segment(dt("2026-07-01T09:00:00Z"), dt("2026-07-01T10:00:00Z"), "IN PROGRESS")],
        }
        result = split_overlapping_in_progress(segments_by_key)
        self.assertAlmostEqual(result["A"], 1200)
        self.assertAlmostEqual(result["B"], 1200)
        self.assertAlmostEqual(result["C"], 1200)

    def test_ticket_with_no_in_progress_segments_gets_zero(self):
        result = split_overlapping_in_progress({"A": []})
        self.assertEqual(result["A"], 0)


from compute_worklog import (
    ExistingWorklog,
    IssueInput,
    compute_all,
    TAG_PARTIAL,
    TAG_FINAL,
    JIRA_MIN_LOGGABLE_SECONDS,
)


class TestComputeAll(unittest.TestCase):
    def test_simple_open_ticket_no_prior_worklog(self):
        now = dt("2026-07-01T12:00:00Z")
        issue = IssueInput(
            key="A-1",
            current_status="IN PROGRESS",
            transitions=[Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS")],
        )
        results = {r.key: r for r in compute_all([issue], now)}
        r = results["A-1"]
        self.assertEqual(r.total_trackable_seconds, 3 * 3600)
        self.assertEqual(r.delta_seconds, 3 * 3600)
        self.assertEqual(r.tag, TAG_PARTIAL)
        self.assertIsNone(r.skip_reason)

    def test_done_ticket_no_prior_worklog_logs_final(self):
        now = dt("2026-07-05T00:00:00Z")  # now is irrelevant once Done reached
        issue = IssueInput(
            key="A-2",
            current_status="DONE",
            transitions=[
                Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS"),
                Transition(dt("2026-07-01T11:00:00Z"), "DONE"),
            ],
        )
        results = {r.key: r for r in compute_all([issue], now)}
        r = results["A-2"]
        self.assertEqual(r.total_trackable_seconds, 2 * 3600)
        self.assertEqual(r.delta_seconds, 2 * 3600)
        self.assertEqual(r.tag, TAG_FINAL)

    def test_done_ticket_already_finalized_is_skipped(self):
        now = dt("2026-07-05T00:00:00Z")
        issue = IssueInput(
            key="A-3",
            current_status="DONE",
            transitions=[
                Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS"),
                Transition(dt("2026-07-01T11:00:00Z"), "DONE"),
            ],
            existing_worklogs=[ExistingWorklog(seconds=2 * 3600, tag=TAG_FINAL)],
        )
        results = {r.key: r for r in compute_all([issue], now)}
        r = results["A-3"]
        self.assertEqual(r.delta_seconds, 0)
        self.assertIsNone(r.tag)
        self.assertEqual(r.skip_reason, "already finalized")

    def test_open_ticket_with_prior_partial_logs_only_new_delta(self):
        now = dt("2026-07-01T13:00:00Z")
        issue = IssueInput(
            key="A-4",
            current_status="IN PROGRESS",
            transitions=[Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS")],
            existing_worklogs=[ExistingWorklog(seconds=3 * 3600, tag=TAG_PARTIAL)],
        )
        results = {r.key: r for r in compute_all([issue], now)}
        r = results["A-4"]
        self.assertEqual(r.total_trackable_seconds, 4 * 3600)
        self.assertEqual(r.delta_seconds, 3600)
        self.assertEqual(r.tag, TAG_PARTIAL)

    def test_no_new_time_is_skipped_not_logged(self):
        now = dt("2026-07-01T11:00:00Z")
        issue = IssueInput(
            key="A-5",
            current_status="IN PROGRESS",
            transitions=[Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS")],
            existing_worklogs=[ExistingWorklog(seconds=2 * 3600, tag=TAG_PARTIAL)],
        )
        results = {r.key: r for r in compute_all([issue], now)}
        r = results["A-5"]
        self.assertEqual(r.delta_seconds, 0)
        self.assertIsNone(r.tag)
        self.assertEqual(r.skip_reason, "no new time to log")

    def test_delta_below_jira_minimum_is_not_logged(self):
        now = dt("2026-07-01T09:00:30Z")
        issue = IssueInput(
            key="A-7",
            current_status="IN PROGRESS",
            transitions=[Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS")],
        )
        results = {r.key: r for r in compute_all([issue], now)}
        r = results["A-7"]
        self.assertEqual(r.delta_seconds, 0)
        self.assertIsNone(r.tag)
        self.assertEqual(
            r.skip_reason, "delta below 60s Jira minimum, will accumulate next run"
        )

    def test_done_ticket_with_no_new_time_still_gets_finalized(self):
        # Ticket reached Done but the existing partial worklog already covers the
        # full computed total (e.g. it went straight IN-REVIEW -> DONE with no
        # extra IN PROGRESS time). It must still end up tagged final with the Jira
        # minimum, so it stops being re-proposed forever as "no new time to log".
        now = dt("2026-07-05T00:00:00Z")
        issue = IssueInput(
            key="A-8",
            current_status="DONE",
            transitions=[
                Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS"),
                Transition(dt("2026-07-01T11:00:00Z"), "IN-REVIEW"),
                Transition(dt("2026-07-02T09:00:00Z"), "DONE"),
            ],
            # total = 2h IN PROGRESS + 1h capped review = 3h, already fully logged
            existing_worklogs=[ExistingWorklog(seconds=3 * 3600, tag=TAG_PARTIAL)],
        )
        results = {r.key: r for r in compute_all([issue], now)}
        r = results["A-8"]
        self.assertEqual(r.delta_seconds, JIRA_MIN_LOGGABLE_SECONDS)
        self.assertEqual(r.tag, TAG_FINAL)
        self.assertIsNone(r.skip_reason)

    def test_done_ticket_with_sub_minimum_new_time_gets_finalized_at_minimum(self):
        # Delta is nonzero but below Jira's 60s minimum. For an open ticket this
        # accumulates for next run, but a Done ticket has no "next run" for this
        # cycle, so it must be finalized now at the 60s minimum instead of stalling.
        now = dt("2026-07-05T00:00:00Z")
        issue = IssueInput(
            key="A-9",
            current_status="DONE",
            transitions=[
                Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS"),
                Transition(dt("2026-07-01T11:00:00Z"), "DONE"),
            ],
            # total = 2h = 7200s; 30s of it left unlogged
            existing_worklogs=[ExistingWorklog(seconds=7170, tag=TAG_PARTIAL)],
        )
        results = {r.key: r for r in compute_all([issue], now)}
        r = results["A-9"]
        self.assertEqual(r.delta_seconds, JIRA_MIN_LOGGABLE_SECONDS)
        self.assertEqual(r.tag, TAG_FINAL)
        self.assertIsNone(r.skip_reason)

    def test_reopened_after_final_logs_new_partial_delta(self):
        # Ticket was Done + finalized, then reopened and worked again.
        now = dt("2026-07-03T10:00:00Z")
        issue = IssueInput(
            key="A-6",
            current_status="IN PROGRESS",
            transitions=[
                Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS"),
                Transition(dt("2026-07-01T11:00:00Z"), "DONE"),
                Transition(dt("2026-07-02T09:00:00Z"), "IN PROGRESS"),
            ],
            existing_worklogs=[ExistingWorklog(seconds=2 * 3600, tag=TAG_FINAL)],
        )
        results = {r.key: r for r in compute_all([issue], now)}
        r = results["A-6"]
        # Only the last (current) stint counts now (07-02 09:00 -> 07-03 10:00 = 25h),
        # the earlier finalized cycle's 2h is excluded from total entirely.
        # NOTE: already_logged (2h, from the old finalized cycle) still gets subtracted
        # here even though it belongs to a disjoint, now-excluded period -- known gap,
        # see journal/conversation: needs worklog timestamps to fix properly.
        self.assertEqual(r.total_trackable_seconds, 25 * 3600)
        self.assertEqual(r.delta_seconds, 23 * 3600)
        self.assertEqual(r.tag, TAG_PARTIAL)

    def test_overlap_split_feeds_into_final_delta(self):
        now = dt("2026-07-01T11:00:00Z")
        issue_a = IssueInput(
            key="B-1",
            current_status="IN PROGRESS",
            transitions=[Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS")],
        )
        issue_b = IssueInput(
            key="B-2",
            current_status="IN PROGRESS",
            transitions=[Transition(dt("2026-07-01T09:00:00Z"), "IN PROGRESS")],
        )
        results = {r.key: r for r in compute_all([issue_a, issue_b], now)}
        self.assertEqual(results["B-1"].total_trackable_seconds, 3600)
        self.assertEqual(results["B-2"].total_trackable_seconds, 3600)


class TestComputeAllCustomStatusNames(unittest.TestCase):
    def test_custom_status_names_are_respected(self):
        now = dt("2026-07-01T13:00:00Z")
        issue = IssueInput(
            key="C-1",
            current_status="Closed",
            transitions=[
                Transition(dt("2026-07-01T09:00:00Z"), "Doing"),
                Transition(dt("2026-07-01T11:00:00Z"), "Closed"),
            ],
        )
        results = {
            r.key: r
            for r in compute_all(
                [issue],
                now,
                in_progress_status="Doing",
                review_status="Peer Review",
                done_status="Closed",
            )
        }
        r = results["C-1"]
        self.assertEqual(r.total_trackable_seconds, 2 * 3600)
        self.assertEqual(r.tag, TAG_FINAL)


import io
import json
import sys
import tempfile
import os

from compute_worklog import issues_from_json, main


class TestIssuesFromJson(unittest.TestCase):
    def test_builds_issue_inputs_from_json_dict(self):
        data = {
            "issues": [
                {
                    "key": "ABC-1",
                    "current_status": "IN PROGRESS",
                    "transitions": [
                        {"timestamp": "2026-07-01T09:00:00Z", "to_status": "IN PROGRESS"}
                    ],
                    "existing_worklogs": [
                        {"seconds": 100, "tag": "[auto-tracked:partial]"}
                    ],
                }
            ]
        }
        issues = issues_from_json(data)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].key, "ABC-1")
        self.assertEqual(issues[0].current_status, "IN PROGRESS")
        self.assertEqual(issues[0].transitions[0].to_status, "IN PROGRESS")
        self.assertEqual(issues[0].existing_worklogs[0].seconds, 100)

    def test_defaults_existing_worklogs_to_empty_list(self):
        data = {
            "issues": [
                {
                    "key": "ABC-2",
                    "current_status": "IN PROGRESS",
                    "transitions": [
                        {"timestamp": "2026-07-01T09:00:00Z", "to_status": "IN PROGRESS"}
                    ],
                }
            ]
        }
        issues = issues_from_json(data)
        self.assertEqual(issues[0].existing_worklogs, [])


class TestMain(unittest.TestCase):
    def test_main_prints_json_results_to_stdout(self):
        payload = {
            "issues": [
                {
                    "key": "ABC-3",
                    "current_status": "IN PROGRESS",
                    "transitions": [
                        {"timestamp": "2026-07-01T09:00:00Z", "to_status": "IN PROGRESS"}
                    ],
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(payload, f)
            path = f.name
        try:
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                exit_code = main([path, "--now", "2026-07-01T12:00:00Z"])
            finally:
                sys.stdout = old_stdout
            self.assertEqual(exit_code, 0)
            output = json.loads(captured.getvalue())
            self.assertEqual(len(output), 1)
            self.assertEqual(output[0]["key"], "ABC-3")
            self.assertEqual(output[0]["delta_seconds"], 3 * 3600)
            self.assertEqual(output[0]["tag"], "auto-tracked:partial")
        finally:
            os.unlink(path)

    def test_main_respects_custom_status_flags(self):
        payload = {
            "issues": [
                {
                    "key": "C-2",
                    "current_status": "Closed",
                    "transitions": [
                        {"timestamp": "2026-07-01T09:00:00Z", "to_status": "Doing"},
                        {"timestamp": "2026-07-01T11:00:00Z", "to_status": "Closed"},
                    ],
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(payload, f)
            path = f.name
        try:
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                exit_code = main(
                    [
                        path,
                        "--now",
                        "2026-07-01T13:00:00Z",
                        "--in-progress-status",
                        "Doing",
                        "--review-status",
                        "Peer Review",
                        "--done-status",
                        "Closed",
                    ]
                )
            finally:
                sys.stdout = old_stdout
            self.assertEqual(exit_code, 0)
            output = json.loads(captured.getvalue())
            self.assertEqual(output[0]["delta_seconds"], 2 * 3600)
            self.assertEqual(output[0]["tag"], "auto-tracked:final")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
