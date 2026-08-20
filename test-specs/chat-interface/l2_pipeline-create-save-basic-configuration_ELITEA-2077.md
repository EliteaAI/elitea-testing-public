# Test Case: Chat – Create Pipeline from Conversation – Save Basic Configuration and Verify Pipeline is Created

## Metadata
- **TMS ID**: ELITEA-2077
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", `projectId=399`, matches `${ELITEA_PROJECT_ID}`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer / test-automation-engineer combined slot (agent) — same session analysed and implemented, per batch triage (surface already mapped, `test-specs/chat-interface/_surface.md` § "In-chat 'Create New X' canvas family — Pipeline/MCP" applied)
- **Status**: **ready-for-automation** — all 9 case steps + both preconditions executed live against `localhost:5173` via a live browser session before this AFS was written. Every asserted value below (testid presence, exact composer-chip text split, ADVANCED-section content, tab list) is a live-confirmed observable, not carried over from the sibling AFS's provenance notes without re-verification.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- **User has an open conversation in the Chats section.** Automated via the framework's established `conversation_id` API fixture + `ChatPage.navigate_to_chat(conversation_id=...)` (existing pattern, every `test_chat_interface.py`/sibling pipeline-canvas test uses it) rather than a raw `+Chat` sidebar click — sidesteps the known, already-tracked issue #1085 composer-covered-by-loading-overlay class of flake documented against this exact surface (`_surface.md` § "In-chat 'Create New X' canvas family").

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Private project (`${ELITEA_PROJECT_ID}`, `399`) — ambient default for a fresh dev-token session in this environment (confirmed live via the sidebar's `Project: Private` combobox).

### generate-per-test
- **New conversation** — created via the `conversation_id` fixture, cleaned up via `conversation_api.delete_conversation(id)`.
- **New pipeline** — Name `test-pipeline`, Description `A test pipeline for conversation` (both literal case Test Data values). Created via this case's own steps (the pipeline creation *is* the case under test, unlike ELITEA-2079/2076 where it is setup). Cleaned up via `pipeline_api.delete_pipeline(id)` (API), keyed off the numeric `id` returned by the create-mode Save's `201` response body — do NOT rely on conversation deletion to cascade.

## Test Steps

1. Navigate to Chats and open a conversation.
   - **Verify**: `ChatPage.navigate_to_chat(conversation_id=...)`; `chat.message_input` visible.
2. Click the `+` icon, select "Pipelines", click "+ Create New Pipeline".
   - **Verify**: `chat.plus_menu_button` → `chat.pipelines_menuitem` (hover-opens submenu) → `chat.pipelines_create_new_button`; the "Create New Pipeline" canvas opens (`pipeline_canvas.title` == `"Create New Pipeline"`, confirmed live).
3. Type "test-pipeline" in the "Name *" field.
   - **Verify**: `PipelineDetailPage.name_input` (`agent-name-input`) accepts and reflects the value (`to_have_value`).
4. Type "A test pipeline for conversation" in the "Description *" field.
   - **Verify**: `PipelineDetailPage.description_input` (`agent-description-input`) accepts and reflects the value (`to_have_value`).
5. Verify the ADVANCED section shows "Step limit" with value "25" and model chip.
   - **Verify**: confirmed live — the "Advanced" accordion (`agent-canvas-section-advanced`) is expanded by default in create mode (no click needed) and contains the Step limit field (`pipeline-step-limit-input`) pre-filled `"25"`. The "model chip" is the composer-form's own Model Selector control rendered in the same panel (`model-selector-button`/`model-selector-name`) — asserted as visible with non-empty text, NOT a hardcoded model name (`.agents/testing.md` § Known issues: "Model-selector button text changes with the selected model"; live-observed as "Anthropic Claude 4.5 Sonnet" this session, environment-dependent).
6. Click the "Save" button.
   - **Verify**: `PipelineDetailPage.save_button` (`agent-save-button`, confirmed live in create-mode — testid landed via ELITEA-2079's implementation, not a new gap). `page.expect_response` on `POST .../applications/prompt_lib/399` resolves `201 Created`; response body contains a numeric `id` (used for cleanup).
7. Verify the canvas header now shows "test-pipeline" with "base" version tag.
   - **Verify**: `PipelineCanvasPage.title` (`pipeline-canvas-title`) == `"test-pipeline"`; a NEW field `PipelineCanvasPage.subtitle` (`pipeline-canvas-subtitle`) == `"base"` — confirmed live as a sibling `<p>` Typography next to the title, previously untestid'd (see § Concrete Handles, testid added this implementation).
8. Verify two tabs appear at the top: "Configuration" (active) and "Flow Editor".
   - **Verify**: `PipelineCanvasPage.configuration_tab` (`pipeline-canvas-tab-configuration`) visible AND `aria-selected="true"`; `PipelineCanvasPage.flow_editor_tab` (`pipeline-canvas-tab-flow`) visible. Both testids already exist (landed via ELITEA-2079's implementation) — confirmed live, no new gap.
9. Verify a pipeline chip appears in the message input area showing "test-pipeline", "base" version, and "Editing..." status.
   - **Verify**: THREE separate composer elements, confirmed live via `textContent` reads (NOT one concatenated string — same split pattern ELITEA-2079's AFS documented for the post-close state, but this step observes the state WHILE the canvas is still open, immediately after Save):
     - `chat.switch_participant_button` (`chat-switch-participant-button`) == `"test-pipeline"`
     - `chat.chat_version_selector_trigger` (`chat-version-selector-trigger`) == `"base"`
     - `chat.chat_participant_settings_button` (`chat-participant-settings-button`) == `"Editing..."` — this is the element that carries the case's "Editing…" status text; it is a THIRD sibling button in the same composer `ButtonGroup`, not part of either of the two elements above. Confirmed live via a DOM text-node walk during this session's exploration — the case's own wording ("Editing..." status) does not appear anywhere inside `switch_participant_button`'s or `chat_version_selector_trigger`'s own text.

## Expected Results
All 9 steps pass cleanly as specced above. Zero product defects found — this flow behaves exactly as the case describes, confirmed by live execution of every step against `http://localhost:5173` this session (three independent create+save runs during exploration, all identical).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: user has an open conversation in Chats | — | Setup | `conversation_id` fixture + `navigate_to_chat()` | asserted |
| 1 Navigate to Chats and open a conversation → Conversation view displayed | conversation view displayed | step 1 | `chat.message_input` visible | asserted |
| 2 Click + icon, select Pipelines, click + Create New Pipeline → canvas opens | canvas opens | step 2 | `pipeline_canvas.title == "Create New Pipeline"` | asserted |
| 3 Type "test-pipeline" in Name → entered correctly | name entered | step 3 | `name_input` value | asserted |
| 4 Type description → entered correctly | description entered | step 4 | `description_input` value | asserted |
| 5 Verify ADVANCED section (Step limit "25" + model chip) → displayed correctly | advanced section correct | step 5 | `step_limit_input` value + model chip visible/non-empty | asserted |
| 6 Click Save → saved successfully | pipeline saved | step 6 | `201` POST response + numeric `id` in body | asserted |
| 7 Verify canvas header shows "test-pipeline" + "base" version tag → transitions to edit mode | edit-mode header correct | step 7 | `pipeline-canvas-title` + `pipeline-canvas-subtitle` text | asserted |
| 8 Verify Configuration (active) + Flow Editor tabs visible → both visible, Configuration active | tabs correct | step 8 | tab visibility + `aria-selected` | asserted |
| 9 Verify composer chip shows "test-pipeline", "base", "Editing..." → chip visible in message input | composer chip correct | step 9 | 3-way `textContent` split across `chat-switch-participant-button`/`chat-version-selector-trigger`/`chat-participant-settings-button` | asserted |
| Expected Final State: "pipeline created and saved; canvas shows Configuration/Flow Editor tabs; chip with Editing... status in message input" | — | steps 6-9 | — | asserted |
| Pass/Fail: "any step produces an error or unexpected result... pipeline not created, tabs not shown, or chip missing" | — | all steps | side-channel console/network checks throughout | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 6's underlying network call is asserted (`POST … 201` + response body `id`) rather than only a UI signal — *added: matches this suite's established pattern of confirming persistence via the API, and the returned `id` is needed for API-based cleanup (Rule 10 read-only-by-default doesn't apply here — a NEW pipeline is exactly what this case observes, so seed-and-cleanup is the correct posture, not read-only-on-existing-data).*
- Step 5's "model chip" is asserted as visible + non-empty text, NOT a hardcoded model name — *added: `.agents/testing.md` § Known issues records the selected model's display text as environment-dependent; hardcoding it would be reverse-masking (asserting a value the environment doesn't control) per `.agents/role-overrides.md` § Implementer slot / Hard Rule 2 reverse-masking guard.*
- Step 9's three-way composer-chip split (`switch_participant_button` / `chat_version_selector_trigger` / `chat_participant_settings_button`) is asserted explicitly rather than as one blob-text check — *added: confirmed live via a full DOM text-node walk that "Editing..." lives on a THIRD button distinct from the name/version chips, not appended to either; a single substring check on `switch_participant_button` alone would have silently passed even if the settings button's text changed, and would not have caught the "Editing…" text moving elsewhere on a future refactor.*
- Console/network side-channel checked after every step — confirmed clean throughout (zero console errors, zero failed 4xx/5xx requests) across all 9 steps + both preconditions, three independent runs this session.

## Cleanup
1. Delete the created pipeline via `pipeline_api.delete_pipeline(id)` (API, keyed off the `id` from step 6's `201` response).
2. Delete the created conversation via `conversation_api.delete_conversation(id)`.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `cd EliteaUI && git fetch origin` (this session) then `git grep` on `origin/main` / `origin/automation/testids`.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| `+` menu → Pipelines menuitem | `pipelines-menuitem` | on-main ✓ | `PlusChatButton.jsx` static config, existing `ChatPage.pipelines_menuitem`. |
| Pipelines submenu → "+ Create New Pipeline" | `pipelines-create-new-button` | on-main ✓ (runtime-composed) | `PlusChatSubmenu.jsx`: `` data-testid={sectionKey ? `${sectionKey}-create-new-button` : undefined} `` — a bare-substring grep false-negatives on this (template literal), confirmed via direct source read on both `origin/main` and `origin/automation/testids`. Existing `ChatPage.pipelines_create_new_button`. |
| Pipeline Name field | `agent-name-input` | on-main ✓ | Existing `PipelineFormPage.name_input`. |
| Pipeline Description field | `agent-description-input` | on-main ✓ | Existing `PipelineFormPage.description_input`. |
| ADVANCED accordion container | `agent-canvas-section-advanced` | on-main ✓ | Confirmed live via DOM query; not yet wired as a `LocatorDescriptor` — implementer may add if a visibility assertion on the container itself is needed (this case only needs the fields inside it). |
| Step limit field | `pipeline-step-limit-input` | on-main ✓ | Existing `PipelineDetailPage.step_limit_input` / `get_step_limit()`. Confirmed live, pre-filled `"25"` in CREATE mode (no accordion-expand click needed — expanded by default). |
| Model chip (button + name) | `model-selector-button` / `model-selector-name` | on-main ✓ | Same testids `ChatPage`'s composer model selector already uses elsewhere; confirmed live inside the create-mode canvas's own Model Selector Menu group. Not yet a `PipelineDetailPage`/`PipelineCanvasPage` field — implementer adds if asserting inside the canvas specifically (vs. reusing `ChatPage`'s existing fields, which target the composer's OWN model selector, a different physical element). |
| Canvas Save button (create-mode) | `agent-save-button` | on-main ✓ | Landed via ELITEA-2079's implementation (was `needs-adding` in ELITEA-2079's original analysis pass; confirmed on-main now). Existing `PipelineDetailPage.save_button`. |
| Canvas header title (post-save) | `pipeline-canvas-title` | on-`automation/testids` only (awaiting human promotion to main) | Existing `PipelineCanvasPage.title`. |
| Canvas header subtitle/version tag (post-save) | `pipeline-canvas-subtitle` | on-`automation/testids` only (awaiting human promotion to main) | **NEW this implementation** — `PipelineEditor.jsx` already forwarded `title`/`subtitle` text to `BaseEditor`, and `BaseEditor`/`EditorHeader` already supported an optional `subtitleTestId` prop end-to-end (same shape as `titleTestId`, already used by `AgentEditor.jsx` as `agent-canvas-subtitle`) — `PipelineEditor.jsx`'s own call site simply never supplied it. Added `subtitleTestId="pipeline-canvas-subtitle"` at that one call site (`EliteaAI/EliteaUI@7b1e2c5a`, `automation/testids`). Confirmed live: renders `"base"` once an existing (non-create-mode) pipeline is open in the canvas. `PipelineCanvasPage.subtitle` field needs adding. |
| Post-save Configuration/Flow-editor tab bar | `pipeline-canvas-tab-configuration` / `pipeline-canvas-tab-flow` | on-main ✓ | Landed via ELITEA-2079's implementation. Existing `PipelineCanvasPage.configuration_tab` / `flow_editor_tab`. Confirmed live: `Configuration` carries `aria-selected="true"` immediately post-save; `Flow editor` present, not selected. |
| Composer active-participant button (name chip) | `chat-switch-participant-button` | on-main ✓ | Existing `ChatPage.switch_participant_button`. Confirmed live: `textContent == "test-pipeline"` exactly (no "Editing..." text inside it). |
| Composer version-selector button | `chat-version-selector-trigger` | on-main ✓ | Existing `ChatPage.chat_version_selector_trigger`. Confirmed live: `textContent == "base"` exactly. |
| Composer settings button (carries "Editing..." status) | `chat-participant-settings-button` | on-main ✓ | Existing `ChatPage.chat_participant_settings_button` (added by a prior case, ELITEA-2362, never previously asserted for its TEXT content — only clicked). Confirmed live via DOM text-node walk: this is the ONLY element on the page whose text matches `/editing/i` immediately post-save; `textContent == "Editing..."` exactly. |

## Network Behavior
- `POST /api/v2/elitea_core/applications/prompt_lib/399` → `201 Created` on the create-mode Save (step 6); response body: `{"id": <int>, ...}`.
- `GET /api/v2/elitea_core/applications/prompt_lib/399?...&agents_type=pipeline...` / `...&agents_type=classic...` → `200 OK`, refire after Save (list re-fetch for the Pipelines/Agents submenus).
- `GET /api/v2/elitea_core/version/prompt_lib/399/{id}/{version_id}`, `GET /api/v2/elitea_core/version_validator/prompt_lib/399/{id}/{version_id}`, `GET /api/v2/elitea_core/application_skills/prompt_lib/399/{version_id}` → `200 OK`, fired as the canvas transitions to edit mode (step 7-8) to hydrate the post-save view.
- No 4xx/5xx observed at any point in this session's live execution of this case's own 9 steps (confirmed across 3 independent create+save runs).

## Known Defects Found During Exploration
None. This flow behaves exactly as the case describes — confirmed by live execution.

## Blocked Steps
None. All 9 case steps plus both preconditions were executed and observed end-to-end live (three independent runs during this session's exploration, used to cross-check the composer-chip text split and to verify the new `pipeline-canvas-subtitle` testid after a dev-server restart — see § Automation Hints).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **Reuse, don't rewrite**: compose `ChatPage` (canvas entry point, composer chip elements) + `PipelineCanvasPage` (canvas chrome: title/subtitle/tabs) + `PipelineDetailPage` (Name/Description/Save/Step-limit fields, inherited via `PipelineFormPage`) on the SAME `page` — identical composition pattern to `test_pipeline_flow_editor_add_llm_node_from_chat_canvas.py` (ELITEA-2079) and `test_pipeline_discard_changes_clears_canvas.py` (ELITEA-2076). Do not write a new page object from scratch; only ONE new field is needed (`PipelineCanvasPage.subtitle`).
- **One new testid required**: `pipeline-canvas-subtitle` — already added and pushed to `automation/testids` this session (`EliteaAI/EliteaUI@7b1e2c5a`). Add the corresponding `PipelineCanvasPage.subtitle = LocatorDescriptor(testid="pipeline-canvas-subtitle")` field.
- **Dev-server HMR gotcha, confirmed this session (record in memory)**: a long-running `npm run dev` process (idle since a much earlier session) silently stopped picking up file-watcher events for at least one edited JSX file — the new `subtitleTestId` prop was committed, pushed, and confirmed present in the file ON DISK, yet the browser kept serving a build without it (`curl .../PipelineEditor.jsx` also served the stale transformed source) across a full page navigation AND three fresh create-pipeline flows. A hard restart of the dev server (`kill` the old `vite`/`npm run dev` processes bound to port 5173, relaunch `npm run dev`) immediately served the correct code and the testid appeared live on the very next flow. Symptom to watch for: a testid you just added reads as absent live even after a full page reload/navigate, with no console/network error explaining it — check `curl http://localhost:5173/src/<file>.jsx | grep <newTestId>` against the on-disk source before concluding the JSX edit itself is wrong.
- Wait strategy: no fixed sleeps — `page.expect_response()` for the create POST (step 6), standard `to_have_value`/`to_have_text`/`is_visible()` polling elsewhere, matching `ChatPage.wait_for_page_load()`'s own idiom.
- No product defect found in this flow — a plain-additive spec, no soft-assert/known-defect handling needed.
