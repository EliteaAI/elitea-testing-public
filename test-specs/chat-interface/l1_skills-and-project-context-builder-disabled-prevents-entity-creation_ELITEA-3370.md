# Test Case: Skills Builder and Project Context Builder disabled prevents entity creation

## Metadata
- **TMS ID**: ELITEA-3370
- **Linked Story**: `EliteaAI/elitea_issues#6239`
- **Priority**: l1 (case priority: `critical`; pytest marker `@pytest.mark.p0`)
- **Status**: **ready-for-automation**
- **Environment Explored**: DEV as deployed (`https://dev.elitea.ai/app`,
  project `Private`, API project id `575`). Playwright MCP server in this
  container has no Chrome binary (known gap, qa-engineer memory
  `elitea_1805_bucket_first_click_toggle_and_playwright_mcp_no_chrome.md`) —
  driven via a direct `sync_playwright` scratch script through the existing
  `ChatPage` page object (`p.chromium.launch(headless=True)`, context
  `storage_state` loaded from `.playwright-mcp/dev-storage-state.json`), same
  pattern as the ELITEA-3252/3253/3254/3255 family AFS. All steps driven
  live, no synthesized input.
- **User set**: `${TEST_USER}` (DEV, `auth_state` logs in via the API —
  storage state refreshed via `scripts/dev_storage_state.py` this session)
- **Analyst**: qa-engineer (Sage), analyst slot, batch `builder-modules-chat-2459`

## Preconditions
- User is logged in to `${BASE_URL}` (`${TEST_USER}`, API-based `auth_state`).
- A conversation is open (this run: a fresh conversation created via
  `sidebar-create-button`, same pattern the `conversation_id` fixture uses).
