---
name: Workflow resume needs resumeFromRunId AND args, not resumeFromRunId alone
description: Workflow({scriptPath, resumeFromRunId}) with no args throws "args required" immediately (0 agents) — always resend the identical args object alongside resumeFromRunId
type: feedback
---

## Rule

Resuming an interrupted `Workflow` call by passing only `{scriptPath,
resumeFromRunId}` fails fast with `Error: args required: { slug, base,
cases: [...], ... }` — 0 agents run, 6ms. The harness does **not** persist or
replay the original `args` object automatically on resume; the script body
re-executes from the top on every invocation (that's how cache-hit replay of
completed `agent()` calls works at all), so it needs `args` on every call,
resume included.

**Always call resume as `Workflow({scriptPath, resumeFromRunId, args})` with
the SAME `args` value the original launch used** — same `slug`/`base`/`cases`
(and `clusters` if used). Completed `agent()` calls with unchanged
`(prompt, opts)` still replay from cache in under a second; only the
first new/edited call runs live. This is a distinct trap from `resumeFromRunId`
itself being wrong or stale (see `subagent_wait_and_resume_mechanics.md` for
that) — here the id was right and the call still failed, purely for missing
`args`.

## Seen 1×

#873/ELITEA-2365 — prior session's `Workflow` launch was reported `stopped`
("no completion record found... may have been killed when the previous
process exited"). Resumed with `{scriptPath, resumeFromRunId}` only → instant
`args required` error, 0 agents. Re-invoked with `args` included → ran clean
to completion (~20 min, 7 agents).

See also: subagent_wait_and_resume_mechanics.md · workflow_hard_failure_can_still_have_landed_real_work.md
