import unittest

from normalize import (
    adf_to_text,
    build_jql,
    extract_existing_worklogs,
    extract_status_transitions,
)


class TestBuildJql(unittest.TestCase):
    def test_current_user_unquoted(self):
        config = {
            "jira_user": "currentUser()",
            "status_in_progress": "In Progress",
            "status_review": "In-Review",
            "status_done": "Done",
        }
        jql = build_jql(config)
        self.assertIn("assignee = currentUser()", jql)
        self.assertNotIn('"currentUser()"', jql)

    def test_hardcoded_user_quoted(self):
        config = {
            "jira_user": "jdoe",
            "status_in_progress": "In Progress",
            "status_review": "In-Review",
            "status_done": "Done",
        }
        jql = build_jql(config)
        self.assertIn('assignee = "jdoe"', jql)

    def test_scopes_to_current_month_by_default(self):
        config = {
            "jira_user": "currentUser()",
            "status_in_progress": "In Progress",
            "status_review": "In-Review",
            "status_done": "Done",
        }
        jql = build_jql(config)
        self.assertIn("updated >= startOfMonth()", jql)

    def test_done_since_defaults_to_7_days_back(self):
        config = {
            "jira_user": "currentUser()",
            "status_in_progress": "In Progress",
            "status_review": "In-Review",
            "status_done": "Done",
        }
        jql = build_jql(config)
        self.assertIn("statusCategoryChangedDate >= -7d", jql)

    def test_updated_since_is_configurable(self):
        config = {
            "jira_user": "currentUser()",
            "status_in_progress": "In Progress",
            "status_review": "In-Review",
            "status_done": "Done",
            "updated_since": "-14d",
        }
        jql = build_jql(config)
        self.assertIn("updated >= -14d", jql)
        self.assertNotIn("startOfMonth()", jql)

    def test_done_since_is_configurable(self):
        config = {
            "jira_user": "currentUser()",
            "status_in_progress": "In Progress",
            "status_review": "In-Review",
            "status_done": "Done",
            "done_since": "-14d",
        }
        jql = build_jql(config)
        self.assertIn("statusCategoryChangedDate >= -14d", jql)

    def test_done_since_accepts_any_jql_date_expression(self):
        config = {
            "jira_user": "currentUser()",
            "status_in_progress": "In Progress",
            "status_review": "In-Review",
            "status_done": "Done",
            "done_since": "startOfMonth()",
        }
        jql = build_jql(config)
        self.assertIn("statusCategoryChangedDate >= startOfMonth()", jql)

    def test_includes_status_filters(self):
        config = {
            "jira_user": "currentUser()",
            "status_in_progress": "In Progress",
            "status_review": "In-Review",
            "status_done": "Done",
        }
        jql = build_jql(config)
        self.assertIn('status in ("In Progress", "In-Review")', jql)
        self.assertIn('status = "Done"', jql)


class TestAdfToText(unittest.TestCase):
    def test_extracts_plain_text_from_paragraph(self):
        adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "[auto-tracked:final]"}]}
            ],
        }
        self.assertEqual(adf_to_text(adf), "[auto-tracked:final]")

    def test_concatenates_multiple_text_nodes(self):
        adf = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "hello "},
                        {"type": "text", "text": "world"},
                    ],
                }
            ],
        }
        self.assertEqual(adf_to_text(adf), "hello world")

    def test_none_comment_returns_empty_string(self):
        self.assertEqual(adf_to_text(None), "")


class TestExtractStatusTransitions(unittest.TestCase):
    def test_extracts_status_field_changes_only(self):
        histories = [
            {
                "created": "2026-07-08T13:11:08.210+0200",
                "items": [
                    {"field": "status", "fromString": "In Progress", "toString": "In-Review"},
                    {"field": "assignee", "fromString": "a", "toString": "b"},
                ],
            },
            {
                "created": "2026-07-09T10:35:06.026+0200",
                "items": [
                    {"field": "status", "fromString": "In-Review", "toString": "Done"},
                ],
            },
        ]
        transitions = extract_status_transitions(histories)
        self.assertEqual(len(transitions), 2)
        self.assertEqual(transitions[0]["to_status"], "In-Review")
        self.assertEqual(transitions[0]["timestamp"], "2026-07-08T13:11:08.210+0200")
        self.assertEqual(transitions[1]["to_status"], "Done")

    def test_ignores_histories_without_status_field(self):
        histories = [
            {
                "created": "2026-07-08T13:11:08.210+0200",
                "items": [{"field": "assignee", "fromString": "a", "toString": "b"}],
            }
        ]
        self.assertEqual(extract_status_transitions(histories), [])


class TestExtractExistingWorklogs(unittest.TestCase):
    def test_extracts_seconds_and_tag(self):
        worklogs = [
            {
                "timeSpentSeconds": 3600,
                "comment": {
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "auto-tracked:partial"}],
                        }
                    ],
                },
            },
            {"timeSpentSeconds": 900, "comment": None},
        ]
        result = extract_existing_worklogs(worklogs)
        self.assertEqual(result, [
            {"seconds": 3600, "tag": "auto-tracked:partial"},
            {"seconds": 900, "tag": None},
        ])

    def test_legacy_bracketed_tag_still_detected_and_normalized(self):
        # Older worklogs were posted with square brackets, which Jira's wiki-markup
        # renderer chokes on ("[text]" looks like link syntax). Still recognize them,
        # normalized to the current unbracketed tag value.
        worklogs = [
            {
                "timeSpentSeconds": 3600,
                "comment": {
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "[auto-tracked:final]"}],
                        }
                    ],
                },
            }
        ]
        result = extract_existing_worklogs(worklogs)
        self.assertEqual(result, [{"seconds": 3600, "tag": "auto-tracked:final"}])

    def test_untagged_comment_text_yields_none_tag(self):
        worklogs = [
            {
                "timeSpentSeconds": 1200,
                "comment": {
                    "type": "doc",
                    "content": [
                        {"type": "paragraph", "content": [{"type": "text", "text": "manual entry"}]}
                    ],
                },
            }
        ]
        self.assertEqual(extract_existing_worklogs(worklogs), [{"seconds": 1200, "tag": None}])


if __name__ == "__main__":
    unittest.main()