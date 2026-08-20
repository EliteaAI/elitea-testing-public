# Test Case: Chat – Create Toolkit from Conversation – Close Canvas Without Saving and Verify No Toolkit Created

## Metadata
- **TMS ID**: ELITEA-2081
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", `projectId=399`, matches `${ELITEA_PROJECT_ID}`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, `.agents/test-automation.yaml` batch tiering)
- **Status**: **ready-for-automation** — case executed end-to-end live (all 5 steps observed against the real app) at analysis time. The precondition ("canvas cleared after discarding, following ELITEA-2080") is reproduced as **transit setup** driving the real Toolkit-canvas Discard flow — not a substitution, ELITEA-2080 itself is not part of this batch and has no covering spec on `origin/automation/base` or this batch's trunk to `extend-existing` against. Three new testids were required to drive the Discard flow honestly (Toolkit/MCP canvas never had a Discard-button/confirm-modal testid path — same gap ELITEA-2076 found and fixed for the sibling Pipeline canvas); added this session, mirroring ELITEA-2076's fix 1:1.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation in the Chats section — satisfied via the `conversation_id` fixture (API-created, real `/chat/{id}` URL).
- **Canvas has been cleared after discarding (following ELITEA-2080)** — reproduced as transit: open the in-chat "Create New Toolkit" canvas, select GitHub type, type a name (dirties the form), click the canvas's Discard button, confirm the Discard-confirmation dialog. Confirmed live this session: `ToolkitEditor.jsx`'s `handleDiscard()` in creation mode resets `editToolDetail` to `null` and `formikInitialValues` to `{type: ''}` — the canvas returns to the type-picker (empty) state, still open. This is the literal live product behavior ELITEA-2080's own case describes ("canvas is cleared"), driven honestly through the real UI — no substitution, nothing mocked or injected.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Private project (`${ELITEA_PROJECT_ID}`, `399`) — ambient default for a fresh dev-token session in this environment (confirmed live).

### generate-per-test
- **New conversation** — created via the `conversation_id` fixture (API, `ConversationAPI`), auto-deleted after the test.
- Transit-only toolkit type: GitHub (`toolkit-type-card-github`), transit-only name `autotest_2081_discard` — never persisted (Discard, never Create/Save; confirmed live via the create-POST network-absence check, see § Network Behavior).

## Test Steps

0. **Transit setup** — reach the "canvas cleared after discard" precondition (ELITEA-2080's own flow, driven live, not this case's own subject):
   0a. Navigate to Chats, open the fixture-created conversation.
   0b. Click `+` → hover Toolkits → click "+ Create New Toolkit" (`ChatPage.open_create_new_toolkit_canvas()`, existing method reused verbatim from ELITEA-2083).
   0c. Click the GitHub type card (`toolkit-type-card-github`) — confirmed live: form renders, header becomes "New GitHub Toolkit", Discard/Create both start disabled.
   0d. Type `autotest_2081_discard` into the Name field (`toolkit-form-name-input`) — confirmed live: Discard button transitions disabled → enabled.
   0e. Click the canvas Discard button (`toolkit-canvas-discard-button`) — confirmed live: opens confirmation modal, body text `"Are you sure you want to discard changes?"`.
   0f. Click the modal's Discard-confirm button (`toolkit-canvas-discard-confirm-button`) — confirmed live: modal closes; canvas returns to the type-picker/empty state (title reverts to "New Toolkit", Name field unmounted, `toolkit-type-card-*` cards visible again); canvas stays open.
1. Verify the canvas is still open and cleared after the previous discard.
   - **Verify**: `toolkit-canvas-close-button` still visible (canvas open); `toolkit-canvas-title` reads `"New Toolkit"` (reverted from "New GitHub Toolkit"); a `toolkit-type-card-*` element is visible again (type-picker/empty state) — confirmed live via all three checks immediately after step 0f.
2. Click the X button in the top right corner to close the canvas.
   - **Verify**: `ToolkitCanvasPage.close()` (`toolkit-canvas-close-button`, existing method reused from ELITEA-2083). Confirmed live: **closes directly, no confirmation dialog** — matches the already-documented behavior (`test-specs/chat-interface/_surface.md` § "Toolkit-from-chat canvas — ELITEA-2080-2083": "with a SAVED toolkit (no unsaved changes), clicking `toolkit-canvas-close-button` closes the canvas DIRECTLY without a confirmation dialog") — the SAME "no unsaved changes" condition applies here because the Discard in step 0f already reset the form's dirty flag (`BaseEditor.jsx`'s `handleDiscard`: `onDiscard?.(); setIsDirty?.(false);`), so `handleCancel`'s `isDirty && !isPublic` guard is false and it calls `onClose()` straight away.
3. Verify the conversation view is displayed.
   - **Verify**: canvas chrome (`toolkit-canvas-close-button`, `toolkit-canvas-title`) absent from the DOM; `chat-message-input` visible again — confirmed live.
