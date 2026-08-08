# Test Case: Build with AI — agent draft is generated from a natural-language description (Agent)

## Metadata
- **TMS ID**: ELITEA-1906
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/agents/build_with_ai/ELITEA-1906_build-with-ai-agent-draft-generated-from-natural-language-description.md`
- **Linked Story**: none
- **Priority**: l2 (case priority: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `UI Testing` (session default at exploration time)
- **User set**: `${TEST_USER}` (localhost `auth_state`/Playwright-MCP dev token skips login; admin-equivalent role, per `.agents/profile.md` § Roles & sample users)
- **Analyst**: qa-engineer (Sage), analyst slot, batch #1298
- **Status**: ready-for-automation
- **Tracking issue**: EliteaAI/elitea-testing-public#1298 (batch tracking issue — no per-case board card)
- **Case-gate note**: source case frontmatter carries `status: draft` / `execution_type: manual` — consistent with the batch's other cases; no exclusion per `.agents/testing.md` § TMS case-gate (no excluded-status list defined for this project), so this run proceeded normally.

## Triangulation against the existing suite (why this is NOT already-covered / extend-existing)

This trunk already carries, on the `/agents/create` entry point (the same
entry point this case's Precondition specifies — "The GenerateAgentModal is
accessible from the New Agent creation page"):

- `TestAgentBuildWithAIGenerationFailureRetry` (ELITEA-1915) — a mocked
  500-then-retry flow. Its Step 6 only waits for `wait_for_review_form()`
  (back/approve buttons visible) after the retry succeeds — it never reads
  ANY review-form field value.
- `TestAgentBuildWithAISuggestedResources` (ELITEA-1907) — a mocked success
  whose assertions are scoped entirely to the Suggested Resources section
  (toolkit/mcp/pipeline/agent cards); it never reads Name/Description/
  Instructions/Welcome Message/Conversation-starters field values either.
- `TestAgentBuildWithAISelectedResourcesAttached` (ELITEA-1909/1911) —
  scoped to resource selection + post-creation attachment; same gap.

`GenerateAgentModalPage` already carries `review_name_input` /
`review_description_input` / `review_instructions_input` locators and
`get_review_name()` / `get_review_description()` / `get_review_instructions()`
getters (added in the ELITEA-1920 fix round per the page object's own
docstring comment) — but a full-suite grep confirms **none of the
`/agents/create`-entry tests above actually call them.** The only test that
calls them is `test_build_with_ai_from_chat_canvas.py`
(`TestBuildWithAIFromChatCanvas.test_build_with_ai_from_chat_canvas_adds_participant`,
covers ELITEA-1920, merged to `automation/base` at commit `485471d2`) — but
that test:
1. Triggers Build with AI from the **in-chat "+ Create New Agent" canvas**,
   not the `/agents/create` page this case's Precondition names — a
   different entry point/component instance, even though it renders the
   same shared `GenerateAgentModal`.
2. Asserts Name/Description/Instructions pre-population only — it never
   reads Welcome Message or Conversation Starters, and never exercises
   field editability (case Step 10).

Live-confirmed (see § Concrete Handles) that the review form's **Welcome
Message field and every Chat-starter input carry NO `data-testid` at all** —
this case is the first to need them, which is itself strong evidence no
existing test already proves this case's observable (an untestid'd field
cannot have been asserted via a testid-only locator anywhere in this suite).

**Verdict**: `ready-for-automation`, not `already-covered` (the 5-field
pre-population + editability observable is proven nowhere, on any entry
point) and not `extend-existing` (the nearest candidate, ELITEA-1920's test,
covers a different entry point and only 3 of 5 fields with no editability
check — extending it would mean duplicating its whole setup under a
different entry point, which is a fresh test in substance, not a small
gap-fill; per the skill's boundary call, a gap this size is routed to
`ready-for-automation`).

## Preconditions
- User is logged in to Elitea (localhost `auth_state`/dev-token bypass) with
  admin/editor role sufficient to create agents — confirmed live (same
  `PERMISSIONS.applications.update` gate documented by ELITEA-1915's AFS).
- A project is selected/accessible (`UI Testing`, this run).
- **Corrected precondition (case-text drift, not a defect — same
  clarification ELITEA-1915's AFS already recorded):** "The GenerateAgentModal
  is accessible from the New Agent creation page" is accurate as a
  precondition (the modal genuinely IS reachable from `${BASE_URL}/agents/create`
  via the General-section "Build with AI" button), so no correction is
  needed here beyond noting the entry point explicitly for the implementer.

## Test Data

### reuse-existing (no fixture creation/teardown needed)
- Natural-language prompt (case's own exact Test Data wording):
  `"An agent that helps write concise JIRA ticket descriptions"`.
- **Mocked generate-draft success payload** (deterministic, matching this
  suite's established pattern in ELITEA-1907/1909/1911/1915 — see
  `mock_generate_success()`), content plausibly aligned with the prompt's
  intent so the assertions genuinely exercise "the UI renders the generated
  draft content", not just "the UI renders some non-empty string":
  ```json
  {
    "name": "JIRA Ticket Description Writer",
    "description": "Helps users turn rough notes into concise, well-structured JIRA ticket descriptions.",
    "instructions": "You are a helpful assistant that writes concise, well-structured JIRA ticket descriptions from rough notes, bug reports, or feature ideas. Keep descriptions compact, use bullet points where helpful, and include acceptance criteria when relevant.",
    "welcome_message": "Hi! I can help you write clear, concise JIRA ticket descriptions. Paste your notes to get started.",
    "conversation_starters": [
      "Turn these notes into a concise JIRA ticket description",
      "Write a bug ticket description from this issue report"
    ],
    "suggested_toolkits": [],
    "suggested_mcp": [],
    "suggested_pipelines": [],
    "suggested_agents": [],
    "suggested_skills": []
  }
  ```
  Suggested-resource arrays are deliberately empty — `ResourceSuggestions.jsx`
  renders `null` for an empty category (already asserted by ELITEA-1907), so
  this keeps the DOM surface focused on the 5 core fields this case actually
  cares about, without re-deriving ELITEA-1907's coverage.
- Live-verified reference (not asserted, informational): a REAL (unmocked)
  generation against the DEV backend for the exact case prompt returned name
  `"JIRA Ticket Writer"`, a JIRA-ticket-focused description/instructions, a
  Welcome Message, and 4 conversation starters (hit `MAX_CONVERSATION_STARTERS`)
  — confirming the mocked payload's shape/spirit matches real backend output.
  Screenshot: `test-results/screenshots/ELITEA-1906-step-05-review-form-populated.png`.

No test data is created or persisted in the product — this case's steps stop
at the review form (case's own Expected Final State is "the review form
displays... editable before agent creation"); "Create Agent" is never
clicked. See Cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/agents/create`. In the "General" accordion
   section header, click **"Build with AI"** (`generate-agent-open-button`)
   to open the `GenerateAgentModal`.
   - **Verify**: the modal (`generate-agent-modal`) opens with the prompt
     input (`generate-agent-prompt-input`) visible. Confirmed live.

