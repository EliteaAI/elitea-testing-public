---
name: Waiting on and resuming subagents — mechanics and recovery
description: Waiting is work done inside the turn; SendMessage always resumes in the background and is fragile in factory mode, ScheduleWakeup can kill the process it waits on, bare sleep is blocked, and a subagent parked "waiting for a notification" has orphaned real work.
type: feedback
---

## Rule

**Waiting is work you do inside the turn.** Never end a turn "to check later" —
in factory mode there is no later. Never `ScheduleWakeup` on a process you started
this turn: it ends the turn, and the teardown can orphan or kill the very process
you were waiting for. A partial gate result from before such an interruption is
not evidence — re-verify branch/PR/dev-server and redo the gate in full.
`ScheduleWakeup` is for `/loop` self-pacing only.

**Preference order** for a dispatch that must finish in-turn:

1. Fresh **foreground** `Agent(run_in_background: false)` — blocks until the result
   returns, no window for a process restart to kill it silently.
2. `TaskOutput(task_id: <agentId>, block: true, timeout: up to 600000)` — one call,
   blocks, returns the parsed final result. First call may return
   `retrieval_status: timeout` + `status: running` and dump a raw JSONL fragment;
   that is expected — call again.
3. Transcript polling. The `<agentId>.output` path is a symlink to
   `~/.claude/projects/<project>/<session>/subagents/agent-<id>.jsonl`; poll
   `wc -l` growth in bounded loops and `tail` + json-parse to read progress. Flat
   growth well past the expected duration ⇒ escalate to a fresh foreground dispatch.

**`SendMessage` ALWAYS resumes in the background** — there is no
`run_in_background: false` equivalent. Interactive sessions: resuming for a narrow,
additive fixup is still right (context loaded, cheaper, and the right call when the
agent holds deep debug state). **Factory/headless: prefer a fresh foreground
`Agent()`**, and after ONE interrupted resume switch immediately — don't resume twice.

**Bare `sleep N` is hard-blocked** (and chaining shorter sleeps is explicitly
refused). Use an arithmetic epoch loop, and give the Bash call a timeout well above
the wait; macOS has no `date -d`:

```bash
NOW=$(date -u +%s); TARGET=$((NOW+300))
until [ "$(date -u +%s)" -ge "$TARGET" ]; do sleep 5; done
```

**Same pattern applies to `Workflow()` calls, not just `Agent()`.** A batch-build
dispatch returns a `taskId` + `runId` immediately (it always backgrounds). Persist
BOTH to disk the instant they return (`.agents/automation/<slug>/run.json`) —
before anything else — then poll `TaskOutput(task_id: <taskId>, block: true,
timeout: 600000)` in a loop in-turn exactly as above; a single-case batch's 4-phase
run (analyst → implement → review → merge → gate → report) easily exceeds one
600s window, so 3-4 consecutive `timeout`/`running` returns before `completed` is
normal, not a stall. Confirmed working end-to-end #477/ELITEA-2040 (~37min, 3
polls to completion).

## Recovery

- **A subagent that ends its turn "waiting for the monitor/notification" has
  orphaned real work** — no such monitor exists in this dispatch model. Don't trust
  the framing: check ground truth (`git log`/`git status`, `gh pr list --head <branch>`,
  `reports/archive/junit_*.xml` for the actual last verdict), locate the process
  (`ps -ef`, `lsof -p <pid>` for its script and log paths), and poll it to
  completion yourself (`until grep -q "<marker>" <log>; do sleep 20; done`). Then
  **resume THAT agent** (it holds the debug state) with an explicit "run every
  pytest foreground, respect the rerun budget, finish the handoff" instruction.
- **After two stalls on the same "run and wait" step**, stop sending full-scope
  dispatches: run the verification yourself (running a test is not editing
  framework code — commit/push/PR stay the implementer's), then hand back a minimal
  "commit + push + open the PR citing this pasted evidence" task.
- **After any interruption of your own turn during a dispatch**, check before
  re-dispatching: `git status`, `git log --oneline <base>..<branch>`, and PRs
  opened since in this repo *and* EliteaUI. The subagent usually finished; verify
  its diff rather than duplicating it into a divergent second attempt.
- **A workflow `agent()` call that dies mid-run** (e.g. `API Error: Claude's
  response exceeded the 64000 output token maximum`) is a harness death, not a
  case finding — the run returns `not-started` for that case with nothing learned.
  A SINGLE such death is a plain retry: re-invoke `Workflow({scriptPath,
  resumeFromRunId, args})` unchanged — the cache replays everything already
  completed (e.g. triage) and only the dead call re-runs live. Confirmed
  #779/ELITEA-2272: analyst died at ~26min/113k tokens, resume completed clean at
  ~56min. Reserve the account-ceiling/circuit-breaker read for **several**
  consecutive deaths, not one.

## Seen 6×

- #19/ELITEA-1737 — interrupted turn; the implementer had already committed and opened 3 EliteaUI PRs.
- #26/ELITEA-1735 — implementer stalled twice on "wait for the background test notification"; narrow commit-only re-dispatch landed first try (PR #203).
- #88/ELITEA-1893/PR#571 — two SendMessage resumes killed by process restarts, correct work left uncommitted both times; fresh foreground dispatch landed immediately.
- …plus 4 earlier occurrence(s) — full per-case detail in the source entries below.

See also: interrupted_dispatch_recovery.md · resuming_subagents_for_narrow_fixups.md ·
sendmessage_resume_fragile_in_factory_mode.md ·
polling_resumed_subagent_transcript_jsonl.md ·
subagent_parks_on_monitor_in_headless_resume_synchronously.md ·
implementer_stalls_on_background_wait.md ·
implementer_can_orphan_own_background_verification.md ·
never_schedulewakeup_on_live_background_process.md ·
bare_sleep_blocked_use_epoch_until_loop.md
