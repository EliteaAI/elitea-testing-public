# Test Case: Chat – Delete Confirmation Modal UI Validation

## Metadata
- **TMS ID**: ELITEA-2116
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend); project **"UI Testing" (id 400)**, same isolation rationale as ELITEA-2115's AFS (dedicated empty sandbox project, avoids touching shared fixture conversations elsewhere)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-14
- **Status**: ready-for-automation

`test_conversation_deletion_flow.py` (ELITEA-2114) already asserts the dialog's
title/body text and button *visibility*, but neither it nor any other merged
test asserts button **styling** (secondary vs. destructive/red) or **Escape /
outside-click dismissal**. Both are genuinely new observables this case adds.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- Test creates its own conversation via API — the case's "at least one
  conversation exists" precondition is satisfied by setup.

## Test Data

### reuse-existing
- `${TEST_USER}`.
- Project 400 ("UI Testing") — same isolation rationale as ELITEA-2115.

### generate-per-test
- **`conv_target`** — via `conversation_api.create_conversation(name)`.

## Test Steps

**Setup (not a numbered case step)**
0. Create `conv_target` via the API. Navigate to `${BASE_URL}/chat` (project
   400), open `conv_target`.

1. Navigate to Chats, hover the conversation, click the three-dot icon, click
   Delete.
   - **Verify**: `[data-testid="delete-confirm-dialog"]` becomes visible (the
     MUI `Dialog`'s own backdrop dims the background — `MuiBackdrop-root`
     element confirmed present in the DOM at `opacity: 1`; not independently
     re-asserted as a numeric opacity value, just dialog-visible is the
     behavioral proxy the case cares about).
2. Verify modal title text is "Delete confirmation" *(live text — case's
   literal "Delete conversation?" is stale, same drift already documented for
   ELITEA-2114/#695; asserting the live string per the reverse-masking
   guard)*.
   - **Verify**: `[data-testid="delete-confirm-title"]`.text ==
     `"Delete confirmation"`.
3. Verify modal body text is *(live text, not the case's literal wording — see
   CLARIFICATION below)*.
   - **Verify**: `[data-testid="delete-confirm-message"]`.text ==
     `f"Are you sure to delete the {conv_target name} chat? It can't be
     restored."`.