2. Enter the case's exact prompt — `"An agent that helps write concise JIRA
   ticket descriptions"` — into the prompt input.
   - **Verify**: `get_prompt_value()` returns exactly the entered text
     (confirmed live: the input field accepts and displays it verbatim),
     and `generate_button` (`generate-agent-submit-button`) transitions from
     disabled to enabled.

3. Install a `mock_generate_success()` route on
   `GENERATE_DRAFT_ROUTE` with the Test Data payload above, then click
   **"Generate Draft"** (`generate-agent-submit-button`).
   - **Verify**: the modal shows the loading state
     (`generate-agent-loading-indicator`, text `"Generating agent
     draft..."`) while the (artificially delayed) mocked response is in
     flight. Confirmed live via the real (unmocked) call — the identical
     loading state renders during a genuine multi-second generation.

4. Wait for the mocked generate-draft response to resolve and for
   `wait_for_review_form()` (`generate-agent-back-button` +
   `generate-agent-approve-button` visible) to succeed.
   - **Verify**: the loading state ends and the modal transitions to the
     review/edit form. Confirmed live (real backend run): loading ends,
     review form renders, in well under the 15s `REVIEW_FORM_TIMEOUT` this
     suite already uses for the mocked-payload tests.

5. Inspect the review form's **Name** field
   (`generate-agent-review-name-input`).
   - **Verify**: `get_review_name()` (or `expect(review_name_input)
     .to_have_value(...)`) equals the mocked payload's `name` —
     `"JIRA Ticket Description Writer"`. Live-confirmed pattern: the real
     (unmocked) run rendered a semantically-matching generated Name
     (`"JIRA Ticket Writer"`) in the identical field.

6. Inspect the review form's **Description** field
   (`generate-agent-review-description-input`).
   - **Verify**: `get_review_description()` equals the mocked payload's
     `description`. Live-confirmed pattern (real run): a non-empty,
     JIRA-relevant description rendered in the identical field.

