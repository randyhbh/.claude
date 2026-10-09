# Running

**Via the slash command** (recommended if you're in a Claude Code session):
```
/track-time
```
Runs a dry run, shows you the proposal, asks which tickets to post (all, a
subset, or none), then posts.

**Directly** (no Claude Code needed — it's a standalone Python script):
```bash
cd scripts
python3 run_track_time.py                          # prints proposal, asks y/N, then posts
python3 run_track_time.py --dry-run                 # prints proposal only, never posts, never prompts
python3 run_track_time.py --yes                     # skip the interactive prompt, post everything postable
python3 run_track_time.py --yes --exclude A-1,A-2   # post everything postable except the listed keys
```

`--dry-run` is a script-level guarantee, separate from the slash command's
own confirmation step: compute + print, then exit — no `input()` prompt, no
posting, no way to accidentally trigger a write. Without it, the bare script
asks its own `y/N` prompt and *could* post if you answer y. `/track-time`
uses `--dry-run` for its own first step so gathering the proposal to show you
in chat can never post on its own; your real confirmation happens afterward,
in the conversation.

## Example flows

### 1. Routine run, post everything

```
/track-time
```
```
Ticket            Delta  Tag / Skip reason
--------------------------------------------------
YKBOT-4048         1h0m  tag=auto-tracked:final
YKBOT-4047         1h4m  tag=auto-tracked:final
YKBOT-3708         2h12m  tag=auto-tracked:final
CPA-1230             --  skipped: no new time to log
```
Reply "post all". `/track-time` runs `run_track_time.py --yes`, which reprints
the proposal and posts the three postable tickets. `CPA-1230` was already
correctly logged last run — no worklog written for it.

### 2. Suspiciously large delta — exclude and investigate first

```
/track-time
```
```
Ticket            Delta  Tag / Skip reason
--------------------------------------------------
YKBOT-4035      144h32m  tag=auto-tracked:partial
YKBOT-3930       14h39m  tag=auto-tracked:partial
```
`YKBOT-4035` at 144h32m looks wrong. Reply "post all except YKBOT-4035" (or
just ask what's driving the number — see below). `/track-time` runs:
```bash
python3 run_track_time.py --yes --exclude YKBOT-4035
```
Only `YKBOT-3930` posts. `YKBOT-4035`'s delta isn't lost — it carries over and
shows up again (usually larger, since more time has passed) next run once
you've confirmed it's legit or fixed the ticket's status history.

To actually investigate a large delta, ask directly — e.g. "in which state did
we spend so much time on YKBOT-4035?" This walks the real changelog and
segments (`build_segments` + `last_in_progress_seconds` per status), not just
the final number, so you can see exactly which stint or reopen is inflating it.

### 3. Re-running is safe (idempotency check)

Run `/track-time` again right after posting:
```
Ticket            Delta  Tag / Skip reason
--------------------------------------------------
YKBOT-4048           --  skipped: already finalized
YKBOT-3708           --  skipped: already finalized
YKBOT-4035         0h3m  tag=auto-tracked:partial
```
Finalized tickets (Done + `auto-tracked:final` already logged) always skip,
forever — no re-triggering. Still-open tickets show only genuinely new
wall-clock time accrued since the last post (here, 3 minutes — the ticket's
still actively "In Progress"). Nothing is ever double-counted.

### 4. Sub-minute deltas accumulate instead of vanishing

```
Ticket            Delta  Tag / Skip reason
--------------------------------------------------
YKBOT-3930           --  skipped: delta below 60s Jira minimum, will accumulate next run
```
Jira rejects `timeSpentSeconds < 60`. Rather than silently dropping a few
seconds, `run_track_time.py` skips posting but does **not** mark it as
logged — the next run's delta includes this time too, so it eventually
crosses 60s and posts correctly.

### 5. Raw script, no Claude Code / LLM involved at all

Everything in `scripts/` is plain Python 3 stdlib — no Claude Code, no MCP, no
LLM call anywhere. Useful for cron, CI, or just running it from a plain
terminal on a machine that has the Keychain token and `config.json` set up:

```bash
cd ~/.claude/track-time/scripts

# Peek at the numbers without any risk of posting.
python3 run_track_time.py --dry-run

# Non-interactive post, e.g. from a cron job or shell script.
# --yes skips the y/N prompt entirely, so this line alone is enough
# to fetch, compute, and post with zero human interaction after setup.
python3 run_track_time.py --yes
```

Since `--yes` removes the interactive gate, wiring `run_track_time.py --yes`
into a cron job means every scheduled run posts automatically. That's the
same "no confirmation" behavior you'd get from typing `y` at the prompt
yourself — think about whether an unattended run is actually what you want
before scheduling one; `/track-time` exists specifically so a human looks at
the proposal before every post.

Exit code is `0` on success (including "nothing to post"); a Keychain lookup
failure, config error, or Jira API error propagates as a non-zero exit and a
traceback, same as any other Python script — so this composes fine with
normal shell error handling (`&&`, `set -e`, cron's mail-on-failure, etc).
