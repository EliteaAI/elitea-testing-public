# Test Case: Build with AI — all generated draft fields are editable before approval

## Metadata
- **TMS ID**: ELITEA-1912
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/agents/build_with_ai/ELITEA-1912_build-with-ai-all-generated-draft-fields-editable-before-approval.md`
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Status**: `extend-existing`
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project "UI Testing" (id `400`)
- **User set**: `${TEST_USER}` (localhost `auth_state`/dev-token bypass skips login)
- **Analyst**: qa-engineer (Sage), analyst slot, batch #1298
- **Tracking issue**: EliteaAI/elitea-testing-public#1298 (batch tracking issue — no per-case board card)
- **Case-gate note**: same recurring gap as every prior "Build with AI" AFS in this family (ELITEA-1903/1905/1906/1907/1908/1909/1910/1911/1914/1915): `.agents/testing.md` has no `TMS case-gate` section defining excluded statuses. Case frontmatter carries `status: draft` / `execution_type: manual`; per the skill's default this run proceeded and fetched/executed the case. Flagging again for scout.

## Extension target

- **Covering spec (existing, merged onto this batch's trunk — `tests/batch-1298-agents-build-with-ai`, confirmed via `git log`)**: `automation/tests/ui/agents/test_agent_build_with_ai.py:1343-1500`, class `TestAgentBuildWithAIDraftFieldPopulation`, method `test_draft_fields_prepopulated_and_editable` (`automation/tests/ui/agents/test_agent_build_with_ai.py:1356`).
- **Covering AFS**: `test-specs/agents/l2_build-with-ai-draft-generated-from-natural-language-description_ELITEA-1906.md`.

## Behavioural overlap (why this is `extend-existing`, not fresh) — and the genuine gap

ELITEA-1912's Pass criteria are, verbatim: "the created agent reflects all edited field values, not the original generated values." Its steps decompose into two halves:

1. **Steps 1-6 + 10** — generate a draft, then edit each of the 5 fields (Name,
   Description, Instructions, Welcome message, one Chat starter) and confirm
   each accepts/displays the new value. **This half is proven, verbatim, by
   ELITEA-1906's implemented test** (`test_draft_fields_prepopulated_and_editable`,
   Step 10, `automation/tests/ui/agents/test_agent_build_with_ai.py:1460-1499`):
   it already edits Name/Description/Instructions/Welcome Message/first Chat
   starter via `.click()` + `.fill()` on the exact same testid-only locators
   this case's Preconditions/Steps reference, and re-reads each value to
   confirm the edit took. Live re-verification this run (see Test Steps)
   confirmed the identical editability contract on all 5 fields, using the
   identical testids (`generate-agent-review-name-input`,
   `-description-input`, `-instructions-input`, `-welcome-message-input`,
   `-starter-input-0`).
2. **Steps 7-8 — click "Approve"/"Create Agent", then open the created Agent
   and verify ALL fields carry the EDITED values, not the original generated
   ones.** This is **not exercised anywhere in this suite.**
   `test_draft_fields_prepopulated_and_editable` never clicks the approve
   button — it stops at Step 10's in-modal re-read (confirmed by reading the
   full method body, `automation/tests/ui/agents/test_agent_build_with_ai.py:1356-1500`,
   no `approve_button`/`click_approve_and_wait_for_agent_created()` call
   anywhere in it). The other tests in this file that DO click approve
   (`TestAgentBuildWithAISelectedResourcesAttached`'s three methods,
   ELITEA-1909/1911/1914) never edit any review-form field first — they
   approve the draft's original generated values verbatim, so none of them
   can distinguish "the created agent got the generated value" from "the
   created agent got the edited value." Live-confirmed this run (see Test
   Steps): editing all 5 fields and then clicking "Create Agent" produces a
   created agent whose Name/Description/Instructions/Welcome
   Message/first-Chat-starter are the **edited** strings, not the generated
   draft's original values — this specific persistence contract (edit-then-
   approve-carries-the-edit, not the draft) is proven nowhere else in the
   suite.

This overlap is large (steps 1-6/10 are proven, verbatim, by the exact same
testids and edit/re-read pattern) and the remaining gap is small and
self-contained (one more click + one page navigation + 5 read-only
assertions on an already-existing page object, `AgentFormPage`/
`AgentDetailPage`, reusing the `agent_api` cleanup fixture pattern
ELITEA-1909/1911/1914 already established) — hence `extend-existing` (a
continuation of the SAME test method, or a new sibling method in the same
class reusing the SAME edit helper) rather than `ready-for-automation`,
which would re-derive the entire generate+edit setup ELITEA-1906 already
built and proved.

## Preconditions
- User is logged in to Elitea (localhost `auth_state`/dev-token bypass) with
  admin/editor role sufficient to create agents — confirmed live (same
  permission finding as every prior case in this family).
- A project is selected/accessible ("UI Testing", id `400`, this run).
- **Corrected precondition (case-text drift, not a defect — same
  clarification ELITEA-1906/1915's AFS already recorded):** "An agent draft
  has been generated and the review/edit form is displayed" is accurate;
  the modal is reached via `${BASE_URL}/agents/create` → "Build with AI"
  (`generate-agent-open-button`), same entry point as the rest of this
  family.

## Test Data

### reuse-existing (no fixture creation/teardown needed beyond the created agent itself)
- Natural-language prompt (same as ELITEA-1906's Test Data, reused
  deliberately so this case's edit-then-approve behaviour is isolated from
  any prompt-content variable): `"An agent that helps write concise JIRA
  ticket descriptions"`.