7. Inspect the review form's **Instructions** field
   (`generate-agent-review-instructions-input`).
   - **Verify**: `get_review_instructions()` equals the mocked payload's
     `instructions`. Live-confirmed pattern (real run): a non-empty,
     multi-paragraph, JIRA-relevant instructions block rendered in the
     identical field.

8. Inspect the review form's **Welcome Message** field — **testid
   needed**, see § Concrete Handles.
   - **Verify**: the field's value equals the mocked payload's
     `welcome_message`. Live-confirmed live (real run, screenshot cited
     above): a non-empty Welcome Message rendered under the label
     `"Welcome Message"`, directly below Instructions.

9. Inspect the review form's **Chat starters** section — **testid
   needed per starter input**, see § Concrete Handles. Section only
   renders when `conversation_starters.length > 0`
   (`GenerateAgentReviewForm.jsx` — source-confirmed), which the mocked
   payload's 2-item array satisfies.
   - **Verify**: the section header `"Chat starters:"` is visible, and each
     starter input's value equals the corresponding mocked payload entry
     (2 inputs, in order). Live-confirmed live (real run): 4 starter inputs
     rendered, each pre-filled with a generated, JIRA-relevant suggestion,
     plus a live `"N/4 added."` counter and a disabled "Starter" add-button
     once the max was reached (informational — out of this case's scope,
     see § Coverage Map Axis 2).

10. For each of the 5 fields (Name, Description, Instructions, Welcome
    Message, and the first Chat-starter input), click into the field and
    replace its value with new test text (e.g. `"<original> [edited]"`),
    then re-read the field's value.
    - **Verify**: each field's value reflects the newly typed text — i.e.
      every field is genuinely editable (not disabled/readonly) and its
      change is real React-controlled state, not just a DOM-level artifact.
      Live-confirmed for the Welcome Message field: typing into it made a
      character-counter (`"N characters left"`, driven by
      `isFocused('welcome_message')` + the controlled `draft.welcome_message`
      value) appear and update live — a stronger signal than "the input's
      value attribute changed", since the counter only reacts to genuine
      component state, proving the field is wired through React state, not
      merely DOM-editable. The Name/Description/Instructions inputs use the
      identical `Input.InputBase` + `inputProps={'data-testid': ...}`
      pattern already proven `.fill()`-compatible by `fill_prompt()`'s own
      docstring (testid resolves to the native element, so plain `.fill()`
      triggers React's `onChange` correctly — no `press_sequentially()`
      workaround needed here, unlike the general MUI caution in
      `.claude/rules/mui-patterns.md`).

## Expected Results
Matches the case's stated Pass criteria and Expected Final State exactly:
the GenerateAgentModal, after a natural-language description is submitted
and generation completes, displays a fully populated review/edit form with
Name, Description, Instructions, Welcome message, and Conversation starters
— all pre-populated with generated values and all editable — before agent
creation. Live-verified end-to-end (real, unmocked backend call) that this
is exactly what the live product does; the mocked-payload version above
makes the same observable deterministic for CI.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: "GenerateAgentModal is accessible from the New Agent creation page" | modal reachable from `/agents/create` | step 1 | step 1: navigate + click Build with AI, modal opens | asserted |
| 1 Open the GenerateAgentModal | modal opens with prompt input field | step 1 | step 1: `modal.modal` + `modal.prompt_input` visible | asserted |
| 2 Enter natural-language description | input field accepts/displays entered text | step 2 | step 2: `get_prompt_value() == PROMPT_TEXT` | asserted |
| 3 Click "Generate agent" | loading state shown while generation in progress | step 3 | step 3: `loading_indicator` visible during the mocked (delayed) request | asserted |
| 4 Wait for generation to complete | loading ends, transitions to review/edit form | step 4 | step 4: `wait_for_review_form()` succeeds | asserted |
| 5 Review form pre-populated with Name | Name field has a generated value | step 5 | step 5: `get_review_name() == mocked payload name` | asserted |
| 6 Review form pre-populated with Description | Description field has a generated value | step 6 | step 6: `get_review_description() == mocked payload description` | asserted |
| 7 Review form pre-populated with Instructions | Instructions field has generated content | step 7 | step 7: `get_review_instructions() == mocked payload instructions` | asserted |
| 8 Review form pre-populated with Welcome message | Welcome message field has a generated value | step 8 | step 8: new getter against new testid == mocked payload `welcome_message` | asserted (implementer adds testid + getter) |
| 9 Review form pre-populated with Conversation starters | Conversation starters field has generated suggestions | step 9 | step 9: per-starter-input getter == mocked payload `conversation_starters[i]` | asserted (implementer adds dynamic testid + getter) |
| 10 All fields editable before approval | all pre-populated fields can be edited | step 10 | step 10: type into each of the 5 fields, re-read value, confirm it reflects the edit | asserted |

