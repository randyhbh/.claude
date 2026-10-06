#!/usr/bin/env bash
# Tests for episodic-memory-abi-check.sh. Run: bash ~/.claude/hooks/episodic-memory-abi-check.test.sh
set -u
here="$(cd "$(dirname "$0")" && pwd)"
hook="$here/episodic-memory-abi-check.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
failures=0

check() { # name, condition result (0 = pass)
  if [ "$2" -eq 0 ]; then echo "ok   $1"; else echo "FAIL $1"; failures=$((failures + 1)); fi
}

# Fake plugin root whose better-sqlite3 throws the given message when constructed.
make_root() {
  local root="$tmp/$1"
  mkdir -p "$root/node_modules/better-sqlite3"
  printf 'module.exports = function () { throw new Error(%s) }\n' "$2" \
    > "$root/node_modules/better-sqlite3/index.js"
  echo "$root"
}

# Fake npm on PATH that records its arguments instead of rebuilding.
mkdir -p "$tmp/bin"
cat > "$tmp/bin/npm" <<'EOF'
#!/usr/bin/env bash
echo "$*" >> "$NPM_LOG"
EOF
chmod +x "$tmp/bin/npm"
export NPM_LOG="$tmp/npm.log"

# 1. ABI mismatch triggers a rebuild and reports it.
root="$(make_root abi "'was compiled against a different Node.js version using NODE_MODULE_VERSION 141'")"
: > "$NPM_LOG"
out="$(EPISODIC_MEMORY_ROOT="$root" PATH="$tmp/bin:$PATH" bash "$hook" 2>&1)"; rc=$?
check "abi mismatch exits 0" "$rc"
grep -qx 'rebuild better-sqlite3' "$NPM_LOG"; check "abi mismatch runs npm rebuild better-sqlite3" $?
[[ "$out" == *"rebuilt better-sqlite3"* ]]; check "abi mismatch reports the rebuild" $?

# 2. Any other load error is reported but does not rebuild.
root="$(make_root other "'boom: disk on fire'")"
: > "$NPM_LOG"
out="$(EPISODIC_MEMORY_ROOT="$root" PATH="$tmp/bin:$PATH" bash "$hook" 2>&1)"; rc=$?
check "other error exits 0" "$rc"
[ ! -s "$NPM_LOG" ]; check "other error does not rebuild" $?
[[ "$out" == *"boom: disk on fire"* ]]; check "other error is reported" $?

# 3. Missing plugin is silent.
out="$(EPISODIC_MEMORY_ROOT="$tmp/does-not-exist" bash "$hook" 2>&1)"; rc=$?
check "missing plugin exits 0" "$rc"
[ -z "$out" ]; check "missing plugin is silent" $?

# 4. The real, healthy install is silent and does not rebuild.
: > "$NPM_LOG"
out="$(PATH="$tmp/bin:$PATH" bash "$hook" 2>&1)"; rc=$?
check "healthy install exits 0" "$rc"
[ -z "$out" ]; check "healthy install is silent" $?
[ ! -s "$NPM_LOG" ]; check "healthy install does not rebuild" $?

# 5. Works under the minimal PATH hooks get when Claude Code is launched outside a login shell.
out="$(env -i HOME="$HOME" /bin/bash "$hook" 2>&1)"; rc=$?
check "minimal PATH exits 0" "$rc"
[ -z "$out" ]; check "minimal PATH finds node and stays silent" $?

[ "$failures" -eq 0 ] && echo "all passed" || { echo "$failures failed"; exit 1; }