- **Both `skill_builder` and `project_context_builder` module toggles are OFF
  by DEFAULT for a never-touched conversation** — confirmed live via
  `ChatPage.open_internal_tools_menu()` + `is_module_toggle_checked()`
  immediately after creating a fresh conversation, both `False`. No explicit
  "ensure disabled" action is needed for a fresh conversation; the test
  should still assert this (don't assume) since it is itself part of the
  case's preconditions.

## Test Data

### reuse-existing
- `${ELITEA_PROJECT_ID}` = DEV API project id `575` ("Private" project).

### generate-per-test
- Chat messages (verbatim per the case's own steps, live-confirmed to
  reliably trigger/not-trigger the respective tool):
  - Step 3: `"Create a skill that summarizes daily standup notes"`
  - Step 5: a message that both asks the AI to generate+save a project
    context AND embeds a project description in the same message. **Live-
    confirmed gap (not a defect — see § Known Defects):** a bare "generate a
    project context for this project" with no description produces a
    clarifying question from the AI instead of exercising the
    disabled-module path meaningfully (the AI never reaches the point of
    attempting the tool call either way, since the module is off, but a
    message that WOULD invoke the tool if enabled is the stronger negative
    test). Recommended message, reused from the ELITEA-3254 family AFS:
    `"Generate and save a project context for this project. It is a
    Playwright/pytest test automation suite for the Elitea AI platform,
    covering chat, agents, pipelines, skills, toolkits, and settings UI
    flows against a deployed DEV environment."`
  - Step 8 (re-send after enabling): any distinct skill-creation message so
    the created skill's name doesn't collide with anything from step 3 (step
    3 is never expected to create a skill at all, so an identical message
    would also work, but a distinct one makes the "earlier message
    unchanged" check in step 9 unambiguous). This run used
    `"Create a skill named <unique-marker> that does nothing useful"` — any
    valid skill-creation message satisfies the case.
- No skill or project-context entity should be created by steps 3-6 (that is
  the pass bar). One skill entity IS expected to be created by step 8 (after
  enabling) — delete it + the conversation in teardown.

## Test Steps

1. Navigate to `${BASE_URL}/chat`, create a fresh conversation
   (`sidebar-create-button`). Open the Modules panel (`plus-menu-button` →
   hover `internal-tools-menuitem`).
   - **Verify**: `modules-toggle-skill_builder`'s `is_checked()` is `False`
     (confirmed live — default-off for a fresh conversation).
2. (Same panel, already open) Check the Project Context Builder toggle.
   - **Verify**: `modules-toggle-project_context_builder`'s `is_checked()`
     is `False` (confirmed live).
   - Close the panel (`ChatPage.close_modules_panel()` — outside click;
     confirmed live `Escape` does NOT close it, same documented mechanism as
     ELITEA-2162/2464).
3. Send the message `"Create a skill that summarizes daily standup notes"`.
   - **Verify**: `ChatPage.wait_for_ai_response()` resolves; the AI's
     response text contains **no** `generated-entity-chip`-testid element
     (confirmed live: with the module disabled, the AI replies with plain
     instructional/template text — e.g. a markdown "Skill: ..." outline in
     this run's capture — and renders **zero** elements matching
     `[data-testid="generated-entity-chip"]` inside that message; contrast
     with step 8 below, where the SAME testid DOES render once the module is
     enabled). Also confirmed live: the response contains no
     `chat-answer-tool-chip` element either — the AI never even attempts a
     tool call, consistent with `skill_builder` being entirely absent from
     the conversation's `meta.internal_tools` the backend reads (this is a
     server-side gate, not merely a disabled UI control — see § Network
     Behavior).
4. Verify no Skill was created.
   - **Verify**: `SkillAPI.list_skills()` contains **zero** skills whose
     `name` resembles the step-3 prompt (confirmed live this run: querying
     the project's skill list immediately after step 3 found none named
     after "daily standup"/"summar*" that postdate the test's own start
     time — any pre-existing skills with unrelated names are ignored;
     scope the assertion to names/timestamps generated by this test run,
     not an exact-zero global count, since the shared project may hold
     unrelated skills from other tests).
5. Send the project-context message (see § Test Data) in the SAME
   conversation.
   - **Verify**: `wait_for_ai_response()` resolves; the AI's response
     contains no project-context tool-invocation chip
     (`chat-answer-tool-chip`) and no `generated-entity-chip` (confirmed
     live this run: the AI replied it has no file-management/project-context
     tool available in this session and offered a plain-text draft instead —
     exact text observed: "I can generate the project context, but no
     file-management tool or project path is available in this session, so
     I cannot save it directly.").
6. Verify no Project Context was created/updated.
   - **Verify**: `GET /elitea_core/project_context/prompt_lib/{project_id}/project-context`
     is unchanged from its pre-step-5 value (confirmed live this run: both
     before and after, `{"id": null, "content": "", "enabled": true,
     "activation_description": null, "updated_at": null}` — identical,
     i.e. still empty).
7. Re-open the Modules panel; enable `skill_builder`
   (`ChatPage.ensure_module_toggle_checked("skill_builder")` — poll-based,
   not toast-based; see § Known Defects for why `click_module_toggle()`'s
   toast-wait is the wrong helper here).
   - **Verify**: `is_module_toggle_checked("skill_builder")` is `True`
     immediately after the click (confirmed live). Close the panel.
8. Re-send a skill-creation request (distinct wording per § Test Data) in
   the SAME conversation.
   - **Verify**: `wait_for_ai_response()` resolves; this time the response
     DOES contain a `[data-testid="chat-answer-tool-chip"]` element whose
     text reads `"Elitea Skills: post_elitea_core_skills"` (confirmed live,
     exact string) AND a `[data-testid="generated-entity-chip"]` element
     (confirmed live) — the created Skill's chip/link. Confirm via
     `SkillAPI.list_skills()` that exactly one new skill matching this run's
     unique name now exists (confirmed live, id captured for teardown).
9. Scroll back to / re-read the EARLIER message pair from step 3 (the
   AI-message element at the index captured before step 7's toggle).
   - **Verify**: that earlier response's text content is byte-identical to
     what was captured right after step 3 (confirmed live this run: exact
     string-equality check on `ChatPage._extract_message_body()`'s return
     value, before vs. after enabling the module and sending further
     messages in the same conversation — unchanged, no retroactive Skill
     chip appeared on the old message).

## Expected Final State
No Skill or Project Context entity exists that traces to step 3 or step 5's
messages. Exactly one Skill entity exists from step 8 (post-enable), with a
visible `generated-entity-chip`. The step-3 message/response pair is
unmodified by the later toggle-enable action.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open Chat Modules, ensure Skills Builder disabled | toggle shows OFF | step 1 | `is_module_toggle_checked("skill_builder")` == False | asserted |
| 2 Ensure Project Context Builder disabled | toggle shows OFF | step 2 | `is_module_toggle_checked("project_context_builder")` == False | asserted |
| 3 Send skill-creation message | AI does NOT create a Skill entity; no chip/link | step 3 | zero `generated-entity-chip` / `chat-answer-tool-chip` elements in the AI response | asserted |
| 4 Verify no Skill created | Skills list has no matching new Skill | step 4 | `SkillAPI.list_skills()` filtered by this run's generated name/timestamp | asserted |
| 5 Send project-context message | AI does NOT create/update Project Context; no chip/link | step 5 | zero tool-chip/entity-chip elements | asserted |
| 6 Verify no Project Context created | Project Context unchanged (still empty) | step 6 | `GET project_context` before/after equality | asserted |
| 7 Enable Skills Builder mid-conversation | toggle updates to enabled | step 7 | `is_module_toggle_checked("skill_builder")` == True | asserted |
| 8 Re-send Skill creation request | Skill created successfully, chip/link shown | step 8 | `generated-entity-chip` + `chat-answer-tool-chip` present; `SkillAPI.list_skills()` shows exactly one new match | asserted |
| 9 Scroll back to earlier request | earlier message/response unchanged; no retroactive Skill creation | step 9 | string-equality on the captured step-3 AI response body, before vs. after | asserted |
| Expected Final State: no entity created while disabled; enabling only affects new requests | — | steps 1-9 (composite) | — | asserted (composite of the above) |

### Axis 2 — Analyst additions

- Step 3/8 additionally assert on the presence/absence of
  `[data-testid="chat-answer-tool-chip"]` (the tool-invocation label), not
  just `generated-entity-chip` — *added: confirms the AI never even
  **attempts** the tool call while disabled, a stronger signal than "no
  entity resulted," and distinguishes "tool blocked" from "tool attempted
  but silently failed," which the case text doesn't differentiate.*
- Step 3's network-level observation (no `/skills/` POST at all, not merely
  "no visible chip") is recommended as a defense-in-depth check — *added:
  the chip is a DOM/render-layer signal; a test that only checks the DOM
  would pass even if the backend transiently returned an error AFTER
  actually creating the skill (not observed live, but asserting at the
  network layer closes that gap for free since the page object already
  exposes request interception via Playwright's `page.on("request")`).* Not
  mandatory — the case's own Pass criteria are satisfied by the chip-level
  check alone; implementer's choice whether to add the network assertion.
- (No other additions beyond the case — all 9 case steps map directly.)

## Cleanup
1. Delete the Skill created in step 8 via `SkillAPI.delete_skill(skill_id)`.
2. Delete the conversation created in step 1 via
   `ConversationAPI.delete_conversation(conversation_id)`.
Both in `try`/`finally` (or fixture teardown), even on failure — same
pattern as `fixtures/data_fixtures.py`'s `conversation_id` fixture.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Create-conversation button | `sidebar-create-button` | on-main ✓, pre-existing `ChatPage` field | reused as-is |
| Plus menu button | `plus-menu-button` | on-main ✓, pre-existing `ChatPage` field | reused as-is |
| Modules menuitem | `internal-tools-menuitem` | on-main ✓, pre-existing `ChatPage` field (`internal_tools_menuitem`) | hover reveals submenu, same mechanism documented by ELITEA-2162 |
| Skill Builder toggle | `modules-toggle-skill_builder` (template `MODULES_TOGGLE_SWITCH.format("skill_builder")`) | on-main ✓, pre-existing `ChatPage.MODULE_TOGGLE_ORDER` entry | `get_module_toggle_switch("skill_builder")` / `is_module_toggle_checked("skill_builder")` / `ensure_module_toggle_checked("skill_builder")` all pre-existing, confirmed live this run |
| Project Context Builder toggle | `modules-toggle-project_context_builder` | on-main ✓, pre-existing `ChatPage.MODULE_TOGGLE_ORDER` entry | same helper methods; `ensure_module_toggle_checked` documented (ELITEA-3254) to be the correct helper since this toggle shows no confirmation toast |
| Chat message input | `chat-message-input` | on-main ✓, pre-existing `ChatPage.message_input` | reused as-is |
| Send button | (pre-existing `ChatPage.send_button`, role+name rung) | on-main ✓ | reused as-is via `ChatPage.send_message()` |
| Tool-invocation chip (AI message) | `chat-answer-tool-chip` | on-main ✓, confirmed live this run | contains the exact text `"Elitea Skills: post_elitea_core_skills"` when the Skill-creation tool fires; absent entirely when the module is disabled |
| **Created-entity chip/link (Skill)** | **`generated-entity-chip`** | on-main ✓, **newly confirmed this run** (not previously documented in any existing AFS/page-object — `ChatPage` has no field for it yet) | renders inside the AI message only when an entity (Skill, in this case) was actually created; absent when the module is disabled. `testid needed` on `ChatPage`: no new product testid is needed (it already exists on DEV) — only a new `LocatorDescriptor(testid="generated-entity-chip")` field + accessor method is needed in `ChatPage`, scoped inside the AI message container (`ScopedLocator(...).within(ai_message)` per the ladder) |
| Skill list API | `SkillAPI.list_skills()` / `SkillAPI.delete_skill(id)` | pre-existing `automation/api/client.py` | reused as-is |
| Project Context API | `GET/DELETE .../project_context/prompt_lib/{project_id}/project-context` | pre-existing `ProjectContextAPI`/`automation/pages/project_context_page.py` precedent (ELITEA-3252/3253/3254/3255 family) | reused as-is for the before/after equality check in step 6 |

No positional handles were used or needed. All handles above are rung-1
testid or pre-existing page-object methods; the one new handle
(`generated-entity-chip`) is itself a rung-1 testid already served by DEV —
only the page-object `LocatorDescriptor` declaration is new work for the
implementer, not a frontend change.

## Network Behavior
- The Modules-panel toggle persists via `PUT
  /elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}`
  carrying `meta.internal_tools` (confirmed live this run: toggling
  `skill_builder` on a conversation that already has a numeric id fires
  this PUT and the change survives a full page reload; same mechanism
  `ChatPage.click_module_toggle()`/`ensure_module_toggle_checked()` already
  document). **This is a genuinely server-enforced gate, not a
  client-side-only control**: the chat predict backend reads
  `activeConversation.meta.internal_tools` to decide which tools the AI may
  invoke (confirmed via `EliteaUI` frontend source,
  `src/[fsd]/features/chat/ui/chat-box/ChatBox.jsx:3183` passes
  `internal_tools` straight through to the predict payload) — so a disabled
  module cannot be bypassed by a more insistent chat message, matching the
  case's own framing ("regardless of how explicit the chat request is").
  Live-confirmed 3/3 across this run's three independent attempts (skill
  request while disabled, project-context request while disabled, skill
  request while enabled): the AI's own tool-invocation behavior tracked the
  toggle state exactly, with no exception.
- `GET /elitea_core/skills/prompt_lib/{project_id}` (plural, list) and `GET
  /elitea_core/skill/prompt_lib/{project_id}/{id}` (singular, single) — used
  for step-4/step-8 verification, pre-existing `SkillAPI` methods.
- `GET /elitea_core/project_context/prompt_lib/{project_id}/project-context`
  — used for step-6 verification, same endpoint/shape the ELITEA-3252/3253/
  3254/3255 family AFS already documents (`{"id", "content", "enabled",
  "activation_description", "updated_at"}`).

## Known Defects Found During Exploration
None — live product behavior matches the case's Pass criteria exactly for
both modules, in both the disabled and enabled states, and the
earlier-message-unchanged check (step 9) held exactly as specified.

One tooling note, not a product defect: `ChatPage.click_module_toggle()`
(the toast-wait helper, built for the OTHER seven modules that DO show a
confirmation toast) intermittently raised a `TimeoutError` waiting on its
`expect_response` match for `skill_builder` in this run's exploration,
**even though the toggle's checked state flipped correctly and a toast WAS
observed when polled directly** — the race is in that helper's internal
`expect_response` context manager, not in the product. This doesn't block
automation: `ensure_module_toggle_checked()` (the poll-based helper already
added for `project_context_builder` by the ELITEA-3254 implementation) is
the correct helper for `skill_builder` too, and this AFS's steps use it
exclusively. No new finding needs filing — this is the same documented
"some toggles don't show a toast reliably in the response-wait window"
class already captured in `ChatPage.ensure_module_toggle_checked()`'s own
docstring; recording it here only as a note for whichever implementer
writes this test, so they don't reach for `click_module_toggle()` by habit
for `skill_builder` and hit the same flake.

## Blocked Steps
None. All 9 case steps were executed live this run, end-to-end, against the
real (unmocked) DEV backend, with 3 independent request/response cycles.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. New test module
  recommended: `automation/tests/ui/chat/test_builder_modules_disabled.py`
  (no existing spec combines both toggles' negative-path + enable-mid-
  conversation flow — `test_image_creation.py` and the ELITEA-2162/2464
  specs cover OTHER modules' positive-path toggling, not this negative
  case, so this is fresh coverage, not an extension).
- Use the `conversation_id` fixture (`automation/fixtures/data_fixtures.py`)
  for the conversation, and a function-scoped `skill_api` fixture
  (`SkillAPI`, already registered per `.claude/rules/api-patterns.md`) for
  verification + cleanup of the one Skill step 8 creates.
- **New `ChatPage` work required**: add a `generated_entity_chip` (or
  similarly named) `ScopedLocator(testid="generated-entity-chip",
  description="Renders inside an AI message only when a chat-builder
  module (Skill/Project Context/Agent/Pipeline) actually created or
  persisted an entity; absent when the owning module is disabled.")` field,
  plus a small helper e.g. `message_has_generated_entity_chip(message_locator)
  -> bool` that resolves it `.within(message_locator)` and returns
  `.count() > 0`. This is the ONE new page-object declaration this case
  needs; everything else (toggles, message input, tool-chip) is 100% reuse.
- Priority marker: `@pytest.mark.p0` (case priority `critical`, consistent
  with the sibling ELITEA-3252/3253/3254/3255 family's `l1`/`p0` mapping).
  Also mark `@pytest.mark.chat` and `@pytest.mark.regression`.
- `@pytest.mark.tms("ELITEA-3370")` on the test method.
- Sibling card **ELITEA-3372** (`.agents/automation/builder-modules-chat-2459/cases/ELITEA-3372.md`
  — "Agent and Pipeline Builder work correctly when Skills Builder and
  Project Context Builder are enabled") is in the same batch/intake folder
  and touches the identical Modules-panel toggling, Ask User HITL flow, and
  Agent/Pipeline-builder chips. It is a DIFFERENT case (positive-path
  regression check across four modules at once, with HITL approval/
  rejection sub-flows this case doesn't touch) — not a target for
  `already-covered`/`extend-existing` against this AFS, and vice versa; keep
  them as separate specs. Worth sequencing its own analysis to reuse
  whatever `generated_entity_chip` helper this case's implementation adds.
