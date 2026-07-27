---
name: Resuming subagents for narrow fixups
description: Use SendMessage to resume the SAME analyst/implementer session for a narrow, additive gap (missing AFS section, small fix-only review finding) instead of a fresh dispatch — cheaper and carries context already
type: feedback
---

## What happened

On ELITEA-1735 (issue #26), the analyst's first AFS draft was missing the
required `## Cleanup` section (project convention, established precedent in
ELITEA-1737's AFS). Rather than re-dispatching a fresh analyst `Agent()` call
(which would re-read the whole case, re-establish context, and cost a full
session), I used `SendMessage(to: <agentId>, ...)` to resume the SAME analyst
session with a narrow, scoped ask: "add the missing Cleanup section, you don't
need to re-run the whole case." It worked well — the agent already had all the
skill-ID/agent-ID/fixture context loaded and just needed to check the API
client for delete methods and append the section.

Same pattern applied for the implementer: after reviewer round 1 returned
CHANGES_REQUESTED with 2 small findings (a locator-scoping bug + an import
nit), I resumed the implementer's session via SendMessage rather than
re-dispatching fresh — it already had the PR, branch, and full context loaded.

## When to use this vs. a fresh dispatch

- **Resume (SendMessage)** — the ask is a narrow, additive fix to the SAME
  artifact the agent just produced (add a missing section, fix a specific
  locator, address a fix-only review finding). The agent's existing context
  (case details, IDs, fixture knowledge, DOM observations) is still valid and
  saves real re-exploration cost.
- **Fresh dispatch (Agent tool)** — anything that needs an adversarial/fresh
  eye (the reviewer slot, ALWAYS), or where the prior agent's approach itself
  is suspect (re-scoping, `needs-analyst-rerun` for AFS drift, R2-cap
  escalations).

## Mechanical note

`SendMessage` to an agent with no live task resumes it **in the background**
— there's no synchronous/foreground option like the `Agent` tool's
`run_in_background: false`. In unattended/factory mode (where every dispatch
normally must be foreground so its result lands in the same turn), I ended the
turn and let the harness's automatic task-notification re-invoke me when the
resumed agent finished — that is NOT the same failure mode as "ending a turn
to check later out of laziness"; it's the only mechanism available for a
resumed agent, and the harness notification does reliably fire. Don't try to
gin up a polling wrapper (I first tried a `pgrep`-based Monitor loop to detect
completion — it false-positived immediately since no process is literally
named the agent ID; a `grep`-on-expected-file-content Bash `run_in_background`
loop, or just trusting the native task-notification, both work better).
