#!/usr/bin/env bash
# run.sh — one factory loop. Several loops (different agents, different queues)
# may run at the same time: one terminal each.
#
#   ./factory/run.sh                 # the default loop (loops/tal.env)
#   ./factory/run.sh sage            # another agent, its own queue
#   ./factory/run.sh tal --once      # one card, then stop
#   ./factory/run.sh --all           # every loop in loops/ (except EXAMPLE-*),
#                                    # in parallel, each on its own POLL cadence
#
# THE ONE RULE: a card in Approved is the only "go" signal — first time and
# every resume. Blocked cards sit untouched, however their questions/bugs get
# answered, until a human drags them back to Approved. The human is both the
# approval gate and the wake gate; the loop never decides that answering is
# finished. Question/bug issues are conversation places, never tasks —
# loops refuse them even if one is dragged to Approved by mistake.
#
# The agent moves statuses himself, exactly as in an interactive session
# (SEED.md — layer 2). The loop READS the board, with ONE write exception:
# after MAX_ATTEMPTS failed sessions it moves the card to Blocked itself —
# no agent is alive to do it, and it keeps the retry gesture uniform (drag
# back to Approved, same as everything else).
set -euo pipefail
# Any set -e death is LOUD: a loop that dies must say so (a tal loop once
# died silently mid-night on a transient API failure while its siblings ran on).
trap 'echo "[${LOOP:-?}] FATAL: command failed at line $LINENO — loop exiting" >&2' ERR

FACTORY="$(cd "$(dirname "$0")" && pwd)"