4. Verify Cancel button is on the left as a secondary/outlined button.
   - **Verify**: `[data-testid="delete-confirm-cancel-button"]` is the FIRST
     of the two action buttons in DOM order (Cancel precedes Delete — matches
     "on the left" for the case's default LTR reading order); computed CSS
     class list contains `MuiButton-eliteaSecondary` (live-confirmed this
     session via `getComputedStyle` — background `rgba(255,255,255,0.1)`,
     NOT the alarm/red styling).
5. Verify Delete button is on the right as a red/destructive button.
   - **Verify**: `[data-testid="delete-confirm-button"]` is the SECOND action
     button; computed CSS class list contains `MuiButton-eliteaAlarm`
     (live-confirmed: computed `background-color: rgb(215, 22, 22)` — genuine
     red).
6. Click outside the modal, then (separately) press Escape.
   - **Verify (outside click)**: a real mouse click at a point on the
     `MuiDialog-container` overlay OUTSIDE the dialog Paper (e.g. viewport
     top-left corner, well clear of the centered Paper) closes the dialog
     (`delete-confirm-dialog` count → 0) WITHOUT the underlying `DELETE`
     network call firing.
   - **Verify (Escape)**: re-open the dialog (repeat step 1), press `Escape` →
     dialog closes (count → 0), no `DELETE` call fires.
7. Verify the conversation remains in the list after dismissing via Escape or
   outside click.
   - **Verify**: `[data-testid="chat-conversation-item-{conv_target_id}"]`
     still visible/present after BOTH dismissal paths (live-confirmed: neither
     dismissal removes the conversation).

## Expected Results
- The delete dialog dims the background, shows the correct live title/body
  text, and both action buttons are styled per their semantic role (Cancel =
  secondary/neutral, Delete = red/destructive) — all live-confirmed via
  computed styles, not assumed from class names alone.
- Both Escape and an outside/backdrop click dismiss the dialog without
  deleting the conversation — live-confirmed via the DOM (dialog gone,
  conversation still present) and, for outside-click, network-observed (no
  `DELETE` call fires).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: ≥1 conversation exists | — | Setup | `create_conversation` | asserted |
| 1 Open delete modal → overlay dims background | dialog visible | step 1 | `delete-confirm-dialog` visible | asserted |
| 2 Verify title "Delete conversation?" | title correct | step 2 | `delete-confirm-title` text | asserted *(live text differs from case wording — documented drift, same as ELITEA-2114/#695; not re-filed as a new clarification)* |
| 3 Verify body text | body correct | step 3 | `delete-confirm-message` text | asserted *(live text differs from case wording — same drift)* |
| 4 Verify Cancel secondary/outlined, on left | button styled correctly | step 4 | DOM order + computed CSS class | asserted |
| 5 Verify Delete red/destructive, on right | button styled correctly | step 5 | DOM order + computed CSS class + background color | asserted |
| 6 Click outside or press Escape → modal closes without deleting | modal closes, no delete | step 6 | dialog count 0 + no `DELETE` network call | asserted |
| 7 Conversation remains after dismissal | conversation preserved | step 7 | item still visible | asserted |
| Expected Final State: "correct UI elements, dismissible without deleting" | — | steps 1–7 | covered by rows above | asserted |
| Pass/Fail: "no errors; correct title/body/styles; Escape doesn't delete" | — | steps 2,3,4,5,6 | covered by rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- Step 6 asserts the underlying `DELETE` network call does NOT fire on EITHER
  dismissal path — *added: proves the dismissal is a genuine no-op at the
  network layer, not just a DOM/visual close that could theoretically race a
  fire-and-forget delete call.*
- Step 4/5 assert DOM order (Cancel-before-Delete) as the concrete proxy for
  "Cancel on the left" / "Delete on the right" — *added: the case's spatial
  language ("left"/"right") isn't directly assertable without a bounding-box
  comparison; DOM order in a standard LTR flex row is the honest,
  implementation-grounded equivalent, and was cross-checked live (Cancel
  renders before Delete in the actions row).*

## CLARIFICATION (case-text drift, shared with ELITEA-2114/#695)

Case steps 2–3 quote: title `"Delete conversation?"`, body `"Are you sure to
delete conversation? It can't be restored."`. Live product shows title
`"Delete confirmation"` and body
`"Are you sure to delete the {name} chat? It can't be restored."` (named
conversation, not generic "conversation"). This is the SAME drift already
documented and asserted-around in ELITEA-2114's AFS/test and tracked by
existing issue #695 — not re-filed as a new clarification, just re-confirmed
live this session (title-case string re-verified via
`getComputedStyle`-adjacent DOM read, not assumed from the prior AFS).

## Cleanup
1. `conversation_api.delete_conversation(conv_target_id)` in a `finally` block
   (the conversation is never actually deleted by this test's own actions —
   both dismissal paths are no-ops by design).
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

| Element | Testid handle | Notes |
|---|---|---|
| Delete confirm dialog | `[data-testid="delete-confirm-dialog"]` | Existing (ELITEA-2114). |
| Delete confirm title | `[data-testid="delete-confirm-title"]` | Existing (ELITEA-2114) — live text `"Delete confirmation"`. |
| Delete confirm body | `[data-testid="delete-confirm-message"]` | Existing (ELITEA-2114). |
| Cancel button | `[data-testid="delete-confirm-cancel-button"]` | Existing (ELITEA-2114). Computed class includes `MuiButton-eliteaSecondary`/`MuiButton-colorSecondary`; background `rgba(255,255,255,0.1)`. |
| Delete (confirm) button | `[data-testid="delete-confirm-button"]` | Existing. Computed class includes `MuiButton-eliteaAlarm`/`MuiButton-colorAlarm`; background `rgb(215,22,22)`. |
| Dialog backdrop | `.MuiBackdrop-root` (raw CSS — MUI library-internal node, no app testid exists or is placeable on a library backdrop; scoped stop+flag exception, #579-shape 1: third-party-library subtree, here the MUI `Dialog`'s own generated backdrop) | Used ONLY for computing a real click coordinate outside the dialog Paper — a genuine `page.mouse.click(x, y)` at that coordinate is the actual interaction (not a raw locator-based click on this element; MUI's `Dialog` container intercepts direct element clicks, confirmed live — a coordinate-based mouse click is the correct honest technique, matching the case's own literal "click outside the modal" instruction). |

No new testids needed for the app's own DOM — all handles pre-exist from
ELITEA-2114's implementation. The one raw handle (`.MuiBackdrop-root`) is a
third-party MUI internal node used only to compute a coordinate, not as an
assertion target — see § Automation Hints for the exact technique.

## Network Behavior
- Neither dismissal path (Escape, outside click) triggers
  `DELETE /api/v2/elitea_core/conversation/prompt_lib/400/{conv_target_id}` —
  live-confirmed via `capture_requests_matching()` (existing `BasePage`
  helper) registered before each dismissal attempt.

## Known Defects Found During Exploration
None. All 7 case steps matched live product behavior (module the
already-tracked title/body wording drift, #695).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest. Extend `ChatPage`
  (`automation/pages/chat_page.py`) — a new
  `dismiss_delete_dialog_via_outside_click()` method is the right home for the
  coordinate-click technique below (don't inline it in the spec, per
  `.agents/testing.md` § Locator policy — locators/techniques live in the page
  object).
- **Outside-click technique, live-verified working:** MUI's `Dialog` renders a
  `MuiDialog-container` that visually covers the whole viewport and
  intercepts direct-element `.click()` calls anywhere except the dialog
  Paper itself and the actual `MuiBackdrop-root` node underneath it (Playwright
  correctly reports `<div class="MuiDialog-container...">... intercepts
  pointer events` if you try to click the backdrop element directly at its
  center — the container sits above it in paint order). The honest fix is a
  **coordinate-based mouse click**: `page.mouse.click(x, y)` at a point
  provably outside the dialog Paper's bounding box (e.g. `(5, 5)`, the
  viewport's top-left corner) — this is a REAL synthetic-free mouse event
  Playwright dispatches at the OS/CDP level, landing on whichever element is
  actually there (`MuiDialog-container`, which still correctly triggers MUI's
  `onClose(reason: 'backdropClick')` handler since it wraps the backdrop
  region). This is NOT a `page.evaluate()`/JS-dispatched substitution — it's
  the framework's own supported click-at-coordinate API, and it's exactly what
  the case step ("Click outside the modal") asks for.
- Escape is a plain `page.keyboard.press("Escape")` — no special handling
  needed, confirmed working on the first attempt.
- Button-styling assertions read `element.evaluate("el =>
  getComputedStyle(el).backgroundColor")` (or a Playwright
  `expect(locator).to_have_css("background-color", ...)` assertion) rather
  than string-matching the MUI-generated class name alone (those are
  content-hashed/unstable — `css-1et8is9-...` — the class *name segments*
  `MuiButton-eliteaAlarm`/`MuiButton-eliteaSecondary` ARE stable and
  documented in EliteaUI's own Button component, but pairing the class check
  with a computed-style check is more robust and directly proves the visual
  "red" claim rather than inferring it from a class name).
