---
name: Run Details before/after first-step defect
description: RunStateDialog's "Before" value at timeline step 0 is hardcoded '' — filed #1271; never assert unmodified==Before/After using the FIRST node
type: reference
---

`RunStateDialog.jsx` (`src/[fsd]/features/pipelines/flow-editor/ui/state/`):

```js
valueBefore={selectedStep ? data.timeline[selectedStep - 1].state[variable] : ''}
```

For `selectedStep === 0` (the pipeline's FIRST executed node), Before is always the
literal `''`, never the variable's real pre-run value — even if the variable has a
non-empty starting default (STATE panel "Add default value", ELITEA-2042). Confirmed
live: a `seed_var` preset to `'PRESET_DEFAULT_VALUE'`, untouched by the only node,
showed Before=`""`/After=`"PRESET_DEFAULT_VALUE"` — a false "modified" read.

Filed as `EliteaAI/elitea-testing-public#1271`.

**Test-writing implication**: any assertion of the shape "variable NOT modified by
this node ⇒ Before == After" must target a NON-FIRST timeline step (works correctly
for `selectedStep > 0`). Never build that assertion around the pipeline's first node,
even if it seems like the natural/simplest choice.

Also note (not a defect, just a UI quirk): the default-selected timeline step on
panel open is the LAST step (not index 0) for an already-Completed run — confirmed
on 2 independent live executions. Don't assume `selectedStep === 0` at open.

Full AFS: `test-specs/pipelines/l3_run-details-state-before-after-per-node_ELITEA-2452.md`.
Digest: `test-specs/pipelines/_surface.md` § "Run Details panel — State Before/After per node".