# --all: run every configured loop as a child, Ctrl-C stops them all.
if [ "${1:-}" = "--all" ]; then
  shift || true
  pids=""
  for f in "$FACTORY"/loops/*.env; do
    name="$(basename "$f" .env)"
    case "$name" in EXAMPLE-*) continue ;; esac
    "$FACTORY/run.sh" "$name" "$@" &
    pids="$pids $!"
    echo "[all] started loop '$name' (pid $!)"
  done
  [ -n "$pids" ] || { echo "no loops in $FACTORY/loops/"; exit 2; }
  # kill 0 = the entire process group: the loops AND their in-flight claude
  # sessions. Killing only the loop scripts orphans live sessions, which keep
  # working their old missions beside the next fleet — twin sessions on one
  # conversation, /tmp collisions, phantom "injections" (live finding).
  trap 'trap - INT TERM; kill 0' INT TERM
  wait
  exit 0
fi

cd "$(dirname "$FACTORY")"                    # the work repo (default cwd)
. "$FACTORY/config.env"
TRACKING_REPO="${TRACKING_REPO#/}"; TRACKING_REPO="${TRACKING_REPO%.git}"   # tolerate "/owner/repo" and ".git"

LOOP="tal"; ONCE=""
for a in "$@"; do
  case "$a" in --once) ONCE=1 ;; *) LOOP="$a" ;; esac
done
[ -f "$FACTORY/loops/$LOOP.env" ] || { echo "no such loop: $FACTORY/loops/$LOOP.env"; exit 2; }
[ -f "$FACTORY/loops/$LOOP.md" ]  || { echo "no loop prompt: $FACTORY/loops/$LOOP.md"; exit 2; }
. "$FACTORY/loops/$LOOP.env"
[ -n "${WORKDIR:-}" ] && cd "$WORKDIR"        # writers get their own clone

STATE="$FACTORY/state"; mkdir -p "$STATE"

# One instance of a loop per factory — a second `run.sh intake` while one is
# already alive would resume the SAME conversations beside it (interleaved
# transcripts, duplicate work; live finding). PID-stamped, stale-swept.
if [ -f "$STATE/loop-$LOOP.pid" ] && kill -0 "$(cat "$STATE/loop-$LOOP.pid" 2>/dev/null)" 2>/dev/null; then
  echo "[$LOOP] already running (pid $(cat "$STATE/loop-$LOOP.pid")) — refusing a twin. Stop it first."
  exit 4
fi
echo $$ > "$STATE/loop-$LOOP.pid"

# POLL (loop env, e.g. "30s", "5m", "1h"): with it set, an empty queue means
# sleep and check again — the loop keeps watching. Without it, an empty queue
# ends the run. The wait is plain bash sleep: zero tokens.
poll_secs() {
  case "${POLL:-}" in
    "")     echo "" ;;
    *h)     echo $(( ${POLL%h} * 3600 )) ;;
    *m)     echo $(( ${POLL%m} * 60 )) ;;
    *s)     echo "${POLL%s}" ;;
    *)      echo "$POLL" ;;
  esac
}
POLL_SECS="$(poll_secs)"

# One conversation per issue PER AGENT, forever. The id is DERIVED — never
# stored anywhere: the same issue always maps to the same conversation for
# this loop's agent. Drag a card back to Approved a week later and the loop
# recomputes the same id and resumes the same conversation, memory intact.
# SID_SCOPE (loop env) overrides the namespace when two loops share an agent
# but must NOT share conversations — e.g. an auditor loop running the same
# agent as the deliverer: without its own scope it would resume the
# deliverer's conversation and "independently" audit from inside the
# deliverer's memory (live finding).
sid_for() {
  local key="$TRACKING_REPO#$1#${SID_SCOPE:-$AGENT}" h
  h=$(printf '%s' "$key" | md5 -q 2>/dev/null || printf '%s' "$key" | md5sum | cut -d' ' -f1)
  printf '%s-%s-4%s-a%s-%s' "${h:0:8}" "${h:8:4}" "${h:13:3}" "${h:17:3}" "${h:20:12}"
}

# Child issues are never tasks: refuse them even if approved by mistake.
is_child() {
  local l
  l=$(gh issue view "$1" -R "$TRACKING_REPO" --json labels -q '[.labels[].name]|join(" ")' 2>/dev/null) || return 1
  local c; for c in $CHILD_LABELS; do
    case " $l " in *" $c "*) return 0 ;; esac
  done
  return 1
}

# Does a local transcript exist for this issue's conversation? Reads Claude's
# per-cwd transcript store directly (verified layout). If that internal layout
# ever changes, this returns false and queue priority degrades to plain
# board order — nothing breaks.
has_conversation() {
  local dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/$(printf '%s' "$PWD" | sed 's/[^a-zA-Z0-9]/-/g')"
  [ -f "$dir/$(sid_for "$1").jsonl" ]
}

# Say WHY a board read failed. The reason was discarded (2>/dev/null) for
# months, and it turned out to be neither network nor a blip: the GraphQL
# rate limit — 5000 points/hour, ONE pool for every token of the same GitHub
# user, i.e. the loop's keyring login AND every agent session's `gh` calls —
# exhausted by the agents' own `gh issue list --limit 300` / `gh project
# item-list` sweeps. Every board read then fails until the hourly reset,
# which reads as a broken loop ("board read failed" ×2 per pass for 40 min,
# 2026-09-10). Name the reason and, for a rate limit, the reset time
# (`gh api rate_limit` is REST — a separate pool, so it still answers).
board_read_failed() {
  local err="$STATE/board-error-$LOOP.txt" why reset=""
  why=$(head -1 "$err" 2>/dev/null | cut -c1-160)
  if printf '%s' "$why" | grep -qi "rate limit"; then
    reset=$(gh api rate_limit --jq '.resources.graphql.reset' 2>/dev/null || true)
    [ -n "$reset" ] && reset=" (GraphQL pool resets at $(date -r "$reset" +%H:%M 2>/dev/null || echo "$reset"))"
  fi
  echo "[$LOOP $(date +%H:%M:%S)] board read failed — $1: ${why:-no error text}${reset} — treating it as empty this pass" >&2
}

cards_in() { # status → issue numbers, in BOARD ORDER (top of column first)
  # Board reads WILL fail transiently over a multi-day run (rate limits,
  # network). A failed read is an empty queue THIS PASS — the next POLL tick
  # retries — never a reason to die (a loop died silently on this once).
  local out err="$STATE/board-error-$LOOP.txt"
  if ! out=$(gh project item-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" \
       --query "status:\"$1\" $QUERY" --format json --limit 50 2>"$err"); then
    sleep 5
    out=$(gh project item-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" \
       --query "status:\"$1\" $QUERY" --format json --limit 50 2>"$err") \
      || { board_read_failed "queue read: $1"; : > "$STATE/read-failed-$LOOP"; return 0; }
  fi
  # BOARD ORDER, not numeric: the Projects API returns items in the board's
  # manual top-to-bottom order (verified 2026-07-23 — dragging a card up moves
  # it up in this list, no field on the card changes), so a human drag
  # re-prioritises the queue directly. We deliberately do NOT
  # sort_by(.content.number). Caveat: this manual rank is a per-view property
  # with no documented API contract — applying an explicit sort to the board
  # view disables drag ranking, after which pickup follows whatever order the
  # API then yields. If you need auditable priority, add a field and sort on it.
  printf '%s' "$out" | jq -r '.items[] | select(.content.type == "Issue") | .content.number'
}

# The queue: Approved cards (fresh work AND dragged-back resumes — the drag is
# the only wake signal), plus our In Progress cards (a session ended without
# moving the card on; without this, retry could never actually happen).
# CONTINUATIONS FIRST: a card whose conversation already exists on disk is a
# dragged-back resume or a mid-retry case — a human acted on it and warm
# context exists. Fresh cases after, in board order — drag a card up to work
# it sooner.
# Cards escalated THIS RUN are never re-claimed in the same run: the Projects
# API is eventually consistent, so the queue read right after our own Blocked
# write can still return the stale status — without this, escalate→reclaim
# hot-loops, burning a session a minute (seen live). A restart or the next
# POLL tick re-evaluates from fresh reads, by which time the write has landed.
# …but "this run" must NOT mean "until restart": a card the loop parked and a
# human later dragged back to Approved was skipped for as long as the loop
# lived, so the drag-back "needed a restart" (live finding, 2026-09-10). The
# Blocked write lands in seconds; skip the card for ESCALATE_GRACE seconds
# (default 15 min), after which its presence in the trigger column is a real
# drag-back again.
ESCALATED=""
mark_escalated() { ESCALATED="$ESCALATED
$1 $(date +%s)"; }
skip_escalated() {
  local when
  when=$(printf '%s\n' "$ESCALATED" | awk -v n="$1" '$1==n{t=$2} END{print t}')
  [ -n "$when" ] || return 1
  [ $(( $(date +%s) - when )) -lt "${ESCALATE_GRACE:-900}" ]
}

next_card() {
  # STATUS_ACTIVE is the retry path for THIS loop's own mid-flight work — but
  # the column is SHARED across loops, and query disjointness cannot be
  # trusted there (a catch-all QUERY matches every mid-flight card, whoever
  # dispatched it). A card is claimable from it ONLY when state/claim-<n>
  # names this loop. Unclaimed cards in the column (dragged there by hand, or
  # mid-flight when claims landed) are left alone, loudly: the recovery is
  # the universal gesture — drag back to the trigger column. A verdict-only
  # loop (agent never moves cards) still sets STATUS_ACTIVE="" in its env:
  # it has no mid-flight work to retry there, claim or no claim.
  local nums ready n c active=""
  ready="$(cards_in "$STATUS_READY")"
  if [ -n "${STATUS_ACTIVE:-}" ] && [ "$STATUS_ACTIVE" != "$STATUS_READY" ]; then
    for n in $(cards_in "$STATUS_ACTIVE"); do
      c="$(claim_of "$n")"
      if [ "$c" = "$LOOP" ]; then
        active="$active
$n"
      elif [ -z "$c" ]; then
        echo "[$LOOP] #$n sits in $STATUS_ACTIVE unclaimed — leaving it (drag to $STATUS_READY to (re)start it)." >&2
      fi
      # a foreign claim is another loop's mid-flight card — not ours, no noise
    done
  fi
  nums="$ready$active"
  nums="$(echo "$nums" | grep -v '^$' || true)"
  [ -n "$nums" ] || return 0
  for n in $nums; do
    skip_escalated "$n" && continue
    has_conversation "$n" && ! is_child "$n" && { echo "$n"; return 0; }
  done
  for n in $nums; do
    skip_escalated "$n" && continue
    is_child "$n" || { echo "$n"; return 0; }
  done
  return 0
}

# One issue's card on THIS board: "<item id>\t<status>" (empty = no card),
# read through the issue's own projectItems — never a board-wide scan. The
# old `item-list --limit 200` scan silently missed every card past position
# 200: once the board passed 1000 items (2026-09) status_of read "gone" for
# every recent card and park_card did NOTHING for them while the loop
# announced the park (live finding). This costs 1 GraphQL point, any board size.
item_of() {
  local out
  out=$(gh api graphql -F o="${TRACKING_REPO%%/*}" -F r="${TRACKING_REPO#*/}" -F n="$1" \
    -f query='query($o:String!,$r:String!,$n:Int!){ repository(owner:$o,name:$r){ issue(number:$n){ projectItems(first:20){ nodes{ id project{ number } fieldValueByName(name:"Status"){ ... on ProjectV2ItemFieldSingleSelectValue { name } } } } } } }' \
    2>"$STATE/board-error-$LOOP.txt") || return 1
  printf '%s' "$out" | jq -r --argjson p "$PROJECT_NUMBER" \
    '.data.repository.issue.projectItems.nodes[] | select(.project.number == $p) | [.id, (.fieldValueByName.name // "gone")] | @tsv' \
    | head -1
}

