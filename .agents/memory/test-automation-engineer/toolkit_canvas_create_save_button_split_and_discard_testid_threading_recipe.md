---
name: Toolkit canvas Create/Save button split and discard-testid threading recipe
description: ToolkitEditor.jsx uses TWO separate button components (Create vs Save) unlike Agent's one-component-both-states pattern; the reusable 3-prop discard-testid threading recipe through BaseEditor/EditorHeader into DiscardButton.jsx's existing props.
type: feedback
---

## Create/Save button split (ELITEA-2082/2083/2080)

`ToolkitEditor.jsx` swaps in ONE of two entirely different components based on
`isCreating`: `CreateToolkitButton.jsx` (create mode, hardcoded text "Create",
zero testid before this pass) vs `SaveToolkitButton.jsx` (edit mode, text
"Save"). This is DIFFERENT from `AgentEditor.jsx`'s pattern, where ONE
component (`CreateApplicationSaveButton.jsx`) handles both create and re-save
states under a single `agent-save-button` testid — so don't assume the Agent
precedent's "one testid covers both states" generalizes to Toolkit.

Also: `toolkit-form-save-button` already exists as a testid, but it belongs to
a completely UNRELATED component — `CreateToolkitToolTabBar.jsx`, the
standalone `/toolkits/create` wizard's own Save button. Don't reuse it for the
in-chat canvas's `SaveToolkitButton.jsx` — they're different DOM elements on
different routes.

**Pattern for proving the create→save mode flip without adding a 7th testid:**
if no case in your family ever clicks the Save-mode button (only asserts the
state transition happened), add a testid ONLY to the Create-mode button
(here: `toolkit-form-create-button`) and prove the flip via
`expect(create_button).to_have_count(0)` after the successful create — an
absence assertion (canon ruling #511 extension: absence assertions count as
testid references). Combine with the persisted toast text + the 201 response
+ the header title update for a stronger, more independent confirmation set
than a single button-label read would give you. Avoids inventing a testid
whose only use is a one-off text check.

## Discard-testid threading recipe (reusable for Pipeline/Artifact editors)

`EditorHeader.jsx`'s `<Button.DiscardButton>` call previously passed NONE of
`DiscardButton.jsx`'s three ALREADY-EXISTING props
(`dataTestId`/`modalDataTestId`/`confirmButtonDataTestId` — these already
flow straight through to the trigger button, the warning `Modal.BaseModal`,
and its confirm button respectively; `DiscardButton.jsx` itself needs ZERO
changes). The gap was pure prop-threading through the SHARED chain:

```
ToolkitEditor.jsx (call site — supplies actual testid strings)
  -> BaseEditor.jsx (add 3 new optional props: discardButtonTestId /
     discardModalTestId / discardConfirmButtonTestId, forward to EditorHeader)
  -> EditorHeader.jsx (accept same 3 props, pass to
     <Button.DiscardButton dataTestId={discardButtonTestId}
       modalDataTestId={discardModalTestId}
       confirmButtonDataTestId={discardConfirmButtonTestId} />)
```

Both `BaseEditor.jsx`/`EditorHeader.jsx` are shared across Agent/Pipeline/
Toolkit/Artifact editors — adding the 3 new OPTIONAL props is additive and
harmless to every other editor (they stay `undefined`, rendering no
`data-testid` — unchanged behavior). Only the ONE call site you're actually
working on (here: `ToolkitEditor.jsx`) supplies real values — matches the
existing `titleTestId`/`subtitleTestId`/`closeButtonTestId` precedent
`AgentEditor.jsx` already established on the exact same shared components.
Same recipe applies verbatim the next time Pipeline or Artifact's own
Discard flow needs testids.

## Worktree-depth gotcha (isolated batch-build worktrees)

An isolated worktree living at
`elitea-testing-public/.claude/worktrees/<id>/` sits 4 directories deeper
than the repo root — `../EliteaUI` from `automation/` resolves to a
non-existent path. Use the ABSOLUTE workspace path (or count up 5 levels:
`automation` -> worktree-id -> `worktrees` -> `.claude` -> `elitea-testing-public`
-> workspace root) to reach `EliteaUI`/`onetest-ai-tm-Elitea`/`.env.test`
siblings. `automation/.env.test` (normally a symlink `../../.env.test`
relative to the repo root) doesn't exist at all in a fresh isolated
worktree — recreate it as an ABSOLUTE symlink
(`ln -sf <absolute-workspace>/.env.test automation/.env.test`) before running
pytest; a relative symlink would break again at this nesting depth.
