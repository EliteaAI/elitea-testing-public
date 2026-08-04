---
name: Workflow tool named-registry is empty — use scriptPath, not workflow('name', ...)
description: workflow('batch-build', args) inside a script body fails with "no workflow with that name" — the named registry is empty on this project; invoke via Workflow({scriptPath, args}) directly.
type: feedback
---

## What happened

Dispatched the batch pipeline for ELITEA-2227 by calling the `Workflow` tool
with a script body containing:

```js
export const meta = { name: 'ta-batch-build-elitea-2227', ... }
return await workflow('batch-build', { slug: ..., base: ..., cases: [...] })
```

This failed immediately (8ms, 0 agents):

```
Error: workflow('batch-build'): no workflow with that name. Available: (none)
```

`workflow(nameOrRef, args)` inside a script body only resolves **named
workflows already registered** (i.e. copied into `.claude/workflows/` and
invoked by name) or a `{scriptPath}` ref. `'batch-build'` is neither — it is
the *installed skill's* script, which lives at
`.claude/skills/test-automation-workflow/scripts/workflows/batch-build.workflow.mjs`
and is meant to be invoked directly via the top-level `Workflow` tool call's
`scriptPath` param, per `workflow-accelerant.md` § The canonical script — NOT
wrapped inside another script's `workflow()` call.

## Fix

Call the `Workflow` tool directly with `scriptPath` + `args` — no wrapper
script:

```
Workflow({
  scriptPath: "<repo>/.claude/skills/test-automation-workflow/scripts/workflows/batch-build.workflow.mjs",
  args: { slug: "...", base: "origin/automation/base", cases: [...] }
})
```

This launched correctly (9 agents, ~44 min, gate GREEN 3/3).

## Why it matters

The failure is silent-fast (8ms) and easy to mistake for "the tool doesn't
support this" rather than "the invocation shape is wrong" — the error message
("Available: (none)") does correctly say the registry is empty, but it's easy
to skim past under time pressure. Always use `scriptPath` pointing at the
installed skill's `.mjs` file for the canonical batch scripts
(`batch-build`, `batch-integrate`, `batch-stabilize`, `batch-campaign`) unless
you have explicitly copied one into `.claude/workflows/` first.
