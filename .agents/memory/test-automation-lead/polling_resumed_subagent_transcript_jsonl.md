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

## Simpler alternative found later (#317, ELITEA-2114, PR #696, round-3 review)

A reviewer subagent (dispatched foreground) itself spawned a background
sub-agent for deep EliteaUI source-tracing and returned to me mid-review
with "waiting on the background agent's report... will report once it
lands" — the same "assume someone else is watching" trap, one level
removed (the reviewer, not me, started the background work). Before
reaching for the transcript-JSONL technique above, I tried
`TaskOutput(task_id: <agentId-from-the-Agent-tool-result>, block: true,
timeout: 600000)` directly on the reviewer's own agentId — no
`SendMessage` resume needed first in this case (the reviewer's *own*
foreground turn had already ended after launching its child; the parent
`Agent()` call had returned). `TaskOutput` blocked correctly, and on the
first call returned `<retrieval_status>timeout</retrieval_status>` +
`status: running` (worth knowing: a mid-poll `TaskOutput` timeout can dump
a raw JSONL fragment into the tool result, same shape as this entry's
transcript file — that's expected, not an error). Calling it a second time
with the same `block: true` returned `<retrieval_status>success</retrieval_status>`
+ `status: completed` + the reviewer's full final APPROVED verdict, cleanly
parsed — no manual `wc -l`/`tail`/JSON-parsing needed.

**Preference order going forward:** try `TaskOutput(task_id, block: true,
timeout: <up to 600000>)` on the relevant agentId FIRST — it's a single
tool call, blocks correctly, and returns the parsed final result on
success. Fall back to the manual transcript-JSONL polling loop above only
if `TaskOutput` itself errors on the task_id (e.g. the id format it wants
doesn't resolve) or you need to watch intermediate progress rather than
just the terminal result.
