# Setup

1. **API token** — create one at
   `id.atlassian.com/manage-profile/security/api-tokens`. Store it in the
   macOS Keychain, never in a file:
   ```bash
   security add-generic-password -a "you@yourcompany.com" -s "track-time-jira-api-token" -w '<token>' -U
   ```
2. **`config.json`** (in `track-time/`, alongside `scripts/`):
   ```json
   {
     "jira_base_url": "https://yourorg.atlassian.net",
     "jira_email": "you@yourcompany.com",
     "jira_user": "currentUser()",
     "status_in_progress": "In Progress",
     "status_review": "In-Review",
     "status_done": "Done",
     "review_cap_seconds": 3600,
     "updated_since": "startOfMonth()",
     "done_since": "-7d"
   }
   ```
   Status names must match your Jira instance **exactly** (case-sensitive) —
   JQL search is case-insensitive so a mismatch won't error, it'll silently
   compute zero time. Check your instance's actual status names first.

   `jira_email` in this config must match the account tied to the Keychain
   entry above (`-a` value) — that's how the script finds the right token.

   `updated_since` and `done_since` control the search window
   (`normalize.build_jql`). Both are optional — omit either and it falls back
   to the defaults shown above. Both accept **any JQL date expression**, not
   just relative day counts — e.g. `"-14d"`, `"startOfWeek()"`,
   `"startOfMonth()"`.
   - `updated_since` — bounds `updated >=`: which tickets show up in the
     search at all (touched recently enough). Doesn't change how much of a
     ticket's history counts toward trackable time (that's always just the
     last In-Progress stint, see [How it works](how-it-works.md)) — only
     changes which tickets are considered in the first place.
   - `done_since` — bounds `statusCategoryChangedDate >=`, only for tickets
     currently in the **Done** status: how far back a finished ticket can
     still surface for a final worklog. Still-open tickets ("In Progress" /
     "In Review") always show up regardless of this value; it only gates
     already-finished ones. Set to `"startOfMonth()"` to match `updated_since`
     if you want "only Done tickets finished this month" instead of a
     rolling window.
