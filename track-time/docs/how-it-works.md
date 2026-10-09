# How it works

1. Search Jira for your tickets updated this month, in progress / in review,
   or done in the last 7 days (JQL built by `normalize.build_jql`).
2. Pull each ticket's status changelog + existing worklogs.
3. Reconstruct wall-clock time spent in the most recent contiguous
   "In Progress" stint (full) plus "In Review" (capped once per ticket,
   default 1h). Earlier stints from before a reopen don't count — only the
   current one.
4. If multiple tickets were "In Progress" at the same time, split the
   overlapping wall-clock window between them instead of double-counting.
5. Diff against already-logged, tagged worklogs to find the delta.
6. Print a proposal table. **Nothing is posted without explicit confirmation.**
7. On confirm, post one worklog per ticket, tagged `auto-tracked:partial`
   (still open) or `auto-tracked:final` (ticket reached Done — logged once).
   No square brackets in the tag: Jira's wiki-markup renderer treats `[text]`
   as link syntax and fails to render it (shows blank in some views, e.g. the
   activity feed). Older worklogs posted with brackets are still detected via
   substring match, so nothing needs re-tagging for idempotency to keep working.

Idempotent: safe to re-run. Reopened-after-final tickets are handled by the
same delta rule, no special-casing needed. Deltas under Jira's 60s worklog
minimum are held over to the next run instead of being dropped.

## Known gap

If a ticket was Done + finalized, then reopened and worked again,
`already_logged` still subtracts the old (now-excluded) stint's logged time
from the new stint's total — undercounts the delta. Needs worklog timestamps
to know which stint a logged worklog belongs to; not implemented, will
surface if/when it happens on a real ticket.