### Axis 2 — Analyst additions

- step 3/9 documents that this exact loading-state and review-form-population
  behavior was independently confirmed against a REAL, unmocked backend call
  (live exploration, this session) — *added: gives the implementer confidence
  the mocked-payload version is testing a real contract, not an invented one,
  and supplies the reference screenshot as evidence.*
- step 9 documents the live-observed `MAX_CONVERSATION_STARTERS = 4` limit
  behavior (disabled "Starter" add-button + "4/4 added." counter once
  reached) — *added: out of this case's own scope (the case only requires
  starters to be pre-populated and editable, not exhaustively at the limit),
  but useful precedent for a future starter-limit-specific case.*
- step 10 documents the character-counter side-effect as a stronger-than-
  literal editability signal (proves controlled-state wiring, not just DOM
  mutation) — *added: a more rigorous editability assertion than the case's
  own literal wording asks for, recommended because a `.fill()` that only
  changes the DOM attribute without touching React state would otherwise
  pass a naive `input_value()` check while failing to prove real
  editability — this project's `Input.InputBase` fields do NOT have this
  failure mode (native-element testid wiring), but asserting the visible
  counter increments is a cheap extra confirmation worth keeping.*
- **Console side-channel finding, not filed as a new issue — already
  tracked.** A React `"does not recognize the disableUnderline prop"`
  warning fires on every review-form field render (confirmed via CDP
  console capture during this exploration). This is the exact same root
  cause already tracked as
  [EliteaAI/elitea-testing-public#1050](https://github.com/EliteaAI/elitea-testing-public/issues/1050)
  (filed against the chat-canvas entry point's identical
  `GenerateAgentReviewForm.jsx` / shared `Input.InputBase` component) — same
  object (shared `InputBase.jsx` leak), same trigger (review form render),
  same expected/actual. Per dedup policy this was **not** re-filed; instead
  a confirming comment was added to #1050 noting it also reproduces from the
  `/agents/create` entry point (not just chat canvas), consolidating
  evidence for the "reproducible on ANY caller" hypothesis #1050 already
  raises. **Implementer note:** this is a pre-existing, already-tracked,
  non-blocking console warning — do not let it block this case's gate (it
  is not a new/blocking defect this case introduces or must wait on).

## Cleanup
1. No product state is created — "Create Agent"/`approve_button` is never
   clicked in this AFS (matches the case's own Expected Final State, which
   stops at the populated, editable review form). Closing the modal (not a
   case step) fully resets local state per `GenerateEntityModal.jsx`'s
   `handleClose`, same as documented in ELITEA-1915's AFS.
2. No API/DB cleanup fixture needed for this case as scoped.
3. The mocked route (`mock_generate_success()` / `page.route(...)`) is
   scoped to the test's own browser context/page — no explicit teardown
   needed beyond the normal per-test fixture lifecycle, same pattern already
   used by ELITEA-1907/1909/1911/1915's tests in this file.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| "Build with AI" open button | `generate-agent-open-button` — existing `LocatorDescriptor` on `GenerateAgentModalPage.open_button` | n/a — already present |
| Modal container | `generate-agent-modal` — existing `LocatorDescriptor.modal` | n/a — already present |
| Prompt input | `generate-agent-prompt-input` — existing `LocatorDescriptor.prompt_input` | n/a — already present |
| Generate button | `generate-agent-submit-button` — existing `LocatorDescriptor.generate_button` | n/a — already present |
| Loading indicator | `generate-agent-loading-indicator` — existing `LocatorDescriptor.loading_indicator` | n/a — already present |
| Review-form Name input | `generate-agent-review-name-input` — existing `LocatorDescriptor.review_name_input` (unused by any `/agents/create`-entry test until this case) | n/a — already present |
| Review-form Description input | `generate-agent-review-description-input` — existing `LocatorDescriptor.review_description_input` | n/a — already present |
| Review-form Instructions input | `generate-agent-review-instructions-input` — existing `LocatorDescriptor.review_instructions_input` | n/a — already present |
| Review-form **Welcome Message** input (`GenerateAgentReviewForm.jsx:162-187`) | **testid needed** — source-confirmed ZERO `inputProps`/`data-testid` on this `Input.InputBase` (unlike Name/Description/Instructions, which already carry one). Suggested name: `generate-agent-review-welcome-message-input`, wired the identical way as the Name field: `inputProps={{ 'data-testid': 'generate-agent-review-welcome-message-input' }}` | `page.get_by_label("Welcome Message")` — exploration only, not for automated tests per locator policy |
| Review-form **Chat starter** inputs (`GenerateAgentReviewForm.jsx:193-221`, one per array index) | **testid needed** — source-confirmed ZERO testid on the per-index `Input.InputBase`. Per this project's dynamic-testid convention (`.agents/testing.md` § Locator policy), suggested class-level template: `generate-agent-review-starter-input-{}` → `generate-agent-review-starter-input-0`, `-1`, … wired via `inputProps={{ 'data-testid': \`generate-agent-review-starter-input-${index}\` }}` | n/a — exploration confirmed the section/inputs exist via accessibility snapshot only (no stable non-testid handle for a specific index; siblings are visually identical) |
| "Back to prompt" / "Create Agent" buttons | `generate-agent-back-button` / `generate-agent-approve-button` — existing `LocatorDescriptor`s, used only for `wait_for_review_form()` in this case | n/a — already present |

