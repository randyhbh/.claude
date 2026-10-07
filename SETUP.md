# Claude Code Setup

Inventory of the Claude Code plugins, skills, MCP servers, hooks, commands and instruction files in use.
Snapshot taken 2026-10-06 from `~/.claude/`, `~/.agents/`, `~/.claude.json` and the `mrge-pub-intelligence-hub` checkout.

## Instruction files (CLAUDE.md)

| File | Scope | Link |
|------|-------|------|
| `~/.claude/CLAUDE.md` | Global, all projects | https://github.com/randyhbh/.claude/blob/main/CLAUDE.md |
| `~/.claude/RTK.md` | Global, imported by `CLAUDE.md` via `@RTK.md` | https://github.com/randyhbh/.claude/blob/main/RTK.md |
| `mrge-pub-intelligence-hub/CLAUDE.md` | Project | No link: gitignored (`.gitignore:153`), exists only on local disk |

## Settings

`~/.claude/settings.json` is not tracked: its `autoMode.environment` block holds org-specific details, and `autoMode`
is only read from user (or managed) settings, so it cannot move to a local file. The shareable copy is
[`settings.example.json`](https://github.com/randyhbh/.claude/blob/main/settings.example.json) — everything except
`autoMode.environment`. On a new machine copy it to `settings.json` and add the `autoMode.environment` block by hand. Regenerate the example after settings changes:

```bash
python3 -c "import json,os;p=os.path.expanduser('~/.claude/');d=json.load(open(p+'settings.json'));d.get('autoMode',{}).pop('environment',None);open(p+'settings.example.json','w').write(json.dumps(d,indent=2,ensure_ascii=False)+'\n')"
```

## Plugin marketplaces

| Marketplace | Source |
|-------------|--------|
| `claude-plugins-official` | https://github.com/anthropics/claude-plugins-official |
| `superpowers-marketplace` | https://github.com/obra/superpowers-marketplace |
| `caveman` | https://github.com/JuliusBrussee/caveman |
| `ponytail` | https://github.com/DietrichGebert/ponytail |
| `aiguide` | https://github.com/timescale/pg-aiguide |
| `redpanda-connect-plugins` | https://github.com/redpanda-data/connect |
| `gitkraken` | Local directory `~/.claude/plugins/marketplaces/gitkraken` (installed by GitKraken Desktop / GitLens) |

## Plugins (user scope)

| Plugin | Version | What it does | Link |
|--------|---------|--------------|------|
| `superpowers@superpowers-marketplace` | 6.4.2 | Skills library: brainstorming, TDD, systematic debugging, plans, subagent-driven dev | https://github.com/obra/superpowers |
| `episodic-memory@superpowers-marketplace` | 1.6.0 | Semantic search over past conversations | https://github.com/obra/episodic-memory |
| `caveman@caveman` | 25d22f8 | Terse output mode + skills (caveman, caveman-commit/-compress/-help/-review/-stats, cavecrew), cavecrew subagents, statusline. Skills come only from the plugin, not `npx skills` | https://github.com/JuliusBrussee/caveman |
| `ponytail@ponytail` | 4.8.4 | YAGNI / laziest-working-solution mode | https://github.com/DietrichGebert/ponytail |
| `code-review@claude-plugins-official` | d182ca4 | Multi-agent PR review | https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-review |
| `code-simplifier@claude-plugins-official` | 1.0.0 | Simplify-recent-code agent | https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-simplifier |
| `skill-creator@claude-plugins-official` | d182ca4 | Create and evaluate skills | https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator |
| `claude-md-management@claude-plugins-official` | 1.0.0 | Audit and revise CLAUDE.md files | https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-md-management |
| `jdtls-lsp@claude-plugins-official` | 1.0.0 | Java LSP (Eclipse JDT.LS) | https://github.com/anthropics/claude-plugins-official/tree/main/plugins/jdtls-lsp |
| `kotlin-lsp@claude-plugins-official` | 1.0.0 | Kotlin LSP | https://github.com/anthropics/claude-plugins-official/tree/main/plugins/kotlin-lsp |
| `pg@aiguide` | 0.5.1 | PostgreSQL docs MCP + schema design skills | https://github.com/timescale/pg-aiguide |
| `redpanda-connect@redpanda-connect-plugins` | 0.2.0 | Redpanda Connect pipeline + Bloblang skills | https://github.com/redpanda-data/connect |
| `gitkraken-hooks@gitkraken` | 3.1.76 | Live session tracking in GitKraken products | No public link (local marketplace) |

## Standalone skills (installed with `npx skills`, tracked in `~/.agents/.skill-lock.json`)

Symlinked from `~/.agents/skills/` into `~/.claude/skills/`.

### mattpocock/skills — https://github.com/mattpocock/skills

| Skill | skills.sh |
|-------|-----------|
| ask-matt | https://skills.sh/mattpocock/skills/ask-matt |
| claude-handoff | https://skills.sh/mattpocock/skills/claude-handoff |
| code-review | https://skills.sh/mattpocock/skills/code-review |
| codebase-design | https://skills.sh/mattpocock/skills/codebase-design |
| diagnosing-bugs | https://skills.sh/mattpocock/skills/diagnosing-bugs |
| domain-modeling | https://skills.sh/mattpocock/skills/domain-modeling |
| git-guardrails-claude-code | https://skills.sh/mattpocock/skills/git-guardrails-claude-code |
| grill-me | https://skills.sh/mattpocock/skills/grill-me |
| grill-with-docs | https://skills.sh/mattpocock/skills/grill-with-docs |
| grilling | https://skills.sh/mattpocock/skills/grilling |
| handoff | https://skills.sh/mattpocock/skills/handoff |
| implement | https://skills.sh/mattpocock/skills/implement |
| improve-codebase-architecture | https://skills.sh/mattpocock/skills/improve-codebase-architecture |
| loop-me | https://skills.sh/mattpocock/skills/loop-me |
| migrate-to-shoehorn | https://skills.sh/mattpocock/skills/migrate-to-shoehorn |
| prototype | https://skills.sh/mattpocock/skills/prototype |
| research | https://skills.sh/mattpocock/skills/research |
| resolving-merge-conflicts | https://skills.sh/mattpocock/skills/resolving-merge-conflicts |
| scaffold-exercises | https://skills.sh/mattpocock/skills/scaffold-exercises |
| setup-matt-pocock-skills | https://skills.sh/mattpocock/skills/setup-matt-pocock-skills |
| setup-pre-commit | https://skills.sh/mattpocock/skills/setup-pre-commit |
| setup-ts-deep-modules | https://skills.sh/mattpocock/skills/setup-ts-deep-modules |
| tdd | https://skills.sh/mattpocock/skills/tdd |
| teach | https://skills.sh/mattpocock/skills/teach |
| to-questionnaire | https://skills.sh/mattpocock/skills/to-questionnaire |
| to-spec | https://skills.sh/mattpocock/skills/to-spec |
| to-tickets | https://skills.sh/mattpocock/skills/to-tickets |
| triage | https://skills.sh/mattpocock/skills/triage |
| wait-what | https://skills.sh/mattpocock/skills/wait-what |
| wayfinder | https://skills.sh/mattpocock/skills/wayfinder |
| wizard | https://skills.sh/mattpocock/skills/wizard |
| writing-beats | https://skills.sh/mattpocock/skills/writing-beats |
| writing-for-agents | https://skills.sh/mattpocock/skills/writing-for-agents |
| writing-fragments | https://skills.sh/mattpocock/skills/writing-fragments |
| writing-shape | https://skills.sh/mattpocock/skills/writing-shape |

### Other sources

| Skill | Repo | skills.sh |
|-------|------|-----------|
| find-skills | https://github.com/vercel-labs/skills | https://skills.sh/vercel-labs/skills/find-skills |
| github-actions-docs | https://github.com/xixu-me/skills | https://skills.sh/xixu-me/skills/github-actions-docs |
| java-spring-boot | https://github.com/pluginagentmarketplace/custom-plugin-java | https://skills.sh/pluginagentmarketplace/custom-plugin-java/java-spring-boot |
| kotlin-springboot | https://github.com/github/awesome-copilot | https://skills.sh/github/awesome-copilot/kotlin-springboot |
| kubernetes-specialist | https://github.com/jeffallan/claude-skills | https://skills.sh/jeffallan/claude-skills/kubernetes-specialist |

## MCP servers

| Server | Scope | Transport | Link |
|--------|-------|-----------|------|
| `context7` | User (`~/.claude.json`, `CONTEXT7_API_KEY` header) | HTTP `https://mcp.context7.com/mcp` | https://github.com/upstash/context7 |
| `jetbrains` | User | SSE `localhost:64342` (IntelliJ built-in MCP server) | https://www.jetbrains.com/help/idea/mcp-server.html |
| `jcodemunch` | User (`~/.claude.json`, all repos) + Project (`.mcp.json` in mrge-pub-intelligence-hub, wins there) | stdio `/Users/randyhbh/.local/bin/jcodemunch-mcp` / `${JCODEMUNCH_BIN:-jcodemunch-mcp}` (pipx install) | https://github.com/jgravelle/jcodemunch-mcp |
| `grafana` | Project | stdio `uvx mcp-grafana` | https://github.com/grafana/mcp-grafana |
| `radar` | Project | HTTP `localhost:9280/mcp` | Unknown origin |
| `pg-aiguide` | Plugin (`pg@aiguide`) | — | https://github.com/timescale/pg-aiguide |
| `episodic-memory` | Plugin | — | https://github.com/obra/episodic-memory |
| Atlassian Rovo (Jira/Confluence), Claude Docs | claude.ai connectors | — | Managed in claude.ai settings |

## CLI tools wired into Claude Code

| Tool | Version | Used for | Link |
|------|---------|----------|------|
| `rtk` | 0.51.0 | `PreToolUse` Bash hook, rewrites commands to token-optimized output | https://github.com/rtk-ai/rtk |
| `jcodemunch-mcp` | 1.108.x (pipx; MCP server, hooks and watcher) | MCP server + Read/Edit/Subagent/Compact/Worktree hooks | https://github.com/jgravelle/jcodemunch-mcp |

## Rebuilding the jcodemunch setup

jcodemunch state lives in four places, none of them in this repo:

| What | Where |
|------|-------|
| CLI + `watchfiles` dependency | pipx venv `~/.local/pipx/venvs/jcodemunch-mcp` |
| Config (`max_folder_files`) | `~/.code-index/config.jsonc` |
| Indexes, watcher logs | `~/.code-index/*.db`, `~/.code-index/logs/` |
| Watcher service | `~/Library/LaunchAgents/us.gravelle.jcodemunch-watch.plist` |

Steps on a new machine:

```bash
# 1. CLI used by hooks and the watcher; watchfiles is required by watch/watch-all
pipx install jcodemunch-mcp
pipx inject jcodemunch-mcp watchfiles

# 2. Raise the local-folder file cap; the default 2000 truncates mrge-pub-intelligence-hub (~2.6k tracked files)
#    In ~/.code-index/config.jsonc set:  "max_folder_files": 5000,

# 3. MCP server at user scope (all repos). mrge-pub-intelligence-hub also ships it in .mcp.json, which wins there:
#    one server runs; ignore the "different endpoints" warning from claude mcp list (OAuth-only).
claude mcp add jcodemunch -s user -- /Users/randyhbh/.local/bin/jcodemunch-mcp

# 4. Hooks into ~/.claude/settings.json with absolute paths (worktree + enforcement hooks). Run in a throwaway dir:
#    init also writes CLAUDE.md/AGENTS.md into the current dir. Re-run after upgrades to converge to shipped hooks.
(cd "$(mktemp -d)" && jcodemunch-mcp init --client none --claude-md project --hooks --yes)

# 5. Background re-indexing (launchd, starts at login, KeepAlive)
jcodemunch-mcp watch-install

# 6. Initial index per repo; the watcher keeps it fresh afterwards
jcodemunch-mcp index /Users/randyhbh/workspace/mrge-pub-intelligence-hub
```

Verify with `jcodemunch-mcp watch-status` (service `active: true`, repos `fresh`) and check
`~/.code-index/logs/watch.err` for `Now watching <repo>` and no `crashed` lines.

There is no watch list: `watch-all` re-scans the index registry every 30s and watches every indexed repo. To watch a new
repo, index it (`jcodemunch-mcp index <repo-root>`); to stop watching one, delete its index.

Upgrading:

```bash
pipx upgrade --include-injected jcodemunch-mcp                      # also upgrades watchfiles
launchctl kickstart -k gui/$(id -u)/us.gravelle.jcodemunch-watch   # watcher keeps running old code until restarted
```

Then restart Claude Code so the MCP server starts on the new version. Avoid `jcodemunch-mcp upgrade`: it runs
`pip install -U` inside the venv instead of going through pipx.

Index repo roots only. Indexing a parent folder like `~/workspace` creates a separate giant index that the watcher also
picks up; remove one with the `invalidate_cache` MCP tool and restart the service with
`launchctl kickstart -k gui/$(id -u)/us.gravelle.jcodemunch-watch`.

## Hooks (`~/.claude/settings.json`)

| Event | Command |
|-------|---------|
| `PreToolUse` Read\|Grep\|Glob\|Bash | `/Users/randyhbh/.local/bin/jcodemunch-mcp hook-pretooluse` (advisory: steers code searches in indexed repos to jcodemunch, never blocks) |
| `PreToolUse` Bash | `/opt/homebrew/bin/rtk hook claude` |
| `PostToolUse` Edit\|Write | `/Users/randyhbh/.local/bin/jcodemunch-mcp hook-posttooluse` |
| `PreCompact` | `/Users/randyhbh/.local/bin/jcodemunch-mcp hook-precompact` |
| `SubagentStart` | `/Users/randyhbh/.local/bin/jcodemunch-mcp hook-subagent-start` |
| `TaskCompleted` | `/Users/randyhbh/.local/bin/jcodemunch-mcp hook-taskcomplete` |
| `WorktreeCreate` / `WorktreeRemove` | `/Users/randyhbh/.local/bin/jcodemunch-mcp hook-event create` / `remove` |
| `SessionStart` compact\|resume\|fork | `/Users/randyhbh/.local/bin/jcodemunch-mcp hook-sessionstart` (restores jcodemunch session state) |
| `SessionStart` | `caveman-activate.js` (from the caveman plugin) |
| `SessionStart` | `/bin/bash ~/.claude/hooks/episodic-memory-abi-check.sh` — rebuilds episodic-memory's `better-sqlite3` after a Node ABI change; silent when healthy (~85 ms). Tests: `bash ~/.claude/hooks/episodic-memory-abi-check.test.sh`. Remove once obra/episodic-memory#94/#170 are fixed |
| `UserPromptSubmit` | `caveman-mode-tracker.js` (from the caveman plugin) |
| `statusLine` | `bash ~/.claude/hooks/caveman-statusline.sh` |

jcodemunch hooks must use the absolute path `/Users/randyhbh/.local/bin/jcodemunch-mcp` (pipx install), which is what
`jcodemunch-mcp init` writes. The bare name is not on the minimal `PATH` hooks get when Claude Code is launched outside a
login shell (desktop app, IDE): `env -i /bin/sh -c 'jcodemunch-mcp --version'` fails with `command not found`.

## Custom slash commands (`~/.claude/commands/`)

| Command | Purpose | Link |
|---------|---------|------|
| `/ship` | Branch, conventional commits, push, open PR (why-first body) | Project skill in mrge-pub-intelligence-hub: `.claude/skills/ship/SKILL.md` (no longer personal) |
| `/track-time` | Rebuild Jira time from status history and log worklogs | https://github.com/randyhbh/.claude/tree/main/commands/track-time |
| `/make-local-issues` | Review code, write issues to `docs/issues` | https://github.com/randyhbh/.claude/blob/main/commands/make-local-issues.md |

## Project-level (`mrge-pub-intelligence-hub/.claude/`, gitignored)

- `.claude/agents/code-reviewer.md` — plan-vs-implementation review agent
- `.claude/settings.local.json` — project permission allowlist
