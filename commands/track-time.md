---
description: Reconstruct time spent on my assigned Jira tickets from status history and log worklogs after confirmation
---

# /track-time

Reconstruct how long each of my assigned Jira tickets was actively worked on, using status-change
history, and log that time as Jira worklogs — never without my explicit confirmation.

All Jira fetching, computation, and posting happens in `run_track_time.py` — a standalone script
that talks to the Jira REST API directly (no MCP tool calls). Your job is just to run it, relay
its output, gate on confirmation, and run it again to post. Never call `searchJiraIssuesUsingJql`,
`getJiraIssue`, or `addWorklogToJiraIssue` for this command — the script replaces all of that.

## Steps

1. **Dry run.**
   ```bash
   python3 ~/.claude/commands/track-time/scripts/run_track_time.py --dry-run
   ```
   This prints a proposal table (ticket key, delta hours/minutes, tag or skip reason) and exits —
   nothing is posted, nothing is prompted.

2. **Present the proposal** to the user exactly as printed. If a ticket has an unusually large
   delta, flag it — but don't silently exclude it or change the computation; that's a decision for
   the user, not you.

3. **Wait for explicit confirmation.** Ask which tickets to post: all of them, a subset, or none.
   If the user excludes specific tickets, note their keys.

4. **Post.**
   ```bash
   python3 ~/.claude/commands/track-time/scripts/run_track_time.py --yes
   ```
   or, if the user excluded specific tickets:
   ```bash
   python3 ~/.claude/commands/track-time/scripts/run_track_time.py --yes --exclude YKBOT-1,YKBOT-2
   ```
   `--yes` skips the script's own interactive prompt (already satisfied by step 3 in this
   conversation) — it still prints the proposal again before posting.

5. **Report results.** Relay what the script printed: each `Posted <key>: <seconds>s (<tag>)` line,
   plus anything skipped and why.

## Setup note

If the script errors on missing config or a Keychain token, see
`~/.claude/commands/track-time/README.md` for one-time setup (API token in Keychain, `config.json`
fields). Don't try to work around a missing token by falling back to MCP tools — surface the setup
error to the user instead.