**Summary for the implementer / `add-data-testid`:** 2 new testids needed,
both additive `inputProps` wiring on already-testid'd sibling fields in the
same component (`GenerateAgentReviewForm.jsx`) — mechanically identical to
the existing Name/Description/Instructions wiring, so low risk. Scope
discipline per `.agents/role-overrides.md`: only the Welcome Message input
and as many starter-input indices as this test's mocked payload actually
uses (2, matching the Test Data payload above) need testids — do NOT
blanket-wire all `MAX_CONVERSATION_STARTERS` (4) index slots if only 2 are
exercised by this test's own code path.

## Network Behavior
- `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/{project_id}`
  — same sole endpoint documented by ELITEA-1915's AFS. This case mocks it
  (200 + the Test Data payload above) rather than hitting the real backend,
  for CI determinism — matching ELITEA-1907/1909/1911/1915's established
  pattern in this file.
- Real (unmocked) reference call made during this exploration for the
  case's exact prompt resolved 200 in well under 30s, with a response body
  shape (`name`, `description`, `instructions`, `welcome_message`,
  `conversation_starters`, plus empty `suggested_*` arrays for this prompt)
  matching what the mocked payload above encodes.

## Known Defects Found During Exploration
None blocking. See § Coverage Map Axis 2 for the already-tracked, non-
blocking `disableUnderline` console warning (issue #1050 — confirming
comment added, not re-filed).

## Blocked Steps
None. All 10 case steps were executed end-to-end live against the real DEV
backend (Steps 1-9 with genuine generated content; Step 10's editability
confirmed on the Welcome Message field via the character-counter signal —
see Axis 2). This AFS is `ready-for-automation` for all 10 steps; the only
implementer prerequisite is the 2 new testids in § Concrete Handles.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Home:
  `automation/tests/ui/agents/test_agent_build_with_ai.py` (existing file —
  add a new test class, e.g. `TestAgentBuildWithAIDraftFieldPopulation`,
  alongside the existing `TestAgentBuildWithAIGenerationFailureRetry` /
  `TestAgentBuildWithAISuggestedResources` / `TestAgentBuildWithAISelectedResourcesAttached`
  classes — same module, same fixtures/imports, same
  `mock_generate_success()` pattern, new payload constant e.g.
  `FIELD_POPULATION_DRAFT_PAYLOAD`).
- Page object: extend `automation/pages/generate_agent_modal_page.py`'s
  `GenerateAgentModalPage` with:
  - `review_welcome_message_input = LocatorDescriptor(testid="generate-agent-review-welcome-message-input", ...)`
    + `get_review_welcome_message()` getter, mirroring the existing
    `get_review_name/description/instructions()` trio exactly.
  - A class-level dynamic-testid template constant, e.g.
    `REVIEW_STARTER_INPUT = '[data-testid="generate-agent-review-starter-input-{}"]'`
    (per `.agents/testing.md` § Locator policy's dynamic-testid pattern),
    plus a `get_review_starter(index)` getter using
    `self.page.locator(self.REVIEW_STARTER_INPUT.format(index))`.
- Editability assertions: `.click()` + `.fill(new_text)` on each field
  (native-element testid wiring makes plain `.fill()` React-correct here,
  per `fill_prompt()`'s own docstring — no `press_sequentially()` needed),
  then re-read via the corresponding getter and assert the value changed to
  the new text.
- Wait strategy: `expect_generate_response()` / `wait_for_review_form()`
  (both already exist in the shared base) — no fixed sleeps.
- This test does NOT need `agent_api` cleanup (no agent is created) — same
  as ELITEA-1907/1915's tests in this file.