4. Verify no new TOOLKITS section appears in the PARTICIPANTS panel.
   - **Verify**: `ChatPage.is_participants_badge_visible(section="toolkits")` returns `False` — confirmed live (the `chat-participants-badge-toolkits` container is absent from the DOM at participant count 0 — same established idiom ELITEA-2076 uses for `section="pipelines"`, ELITEA-2083 uses positively for the saved-toolkit case).
5. Verify no toolkit was created.
   - **Verify**: same observable as step 4 (PARTICIPANTS panel has no TOOLKITS section == no toolkit entries) — asserted once, satisfies both case steps 4 and 5 (case text states the same check twice, once per-section and once per-entries). **Network-level confirmation**: zero `POST` requests to `/tools/prompt_lib/` fired at any point across the whole flow (registered before opening the canvas) — a stronger, system-produced signal than the DOM/participants-badge check alone, same idiom ELITEA-2076 uses for its own "no pipeline created" step.

## Expected Results
All 5 case steps pass cleanly as specced above once the three `needs-adding` Discard testids (§ Concrete Handles) land: after the transit discard, the canvas is confirmed open and reverted to its empty/type-picker state; clicking X closes it directly (no confirmation, no unsaved changes); the conversation view returns; the PARTICIPANTS panel shows no TOOLKITS section and zero toolkit-create requests fired at any point. No product defect found — this flow behaves exactly as the case describes.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: open conversation in Chats section | — | Setup | `conversation_id` fixture + `navigate_to_chat()` | asserted |
| Precondition: canvas cleared after discarding (following ELITEA-2080) | canvas open, empty fields | transit step 0 | steps 0a-0f drive the real Discard flow live | asserted (transit, honest — not a substitution) |
| 1 Verify canvas still open and cleared → Canvas open with empty fields | canvas open, empty fields | step 1 | `close_button` visible + title == "New Toolkit" + type-picker card visible | asserted |
| 2 Click X to close canvas → Canvas closes completely | canvas closed | step 2 | canvas chrome absent from DOM | asserted |
| 3 Verify conversation view is displayed → Conversation view shown | conversation view shown | step 3 | `chat-message-input` visible, canvas chrome gone | asserted |
| 4 Verify no new TOOLKITS section in PARTICIPANTS → No toolkit was created | no toolkits section | step 4 | `is_participants_badge_visible(section="toolkits")` == False | asserted |
| 5 Verify no toolkit was created → PARTICIPANTS panel shows no toolkit entries | no toolkit entries | step 5 | same badge-absence check + zero create-POST network assertion | asserted |
| Expected Final State: "The canvas is closed without saving and no toolkit is created or shown in the PARTICIPANTS panel" | — | steps 2, 4, 5 | canvas-closed + badge-absence + network assertions | asserted |
| Pass/Fail: "No toolkit is created; PARTICIPANTS panel has no TOOLKITS section" / "A toolkit appears in PARTICIPANTS despite not being saved" | — | steps 4, 5 | same as above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 1 adds two extra checkpoints beyond the case's own "canvas is open with empty fields" wording — the title reverting to "New Toolkit" and a type-picker card being visible again — *added: these are the concrete, testid-observable form of "cleared" for THIS canvas (create-mode Discard resets to the type-picker, not to a blank-form-with-empty-Name-field state, per `handleDiscard()`'s `isCreating` branch confirmed live) — a bare "no toolkit and canvas open" check would under-specify what "cleared" means here and could pass even if the reset were only partial.*
- Step 5 adds a network-level assertion (zero `POST` to `/tools/prompt_lib/`) alongside the DOM-level participants-badge check — *added: same rationale as ELITEA-2076's step 8 — a network-level check is a stronger, system-produced signal of "not created" than the DOM/participants-badge check alone. Confirmed live during this analysis: the whole discard→close flow fires zero `POST` to the toolkit-create endpoint.*
- Console/network side-channel checked after every step — confirmed clean throughout (zero unexpected console errors beyond the pre-filtered known-noise patterns already documented for this canvas family, zero unexpected failed (4xx/5xx) requests) across the whole session.

