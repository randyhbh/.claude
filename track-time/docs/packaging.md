# Packaging for the team

`config.json` as checked in here has **your** email and instance URL — do not
hand this folder to teammates as-is without genericizing it first. Two things
need to change before it's shareable:

1. **Split config into template + local override.** Rename current
   `config.json` → `config.example.json` with placeholder values
   (`"jira_email": "you@yourcompany.com"`), and have `run_track_time.py` read
   from `config.json` if present, falling back to `config.example.json`.
   Add `config.json` to `.gitignore` in whatever repo you package this into,
   so each teammate creates their own from the example without it landing in
   git.
2. **Each teammate needs their own Keychain entry.** The token is tied to
   their own Atlassian account — there's no way around each person running
   the one `security add-generic-password` command themselves with their own
   token.
3. **Scrub `scripts/fixtures/`** — they contain a real account's name/email/
   avatar URL and real ticket keys. Not secret, but personal; regenerate or
   redact before sharing outside the team (see `scripts/fixtures/README.md`).

Once that split is done, two realistic ways to distribute:

- **Plain shared repo** (simplest, works today): push this folder to a small
  git repo (internal GitHub/GitLab). Teammates `git clone` it wherever they
  keep personal tooling, then symlink or copy `track-time/` into their own
  `~/.claude/commands/`. No Claude Code–specific packaging needed since
  `run_track_time.py` doesn't require Claude Code at all — it's a standalone
  Python script. `/track-time` the slash command still needs to live under
  `~/.claude/commands/` to be invocable, so that part does need the copy/symlink step.
- **Claude Code plugin**: Claude Code supports installable plugins with their
  own marketplace format. I haven't verified the current manifest schema
  against this codebase — before building that route, want to confirm the
  plugin.json shape against Claude Code's docs rather than guess. Say the
  word and I'll look it up before implementing.
