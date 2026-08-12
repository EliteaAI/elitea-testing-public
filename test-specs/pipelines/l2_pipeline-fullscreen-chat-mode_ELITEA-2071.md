# Test Case: Pipeline — Fullscreen Chat Mode

## Metadata
- **TMS ID**: ELITEA-2071
- **Linked Story**: none
- **Priority**: l2 (medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN` — no explicit login needed)
- **Analyst**: qa-engineer (Sage), analyst slot, pipelines-remaining wave-05
- **Status**: defect-found — bug filed:
  [`elitea-testing-public#1363`](https://github.com/EliteaAI/elitea-testing-public/issues/1363)

  **Classification note.** This is not a one-isolable-step-at-the-tail defect
  (the Sanctioned-RED / declared-improvisation shape used elsewhere in this
  suite, e.g. ELITEA-1965) — the missing control blocks 6 of the case's 7
  steps (2 through 7) from the very first interaction. Only step 1 (pipeline
  loads with both panels visible) is independently verifiable and already
  covered by other merged pipeline specs (see § Coverage Map). Per
  `.agents/testing.md` § Merge gate's amend, `defect-found` — not a
  Sanctioned-RED `ready-for-automation` — is correct here because the defect
  "blocks further exploration," not merely one tail assertion.

## Preconditions
- User is authenticated (localhost `auth_state` fixture).
- A pipeline exists and is open, with the left configuration panel and the
  right chat/canvas panel both visible (any existing pipeline satisfies
  this — verified live on pre-existing pipeline `probe-pipeline`, id 6934).

## Test Data
### reuse-existing
- Any existing pipeline (verified against `probe-pipeline`, id 6934,
  `LLM 1 -> END`). No fixture data needed — this case makes no assertion tied
  to node type/count/content.

## Test Steps

1. Open a pipeline (`PipelineDetailPage.navigate(pipeline_id)`).
   - **Verify**: pipeline loads with left configuration panel
     (`pipeline-config-tab`, confirmed 320px expanded width — see
     `l2_pipeline-collapse-left-panel_ELITEA-2072.md`) and right chat/canvas
     visible. **Asserted** — this observable is already proven by merged
     specs; see § Coverage Map.
2. In the chat panel header (right side), locate a fullscreen/expand button.
   - **Verify (case's literal expectation)**: a fullscreen button is visible.
   - **Actual (confirmed live, `probe-pipeline` id 6934, 2026-08-09):** no
     such control exists anywhere in the chat panel header. The only header
     icon present is a **collapse** toggle (`ChatPanel.jsx`'s
     `onClickCollapsed`, rendered as a `DoubleLeftIcon`/`DoubleRightIcon`
     `IconButton`) that does the *opposite* of "fullscreen": clicking it
     shrinks the chat panel itself down to a ~28px strip. It does not expand
     anything and does not touch the left configuration panel.
   - **Confirmed via source read** (`EliteaAI/EliteaUI` `automation/testids`,
     `src/pages/Pipelines/Components/ChatPanel.jsx` and
     `.../ConfigurationTab.jsx`): the Agent/Skill/Toolkit-Index chat surfaces
     each wire a real `FullScreenToggle` component
     (`src/components/Chat/FullScreenToggle.jsx`) via a genuine
     `useState`-backed `isFullScreenChat`/`setIsFullScreenChat` pair
     (`Applications/ConfigurationTab.jsx:220`, `SkillTestPanel.jsx:67`,
     `IndexChat.jsx:21`). The Pipeline surface's `ConfigurationTab.jsx:205`
     only carries a **hardcoded literal** `isFullScreenChat: false` inside
     the `settings` object passed to the chat — no state, no setter, nothing
     ever flips it — and `ChatPanel.jsx` never imports `FullScreenToggle` at
     all. **This blocks the rest of the case — see § Known Defects and
     § Blocked Steps.**
3. Click the fullscreen button.
   - **Blocked** — no such button exists (see step 2). Cannot execute.
4. Verify chat panel expands to full screen (left configuration panel hides).
   - **Blocked** — depends on step 3.
5. Verify pipeline execution still works in fullscreen mode.
   - **Blocked** — depends on step 3/4.
6. Click exit fullscreen button.
   - **Blocked** — depends on step 3.
7. Verify returns to split view (left panel + right chat/canvas).
   - **Blocked** — depends on step 6.

## Expected Results
Per the case: fullscreen chat mode expands the chat to full width (hiding the
left panel), execution keeps working in fullscreen, and exiting restores the
split view. **Not achievable on the live product** — the control described
does not exist on the Pipeline surface (see § Known Defects). No expected
result beyond step 1 could be observed.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline | left panel + chat/canvas visible | step 1 | Already proven: `l2_pipeline-collapse-left-panel_ELITEA-2072.md` (320px baseline), plus every other merged pipeline detail-page spec that navigates and asserts panel visibility | already-covered (this element only) |
| 2 Locate fullscreen button in chat header | button visible | step 2 | live exploration — **does not exist** | known defect (#1363) |
| 3 Click fullscreen button | chat panel expands | step 3 | n/a — no button to click | blocked (depends on #1363) |
| 4 Chat expands to full screen, left panel hides | left panel hidden, chat fills space | step 4 | n/a | blocked (depends on #1363) |
| 5 Pipeline execution works in fullscreen | execution responds in fullscreen chat | step 5 | n/a | blocked (depends on #1363) |
| 6 Click exit fullscreen button | fullscreen exits | step 6 | n/a | blocked (depends on #1363) |
| 7 Returns to split view | left panel + chat restored | step 7 | n/a | blocked (depends on #1363) |

### Axis 2 — Analyst additions

- Confirmed live that clicking the *actual* existing header control (the
  chat-panel collapse toggle) leaves the left configuration panel completely
  unaffected (all sections — General/Tools/Welcome message/Chat
  starters/Advanced/Editor Notes/Information — remain visible and unchanged)
  and fires zero console errors — *added: rules out "maybe it's mislabeled
  but functionally equivalent," which would have let the case be quietly
  reframed around the wrong control instead of flagged as a genuine gap.*
- Interaction-discovery ladder (`role-overrides.md`) was exhausted before
  concluding "does not exist": checked the chat panel header, the canvas's
  own "Flow"/"Yaml"/"Add node" button group (unrelated — canvas view mode,
  already covered by `l2_pipeline-yaml-editor-view_ELITEA-2026.md`), and the
  ReactFlow Control Panel (Zoom/Fit View/etc., unrelated) — no fullscreen
  affordance anywhere on the page. Source read of `ChatPanel.jsx` and
  `ConfigurationTab.jsx` confirms no dead/hidden implementation to surface
  via a different trigger.

## Cleanup
None — no state created.

## Concrete Handles (discovered during exploration)

Locator policy: **testid-only** (`.agents/testing.md` § Locator policy). No
handles are captured for steps 2–7 because the control under test does not
exist; nothing to bind a `LocatorDescriptor` to.

| Element | Testid | Provenance | Fallback |
|---|---|---|---|
| Chat panel collapse toggle (the control that DOES exist at this location, but is a different feature — not usable as a substitute for this case) | none (`ChatPanel.jsx`'s `IconButton` has no `data-testid` on either `main` or `automation/testids`) | needs-adding, only relevant if a future case targets the collapse feature itself | none |

## Network Behavior
Not applicable — execution stopped at step 2; no network traffic pertains to
a control that doesn't exist.

## Known Defects Found During Exploration

1. **[MAJOR] Pipeline chat panel has no Fullscreen Mode toggle** (present on
   every other chat-hosting surface — Agents, Skills, Toolkit Indexes).
   Filed: [`elitea-testing-public#1363`](https://github.com/EliteaAI/elitea-testing-public/issues/1363).
   Confirmed live on `probe-pipeline` (id 6934): no fullscreen/expand control
   in the chat panel header; the only header icon collapses the chat panel
   itself (opposite direction, does not touch the left panel). Root cause:
   `src/pages/Pipelines/Components/ConfigurationTab.jsx:205` hardcodes
   `isFullScreenChat: false` (dead literal, no `useState`/setter), and
   `ChatPanel.jsx` never imports `FullScreenToggle`
   (`src/components/Chat/FullScreenToggle.jsx`) — unlike
   `Applications/ConfigurationTab.jsx`, `SkillTestPanel.jsx`, and
   `IndexChat.jsx`, which all wire it for real. Looks like a genuine
   feature-parity gap, not a case-authoring mistake.

## Blocked Steps
- Steps 3–7 — all depend on the fullscreen button from step 2, which does not
  exist on the live product. See § Known Defects #1
  ([`elitea-testing-public#1363`](https://github.com/EliteaAI/elitea-testing-public/issues/1363)).
  Automation paused until the product implements the feature (or the case is
  retired/rewritten to describe the actual chat-collapse behavior, which is a
  different feature and would need its own case/AFS).

## Automation Hints
Not applicable while `defect-found` — no test to write yet. When
`elitea-testing-public#1363` is resolved (feature implemented for Pipelines),
re-run this analysis: expect the fix to mirror the Agent surface's
`FullScreenToggle` wiring, so the resulting AFS's handles/flow should closely
match whatever pattern the Agent-surface fullscreen-chat case (if one exists)
already established — check `test-specs/agents/` for a sibling case before
re-deriving from scratch.
