# Ship PR

Create a branch, group uncommitted changes into logical conventional commits, push, and open a PR assigned to Randy with Anesto as reviewer.

**Usage:** `/ship [branch-name] ["PR title"]`  
All arguments are optional — infer from context when not provided.

**Arguments:** $ARGUMENTS

## Step 1 — Gather context

Run these in parallel:
- `rtk git status` — what files changed
- `rtk git diff` — what actually changed
- `rtk git log --oneline -5` — recent commit style in this repo

## Step 2 — Infer missing arguments

If branch name not provided: derive a short kebab-case name from the nature of the changes (e.g. `feat/remove-v1-search-endpoints`, `fix/null-pointer-on-lookup`).

If PR title not provided: derive from the dominant change (e.g. `refactor(NO_JIRA): remove v1 programs-catalog-api endpoints`). Match the conventional commit style seen in `git log`.

## Step 3 — Create branch

```
git checkout -b <branch-name>
```

If branch already exists remotely: stop and ask Randy.

## Step 4 — Group changes into logical commits

Analyze `git diff` output and group files by concern. Each group becomes one commit. Aim for 2–5 commits that tell a coherent story. Examples of good groupings:

- OpenAPI spec changes → one commit
- Deleted dead service/delegate classes → one commit  
- Mapper / DTO migrations → one commit
- Test cleanup → one commit
- Explorer / client-side changes → one commit

For each group:
1. Stage only the files in that group explicitly by name (never `git add -A` or `git add .`)
2. Commit using conventional commit format with no `Co-Authored-By`:
   ```
   git commit -m "type(scope): description"
   ```
   Types: `feat`, `fix`, `refactor`, `chore`, `test`, `docs`  
   Scope: module or area affected (e.g. `programs-catalog-api`, `api-explorer`, `openapi`)

## Step 5 — Push

```
rtk git push -u origin <branch-name>
```

## Step 6 — Open PR

```
gh pr create \
  --title "<PR title>" \
  --assignee randyhbh \
  --reviewer anesto-deltoro \
  --body "..."
```

PR body: bullet-point summary of what changed + test plan checklist. No co-author lines.

## Step 7 — Print PR URL

## Rules
- Never `git add -A` or `git add .` — always stage files explicitly after reviewing status
- No `Co-Authored-By` in any commit
- Assignee always: `randyhbh`
- Reviewer always: `anesto-deltoro`
- All commits must follow conventional commits format
- Prefer more focused commits over one big commit
