---
name: Agent Variables section shared-component call-site gotcha
description: ELITEA-1884 — ApplicationVariables/VariableList render the agent-detail "Variables" accordion but are wired at TWO separate call sites (edit vs create); editing the wrong one is a silent no-op with HMR, no error
type: feedback
---

## What happened

Analyzing ELITEA-1884 (remove a variable, verify removal persists), the agent detail
page's "Variables" accordion (shown below Instructions whenever the text contains
`{{name}}` tokens) had **zero `data-testid` anywhere** — not even a section wrapper.
The component is `src/components/ApplicationVariables.jsx` (renders a `BasicAccordion`
with one item, title "Variables") + `src/components/VariableList.jsx` (renders one row
per variable, each an `Input.StyledInputEnhancer`).

**The trap:** `ApplicationVariables` is used at TWO different call sites:
- `src/[fsd]/features/agent/ui/agent-details/configurations/form/CreateAgentForm.jsx`
  — used ONLY by the agent-**create** flow (`/agents/create`, `CreateApplication.jsx`)
- `src/pages/Applications/Components/Applications/ApplicationConfigurationForm.jsx`
  — used by the agent-**edit** flow (`ApplicationsDetail` route → `EditApplication.jsx`
  → `ConfigurationTab.jsx` → this file). **This is the one that renders for
  `/agents/all/:tab/:agentId` (viewMode=owner), i.e. every existing-agent test.**

First pass wired the new testid props (`sectionTestId`/`rowTestId`/`inputTestId`) only
into `CreateAgentForm.jsx` — the intuitively "current/FSD" one. HMR applied cleanly,
console showed zero errors, but `document.querySelectorAll('[data-testid*="variable"]')`
on the live `/agents/all/3` page kept returning `[]`. No error, no warning — just
silently the wrong component tree. Root-caused by grepping `grep -rn "'Variables'"` across
the whole repo (only 2 hits total — `ApplicationVariables.jsx` and an unrelated chat
`VariablesEditor.jsx` "Variables" button label) and then tracing which page-level
component (`EditApplication.jsx` → `ConfigurationTab.jsx` → `ApplicationConfigurationForm.jsx`)
actually renders for the route under test, rather than trusting "this looks like the
current implementation" instinct.

## Fix applied

Added testid props to BOTH `ApplicationVariables.jsx`/`VariableList.jsx` (shared,
generic optional props: `sectionTestId`, `rowTestId`/`inputTestId` with `{}` template
substitution) but wired the actual `sectionTestId="agent-variables-section"` /
`rowTestId="agent-variable-row-{}"` / `inputTestId="agent-variable-input-{}"` values
**only** at `ApplicationConfigurationForm.jsx` (the exercised call site) — reverted the
initial `CreateAgentForm.jsx` edit since the create flow was never exercised live in
this run (blocked anyway by open defect #524) and the project's testid-scope rule
(`.agents/testing.md`) forbids testids on untouched elements. See
EliteaAI/EliteaUI#568 and `test-specs/agents/l3_remove-variable-verify-removal-persists_ELITEA-1884.md`.

## Takeaway for future cases

When a shared component (title text is unique/greppable, e.g. `'Variables'`,
`'Save As Version'`) has multiple render call sites for what looks like "the same
UI", **verify via the route → page → container chain** which call site actually
serves the route under test, before editing JSX. A clean HMR reload with zero
console errors is NOT proof you edited the right file — `document.querySelector`
against a fresh navigation for the new testid is the only reliable check.
