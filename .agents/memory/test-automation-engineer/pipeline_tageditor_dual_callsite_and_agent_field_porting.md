---
name: Pipeline forms — TagEditor renders from TWO different components (create vs detail), and PipelineFormPage/PipelineDetailPage needed porting for Welcome/Starter/StepLimit/Toolkit
description: Tags on the Pipeline create form come from CreateAgentForm.jsx, but Tags on the Pipeline DETAIL/edit page come from a completely different component, ApplicationEditForm.jsx — a testid wired only in one is invisible in the other, caught by a reload-persistence assertion. Also documents which Agent-shared-component locators/methods PipelineFormPage/PipelineDetailPage were missing before ELITEA-2021.
type: feedback
---

## TagEditor has two independent call sites for Agent/Pipeline entities — wire both

`CreateAgentForm.jsx` (the CREATE-time form, entityType `application`|`pipeline`) and
`ApplicationEditForm.jsx` (the DETAIL/edit-page form) both import and render
`TagEditor` independently — they are NOT the same component instance, despite
Name/Description/Save testids being identical strings across both files (a
coincidence of both files independently hardcoding `agent-name-input` etc., not
evidence they share the Tags render).

**Symptom this caused (ELITEA-2021):** wiring `inputTestId`/`chipTestId`/
`getOptionTestId` only in `CreateAgentForm.jsx` made tag-add work perfectly
during the CREATE step (steps 1-8 of the AFS), but the reload-persistence
assertion at the end (now on the DETAIL page, `/pipelines/all/{id}`) failed —
`has_tag_chip()` returned `False` even though the tag chip WAS visible on
screen (confirmed via screenshot: not a product bug, a missing-testid bug).
Root cause: `ApplicationEditForm.jsx`'s separate `<TagEditor>` call had zero
testid props, so the chip rendered on the detail page carried no
`data-testid="agent-tag-chip"` at all.

**Rule for any future case touching Tags on an Agent OR Pipeline form:** wire
the SAME testid props (`data-testid`, `inputTestId`, `chipTestId`,
`getOptionTestId`) on BOTH call sites if the case's assertions span both the
create flow AND a reload/detail-page re-verification — which is the common
shape for a "fill everything, save, reload, verify persistence" case. Grep
`TagEditor` across `EliteaUI/src` first to confirm you've found every call
site before declaring the gap closed (there were exactly 2 as of 2026-07-24;
`CreateSkillForm.jsx` is a 3rd but for Skills, a different entity with its own
already-wired `skill-*` testids — don't touch it for an Agent/Pipeline case).

## PipelineFormPage/PipelineDetailPage were missing several Agent-shared-component locators

Before ELITEA-2021, `PipelineFormPage` only had `name_input`/`description_input`/
`save_button`/`cancel_button`/`discard_button` — despite `CreateAgentForm.jsx`
(entityType="pipeline") ALSO rendering Welcome message, Conversation Starters,
and the Advanced/Step-limit accordion identically to the Agent create form
(confirmed by reading `CreateAgentForm.jsx`'s JSX directly: it composes
`AgentInput.WelcomeMessageInput`, `ConversationStarters`, and
`ApplicationAdvanceSettings` unconditionally, regardless of `entityType`).
Ported the exact same testids (`agent-welcome-message-input`,
`agent-conversation-starter-add`, `agent-conversation-starter-input`,
`agent-step-limit-input`) into `PipelineFormPage` as new `LocatorDescriptor`
fields + thin fill/get methods — following this file's OWN existing
precedent of re-declaring the same testid strings as `AgentFormPage` rather
than composing `AgentFormPage(page)` (composition is the newer, cleaner
pattern used by `AgentCanvasPage`, but `PipelineFormPage` had ALREADY chosen
redeclaration for name/description/save before this case; extending that
established in-file precedent for 3 more fields was the lower-risk, more
consistent choice than mixing patterns within one file).

Similarly, `PipelineDetailPage` had `add_mcp_button`/`open_mcp_popper()`/
`select_mcp_in_popper()` (from ELITEA-1955) but no Toolkit-equivalent — added
`add_toolkit_button` + `open_toolkit_popper()` + `select_toolkit_in_popper()`
as **additive siblings** (existing MCP methods left byte-identical, per the
shared-caller-file rule — ELITEA-1955's test is a merged caller of
`select_mcp_in_popper`). The one behavioural difference from the MCP variant:
the Toolkit popper strips spaces from displayed names (confirmed by
`AgentDetailPage.add_toolkit`'s own docstring), so `select_toolkit_in_popper`
matches on `toolkit_name.replace(" ", "")` while `select_mcp_in_popper` does
not — didn't matter for THIS case (the `artifact_toolkit` fixture's generated
name has no spaces), but matters for any future toolkit-name-with-spaces case.

## Step limit's default-value clear — Playwright's native `.clear()` sufficed here

The field defaults to `"25"` on a fresh create form (confirmed live). AFS
ELITEA-2021 explicitly recommended Playwright's native `.clear()` (not a raw
select-all+Backspace key simulation) before typing the target value — this
worked cleanly for setting a NORMAL value ("50", well under `MAX_STEP_LIMIT`
= 999 per `EliteaUI/src/common/constants.js`). This is a DIFFERENT scenario
from `.agents/memory/qa-engineer/gap_003_step_limit_paste_simulation_and_analyst_worktree_scope.md`'s
native-setter-plus-dispatched-event technique, which exists specifically to
reach the **>MAX clamp branch** (a value that per-character typing can never
produce because `onKeyDown` blocks it) — GAP-003's case, not this one. Don't
reach for the heavier paste-simulation technique unless the case specifically
needs to test the clamp/reject behavior; plain `.clear()` + `press_sequentially()`
is correct and sufficient for "just set it to a normal value."
