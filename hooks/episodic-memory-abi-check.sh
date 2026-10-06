#!/usr/bin/env bash
# SessionStart hook: rebuilds the episodic-memory plugin's better-sqlite3 native module when it was compiled for a
# different Node.js ABI (happens after a Node upgrade or plugin update), so conversation search keeps working.
# Upstream bugs: obra/episodic-memory#94, #170. Remove this hook once they are fixed.
# Never fails the session: always exits 0. Silent when the module loads.
set -u
# Hooks may run with a minimal PATH (GUI/IDE launch); append Homebrew so node/npm resolve without shadowing overrides.
PATH="$PATH:/opt/homebrew/bin:/usr/local/bin"

root="${EPISODIC_MEMORY_ROOT:-$(ls -d "$HOME"/.claude/plugins/cache/superpowers-marketplace/episodic-memory/*/ 2>/dev/null | sort -V | tail -1)}"
root="${root%/}"
[ -n "$root" ] && [ -d "$root/node_modules/better-sqlite3" ] || exit 0

err="$(cd "$root" && node -e "const D = require('better-sqlite3'); new D(':memory:').close()" 2>&1)" && exit 0

case "$err" in
  *NODE_MODULE_VERSION*) ;;
  *)
    echo "episodic-memory: better-sqlite3 failed to load: $(printf '%s\n' "$err" | grep -m1 -i error)"
    exit 0
    ;;
esac

if (cd "$root" && npm rebuild better-sqlite3 >/dev/null 2>&1); then
  echo "episodic-memory: rebuilt better-sqlite3 for Node $(node --version)"
else
  echo "episodic-memory: better-sqlite3 rebuild failed; run 'npm rebuild better-sqlite3' in $root"
fi
exit 0