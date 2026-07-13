Real recorded responses from mrge.atlassian.net (2026-07-11), used by
`test_jira_client.py` to exercise request building, pagination, and parsing
against actual API shapes instead of guessed ones.

| File | Source call |
|---|---|
| `myself.json` | `GET /rest/api/3/myself` |
| `search_jql_page1.json`, `search_jql_page2.json` | `GET /rest/api/3/search/jql` (maxResults=3, real multi-page chain via `nextPageToken`) |
| `changelog_page1.json`, `changelog_page2.json`, `changelog_page3.json` | `GET /rest/api/3/issue/YKBOT-4048/changelog` (maxResults=5, real 3-page chain) |
| `worklog_empty.json` | `GET /rest/api/3/issue/YKBOT-4048/worklog` (ticket with no worklogs) |
| `worklog_with_comment.json` | `GET /rest/api/3/issue/YKBOT-4019/worklog` — captured after posting a real throwaway 60s worklog (deleted immediately after capture, not left on the ticket) |
| `error_410_gone.json` | `GET /rest/api/3/search` (the deprecated endpoint) — real error body |

Contains real ticket keys and one real account's name/email/avatar URL
(mine). Not secret, but scrub before sharing this folder outside the team —
see the parent README's "Packaging for the team" section.
