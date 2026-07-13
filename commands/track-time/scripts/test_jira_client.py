"""Unit tests for jira_client.py using recorded real Jira API response fixtures.

Fixtures under fixtures/ are real recorded responses from mrge.atlassian.net
(see fixtures/README.md), except none exist by construction (they're all
real). Only the transport (urllib.request.urlopen) is stubbed -- the request
building, pagination, and parsing logic in jira_client.py runs for real
against the recorded bytes.
"""

import io
import json
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from jira_client import JiraApiError, JiraClient

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


class FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestGetAccountId(unittest.TestCase):
    def test_parses_account_id_from_myself_response(self):
        client = JiraClient("https://mrge.atlassian.net", "randy@example.com", "tok")
        with patch("jira_client.urllib.request.urlopen", return_value=FakeResponse(load_fixture("myself.json"))):
            account_id = client.get_account_id()
        self.assertEqual(account_id, "712020:5f6594bb-5ebe-4826-ab31-adfa524c3f7d")


class TestSearchIssues(unittest.TestCase):
    def test_paginates_via_next_page_token_until_is_last(self):
        client = JiraClient("https://mrge.atlassian.net", "randy@example.com", "tok")
        page1 = load_fixture("search_jql_page1.json")
        page2 = load_fixture("search_jql_page2.json")
        responses = [FakeResponse(page1), FakeResponse(page2)]
        with patch("jira_client.urllib.request.urlopen", side_effect=responses) as mock_urlopen:
            issues = client.search_issues("assignee = currentUser()", fields=["status"])

        expected_count = len(json.loads(page1)["issues"]) + len(json.loads(page2)["issues"])
        self.assertEqual(len(issues), expected_count)
        self.assertEqual(mock_urlopen.call_count, 2)

    def test_sends_basic_auth_header(self):
        client = JiraClient("https://mrge.atlassian.net", "randy@example.com", "tok")
        page1 = json.loads(load_fixture("search_jql_page1.json"))
        page1["isLast"] = True
        with patch(
            "jira_client.urllib.request.urlopen",
            return_value=FakeResponse(json.dumps(page1).encode()),
        ) as mock_urlopen:
            client.search_issues("assignee = currentUser()", fields=["status"])
        sent_request = mock_urlopen.call_args[0][0]
        self.assertTrue(sent_request.get_header("Authorization").startswith("Basic "))


class TestGetStatusChangelog(unittest.TestCase):
    def test_paginates_across_all_recorded_pages(self):
        client = JiraClient("https://mrge.atlassian.net", "randy@example.com", "tok")
        pages = [
            FakeResponse(load_fixture("changelog_page1.json")),
            FakeResponse(load_fixture("changelog_page2.json")),
            FakeResponse(load_fixture("changelog_page3.json")),
        ]
        with patch("jira_client.urllib.request.urlopen", side_effect=pages):
            histories = client.get_status_changelog("YKBOT-4048")

        total = json.loads(load_fixture("changelog_page1.json"))["total"]
        self.assertEqual(len(histories), total)


class TestGetWorklogs(unittest.TestCase):
    def test_empty_worklog_response(self):
        client = JiraClient("https://mrge.atlassian.net", "randy@example.com", "tok")
        with patch(
            "jira_client.urllib.request.urlopen",
            return_value=FakeResponse(load_fixture("worklog_empty.json")),
        ):
            worklogs = client.get_worklogs("YKBOT-4048")
        self.assertEqual(worklogs, [])

    def test_worklog_with_adf_comment_is_returned_intact(self):
        client = JiraClient("https://mrge.atlassian.net", "randy@example.com", "tok")
        with patch(
            "jira_client.urllib.request.urlopen",
            return_value=FakeResponse(load_fixture("worklog_with_comment.json")),
        ):
            worklogs = client.get_worklogs("YKBOT-4019")
        self.assertEqual(len(worklogs), 1)
        self.assertEqual(worklogs[0]["timeSpentSeconds"], 60)
        comment_text = worklogs[0]["comment"]["content"][0]["content"][0]["text"]
        self.assertEqual(comment_text, "[auto-tracked:partial] fixture-capture-scratch")


class TestAddWorklog(unittest.TestCase):
    def test_posts_correct_body_shape(self):
        client = JiraClient("https://mrge.atlassian.net", "randy@example.com", "tok")
        with patch(
            "jira_client.urllib.request.urlopen",
            return_value=FakeResponse(load_fixture("worklog_with_comment.json")),
        ) as mock_urlopen:
            client.add_worklog("YKBOT-4019", 60, "[auto-tracked:partial]")

        sent_request = mock_urlopen.call_args[0][0]
        self.assertEqual(sent_request.get_method(), "POST")
        body = json.loads(sent_request.data)
        self.assertEqual(body["timeSpentSeconds"], 60)
        self.assertEqual(
            body["comment"]["content"][0]["content"][0]["text"], "[auto-tracked:partial]"
        )


class TestErrorHandling(unittest.TestCase):
    def test_http_error_raises_jira_api_error_with_body(self):
        client = JiraClient("https://mrge.atlassian.net", "randy@example.com", "tok")
        error_body = load_fixture("error_410_gone.json")
        http_error = urllib.error.HTTPError(
            url="https://mrge.atlassian.net/rest/api/3/search",
            code=410,
            msg="Gone",
            hdrs=None,
            fp=io.BytesIO(error_body),
        )
        with patch("jira_client.urllib.request.urlopen", side_effect=http_error):
            with self.assertRaises(JiraApiError) as ctx:
                client.get_account_id()
        self.assertIn("410", str(ctx.exception))
        self.assertIn("removed", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