# What does the board say about this issue now? unknown = could not read.
status_of() {
  local row
  row=$(item_of "$1") || { board_read_failed "status of #$1"; echo "unknown"; return 0; }
  [ -n "$row" ] || { echo "gone"; return 0; }
  printf '%s\n' "$row" | cut -f2
}

# The loop's ONE board write: park an escalated card as Blocked. Uses the ids
# setup.sh cached in state/board.json. Returns 0 ONLY when the write went
# through — the caller must not clear attempts on a card that is still in
# the queue (that is how a stuck card got a fresh 3 sessions per restart).
park_card() {
  local b="$STATE/board.json" row item err="$STATE/board-error-$LOOP.txt"
  [ -f "$b" ] || { echo "[$LOOP] park: no state/board.json — card stays where it is (run setup.sh)" >&2; return 1; }
  row=$(item_of "$1") || { board_read_failed "park #$1"; return 1; }
  item=$(printf '%s\n' "$row" | cut -f1)
  [ -n "$item" ] || { echo "[$LOOP] park: #$1 has no card on board $PROJECT_NUMBER — nothing to park" >&2; return 1; }
  gh project item-edit --id "$item" \
    --project-id "$(jq -r .project_id "$b")" \
    --field-id  "$(jq -r .status_field_id "$b")" \
    --single-select-option-id "$(jq -r --arg s "$STATUS_BLOCKED" '.options[$s]' "$b")" \
    >/dev/null 2>"$err" \
    || { echo "[$LOOP] park: board write failed: $(head -1 "$err" 2>/dev/null | cut -c1-160) — card stays where it is" >&2; return 1; }
}

