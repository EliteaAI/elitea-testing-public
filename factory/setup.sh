#!/usr/bin/env bash
# setup.sh — preflight. Checks everything the factory needs and says exactly
# what is missing. Changes nothing except (optionally) gh token scopes.
set -euo pipefail

FACTORY="$(cd "$(dirname "$0")" && pwd)"
HARNESS="$(dirname "$FACTORY")"               # the factory's own folder
cd "$HARNESS"
. "$FACTORY/config.env"
TRACKING_REPO="${TRACKING_REPO#/}"; TRACKING_REPO="${TRACKING_REPO%.git}"   # tolerate "/owner/repo" and ".git"
ok=1; fail() { echo "✗ $*"; ok=0; }; pass() { echo "✓ $*"; }; warn() { echo "△ $*"; }

command -v gh >/dev/null     && pass "gh installed"     || fail "gh missing"
command -v jq >/dev/null     && pass "jq installed"     || fail "jq missing"
command -v claude >/dev/null && pass "claude installed" || fail "claude missing"

# Every active loop MUST set WORKDIR. The harness carries no .claude/.agents of
# its own — skills, agents, rules, hooks and the .agents/* doctrine all arrive
# with the work repo — so a loop that leaves cwd at the harness runs its sessions
# with no tooling and no project doctrine at all.
SESSION_DIR=""
for f in "$FACTORY"/loops/*.env; do
  name="$(basename "$f" .env)"
  case "$name" in EXAMPLE-*) continue ;; esac
  d="$(. "$f"; echo "${WORKDIR:-}")"
  if [ -z "$d" ]; then
    fail "loop \"$name\" sets no WORKDIR — its sessions would run in $PWD, which has no .claude/.agents (they live in the work repo)"
  else
    pass "loop \"$name\" runs in $d"
    [ -n "$SESSION_DIR" ] || SESSION_DIR="$d"
  fi
done

# Execution toolchain — only for loops that run tests (NEEDS_EXEC=1 in
# loops/<name>.env); read-only triage loops stay green without it.
# setup.sh's own cwd is the image harness; the checks must run where the
# session runs — the WORKDIR of the loop that sets NEEDS_EXEC=1.
EXEC_LOOP="$(grep -ls '^NEEDS_EXEC=1' "$FACTORY"/loops/*.env | head -1 || true)"
if [ -n "$EXEC_LOOP" ]; then
  EXEC_DIR="$(. "$EXEC_LOOP"; echo "${WORKDIR:-}")"
  if [ -d "$EXEC_DIR" ] && cd "$EXEC_DIR"; then
    command -v npm >/dev/null && pass "npm installed" || fail "npm missing — MCP servers cannot start"
    command -v npx >/dev/null && pass "npx installed" || fail "npx missing"
    [ -x .venv/bin/pytest ] && pass ".venv/bin/pytest present" || fail ".venv missing in $EXEC_DIR — pip install -e '.[reporting]'"
    [ -d "${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}" ] && pass "Playwright browsers present" || fail "Playwright browsers missing"
    for s in ../EliteaUI ../onetest-ai-tm-Elitea; do
      [ -d "$s/.git" ] && pass "sibling $s present" || fail "sibling $s missing — four-sibling topology incomplete"
    done
    # The factory only READS ../EliteaUI as DEV ships it (main — the interaction-
    # discovery ladder) and adds no testids; automation/testids is the migrator's.
    ui_branch="$(git -C ../EliteaUI rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
    [ "$ui_branch" = main ] && pass "EliteaUI on main" || warn "EliteaUI on \"$ui_branch\", not main — the factory reads the UI source as DEV ships it"
    # The work repo mirrors this factory/ as a backup — the two must match.
    if [ -d factory ] && [ "$(cd factory && pwd)" != "$FACTORY" ]; then
      diff -rq -x state "$FACTORY" factory >/dev/null 2>&1 \
        && pass "work-repo factory/ mirror matches the harness copy" \
        || warn "work-repo factory/ mirror drifted from the harness copy — sync them (diff -r -x state)"
    else
      [ -d factory ] || warn "work repo has no factory/ mirror of the harness copy"
    fi
    (cd automation && ../.venv/bin/python -c 'from config import settings; assert settings.elitea_api_token and settings.test_user_email and settings.test_user_password and settings.elitea_url and settings.elitea_project_id') 2>/dev/null \
      && pass "credentials resolve through config.py" || fail "config.py resolves empty credentials"
    cd "$HARNESS"
  else
    fail "WORKDIR \"$EXEC_DIR\" of $(basename "$EXEC_LOOP") missing"
  fi
fi

gh auth status >/dev/null 2>&1 && pass "gh authenticated" || fail "gh not authenticated"
if gh project list --owner "$PROJECT_OWNER" --limit 1 >/dev/null 2>&1; then
  pass "project scope OK"
else
  fail "token lacks project scope — run: gh auth refresh -s project"
fi

gh repo view "$TRACKING_REPO" >/dev/null 2>&1 \
  && pass "tracking repo $TRACKING_REPO reachable" \
  || fail "tracking repo $TRACKING_REPO not reachable"

# Board exists, its Status column speaks our vocabulary — and cache the ids
# run.sh needs for its one board write (parking an escalated card).
if fields=$(gh project field-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --format json 2>/dev/null); then
  statuses=$(printf '%s' "$fields" | jq -r '.fields[] | select(.name == "Status") | .options[].name')
  pass "board #$PROJECT_NUMBER reachable (statuses: $(echo "$statuses" | paste -sd, -))"
  for s in "$STATUS_READY" "$STATUS_ACTIVE" "$STATUS_BLOCKED" "$STATUS_DONE"; do
    echo "$statuses" | grep -qxF "$s" || fail "board has no status \"$s\" — add the column or fix config.env"
  done
  mkdir -p "$FACTORY/state"
  jq -n --arg pid "$(gh project view "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --format json -q .id 2>/dev/null)" \
        --argjson f "$(printf '%s' "$fields" | jq '[.fields[] | select(.name == "Status")][0]')" \
        '{project_id: $pid, status_field_id: $f.id,
          options: ($f.options | map({(.name): .id}) | add)}' > "$FACTORY/state/board.json" \
    && pass "board ids cached (state/board.json)" \
    || fail "could not cache board ids"
else
  fail "cannot read board #$PROJECT_NUMBER (owner $PROJECT_OWNER)"
fi

# Child-type labels must exist so questions/bugs are recognizably not tasks.
labels="$(gh label list -R "$TRACKING_REPO" --json name -q '.[].name' 2>/dev/null || true)"
for l in $CHILD_LABELS; do
  echo "$labels" | grep -qxF "$l" \
    && pass "label \"$l\" exists in $TRACKING_REPO" \
    || fail "label missing — run: gh label create $l -R $TRACKING_REPO"
done

# Session-side config lives in the WORK REPO, not here: the harness ships no
# .claude/.agents at all, so these three checks must run in a loop's WORKDIR.
if [ -n "$SESSION_DIR" ] && [ -d "$SESSION_DIR" ] && cd "$SESSION_DIR"; then
  grep -qs '"cleanupPeriodDays"' .claude/settings.json .claude/settings.local.json 2>/dev/null \
    && pass "cleanupPeriodDays pinned" \
    || fail "conversations must outlive cases — add { \"cleanupPeriodDays\": 90 } to $SESSION_DIR/.claude/settings.json"

  # Project MCP servers (.mcp.json) need approval to load — and headless has
  # nobody to approve. Without this key, factory sessions silently run without
  # the repo's own tooling (proven on the first live run).
  if [ -f .mcp.json ]; then
    grep -qs '"enableAllProjectMcpServers"[[:space:]]*:[[:space:]]*true' .claude/settings.json 2>/dev/null \
      && pass "project MCP servers auto-enabled for headless sessions" \
      || fail "repo has .mcp.json but factory sessions cannot approve servers — add { \"enableAllProjectMcpServers\": true } to $SESSION_DIR/.claude/settings.json"
  fi

  # The seed is OPTIONAL: loop prompts are self-sufficient on board duties, so
  # an unseeded project runs fine in factory mode (interactive sessions just
  # won't follow the tracking discipline until seeded). But IF the seed exists,
  # its facts must match config.env — the same facts live twice by design
  # (config.env for scripts, profile.md for agents), filled in by hand,
  # separately: a mismatch means agents move cards on one board while the loop
  # reads another. Check it.
  if grep -qs "Work tracking" .agents/profile.md 2>/dev/null; then
    pass "profile.md seeded with § Work tracking"
    grep -qs "$TRACKING_REPO" .agents/profile.md \
      && pass "seed names the same tracking repo as config.env" \
      || fail "SPLIT-BRAIN: profile.md § Work tracking does not mention $TRACKING_REPO — seed and config.env disagree"
    grep -qsE "#${PROJECT_NUMBER}\b" .agents/profile.md \
      && pass "seed names board #$PROJECT_NUMBER" \
      || fail "SPLIT-BRAIN: profile.md does not mention board #$PROJECT_NUMBER — seed and config.env disagree"
    grep -qs "$PROJECT_OWNER" .agents/profile.md \
      && pass "seed names owner $PROJECT_OWNER" \
      || fail "SPLIT-BRAIN: profile.md does not mention owner $PROJECT_OWNER — seed and config.env disagree"
  else
    pass "no seed in profile.md — fine: headed mode stays board-unaware; loop prompts carry the factory's board duties (SEED.md is an optional extra)"
  fi
  cd "$HARNESS"
fi

[ $ok = 1 ] && echo "── ready. ./factory/run.sh" \
            || { echo "── fix the ✗ items first"; exit 1; }
