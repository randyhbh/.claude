"""Direct Jira REST API client. Stdlib-only. No LLM/MCP calls involved.

Auth token read from macOS Keychain (service "track-time-jira-api-token"),
never stored in a file.
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode


class JiraApiError(RuntimeError):
    pass


def get_token(account: str) -> str:
    result = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-a",
            account,
            "-s",
            "track-time-jira-api-token",
            "-w",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


class JiraClient:
    def __init__(self, base_url: str, email: str, token: str):
        self.base_url = base_url.rstrip("/")
        auth = b64encode(f"{email}:{token}".encode()).decode()
        self._auth_header = f"Basic {auth}"

    def _request(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", self._auth_header)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raise JiraApiError(f"{method} {path} -> {e.code}: {e.read().decode()}") from e

    def get_account_id(self) -> str:
        return self._request("GET", "/rest/api/3/myself")["accountId"]

    def search_issues(self, jql: str, fields: list[str]) -> list[dict]:
        issues = []
        page_token = None
        while True:
            params = {"jql": jql, "fields": ",".join(fields), "maxResults": 100}
            if page_token:
                params["nextPageToken"] = page_token
            data = self._request("GET", "/rest/api/3/search/jql", params=params)
            issues.extend(data["issues"])
            if data.get("isLast", True):
                break
            page_token = data["nextPageToken"]
        return issues

    def get_status_changelog(self, key: str) -> list[dict]:
        histories = []
        start_at = 0
        while True:
            data = self._request(
                "GET",
                f"/rest/api/3/issue/{key}/changelog",
                params={"startAt": start_at, "maxResults": 100},
            )
            histories.extend(data["values"])
            start_at += len(data["values"])
            if start_at >= data["total"] or not data["values"]:
                break
        return histories

    def get_worklogs(self, key: str) -> list[dict]:
        worklogs = []
        start_at = 0
        while True:
            data = self._request(
                "GET",
                f"/rest/api/3/issue/{key}/worklog",
                params={"startAt": start_at, "maxResults": 100},
            )
            worklogs.extend(data["worklogs"])
            start_at += len(data["worklogs"])
            if start_at >= data["total"] or not data["worklogs"]:
                break
        return worklogs

    def add_worklog(self, key: str, seconds: int, comment_text: str) -> dict:
        body = {
            "timeSpentSeconds": seconds,
            "comment": {
                "type": "doc",
                "version": 1,
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": comment_text}]}
                ],
            },
        }
        return self._request("POST", f"/rest/api/3/issue/{key}/worklog", body=body)