# Attempts are at the cap: park the card. On success the counter resets (a
# dragged-back card gets fresh attempts); on failure it stays at the cap so no
# further session burns on the card — the park is retried next pass instead.
escalate() {
  if park_card "$1"; then
    gh issue comment "$1" -R "$TRACKING_REPO" \
      -b "🚫 **Factory** ($AGENT): $MAX_ATTEMPTS sessions without the card leaving this loop's queue. Parked as \`$STATUS_BLOCKED\` — a human should look, then drag back to \`$STATUS_READY\` to retry." \
      >/dev/null 2>&1 || echo "[$LOOP] #$1: escalation comment failed — card is parked anyway" >&2
    clear_attempts "$1"; clear_claim "$1"; mark_escalated "$1"
    echo "[$LOOP] #$1 → escalated (parked $STATUS_BLOCKED; not re-claimed for ${ESCALATE_GRACE:-900}s)."
  else
    mark_escalated "$1"
    echo "[$LOOP] #$1 → park FAILED: card still in the queue, attempts stay at the cap; park retried after ${ESCALATE_GRACE:-900}s (no session will run on it)." >&2
  fi
}

attempts()      { cat "$STATE/attempt-$LOOP-$1" 2>/dev/null || echo 0; }
note_attempt()  { echo $(( $(attempts "$1") + 1 )) > "$STATE/attempt-$LOOP-$1"; }
clear_attempts(){ rm -f "$STATE/attempt-$LOOP-$1"; }

