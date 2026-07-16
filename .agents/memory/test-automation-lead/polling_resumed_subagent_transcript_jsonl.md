---
name: Poll a SendMessage-resumed subagent's own transcript JSONL to wait in-turn
description: When a SendMessage-resumed background subagent has no foreground option, honor "wait inside the turn" by polling its transcript file for line-count growth (via the task's .output symlink -> real .jsonl path) in repeated bounded Bash sleep-loops, instead of ending the turn to await a notification
type: feedback
---

## What happened (issue #113, ELITEA-1881, PR #583)

The implementer's first foreground dispatch ended its own turn prematurely
with "I'll report back once the background pytest finishes" — a
session-fatal pattern (AGENT.md rule 5 forbids "check later" in factory
mode). I resumed it via `SendMessage(to: agentId, ...)`, but that tool
*always* backgrounds the resume — there's no `run_in_background: false`
equivalent (same constraint `sendmessage_resume_fragile_in_factory_mode.md`
already documents). That still leaves the orchestrator's own turn needing
to "wait inside the turn" per the delta rules, even though the resume
mechanism itself can't block.

## The technique

The tool result from `SendMessage` names an `<agentId>.output` path under
`/private/tmp/claude-.../tasks/`. That path is a symlink to the agent's real
transcript: `~/.claude/projects/<project>/<session>/subagents/agent-<id>.jsonl`.
That file grows in real time as the resumed agent works. Polling it — not
the shell/task-output layer — is a cheap, reliable "is it still alive and
progressing" signal:

```bash
F="<the real .jsonl path from `ls -la` on the .output symlink>"
START=$(wc -l < "$F")
for i in $(seq 1 27); do        # bounded to fit Bash's ~9min effective window
  sleep 20
  N=$(wc -l < "$F")
  if [ "$N" -gt "$START" ]; then echo "GREW to $N at iter $i"; break; fi
done
```

Re-issue this loop (a fresh Bash call) every time it exhausts without
growth, and periodically `tail -N "$F" | python3 -c '...json parse...'`
to read the actual tool_use/tool_result/text content — this is how I saw
the resumed implementer discover its own background bash process had died,
relaunch the pytest run, and eventually reach its Phase 6 handoff, all
without me ending my turn to "check later."

## Why this matters

- `SendMessage` resumes are unavoidable for factory-mode subagent
  continuation in some cases (there's no foreground variant), but the
  orchestrator's own "wait is work done in-turn" obligation doesn't relax
  just because the tool is async. Polling the transcript file closes that
  gap without needing a `Monitor`/`ScheduleWakeup` that would end the turn.
- A silent, non-growing transcript for multiple poll cycles is itself a
  signal worth investigating (possible death/hang) — don't just poll
  forever blindly; escalate to a fresh foreground `Agent()` dispatch (per
  `sendmessage_resume_fragile_in_factory_mode.md`) if growth stays flat
  well past the task's expected duration.
