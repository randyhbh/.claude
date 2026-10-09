"""Pure functions turning raw Jira REST payloads into compute_worklog's IssueInput JSON shape."""

from __future__ import annotations

from compute_worklog import TAG_FINAL, TAG_PARTIAL

# Substring match, not exact: older worklogs were tagged with square brackets
# ("[auto-tracked:partial]") before we dropped them (Jira's renderer chokes on
# "[text]" as wiki-markup link syntax). The bracketed form still contains the
# unbracketed tag as a substring, so this detects both and normalizes to the
# current unbracketed value.
_KNOWN_TAGS = (TAG_PARTIAL, TAG_FINAL)


def build_jql(config: dict) -> str:
    user = config["jira_user"]
    assignee_clause = f"assignee = {user}" if user == "currentUser()" else f'assignee = "{user}"'
    status_in_progress = config["status_in_progress"]
    status_review = config["status_review"]
    status_done = config["status_done"]
    updated_since = config.get("updated_since", "startOfMonth()")
    done_since = config.get("done_since", "-7d")
    return (
        f'{assignee_clause} AND updated >= {updated_since} AND '
        f'(status in ("{status_in_progress}", "{status_review}") '
        f'OR (status = "{status_done}" AND statusCategoryChangedDate >= {done_since}))'
    )


def adf_to_text(adf: dict | None) -> str:
    if adf is None:
        return ""
    parts: list[str] = []

    def walk(node: dict) -> None:
        if node.get("type") == "text":
            parts.append(node.get("text", ""))
        for child in node.get("content", []):
            walk(child)

    walk(adf)
    return "".join(parts)


def extract_status_transitions(histories: list[dict]) -> list[dict]:
    transitions = []
    for history in histories:
        for item in history["items"]:
            if item["field"] == "status":
                transitions.append({"timestamp": history["created"], "to_status": item["toString"]})
    return transitions


def extract_existing_worklogs(worklogs: list[dict]) -> list[dict]:
    result = []
    for worklog in worklogs:
        text = adf_to_text(worklog.get("comment"))
        tag = next((t for t in _KNOWN_TAGS if t in text), None)
        result.append({"seconds": worklog["timeSpentSeconds"], "tag": tag})
    return result