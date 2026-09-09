---
name: Pipeline run-START latency dominates; node execution is the stable part
description: DEV took 4.5 s / >100 s / 89.3 s to START the same pipeline within one hour; execution itself ~31 s
type: project
aliases: [pipeline run never started, run node missing, AgentStart latency, pipeline timeout budget]
tags: [area/pipelines, type/flake]
created: 2026-09-09
updated: 2026-09-09
---

Measured live 2026-09-09 (ELITEA-2448 repair), same `Code 1 -> END` pipeline,
three runs inside one hour against the DEV backend:

| Run | send → run node on canvas | run node → `Completed` | total |
|---|---|---|---|
| 1 | 4.5 s | 31.0 s | 35.5 s |
| 2 | never (abandoned at 100 s) | — | — |
| 3 | 89.3 s | 31.7 s | 121.0 s |

The pyodide node execution is stable (~31 s). **All the variance is in how long
the backend takes to START the run** — the `AgentStart`/`StartTask` socket event
that creates the canvas run node (`parseRunsByEvent.helpers.js:69-81`).

Consequences:

- A 90 s budget for send→any-assertion is structurally too small. Budget start
  and completion separately (ELITEA-2448 uses 150 s start + 90 s completion).
- `pipeline-run-node-label` visible = the run **started**, not finished. It is
  present throughout `In progress`.
- A run that never starts is upstream of every assertion the case makes — same
  family as the ledger's LLM/HITL trigger-side flakes: **re-run, never accept
  2-of-3**, and never fold it into a sanctioned-RED set.

Related: [[soft_wait_helpers_cannot_fail_and_hide_the_real_failure]]
