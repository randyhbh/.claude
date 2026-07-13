# track-time

Reconstructs time spent on Jira tickets from status-change history and logs it
as worklogs.

`scripts/run_track_time.py` does the actual work — talks to the Jira REST API
directly, no MCP/LLM call anywhere in the fetch → compute → post loop.
`/track-time` the slash command is a thin wrapper around it: run the script,
show you the proposal, gate on your confirmation, run it again to post.

## Docs

- [How it works](docs/how-it-works.md) — the computation pipeline, idempotency
  rules, tag format, and the one known correctness gap.
- [Setup](docs/setup.md) — API token in Keychain, `config.json` fields.
- [Running](docs/usage.md) — slash command vs. raw script, all flags, five
  example flows including running fully raw with no Claude Code involved.
- [Testing](docs/testing.md) — how to run the suite, what each test file covers.
- [Packaging for the team](docs/packaging.md) — what has to change before
  sharing this outside your own machine.

## Files

| File | Purpose |
|---|---|
| `compute_worklog.py` | Pure calculation core: segments, trackable seconds, overlap splitting, idempotent delta/tagging |
| `jira_client.py` | Thin stdlib `urllib` wrapper over Jira REST API v3 (search, changelog, worklog, post) |
| `normalize.py` | Pure functions: JQL builder, ADF↔text, raw Jira JSON → `compute_worklog` input shape |
| `run_track_time.py` | Orchestrator: config → fetch → compute → print → (confirm) → post |
| `config.json` | Per-user Jira instance/status-name/user config (not secret, but personal — see [Packaging](docs/packaging.md)) |
| `fixtures/` | Real recorded Jira API responses used by `test_jira_client.py` |
| `track-time.md` (parent dir) | The `/track-time` slash command — thin wrapper around `run_track_time.py` |