- **Live (unmocked) generation** was used this run (real DEV backend call,
  resolved in well under 30s) — unlike ELITEA-1906's mocked-payload
  implementation, this case's own gap (steps 7-8) requires a REAL
  `POST .../applications/prompt_lib/{project}` create call to observe real
  persistence, so mocking the draft generation (not the create) is
  sufficient and matches the pattern ELITEA-1909/1911/1914 already use for
  their own approve-and-verify flows (draft generation may be mocked or
  live at the implementer's discretion — persistence is verified against the
  real `applications` POST either way).
- Edited values used this run (implementer may reuse literally or
  parameterize per the existing `[edited]`-suffix convention
  ELITEA-1906's test already established at
  `automation/tests/ui/agents/test_agent_build_with_ai.py:1465-1499`):
  - Name: `"<generated name> [edited]"`
  - Description: `"<generated description> [edited]"`
  - Instructions: `"<generated instructions> [edited]"`
  - Welcome message: `"<generated welcome message> [edited]"`
  - First chat starter: `"<generated starter> [edited]"`

The created agent is deleted in Cleanup — verified live via the UI's
"Delete agent" flow (typed-name confirmation dialog).

## Test Steps

1. Navigate to `${BASE_URL}/agents/create`, click **"Build with AI"**
   (`generate-agent-open-button`), enter the case's prompt, click
   **"Generate Draft"** (`generate-agent-submit-button`), wait for the
   review form (`wait_for_review_form()`).
   - **Verify**: review form renders fully populated (Name, Description,
     Instructions, Welcome Message, 4 chat starters) — confirmed live this
     run (real backend call): Name `"JIRA Ticket Writer"`, JIRA-focused
     Description/Instructions, a Welcome Message, and 4 chat starters
     (`MAX_CONVERSATION_STARTERS` hit). Identical to ELITEA-1906's own
     Step 1-4 (already covered — this AFS does not re-derive it).

2-6, 10. Edit each of the 5 fields (Name, Description, Instructions,
   Welcome Message, first Chat-starter) via `.click()` + `.fill()` on
   `generate-agent-review-name-input` / `-description-input` /
   `-instructions-input` / `-welcome-message-input` /
   `-starter-input-0`, then re-read each field's value.
   - **Verify**: each field reflects the newly typed text — confirmed live
     this run, identical mechanism and identical testids to ELITEA-1906's
     implemented Step 10 (`automation/tests/ui/agents/test_agent_build_with_ai.py:1460-1499`).
     **This half of the case is already covered — no new assertion needed
     here**, only the edited values must be retained (not re-read from the
     draft) so Step 7-8 below can assert against them.

7. Click **"Create Agent"** (`generate-agent-approve-button`).
   - **Verify** (genuinely new coverage): `POST
     /api/v2/elitea_core/applications/prompt_lib/400` resolves `201`
     — confirmed live this run, created agent id `157`. No
     `PATCH .../tool/prompt_lib/...`, `PATCH .../application_relation/prompt_lib/...`,
     or `GET`/`PATCH .../skill/prompt_lib/...` call fires (confirmed via the
     full `elitea_core` network log between the approve click and the
     detail-page landing: the only two `elitea_core` POSTs in the whole flow
     are `generate_application_draft` and `applications`) — this is a plain
     draft with no suggested resources, so
     `click_approve_and_wait_for_agent_created()` (the helper
     ELITEA-1914's implementation already added to
     `GenerateAgentModalPage`, `automation/pages/generate_agent_modal_page.py:374`)
     is the correct wait helper to reuse here — NOT
     `click_approve_and_wait_for_creation()`, which would hang waiting on
     relation calls that never fire for this scenario. The UI
     auto-navigates immediately: confirmed live,
     `/agents/all/157?destTab=configuration&name=JIRA%20Ticket%20Writer%20%5BEDITED-1912%5D&viewMode=owner`
     — note the URL's `name` query param already carries the **edited**
     name, not the generated one, an early live signal the edit was
     genuinely submitted.

