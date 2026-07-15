---
name: Agent Save As Version dropdown testid map
description: ELITEA-1888 — full testid inventory for the Agent Save-As-Version/version-dropdown flow (5 added live via EliteaUI#567); proven disposable-agent-reuse test-data pattern that sidesteps the still-open #524 agent-create defect; ?viewMode=owner is required on /agents/all/{id} or it 404s
type: reference
---

## Context
ELITEA-1888 ("Save As Version creates a named version visible in version dropdown")
executed end-to-end live on localhost, status `ready-for-automation`. AFS:
`test-specs/agents/lcritical_save-as-version-creates-named-version-visible-in-dropdown_ELITEA-1888.md`.

## Testid gaps found + closed (EliteaUI PR #567, draft, cut from fresh main)
All five confirmed absent live before this run (verified via
`document.querySelectorAll('[data-testid]')`), added via `add-data-testid` dual-target
flow (commit `2af4c6d` on `automation/testids`):

- `agent-save-as-version-button` — `SaveNewVersionButton.jsx`
- `agent-version-selector-trigger` — new `dataTestId` prop threaded
  `VersionSelect.jsx` → `SingleSelect`; wired ONLY from `ApplicationVersionSelect.jsx`
  (agent side). The Skill-side `VersionSelect` caller (`SkillTabBar.jsx`) was
  deliberately left untouched — don't assume this testid appears on Skill pages.
- `agent-version-dialog-name-input` — via `inputProps={{'data-testid': ...}}` on
  `Input.InputBase` (NOT a top-level `data-testid` prop — `InputBase` only forwards
  `inputProps`/`htmlInput` to the actual `<input>`)
- `agent-version-dialog-save-button` — via `BaseModal`'s pre-existing
  `confirmButtonDataTestId` prop
- `agent-version-dialog-cancel-button` — required adding a **new**
  `cancelButtonDataTestId` prop to `BaseModal.jsx` (mirrors `confirmButtonDataTestId`/
  `closeButtonDataTestId` — Cancel had no testid-plumbing at all before this)

**Cherry-pick gotcha hit while building the review branch**: `BaseModal.jsx` on
`automation/testids` already had `confirmButtonDataTestId` in its destructure (from
someone else's in-flight, not-yet-merged testid PR) but `main` did not — AND `main`'s
confirm button JSX was also missing the `data-testid={confirmButtonDataTestId}` wiring
entirely (it existed in the destructure on `testids` but the JSX usage line wasn't part
of any diff either — a half-wired prop). Cherry-picking only my own diff hunk (which
just added `cancelButtonDataTestId`) produced a conflict AND, if naively resolved by
just taking "my side", would have shipped a PR whose `agent-version-dialog-save-button`
silently did nothing (prop declared but never applied to the button). Had to manually
also add `data-testid={confirmButtonDataTestId}` to the confirm-button JSX in the
worktree so PR #567 is self-contained and doesn't silently depend on an unmerged
sibling PR. **Lesson: after any cherry-pick conflict in a testid PR, grep the resulting
file for every prop your commit references and confirm each is actually *used* in JSX,
not just declared** — a clean conflict resolution can still leave a prop wired to
nothing.

The dynamic `version-option-{name}` testids (`version-option-base`,
`version-option-v2-test`) already existed live — same template pattern as
`skill-version-option-{}` (ELITEA-1789).

## Proven test-data pattern (works around the still-open #524)
Agent creation (UI create form AND `AgentAPI.create_agent()` fixture) is still broken
by issue #524 as of this run (temperature/reasoning_effort 400 on the project's
reasoning-capable default model). This case's precondition only needs an *existing*
agent, so the run reused an existing disposable debris agent (id 4745,
`elitea-1735-skills-agent` — a duplicate left over from prior ELITEA-1735 runs) and
deleted the **whole agent** at teardown (`agent-actions-menu-button` → "AGENT" group →
`delete-agent-menuitem`). Verified via `GET .../applications/prompt_lib/399` `total`
count returning to baseline (10 → 9 → back to 9 after delete... i.e. net zero — the
debris agent itself was the one removed). **Do not target a long-lived shared fixture
agent (e.g. id 3 "Test Agent") with Save-As-Version** — no "delete version" UI/API was
found in this run, only whole-agent delete, so a shared agent would accumulate
versions across every automated run forever.

## Navigation gotcha
`/agents/all/{id}` alone 404s ("Page not found") — the `?viewMode=owner` query param
is required. `AgentDetailPage.navigate()` already does this correctly
(`automation/pages/agent_detail_page.py:153`); a naive re-implementation without
reading the existing page object would drop it.

## Pre-existing violation flagged again (not fixed this run, per scope)
`automation/pages/agent_form_page.py:163-167`'s `save_as_version_button`
`LocatorDescriptor` still carries a forbidden `fallback=` param even though the testid
it names now exists live (added this run). Same finding as ELITEA-1889 — for whoever
implements this case to strip.