# Who CURRENTLY works an issue: the loop that last dispatched a session on it.
# A transcript only proves who EVER worked a card (several loops legitimately
# hold one for the same issue — deliverer, reviewer, re-routed work); the
# claim answers "who is mid-flight NOW". Last writer wins — dispatching from a
# trigger column deliberately takes ownership, so re-routed cards transfer on
# their next dispatch. Cleared when the card leaves the loop's queue, so an
# existing claim always means "mid-flight for that loop". Only the
# STATUS_ACTIVE read consults it; trigger columns never need one. Per-issue,
# unlike the per-loop attempt files.
claim_of()    { cat "$STATE/claim-$1" 2>/dev/null || true; }
write_claim() { echo "$LOOP" > "$STATE/claim-$1"; }
clear_claim() { rm -f "$STATE/claim-$1"; }

# ---- exclusive gate ---------------------------------------------------------
# Every loop marks itself busy while a session runs. A loop with EXCLUSIVE=1
# waits until no other loop is mid-session, then holds a lock for the length
# of each of its sessions; all other loops wait at the gate while it holds.
# PID-stamped files + staleness sweep: a killed loop can never deadlock the
# fleet. Locks live in state/ — loops sharing a factory share the gate.
pid_alive() { kill -0 "$1" 2>/dev/null; }
sweep_stale() {
  local f pid
  for f in "$STATE"/busy-* "$STATE"/exclusive-*; do
    [ -f "$f" ] || continue
    pid=$(cat "$f" 2>/dev/null)
    [ -n "$pid" ] && pid_alive "$pid" || rm -f "$f"
  done
}
wait_gate() { # blocks until this loop may run a session; exclusive acquires
  # SYMMETRIC double-check (TOCTOU fix, live finding): each side plants its
  # marker, sleeps, then re-verifies the OTHER class of marker and backs off
  # if it lost. Without the normal loops' half, a normal loop and an exclusive
  # one could pass each other's checks in the same instant and run
  # concurrently — seen at --all startup; the agent's own prose guard caught
  # it that time.
  while :; do
    sweep_stale
    if [ -n "${EXCLUSIVE:-}" ]; then
      if ! ls "$STATE"/busy-* 2>/dev/null | grep -qv "/busy-$LOOP\$" \
         && ! ls "$STATE"/exclusive-* 2>/dev/null | grep -qv "/exclusive-$LOOP\$"; then
        echo $$ > "$STATE/exclusive-$LOOP"
        sleep 2
        if ls "$STATE"/busy-* 2>/dev/null | grep -qv "/busy-$LOOP\$" \
           || ls "$STATE"/exclusive-* 2>/dev/null | grep -qv "/exclusive-$LOOP\$"; then
          rm -f "$STATE/exclusive-$LOOP"   # lost the race — someone slipped in
        else
          echo $$ > "$STATE/busy-$LOOP"
          return 0
        fi
      fi
    else
      if ! ls "$STATE"/exclusive-* >/dev/null 2>&1; then
        echo $$ > "$STATE/busy-$LOOP"
        sleep 2
        if ls "$STATE"/exclusive-* >/dev/null 2>&1; then
          rm -f "$STATE/busy-$LOOP"        # an exclusive planted meanwhile — yield
        else
          return 0
        fi
      fi
    fi
    echo "[$LOOP] waiting at the exclusive gate…"
    sleep 15
  done
}
release_gate() {
  # NB: no trailing `[ … ] && …` here — for a non-exclusive loop that test
  # fails as the function's LAST command, the function returns non-zero, and
  # set -e kills the whole loop silently right after its first session
  # (live finding). Plain if, explicit return.
  rm -f "$STATE/busy-$LOOP"
  if [ -n "${EXCLUSIVE:-}" ]; then rm -f "$STATE/exclusive-$LOOP"; fi
  return 0
}
trap 'release_gate' EXIT

run_session() { # extra claude args…
  local cap=()
  [ -n "${MAX_TURNS:-}" ] && cap=(--max-turns "$MAX_TURNS")
  # --setting-sources project,local: an unattended session runs on the repo's
  # settings only — a user-level settings.json (personal hooks, permissions,
  # plugins) must not change what the factory does on this machine vs the next.
  # --no-chrome: the Chrome-extension bridge has no browser to attach to
  # headless; its probe only adds startup noise. Both flags need a 2026 CLI.
  set +e
  claude --setting-sources project,local --no-chrome --agent "$AGENT" --permission-mode "$PERMISSION_MODE" \
         ${cap[@]+"${cap[@]}"} "$@" -p "$prompt" 2>&1 | tee "$STATE/last-$LOOP.log"
  set -e
}