8. Open the created Agent (auto-navigated) and verify ALL 5 edited fields
   persisted — **this is the case's core, previously-unproven claim.**
   - **Verify**: live-confirmed this run, reading the created agent's
     detail-page form fields directly (`AgentFormPage`/`AgentDetailPage`
     getters, same page object the rest of the suite already uses for the
     Agent detail form):
     - `get_name()` == the **edited** Name (`"JIRA Ticket Writer
       [EDITED-1912]"` this run) — page title and browser tab also read
       this edited name, not the generated one.
     - `get_description()` == the **edited** Description.
     - `get_instructions()` == the **edited** Instructions.
     - `get_welcome_message()` == the **edited** Welcome Message — also
       independently confirmed via the embedded chat's own greeting
       message (`chat_message_list`), which rendered the edited welcome
       text verbatim, a second, UI-observable confirmation channel beyond
       the form field itself.
     - The first Chat-starter input (`conversation_starter_inputs.nth(0)`)
       == the **edited** starter text — also independently confirmed via
       the embedded chat's own starter-tile UI, which rendered the edited
       starter text verbatim (same second-channel pattern as Welcome
       Message).
     - None of the 5 fields showed the ORIGINAL generated value — the
       negative half of the case's Pass criteria, live-confirmed by
       inspecting each field for the pre-edit generated text and finding
       none present.

