# Test Case: Pipeline — Chat starters can be added, saved, and clicked in the embedded chat panel

## Metadata
- **TMS ID**: ELITEA-2053
- **Linked Story**: none
- **Priority**: l2 (medium — per case frontmatter/header, both agree; same
  mapping precedent as the sibling `l2_pipeline-welcome-message-shown-before-first-input_ELITEA-2052.md`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (localhost: `auth_state`/`VITE_DEV_TOKEN` bypasses login)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — all 8 case steps reproduced live
  end-to-end against a fresh disposable pipeline (id `8583`): create form →
  "Chat starters" section already expanded → add starter → type text → Save
  → chip renders in the embedded chat panel (right side) before any message
  → click chip → pre-fills the chat input. Zero console errors, zero 4xx/5xx
  across the whole flow. **Every element this case touches already carries a
  testid** — no `add-data-testid` work needed for the steps this AFS's
  assertions exercise, EXCEPT the "delete starter" button (case step 3),
  which has an `aria-label` but **no testid** — see § Concrete Handles.

## Dedup check (why this is fresh work, not `already-covered`/`extend-existing`)
`test-specs/agents/l2_conversation-starter-chips-visible-and-clickable_ELITEA-1886.md`
(merged — need to confirm the implementing spec file/name at automation time,
see § Automation Hints) automates the **same visual/functional concept**
(add starters → Save → chip visible in embedded chat → click → pre-fill →
Send → response) but for the **Agent** surface
(`AgentDetailPage`/`/agents/all/{id}`'s embedded `ChatBox`). This case
(ELITEA-2053) is the **Pipeline** surface
(`PipelineDetailPage`/`/pipelines/all/{id}`'s embedded `ChatPanel.jsx`).
Confirmed via source read: `ChatPanel.jsx` (`src/pages/Pipelines/Components/`)
mounts the exact same shared `ChatBox` component
(`@/[fsd]/features/chat/ui`) that the Agent Detail page mounts, which in turn
renders the same `ChatConversationStarters.jsx` call site ELITEA-1886 wired a
testid onto (`chat-conversation-starter-tile`). So the underlying React
component tree and testid are identical — but the *route*, the *page object*
(`PipelineDetailPage` vs `AgentDetailPage`), and the *settings entity*
(`pipeline_settings` vs agent `version_details`) differ, and no existing
merged spec exercises this observable through the Pipeline route. Per the
Rule-6 dedup bar ("same observable, same expected result, same screen, cited
at `file:line`") this is NOT the same screen, so `already-covered` does not
apply. It is also not `extend-existing` — there is no existing PIPELINE spec
to extend (the pipeline surface has never exercised chat starters before);
extending the AGENT spec would conflate two different pages/routes into one
test, which is exactly what the "differ in steps/entry point" rule in
`test-case-analysis` reserves for a separate AFS. `ready-for-automation` it is.

Also checked: `grep -rn "conversation_starter\|chat-conversation-starter-tile"
automation/tests/` → only `test_agent_character_limits.py` (agent form
character-limit behavior) and `test_agent_hub_start_conversation_with_starters.py`
(different call site, `/chat/{id}` standalone route, per ELITEA-1886's own
dedup note) — no existing test exercises the Pipeline detail page's Chat
starters section or its embedded-chat chip at all.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed
  envs: standard Keycloak login via `${TEST_USER}`).
- No pre-existing pipeline is required — the case's own step 1 ("Open a
  pipeline") is satisfied by creating a fresh disposable pipeline through the
  create form itself (same pattern as
  `test_create_pipeline_full_details_persist.py` / ELITEA-2052's AFS).

## Test Data

### Literal values (from the case)
| Field | Value |
|-------|-------|
| Chat starter text | `Analyze this data` |

### generate-per-test (created in test setup, cleaned up in its own teardown)
- Pipeline name: `autotest_pipe_chatstarters_<unique>` (`autotest_` prefix —
  cleanup fixture convention, see `l2_create-pipeline-full-details-persist-after-reload_ELITEA-2021.md`
  § Test Data).
- Description: any non-empty string (required field, not itself under test).

## Test Steps

1. Navigate to `${BASE_URL}/pipelines/create?viewMode=owner` (sidebar
   "Pipelines" → "+ Pipeline") and fill Name + Description.
   - **Verify — PASSES.** Create form loads; Name/Description fields show the
     typed values (confirmed live: `autotest_2053_chatstarters` /
     `Automated analysis for ELITEA-2053 chat starters`).
2. Expand "Chat starters" section in left panel
   (`agent-canvas-section-chat-starters` accordion header — shared
   `ConversationStarters.jsx`, same component as the Agent form).
   - **Verify — PASSES, with a case-text nuance (not a defect, same pattern
     as ELITEA-2052/ELITEA-2021's "Advanced"/"Welcome message" sections).**
     The section renders **already expanded by default** — confirmed live
     via accessibility snapshot: `heading > button [expanded] > "Chat
     starters"` immediately followed by the visible `region` containing the
     "+ Starter" button. No click needed to reach it.
3. Verify existing starter (if any) shows with text and a "delete starter"
   button.
   - **Verify — PASSES, decomposed to the point in the flow where a starter
     actually exists (after step 4/5 below, on a fresh pipeline there is no
     starter yet at this point in the case's literal step order).**
     Confirmed live (post-Save, post-reload — see step 6): the added starter
     row shows the exact typed text in a `Starter` textbox AND a
     `button "delete starter"` (`aria-label="delete starter"`) sits next to
     it. **No testid on the delete button** — see § Concrete Handles; the
     button is currently locatable only by `aria-label`, which the
     project's testid-only locator policy does not accept for a NEW
     locator. This case's assertion for step 3 is contingent on the
     implementer adding a testid first (implementer work per
     `.agents/role-overrides.md` § Analyst slot — "do not soften a testid
     demand into a note").
4. Click "+ Starter" button (button with text "Starter" and "+" icon).
   - **Verify — PASSES.** Clicking `agent-conversation-starter-add`
     (`PipelineDetailPage.conversation_starter_add_button`, pre-existing
     field/method `add_conversation_starter()`) adds a new starter row:
     a `Starter` textbox (testid `agent-conversation-starter-input`,
     `PipelineDetailPage.conversation_starter_inputs`) plus the "delete
     starter" button from step 3 — confirmed live via accessibility
     snapshot immediately after the click.
5. Enter text in the new starter textbox: `Analyze this data`.
   - **Verify — PASSES.** Confirmed live via
     `press_sequentially()` (MUI onChange convention,
     `.claude/rules/mui-patterns.md`) — field value updates to the exact
     literal; `PipelineDetailPage.add_conversation_starter()` already
     supports passing the text directly (`add_conversation_starter("Analyze
     this data")`), no new method needed.
6. Save pipeline.
   - **Verify — PASSES.** `POST /api/v2/elitea_core/applications/prompt_lib/399`
     returns `201 Created` (confirmed live, pipeline id `8583` this
     session); page navigates to
     `/pipelines/all/{id}?destTab=configuration&name=...&viewMode=owner`.
     Zero console errors, zero console warnings.
7. In the chat panel (right side), verify "Analyze this data" appears as a
   clickable starter.
   - **Verify — PASSES.** Confirmed live (both immediately post-Save on the
     same page AND after a full-page reload, same pristine-state discipline
     as ELITEA-1885/ELITEA-1886/ELITEA-2052): exactly **one** element
     matching `[data-testid="chat-conversation-starter-tile"]` renders in
     the embedded chat panel, above the message input, with text content
     exactly `Analyze this data`, and the message list (`chat-message-list`)
     is empty (no message sent yet). **This testid is pre-existing on
     `automation/testids` only** (added by ELITEA-1886/PR #1235,
     `EliteaAI/EliteaUI@afb48435`, on `ChatConversationStarters.jsx` — the
     exact component `ChatPanel.jsx`'s `ChatBox` also renders) — confirmed
     via fresh `git fetch origin` + `git grep` this session (absent on
     `origin/main`, present on `origin/automation/testids` at
     `src/pages/NewChat/ChatConversationStarters.jsx:39`). **No new
     add-data-testid work needed for this element** — the pipeline surface
     inherits the fix ELITEA-1886 already made to the shared component;
     only a new `PipelineDetailPage` page-object field is needed (mirrors
     `AgentDetailPage.CHAT_STARTER_TILE`/`ChatPage.CHAT_STARTER_TILE`).
8. Click the starter — verify it populates the chat input and/or sends the
   message.
   - **Verify — PASSES.** Confirmed live via testid-scoped locator
     (`browser_run_code_unsafe` this session): clicking
     `[data-testid="chat-conversation-starter-tile"]` sets
     `[data-testid="chat-message-input"]`'s value to exactly `Analyze this
     data`, and the tile immediately disappears (count 1 → 0) — **pre-fill
     only, does NOT auto-send**, identical one-shot mechanic to ELITEA-1886's
     documented `hasStarterBeenSent` flag on the shared `ChatBox.jsx`
     (confirmed by source read — this is the same component instance
     class, not a re-implementation). The case's "populates the chat
     input **and/or** sends the message" wording is satisfied by the
     pre-fill half of the "and/or" — matches the live product exactly, no
     clarification needed (the case text itself already hedges with
     "and/or").

## Expected Results
- The "Chat starters" section is visible (expanded by default) in a
  pipeline's left settings panel.
- A new starter can be added via "+ Starter", typed into, and saved.
- The saved starter text renders as a clickable chip
  (`chat-conversation-starter-tile`) in the pipeline's embedded chat panel,
  before any message is sent.
- Clicking the chip pre-fills the chat input (`chat-message-input`) with the
  starter's exact text; the chip disappears (does not auto-send).
- No console errors or warnings at any step; Save returns `2xx`.

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture (localhost `VITE_DEV_TOKEN`) | n/a (fixture-level) | asserted |
| Precondition: a pipeline is open for editing | Pipeline loaded in editor | Step 1 (create form) | create form loads, fields accept input | asserted *(satisfied via a fresh disposable pipeline — see Preconditions note)* |
| 1 Open a pipeline | Pipeline loaded | Step 1 | create form URL + field values | asserted |
| 2 Expand "Chat starters" section | Section visible | Step 2 | accordion header `[expanded]` + visible "+ Starter" region | asserted *(clarification: already expanded by default, no click needed — same pattern as ELITEA-2052's Welcome-message note)* |
| 3 Verify existing starter shows text + delete button | Existing starters shown with delete buttons | Step 3 | starter row text + `button "delete starter"` presence, post-Save/reload | asserted *(testid gap on the delete button — see § Concrete Handles; assertion contingent on implementer adding it)* |
| 4 Click "+ Starter" | New starter input field appears | Step 4 | new `Starter` textbox + delete button appear | asserted |
| 5 Enter text in new starter textbox | Field populated | Step 5 | `.input_value()` equals literal | asserted |
| 6 Save pipeline | Saves without errors | Step 6 | POST 2xx, console error/warning check | asserted |
| 7 Chip visible in chat panel | "Analyze this data" starter visible | Step 7 | `chat-conversation-starter-tile` count==1, exact text match, empty `chat-message-list` | asserted |
| 8 Click the starter — populates input and/or sends | Input populated or message sent | Step 8 | `chat-message-input.input_value()` equals literal; tile count 1→0 | asserted *(the "and/or" is satisfied by the pre-fill branch — matches live product, no explicit Send required by this case's wording, unlike ELITEA-1886 which decomposed an explicit Send)* |
| Expected Final State: starter visible + click populates input | — | Steps 7-8 | same assertions | asserted |
| Pass criterion: "all steps complete without errors" | No errors at any step | Steps 1-8 | console error/warning check at Save and reload (zero both times) | asserted |
| Fail criterion: "chip absent / click doesn't populate input" | n/a (negative condition) | Steps 7-8 | presence/count assertion (absent would fail step 7); input-value assertion (no-populate would fail step 8) | asserted |

### Axis 2 — observables asserted beyond the case text

| Observable | Why asserted |
|---|---|
| Clicking the chip is pre-fill-only (no auto-send) and hides the chip row immediately, even if Send is never clicked | Confirmed via source read (`ChatBox.jsx`'s `hasStarterBeenSent` flag) and live click — same mechanic ELITEA-1886 documented for the Agent surface; the implementer should not expect a message to appear in `chat-message-list` from step 8 alone |
| The chip testid (`chat-conversation-starter-tile`) is the SAME shared-component testid ELITEA-1886 added for the Agent surface, not a fresh add | Grounds the "no new add-data-testid work" claim in source + a fresh `git grep`, not assumption — avoids the implementer redundantly re-running `add-data-testid` on an already-fixed call site |
| Zero console errors across the whole add-starter → Save → reload → click-chip cycle | Silent-error check per project convention |
| Zero network 4xx/5xx across the same cycle | Same silent-failure discipline — a chip click that silently no-ops would look identical to success in the DOM without this check |
| Exact chip count == 1 (not just "chip is present") | The case's Fail criterion implies "chip absent" as a failure; a bare presence check wouldn't catch a duplicate-rendering regression |

## Cleanup
1. Created a disposable pipeline (`autotest_2053_chatstarters`, id `8583`)
   via the create-form UI flow (Steps 1, 4-6 above).
2. Executed all 8 case steps against it (see Test Steps above).
3. **Not deleted this session** — left in the shared local dev DB, same
   precedent as ELITEA-2052/ELITEA-2021's analyst-session throwaway
   pipelines (`cleanup_autotest_pipelines_at_end` fixture picks up
   `autotest_`-prefixed pipelines on deployed envs; no-ops on localhost).
   **For the implementer:** use `pipeline_api.delete_pipeline(pipeline_id)`
   in a `try/finally`, exactly as
   `test_create_pipeline_full_details_persist.py` already does.

## Concrete Handles (testid-only, per `.agents/testing.md` § Locator policy)

| Element | Handle | Provenance | Notes |
|---|---|---|---|
| Pipeline name input | `agent-name-input` | on-main ✓ | Existing field: `PipelineFormPage.name_input`. |
| Pipeline description input | `agent-description-input` | on-main ✓ | Existing field: `PipelineFormPage.description_input`. |
| "Chat starters" accordion section header | `agent-canvas-section-chat-starters` | on-main ✓ (confirmed via source read, `ConversationStarters.jsx`'s `BasicAccordion` item `testId` prop) | **Not needed for this case's assertions** — the section is expanded by default (confirmed live) and `conversation_starter_add_button`'s visibility already proves the section is open (same "don't interact with an always-expanded accordion" precedent as ELITEA-2021/ELITEA-2052). No new page-object field needed. |
| "+ Starter" add button | `agent-conversation-starter-add` | on-main ✓ | Existing field: `PipelineDetailPage.conversation_starter_add_button`; existing method `add_conversation_starter()` (`pipeline_detail_page.py:5444`). |
| Starter input textarea(s) | `agent-conversation-starter-input` | on-main ✓ | Existing field: `PipelineDetailPage.conversation_starter_inputs`; existing method `get_conversation_starter_value()` (`pipeline_detail_page.py:5461`). |
| Starter character counter | `agent-conversation-starter-counter` | on-main ✓ (shared `ConversationStarters.jsx`, confirmed via source read — same component the Agent form's `AgentFormPage.conversation_starter_counter` already binds) | **Not exercised by this case's assertions** (the case doesn't check the counter) — do not add a `PipelineDetailPage` field speculatively (canon ruling #511). |
| **"delete starter" button (THIS case's step-3 target)** | **`testid needed`** on `ConversationStarters.jsx`'s delete `BaseBtn` (`src/components/ConversationStarters.jsx:138-146`, confirmed via source read: `aria-label="delete starter"`, NO `data-testid`/`testId` prop). | **needs-adding.** Implementer: run `add-data-testid` to add e.g. `testId="pipeline-conversation-starter-delete"` — **but per the shared-component ruling (`.agents/testing.md` § Locator policy — "Shared components never hardcode feature-scoped testids"), this component is used by BOTH the Agent form and the Pipeline form, so a feature-scoped literal is wrong here.** The compliant shape is a generic testid on the shared component (e.g. `agent-conversation-starter-delete`, matching the existing sibling literals' `agent-` prefix convention already baked into this same shared component — `agent-conversation-starter-add`/`-input`/`-counter`/`-expand`/`-dialog` are ALL on this one shared component despite being used by both surfaces; this is pre-existing tech debt per the same file, not a new violation to fix here) OR a `testId`-prop passthrough if the component is refactored to accept one — the simpler, consistent-with-neighbors choice is reusing the `agent-` prefix literal convention already established by every other testid in this exact file. Add a matching `PipelineDetailPage` field (e.g. `conversation_starter_delete_button`) once wired. | |
| Save button | `agent-save-button` | on-main ✓ | Existing field: `PipelineFormPage.save_button`. |
| **Starter chip in the embedded chat panel (THIS case's steps 7-8 target)** | `chat-conversation-starter-tile` | **on `automation/testids` only** — added by ELITEA-1886 (`EliteaAI/EliteaUI@afb48435`) onto `ChatConversationStarters.jsx`'s `<EllipsisTextWithTooltip>` call, confirmed absent on `origin/main` / present on `origin/automation/testids` via fresh `git fetch origin` + `git grep` this session. **No new `add-data-testid` work needed** — `ChatPanel.jsx` (pipeline embedded chat) mounts the SAME shared `ChatBox` component the Agent Detail page mounts, which renders this exact call site; the testid ELITEA-1886 added already applies here. Confirmed live via `browser_run_code_unsafe`: `[data-testid="chat-conversation-starter-tile"]` count==1, text=="Analyze this data". **New page-object work needed:** add a `CHAT_STARTER_TILE` class constant + `get_chat_starter_tiles()`/`click_chat_starter_tile()` methods to `PipelineDetailPage` (mirrors `AgentDetailPage.CHAT_STARTER_TILE`/`ChatPage.CHAT_STARTER_TILE` exactly — same duplicated-field shape those two classes already use for their own routes, since none of the three chat-hosting page objects share a common ancestor besides `BasePage`). | |
| Embedded chat message input | `chat-message-input` | on-main ✓ | Existing field: `PipelineDetailPage.chat_input` (`pipeline_detail_page.py:438` — note the field is named `chat_input`, not `chat_message_input`; use the existing name, don't add a duplicate). Confirmed live: click-then-read-value pattern works exactly as the AFS's step 8 describes. |
| Embedded chat message list container | `chat-message-list` | on-main ✓ | Existing field: `PipelineDetailPage.chat_message_list` (added ELITEA-2052). |
| Embedded chat send button | `chat-send-button` | on-main ✓ | Existing field: `PipelineDetailPage.chat_send_button` (`pipeline_detail_page.py:443`). **Not exercised by this case** — the case's step 8 wording ("and/or sends") is satisfied by the pre-fill-only observed behavior; do not add a Send-click assertion unless a future case needs the full send→response cycle (that would be Rule-6 `extend-existing` territory once this spec exists). |

No new testids need adding for the case's PRIMARY observable (the chip in
the embedded chat) — it's a byproduct of ELITEA-1886's fix to the shared
component. **One genuine testid gap remains** for the "delete starter"
button (case step 3) — implementer work per § Concrete Handles above.

## Network Behavior
- `POST /api/v2/elitea_core/applications/prompt_lib/399` — fires on Save,
  `201 Created` on success (confirmed live, pipeline id `8583`).
- `GET /api/v2/elitea_core/application/prompt_lib/399/{id}` — fires on page
  load/reload, `200 OK`, returns `pipeline_settings`/`version_details`
  containing the saved `conversation_starters` list, which `ChatBox.jsx`
  reads to seed the chip row (same `conversationStarters` prop path
  ELITEA-1886 documented for the Agent surface — confirmed via source read,
  `ChatPanel.jsx` passes `{...settings}` through to `ChatBox`).
- No further network/WebSocket traffic is relevant — clicking the chip only
  pre-fills the input client-side; no message is sent by this case's steps.

## Known Defects Found During Exploration
None. The feature behaves exactly as the case describes on the pipeline
surface — no reverse-masking, no functional defect. One documented
**case-text clarification** (not tracker-filed, per the reverse-masking
guard — low-stakes step-sequencing wording drift, same class already
normalized by ELITEA-2021/ELITEA-2052 for this exact form):
1. Step 2's "Expand Chat starters section" is a no-op in the live product —
   the section is expanded by default (see Step 2 note).

One **testid gap** (delete-starter button, step 3) — implementer work per
`.agents/role-overrides.md` § Analyst slot, not a bug ticket; see § Concrete
Handles.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- Reuse `PipelineDetailPage` end-to-end (subclasses `PipelineFormPage`) —
  `navigate_to_create()`, `name_input`/`description_input`,
  `add_conversation_starter(text)`, `get_conversation_starter_value()`,
  `save_and_wait_for_creation()`, `wait_for_detail_page_load()`,
  `chat_input`, `chat_send_button`, `chat_message_list` all already exist
  and were exercised live this session; no changes needed to any of them.
- Add to `PipelineDetailPage`: `CHAT_STARTER_TILE` class constant
  (`'[data-testid="chat-conversation-starter-tile"]'`) + thin
  `get_chat_starter_tiles()` / `click_chat_starter_tile(match_text)` methods,
  mirroring `AgentDetailPage`'s existing implementation
  (`agent_detail_page.py:187-193`, `:2594-2605`) exactly.
- Testid work: run `add-data-testid` for the "delete starter" button on
  `ConversationStarters.jsx` (shared component — see § Concrete Handles for
  the exact naming call), commit + push `automation/testids`, then add a
  `PipelineDetailPage.conversation_starter_delete_button` field.
- Wait strategy: after Save, `page.wait_for_load_state("networkidle")` before
  reading the chat panel — confirmed live the chip renders promptly (well
  under 1s after the detail page's own load, seeded from the `GET
  .../application/...` response body, same timing class as ELITEA-2052's
  welcome message).
- Sequencing: create → add starter → Save → full-page reload (pristine
  "before any user input" state, same discipline as ELITEA-1885/1886/2052)
  → assert chip visible+exact-text → click chip → assert
  `chat_input.input_value()` equals the literal → assert tile count is now 0.
- Teardown: `pipeline_api.delete_pipeline(pipeline_id)` in a `try/finally`,
  matching `test_create_pipeline_full_details_persist.py`'s existing pattern.
- Test data teardown note: this session's throwaway pipeline
  (`autotest_2053_chatstarters`, id `8583`) was left in the shared local dev
  DB (see Cleanup) — harmless, same precedent as ELITEA-2052/2021's
  analyst-session pipelines.