# CARDLESS loops (CARDLESS=1 in the loop env): no board card drives them —
# they run their mission on the POLL cadence and sleep. Every tick is a FRESH
# conversation (random id, echoed so the operator can find the transcript):
# memory was never load-bearing here — dedup is against the board, never
# against memory — so a persistent transcript only accumulated token cost and
# stale context across months of ticks (design change, 2026-07-21). Spent
# ticks expire under cleanupPeriodDays. No claims, no outcome, no attempts:
# whatever the mission files lands on the board like anything else.
if [ -n "${CARDLESS:-}" ]; then
  while :; do
    sid="$(uuidgen | tr '[:upper:]' '[:lower:]')"
    echo "── [$LOOP/$AGENT] cardless tick — conversation $sid ──"
    prompt="$(cat "$FACTORY/loops/$LOOP.md")

Run your mission once, report what you did in your final message, then end
your turn."
    wait_gate
    run_session --session-id "$sid"
    release_gate
    [ -n "$ONCE" ] && exit 0
    [ -n "$POLL_SECS" ] || { echo "[$LOOP] no POLL set — single tick done."; exit 0; }
    echo "[$LOOP] next tick in $POLL."
    sleep "$POLL_SECS"
  done
fi

# Cache the board ids the park write needs (state/board.json) — refreshed at
# startup when missing or older than a day. setup.sh writes the same file;
# this keeps a loop that runs for weeks from parking with a stale option id
# after someone adds or renames a column (the cache was two months stale
# before this existed). Read failure keeps whatever copy is there.
refresh_board_ids() {
  local b="$STATE/board.json" fields pid
  if [ -f "$b" ] && [ -z "$(find "$b" -mtime +1 2>/dev/null)" ]; then return 0; fi
  fields=$(gh project field-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --format json 2>/dev/null) \
    && pid=$(gh project view "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --format json -q .id 2>/dev/null) \
    && jq -n --arg pid "$pid" \
         --argjson f "$(printf '%s' "$fields" | jq '[.fields[] | select(.name == "Status")][0]')" \
         '{project_id: $pid, status_field_id: $f.id, options: ($f.options | map({(.name): .id}) | add)}' \
         > "$b.tmp" \
    && mv -f "$b.tmp" "$b" \
    && echo "[$LOOP] board ids refreshed (state/board.json)" \
    || { rm -f "$b.tmp"; echo "[$LOOP] board ids: refresh failed — $( [ -f "$b" ] && echo "keeping the cached copy" || echo "no cache; run setup.sh")" >&2; }
}
refresh_board_ids

while :; do
  issue="$(next_card)"
  if [ -z "$issue" ]; then
    if [ -n "$POLL_SECS" ] && [ -z "$ONCE" ]; then
      echo "[$LOOP] queue empty — next check in $POLL."
      sleep "$POLL_SECS"
      continue
    fi
    echo "[$LOOP] Nothing in $STATUS_READY. Stopping."
    exit 0
  fi

  n=$(attempts "$issue")
  if [ "$n" -ge "$MAX_ATTEMPTS" ]; then
    # Already at the cap (an earlier park failed, or a restart): retry the
    # park instead of burning a 4th session.
    escalate "$issue"
    [ -n "$ONCE" ] && exit 0
    continue
  fi
  sid="$(sid_for "$issue")"
  echo "── [$LOOP/$AGENT] #$issue (attempt $((n + 1)) of $MAX_ATTEMPTS) — conversation $sid ──"

  # Dispatch = this loop's prompt (who you are, unattended deltas, mission,
  # what Done means — subagents never see it; their context comes from their
  # own agent defs and hooks, same as interactive mode) + the task.
  prompt="$(cat "$FACTORY/loops/$LOOP.md")

Work issue #$issue in $TRACKING_REPO.

YOUR FIRST ACTION, before anything else — even if you remember this issue:
read ALL comments on it (and on any question/bug issues it references) newer
than your last work-log entry. Humans steer by commenting, and a human
comment outranks whatever you were doing when your last turn ended. Acting
from memory without reading the latest comments is a protocol violation."

  # The intro comment (conversation id + takeover instructions) must exist on
  # the thread — self-healing: posted whenever absent, not only at creation,
  # so a deleted or outdated one gets restored on the next claim.
  # NOTE: it is PUBLIC. Never include local paths, usernames, or machine
  # details — the operator knows where the factory runs; the id is enough.
  if ! gh issue view "$issue" -R "$TRACKING_REPO" --json comments \
       -q '.comments[].body' 2>/dev/null | grep -qF "$sid"; then
    gh issue comment "$issue" -R "$TRACKING_REPO" \
      -b "🔧 **Factory** ($AGENT) works this card. Conversation \`$sid\` — to take over: stop the loop, then \`claude --resume $sid\`. One conversation per issue — for history read this thread, to steer comment on it."
  fi

  # Ownership BEFORE the session: from here until the card leaves this
  # loop's queue, only this loop may retry it out of the shared
  # STATUS_ACTIVE column.
  write_claim "$issue"

  wait_gate

  # Resume-first: the transcript on disk is the only truth about whether this
  # conversation exists. Not found → start it fresh under the same derived id.
  run_session --resume "$sid"
  if grep -q "No conversation found" "$STATE/last-$LOOP.log"; then
    # Directory-scoped store (verified): if this conversation exists under a
    # DIFFERENT directory, the folder was moved/renamed or WORKDIR changed —
    # starting fresh would silently orphan every open conversation. Stop.
    stray=$(ls "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects"/*/"$sid.jsonl" 2>/dev/null | head -1 || true)
    if [ -n "$stray" ] && [ -z "${FACTORY_FORCE_FRESH:-}" ]; then
      echo "[$LOOP] #$issue: its conversation exists, but under another directory:" >&2
      echo "    $stray" >&2
      echo "  The loop's working directory is part of conversation identity." >&2
      echo "  Restore the original folder path (or the loop's WORKDIR) and rerun," >&2
      echo "  or set FACTORY_FORCE_FRESH=1 to deliberately start conversations over." >&2
      exit 3
    fi
    run_session --session-id "$sid"
  fi

  release_gate

  # Outcome — read from the board, never from the transcript. SUCCESS means
  # "the card left this loop's queue": for a pipeline loop that's a status
  # move (Done/Blocked), for a verdict-only loop it's a label its own QUERY
  # excludes — the card may legitimately stay in its column forever. Status
  # is used for messaging; queue membership decides.
  rm -f "$STATE/read-failed-$LOOP"
  st="$(status_of "$issue")"
  in_queue=0
  { cards_in "$STATUS_READY"; [ -n "${STATUS_ACTIVE:-}" ] && cards_in "$STATUS_ACTIVE"; } \
    | grep -qx "$issue" && in_queue=1
  if [ "$st" = "unknown" ] || [ -f "$STATE/read-failed-$LOOP" ]; then
    # Board unreadable right now: neither success nor failure — deferring the
    # outcome must not clear attempts (false success) or burn one (false
    # stall). The card is re-evaluated from fresh reads next pass. This
    # covers a failed QUEUE read too: an empty read is not "left the queue"
    # (a rate-limited pass once read an In Progress card as done — live).
    echo "[$LOOP] #$issue: board unreadable — outcome deferred to next pass."
  elif [ "$in_queue" = 0 ]; then
    clear_attempts "$issue"
    clear_claim "$issue"
    case "$st" in
      "$STATUS_DONE"|gone) echo "[$LOOP] #$issue → done." ;;
      "$STATUS_BLOCKED")   echo "[$LOOP] #$issue → parked. It stays parked until a human drags it back to $STATUS_READY." ;;
      *)                   echo "[$LOOP] #$issue → left this loop's queue (status: $st) — done here." ;;
    esac
  else
    note_attempt "$issue"
    if [ "$(attempts "$issue")" -ge "$MAX_ATTEMPTS" ]; then
      escalate "$issue"
    else
      echo "[$LOOP] #$issue still in this loop's queue (status: $st); will retry."
    fi
  fi

  [ -n "$ONCE" ] && exit 0
done