## Cleanup
1. Delete the created conversation via `conversation_api.delete_conversation(id)` (handled automatically by the `conversation_id` fixture's teardown).
2. No toolkit cleanup needed — this flow never persists a toolkit (confirmed live via the network-level check in step 5).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `cd EliteaUI && git fetch origin` (this session) then `git grep` on `origin/main`; `automation/testids` provenance is this session's own commit.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| `+` menu → Toolkits menuitem | `toolkits-menuitem` | on-main ✓ | Existing, reused from ELITEA-2083. |
| `+` menu → Toolkits submenu → "+ Create New Toolkit" | `toolkits-create-new-button` | on-main ✓ | Existing, reused from ELITEA-2083. |
| GitHub type card | `toolkit-type-card-github` | on-main ✓ | Existing, reused from ELITEA-2083. |
| Toolkit Name field (create form) | `toolkit-form-name-input` | on-main ✓ | Existing, reused from ELITEA-2083 (`ToolkitCreationPage.name_input`). |
| Canvas X (close) button | `toolkit-canvas-close-button` | on-main ✓ | Existing, added by ELITEA-2083. |
| Canvas header title | `toolkit-canvas-title` | on-main ✓ | Existing, added by ELITEA-2083. |
| Canvas Discard button | `toolkit-canvas-discard-button` | **on-`automation/testids` only — awaiting human promotion to `main`** | ADDED this session (`EliteaAI/EliteaUI@bc08563f`). `BaseEditor.jsx`/`EditorHeader.jsx` already threaded the `discardButtonTestId`/`discardModalTestId`/`discardConfirmButtonTestId` optional props end-to-end (added for `PipelineEditor.jsx` by ELITEA-2076), and `ToolkitEditor.jsx` already had a working `handleDiscard` wired to `BaseEditor`'s `onDiscard` — only the three testid props were missing at this call site. Supplied as `isMcpTestIdScope ? 'mcp-canvas-discard-button' : 'toolkit-canvas-discard-button'` at `ToolkitEditor.jsx`'s `<BaseEditor>` call, same conditional pattern as the pre-existing title/close/create testids. |
| Discard confirmation modal | `toolkit-canvas-discard-confirm-modal` | **on-`automation/testids` only — awaiting human promotion to `main`** | ADDED this session, same commit/mechanism as the Discard button above. |
| Discard-confirm button (inside the modal) | `toolkit-canvas-discard-confirm-button` | **on-`automation/testids` only — awaiting human promotion to `main`** | ADDED this session, same commit/mechanism as the Discard button above. |
| PARTICIPANTS toolkits badge | `chat-participants-badge-toolkits` | on-main ✓ | Existing `ChatPage.is_participants_badge_visible(section="toolkits")` — same dynamic template ELITEA-2083 uses for the positive-presence case; this case is its negative-absence counterpart. |
| Message input | `chat-message-input` | on-main ✓ | Existing `ChatPage.message_input`. |

## Network Behavior
- `GET /api/v2/elitea_core/configurations/models/399?...section=vectorstorage...` → `200 OK` — fires once after the GitHub type card is clicked (pgvector default-credential fetch, same as ELITEA-2083's transit setup 0c), unrelated to this case's own subject.
- **Zero** `POST` to `/tools/prompt_lib/` at any point — confirmed live across the full type-select → name-type → Discard → confirm-Discard → close sequence. This is the case's own central concern (Pass/Fail: "A toolkit appears in PARTICIPANTS despite not being saved" is a fail) and is asserted directly in the test (see Axis 2).
- No unexpected 4xx/5xx observed at any point in this session's execution of this case's own steps.

## Known Defects Found During Exploration
None. This flow behaves exactly as the case describes — Discard (transit) correctly clears the canvas back to its type-picker state without creating a toolkit, and the X-close afterward closes directly (no unsaved changes to warn about) without ever creating one either.

## Blocked Steps
None. All 5 case steps were executed and observed end-to-end live (via the transit-reproduced precondition).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **Reuse, don't rewrite**: compose `ChatPage` (canvas entry point, plus-menu, participants badge) + `ToolkitCreationPage` (type-card click, Name field, inherited pattern) + `ToolkitCanvasPage` (close/title/discard/discard-confirm chrome) on the SAME `page` — same composition pattern ELITEA-2083's test already uses, plus the new Discard-specific fields/methods.
- **`ToolkitCanvasPage` needs three new fields + two new methods** (mirrors `PipelineCanvasPage`'s ELITEA-2076 `discard_button`/`discard_confirm_modal`/`discard_confirm_button` + `click_discard()`/`confirm_discard()` shape 1:1 — same underlying `Button.DiscardButton`/`BaseModal` components, different call site). Already added this session.
- Three `needs-adding` testids required before compliant automation (all added this session, pushed to `automation/testids` — see § Concrete Handles): `toolkit-canvas-discard-button`, `toolkit-canvas-discard-confirm-modal`, `toolkit-canvas-discard-confirm-button`.
- **No credential/repository fields needed** — unlike ELITEA-2083 (which must complete the full GitHub form to reach a saveable state), this case only needs the form DIRTY, not valid/complete. Typing the Name field alone is sufficient to enable the Discard button — no `github_credential` fixture dependency.
- Wait strategy: no fixed sleeps — `wait_for(state="visible"/"detached")` polling throughout, matching `ToolkitCanvasPage`'s existing `close()` idiom and the new `click_discard()`/`confirm_discard()` methods (mirroring `PipelineCanvasPage`'s idiom).
- Network-absence assertion (step 5): register a `page.on("response", ...)` listener before opening the canvas, collect any `POST` whose URL contains `/tools/prompt_lib/`, assert the collected list is empty after the whole flow — mirrors ELITEA-2076's own network-absence idiom, applied to the toolkit-create endpoint instead of the application-create endpoint.