## Expected Results
Matches the case's stated Pass criteria and Expected Final State exactly:
editing all 5 review-form fields before approval, then clicking "Create
Agent", produces a created agent whose Name, Description, Instructions,
Welcome Message, and (checked) Conversation starter carry the user-edited
values — not the original generated draft values. Live-verified end-to-end
(real backend calls, no mocking of the create step) that this is exactly
what the live product does.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: draft generated, review form displayed | review form populated | step 1 | already covered — ELITEA-1906 Steps 1-4 | already-covered (via extension target) |
| 1 Generate draft, enter review form | review form displayed with pre-populated fields | step 1 | already covered — ELITEA-1906 Steps 5-9 | already-covered |
| 2 Edit Name | Name field accepts/displays new value | steps 2-6/10 | already covered — ELITEA-1906 Step 10 (`test_agent_build_with_ai.py:1465-1470`) | already-covered |
| 3 Edit Description | Description field accepts new value | steps 2-6/10 | already covered — ELITEA-1906 Step 10 (`:1472-1477`) | already-covered |
| 4 Edit Instructions | Instructions field accepts new value | steps 2-6/10 | already covered — ELITEA-1906 Step 10 (`:1479-1484`) | already-covered |
| 5 Edit Welcome message | Welcome message field accepts new value | steps 2-6/10 | already covered — ELITEA-1906 Step 10 (`:1486-1491`) | already-covered |
| 6 Edit/remove a Conversation starter | Conversation starters field reflects the edit | steps 2-6/10 | already covered — ELITEA-1906 Step 10 (`:1493-1499`), "edit" branch only (case offers edit OR remove; edit is what ELITEA-1906 already proves and what this AFS's step 8 needs to trace through to persistence) | already-covered |
| 7 Click "Approve"/"Create Agent" | agent creation initiated with edited values | step 7 (this AFS) | `POST .../applications/...` → 201, no relation calls, URL/title already show edited name | **asserted — genuinely new** |
| 8 Open created Agent, verify all fields reflect edited values | all fields (Name, Description, Instructions, Welcome message, Conversation starters) show user-edited values | step 8 (this AFS) | `get_name()`/`get_description()`/`get_instructions()`/`get_welcome_message()`/`conversation_starter_inputs.nth(0)` == edited values, live-confirmed | **asserted — genuinely new, the case's core claim** |

### Axis 2 — Analyst additions

- Step 8 documents a **second, independent confirmation channel** for
  Welcome Message and the first Chat-starter: the embedded chat panel on
  the created agent's own detail page renders the edited Welcome Message as
  its greeting, and the edited starter text as a clickable starter tile —
  *added: gives the implementer an optional, stronger assertion (UI-visible
  rendering, not just the form-field's `input_value()`) if they want extra
  confidence beyond the form-field read; not required to satisfy the case's
  own Pass criteria, which only asks about "the created agent['s] fields."*
- Step 7 documents that a plain (no-resource) edited draft fires **only**
  the base-create POST, same finding ELITEA-1914 already made for an
  *unedited* plain draft — *added: confirms the edit itself doesn't change
  which network calls fire, so `click_approve_and_wait_for_agent_created()`
  is the correct reuse target regardless of whether the draft was edited
  first.*
- **Console side-channel finding, not filed as a new issue — already
  tracked.** The same `"does not recognize the disableUnderline prop"`
  React warning already tracked as
  [EliteaAI/elitea-testing-public#1050](https://github.com/EliteaAI/elitea-testing-public/issues/1050)
  (and already noted reproducing from this entry point by ELITEA-1906's own
  AFS) fired again this run. Not re-filed, not re-commented (ELITEA-1906's
  AFS already added the confirming comment for this exact entry point) —
  noted here only so the implementer isn't surprised by it and doesn't
  mistake it for a regression this case introduced.

**Amended during implementation (ELITEA-1912, `test_edited_fields_persist_after_approve`):**
the literal `"<generated name> [edited]"` suffix convention for the Name field
(as used verbatim by ELITEA-1906's covering test) breaks the Create Agent
button's enablement for this case's specific draft: `MAX_NAME_LENGTH = 32`
(`EliteaUI/src/common/constants.js`, enforced by
`validateAgentDraft()`/`agentDraftValidation.helpers.js`) rejects
`"JIRA Ticket Description Writer [edited]"` (39 chars, generated name is
already 30 chars) — `isDraftValid` goes `false` and
`generate-agent-approve-button` stays `disabled`, live-confirmed this run
(button click timed out with `element is not enabled`). ELITEA-1906's own
test never clicked Approve, so it never exercised this validation path. The
implementation uses a short, standalone literal (`"Edited Agent Name
[1912]"`, 25 chars) for the Name field instead — still unambiguously
distinct from the generated name (satisfying the case's "not the original
generated value" pass criterion) and within the 32-char cap. The other 4
fields (Description/Instructions/Welcome Message/first Chat starter) keep
the `"<generated value> [edited]"` suffix convention verbatim — their
validation ceilings (2304/none/768/768 chars respectively) have ample
headroom at these draft lengths. Future reuse of the Name-suffix convention
in this file should budget for `MAX_NAME_LENGTH = 32` against whatever
generated name the mocked/live draft actually returns.

## Cleanup
1. Created "JIRA Ticket Writer [EDITED-1912]" agent (id `157`, this run) —
   deleted via the UI's "Delete agent" menu action + typed-name confirmation
   dialog, confirmed via redirect away from the agent's detail page back to
   `/agents/create`. Implementer: reuse the `agent_api.delete_agent(created_agent_id)`
   `finally`-block pattern this file's other approve-and-create tests
   already use (e.g. `automation/tests/ui/agents/test_agent_build_with_ai.py:672-678`).
2. No product state left behind. Project `400` ("UI Testing") agent
   inventory is back to its pre-run baseline (live-confirmed via the
   redirect after delete-confirmation).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| "Build with AI" open button | `generate-agent-open-button` | on-`automation/testids` ✓ (pre-existing, reused by every prior case in this family) | n/a — already present |
| Prompt input | `generate-agent-prompt-input` | on-`automation/testids` ✓ | n/a — already present |
| Generate button | `generate-agent-submit-button` | on-`automation/testids` ✓ | n/a — already present |
| Review-form Name/Description/Instructions inputs | `generate-agent-review-name-input` / `-description-input` / `-instructions-input` — existing `LocatorDescriptor`s on `GenerateAgentModalPage` | on-`automation/testids` ✓ | n/a — already present |
| Review-form Welcome Message input | `generate-agent-review-welcome-message-input` — added for ELITEA-1906, existing `LocatorDescriptor` | on-`automation/testids` ✓ (added by ELITEA-1906's implementation) | n/a — already present |
| Review-form Chat-starter inputs | `generate-agent-review-starter-input-{}` template — added for ELITEA-1906, existing class constant | on-`automation/testids` ✓ | n/a — already present |
| "Create Agent" approve button | `generate-agent-approve-button` | on-`automation/testids` ✓ | n/a — already present |
| Created-agent Name/Description/Instructions/Welcome-message fields (detail page) | `AgentFormPage.name_input` / `description_input` / `instructions_input` / `welcome_message_input` — existing `LocatorDescriptor`s, existing `get_name()`/`get_description()`/`get_instructions()`/`get_welcome_message()` getters (`automation/pages/agent_form_page.py:25-403`) | on-`automation/testids` ✓ (pre-existing, used throughout the suite's non-Build-with-AI agent tests) | n/a — already present |
| Created-agent Chat-starter inputs (detail page) | `AgentFormPage.conversation_starter_inputs` — existing `LocatorDescriptor` (testid `agent-conversation-starter-input`) | on-`automation/testids` ✓ | n/a — already present |
| Delete agent flow | `AgentDetailPage.actions_menu_button` → `delete_agent_menuitem` → typed-name confirm dialog (`delete-confirm-name-input` / `delete-confirm-button`, live-confirmed testids this run) | on-`automation/testids` ✓ | n/a — already present |

**Summary for the implementer: no new `add-data-testid` work is needed.**
Every element steps 1-8 touch already carries a testid, confirmed live this
run (both the review-form inputs added for ELITEA-1906, and the created-
agent's detail-page fields, which are pre-existing and used throughout the
rest of the suite). This case is pure test-code work: extend
`test_draft_fields_prepopulated_and_editable` (or add a sibling method in
the same class) to continue past its existing Step 10 into an approve +
detail-page-read sequence, reusing `click_approve_and_wait_for_agent_created()`
(ELITEA-1914) and the `agent_api` cleanup `finally`-block pattern
(ELITEA-1909/1911/1914).

## Network Behavior
- `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/400` →
  `200` — generates the draft (mocked or live, implementer's discretion —
  see Test Data).
- `POST /api/v2/elitea_core/applications/prompt_lib/400` → `201` — creates
  the agent with the **edited** field values as the request payload (not
  independently field-by-field verified against the request body this run —
  the response/detail-page read is the case's own asserted contract, per its
  Pass criteria; an implementer wanting an additional, earlier signal could
  assert the edited values appear in this POST's request body too, but the
  case's own Pass criteria is satisfied by the created-agent read).
- `GET /api/v2/elitea_core/application/prompt_lib/400/{id}` — fires
  automatically once the detail page mounts (same pattern ELITEA-1914's AFS
  already documented), confirms the created agent is genuinely persisted.
- No toolkit/agent-relation/skill relation calls fire — same finding
  ELITEA-1914 made for an unedited plain draft, reconfirmed here for an
  edited one (see Axis 2).

## Known Defects Found During Exploration
None. All 8 case-relevant steps (1-8, with 2-6/10 already covered by
ELITEA-1906) executed live end-to-end against the real DEV backend with no
functional defect. The only side-channel finding is the already-tracked,
non-blocking `disableUnderline` console warning (see Axis 2) — not part of
this case's Pass/Fail criteria.

## Blocked Steps
None. All case steps executed live.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Home:
  `automation/tests/ui/agents/test_agent_build_with_ai.py`, class
  `TestAgentBuildWithAIDraftFieldPopulation` (extend the existing method,
  continuing past its current Step 10, OR add a new sibling method in the
  same class that repeats the generate+edit sequence and continues into
  approve+verify — implementer's call per the AFS's "Boundary call" note in
  the skill: the shared setup is small enough that either shape is
  reasonable).
- Reuse `click_approve_and_wait_for_agent_created()`
  (`automation/pages/generate_agent_modal_page.py:374`, added for
  ELITEA-1914) — NOT `click_approve_and_wait_for_creation()`, which waits on
  toolkit/agent relation calls that never fire for this plain-draft
  scenario and would hang.
- Reuse `AgentDetailPage`'s inherited `AgentFormPage` getters
  (`get_name()`, `get_description()`, `get_instructions()`,
  `get_welcome_message()`) plus `conversation_starter_inputs.nth(0).input_value()`
  for the created-agent-side assertions — no new page-object work needed.
- Cleanup: `agent_api.delete_agent(created_agent_id)` in a `finally` block,
  same pattern as ELITEA-1909/1911/1914's tests in this same file.
- Wait strategy: `wait_for_review_form()` / `click_approve_and_wait_for_agent_created()`
  / `page.wait_for_url(f"**/agents/all/{created_agent_id}**")` /
  `detail_page.wait_for_page_load()` — all already exist in the shared base,
  no fixed sleeps needed.
