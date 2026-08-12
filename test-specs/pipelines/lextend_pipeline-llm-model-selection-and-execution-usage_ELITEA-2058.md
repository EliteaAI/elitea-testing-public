# Test Case: Pipeline — LLM Model Selection in Chat Panel

## Metadata
- **TMS ID**: ELITEA-2058
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer, batch `pipelines-remaining-w5`
- **Status**: **extend-existing**

## Extension target

**Covering spec**: `automation/tests/ui/pipelines/test_pipeline_execution.py`,
class `TestExecutePipelineStreaming`, method
`test_long_response_streams_progressively`, Step 2 block (lines ~308–316)
+ Step 5 block (lines ~354–367), merged onto this batch's trunk
`tests/batch-pipelines-remaining-w5` (originating commit `59d6987e`, merge
`eb928bf9` — ELITEA-2017). Confirmed present via
`git merge-base --is-ancestor eb928bf9 HEAD` on this session's checkout
(not yet on `origin/automation/base` — qualifies under the batch's
merged-target rule: extend-existing may target a spec already on this
batch's own trunk).

**Behavioural overlap (what's already proven), live-reconfirmed this
session** (pre-existing pipeline `test-pipeline`, id `6938` — LLM-entry
node, TASK `Fixed`/empty; used read-only for this exploration, no state
changed on it):

- Click the model button to open the dropdown (case Step 4) — covered by
  the existing `pipelines.open_model_selector()` call.
- Select a different model, e.g. "GPT-5 mini" (case Step 5) — covered by
  the existing `pipelines.select_llm_model(self.MODEL_DISPLAY_NAME)` call.
- Verify the closed selector's label updates to the newly selected model
  (case Step 6) — covered by the existing
  `assert pipelines.get_selected_model_name() == self.MODEL_DISPLAY_NAME`.
- Precondition "at least two models available" — reconfirmed live: the
  open dropdown lists 15+ models (Anthropic Claude 4.5/4.6 Sonnet, Claude
  Haiku 4.5, Claude Sonnet 5, three Azure variants, GPT-5 mini, GPT-5.2,
  GPT-5.4, GPT-5.4-mini, …).

**The gap (why this isn't `already-covered`).** Three case elements have
NO assertion anywhere in the covering spec:

1. **Case Step 2** — "locate the Model Selector Menu group; selector
   button is visible" is never asserted; the existing test calls
   `open_model_selector()` directly without first confirming the closed
   selector is visible.
2. **Case Step 3** — "verify current model is displayed" (i.e. the
   DEFAULT model, before any switch) is never captured or asserted; the
   existing test goes straight to selecting "GPT-5 mini" without reading
   what was shown beforehand.
3. **Case Step 7 — the substantive gap** — "Execute pipeline — verify
   response uses the selected model" has **no assertion at all**. The
   existing test's Step 5 checks the final response's *length*
   (`> 200` chars) and Step 6 checks for console/network errors, but
   never reads *which model* actually produced the response. A pipeline
   that silently ignored the user's model selection and always ran the
   node's configured default model would pass the covering spec
   unnoticed.

**Live confirmation this session (fills the gap, proves the assertions
are meaningful, not speculative):**

- Opened `test-pipeline` (id `6938`, pre-existing LLM-entry pipeline) in
  the embedded chat panel. The closed selector showed
  **"Anthropic Claude 4.5 Sonnet"** before any interaction — confirmed via
  a fresh accessibility snapshot (`group "Model Selector Menu"` →
  `button` → `paragraph: Anthropic Claude 4.5 Sonnet`). Matches the
  case's own hedged Test Data wording ("Anthropic Claude 4.6 Sonnet (or
  current default)") — the live default is 4.5, not 4.6; the case
  anticipates this variance explicitly ("or current default"), so this is
  **not** case-text drift needing a CLARIFICATION ticket.
- Opened the dropdown, selected "GPT-5 mini" — closed selector's label
  updated to "GPT-5 mini" (confirmed via snapshot), matching the existing
  covering-spec assertion's shape.
- Sent a message ("Hello") and waited ~6s for the response. The
  response's model-attribution chip —
  `[data-testid="chat-answer-model-chip"]` — rendered with text
  **"GPT-5 mini (LLM1)"** (confirmed via `browser_run_code_unsafe`:
  `count == 1`, `textContent == "GPT-5 mini (LLM1)"`). This is the direct,
  concrete proof that pipeline execution used the model the user selected
  in the chat panel — exactly case Step 7's expected result — and it is
  currently unasserted anywhere in the suite.
- Zero console errors and zero failed (≥400) network requests across the
  whole live sequence (open selector → select → send → response). (Two
  console errors DID appear during this session, both from an unrelated,
  earlier cross-origin `fetch()` probe attempt made by this analyst
  outside the app's own code path — not part of the case flow, not a
  product defect; see § Known Defects.)

**Testid provenance** (fresh `git fetch origin` + `git grep` on both refs
in the `EliteaUI` clone, 2026-08-09):

| Testid | on `main` | on `automation/testids` |
|---|---|---|
| `model-selector-button` | ✓ | ✓ |
| `model-selector-name` | ✓ | ✓ |
| `model-selector-option-{slug}` (dynamic) | — | ✓ |
| `chat-answer-model-chip` | — | ✓ |

Both testids-only rows are the SAME pending-promotion set the ELITEA-2017
AFS already flagged — not a fresh gap, and both are usable today since
localhost serves `automation/testids`. **No new `add-data-testid` work is
required for this case.**

**`PipelineDetailPage` gap**: it has `model_selector_button`/
`model_selector_name`/`open_model_selector()`/`select_llm_model()`/
`get_selected_model_name()` (added by the ELITEA-2017 implementation) but
**no `answer_model_chip` field or getter** — mirror
`ChatPage.answer_model_chip` (`chat_page.py:620`,
`testid="chat-answer-model-chip"`) exactly; `PipelineDetailPage`'s
embedded chat renders through the identical shared component chain
(`ApplicationAnswer.jsx`/`ActionView.jsx`), confirmed live this session
and previously by ELITEA-2017/2052/2053.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on
  localhost).
- A pipeline is open with a chat panel visible — satisfied by the
  covering spec's own `pipeline_with_fstring_llm_id` fixture + navigation
  (unchanged).
- At least two models are available for selection — reconfirmed live (15+
  models in the dropdown).

## Test Data
- Reuses the covering spec's existing test data verbatim:
  `USER_PROMPT = "Write a 500-word essay on AI"`,
  `MODEL_DISPLAY_NAME = "GPT-5 mini"`,
  `MIN_RESPONSE_LENGTH = 200`. No new fixture needed.

## Test Steps

(Steps map onto the *existing* test's flow — the implementer inserts the
new assertions immediately before the existing Step 2 block and
immediately after the existing Step 5 block; all other steps are
unchanged.)

1. Pipeline with LLM entry node is created and ready for execution
   (covering spec's existing Step 1, unchanged). **Verify**: pipeline is
   loaded, chat panel visible (case Step 1, already satisfied).
2. **[GAP — new assertion, inserted before the existing Step 2 block]**
   Before opening the selector, assert
   `pipelines.model_selector_button.is_visible()` (case Step 2 — "Model
   Selector Menu" group/button is visible) and capture
   `default_model = pipelines.get_selected_model_name()`, asserting it is
   non-empty (case Step 3 — "current model is displayed"). Confirmed live:
   `"Anthropic Claude 4.5 Sonnet"`.
3. Click the model button to open the dropdown; select "GPT-5 mini"
   (covering spec's existing Step 2, unchanged). **Verify**: closed
   selector's label updates to "GPT-5 mini" (case Steps 4–6, already
   satisfied).
4. Send "Write a 500-word essay on AI"; wait for the progressively-
   streamed response to settle (covering spec's existing Steps 3–5,
   unchanged). **Verify**: response streams progressively, settles at
   > 200 chars (case's own execution mechanics, already satisfied —
   incidental to case Step 7, not itself part of it).
5. **[GAP — new assertion, inserted immediately after the existing Step 5
   response-length assertion]** Read
   `pipelines.answer_model_chip.text_content()` (new field/getter) and
   assert it contains `MODEL_DISPLAY_NAME` ("GPT-5 mini"). Confirmed live:
   chip text `"GPT-5 mini (LLM1)"` — `"GPT-5 mini" in chip_text` is
   `True`. **Verify**: response was produced using the SELECTED model,
   not the pipeline's original default (case Step 7 — the case's core
   assertion).
6. No timeout or error occurs during streaming (covering spec's existing
   Step 6, unchanged). **Verify**: zero console errors, zero failed
   (≥400) requests (already satisfied).

## Expected Results
- Steps 1, 3, 4, 6: unchanged from the existing covering spec — still
  pass.
- Step 2 (gap): the Model Selector Menu button is visible and shows a
  non-empty default model name before any interaction — confirmed live
  (`"Anthropic Claude 4.5 Sonnet"`).
- Step 5 (gap): the settled AI response's model-attribution chip names
  the model the user selected ("GPT-5 mini"), proving execution used the
  selected model, not the pipeline's prior default — confirmed live
  (`"GPT-5 mini (LLM1)"`). No product defect found.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | step 1 | `auth_state` fixture (existing) | asserted (existing) |
| Precondition: pipeline open, chat panel visible | — | step 1 | covering spec's existing fixture + navigation | asserted (existing) |
| Precondition: ≥2 models available | — | step 3 | live dropdown lists 15+ models (reconfirmed this session) | asserted (existing, reconfirmed) |
| 1 Open a pipeline → Pipeline loaded, chat panel visible | pipeline loaded | step 1 | covering spec's existing Step 1 | asserted (existing) |
| 2 Locate "Model Selector Menu" group → selector button visible | button visible | step 2 | **NEW**: `model_selector_button.is_visible()` | **gap — needs new assertion** |
| 3 Verify current model displayed → current model name shown | non-empty model name shown | step 2 | **NEW**: `get_selected_model_name()` captured before switching, asserted non-empty | **gap — needs new assertion** |
| 4 Click model button → dropdown opens | dropdown opens | step 3 | covering spec's existing `open_model_selector()` | asserted (existing) |
| 5 Select a different model → different model selected | model selected | step 3 | covering spec's existing `select_llm_model("GPT-5 mini")` | asserted (existing) |
| 6 Verify model button label updates → shows newly selected model | label updates | step 3 | covering spec's existing `assert get_selected_model_name() == MODEL_DISPLAY_NAME` | asserted (existing) |
| 7 Execute pipeline — verify response uses selected model → execution uses selected model | response attributable to selected model | step 5 | **NEW**: `answer_model_chip` text contains `MODEL_DISPLAY_NAME` | **gap — needs new field/getter + assertion (the core gap)** |
| Expected Final State: selector allows changing model; reflected in label; used for execution | — | steps 2, 3, 5 | as above | asserted once gap assertions land |
| Pass/Fail: selector opens, allows selection, updates label, selected model used for execution | — | all steps | as above | asserted once gap assertions land |

Disposition key: `asserted` / `already-covered` / `clarification` /
`blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Captured the live DEFAULT model name before any switch
  ("Anthropic Claude 4.5 Sonnet") — *added: the case's own Test Data
  table names "Anthropic Claude 4.6 Sonnet (or current default)"; live
  default is 4.5, and the case's own hedge ("or current default") means
  this is expected variance, not case-text drift — noted for the
  implementer so the gap assertion doesn't hardcode a specific default
  name, only that one is present.*
- Confirmed console/network cleanliness across the whole live sequence
  (open selector → select → send → response) — *added: standard
  side-channel discipline; zero errors/failed requests during the case's
  own flow.*
- Cross-checked the model-chip testid's exact rendered text shape
  (`"GPT-5 mini (LLM1)"`, i.e. `"<model> (<node id>)"`) — *added: informs
  the gap assertion's exact form (`in`, not `==`, since the chip also
  embeds the node id).*

## Cleanup
- No new test data is created by the gap assertions — they extend the
  existing test's flow, which already manages its own fixture teardown
  (`pipeline_with_fstring_llm_id`, unchanged).
- This analyst's own live exploration used a pre-existing pipeline
  (`test-pipeline`, id `6938`) read-only — sent one throwaway "Hello"
  message via its chat panel, did not modify its configuration, and did
  not delete it (it predates this session and belongs to another case's
  cleanup responsibility, if any).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text
fallback ladder (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Model Selector Menu (closed button + label) | `model-selector-button` / `model-selector-name` | on-main ✓ | Existing `PipelineDetailPage.model_selector_button`/`model_selector_name` (added by ELITEA-2017). |
| Model option in open dropdown (dynamic) | `model-selector-option-{model-slug}` | on-`automation/testids` only (awaiting human promotion) | Existing `PipelineDetailPage.MODEL_SELECTOR_OPTION_ANY_SELECTOR` class constant. |
| AI response's model-attribution chip | `chat-answer-model-chip` | on-`automation/testids` only (awaiting human promotion) | **`PipelineDetailPage` has NO field/getter for this yet** — implementer adds `answer_model_chip = LocatorDescriptor(testid="chat-answer-model-chip")` + a `get_answer_model_chip_text()` getter, mirroring `ChatPage.answer_model_chip` (`chat_page.py:620`) exactly. |
| Embedded chat message input / send | `chat-message-input` / `chat-send-button` | on-main ✓ | Existing, unchanged. |

## Network Behavior
- Unchanged from the covering spec: message send → `POST
  .../conversations/prompt_lib/399` (`201`) → `PUT
  .../conversation/prompt_lib/399/{id}` (`200`); token stream over
  WebSocket. Reconfirmed live this session with zero failed (≥400)
  requests during the case's own flow.

## Known Defects Found During Exploration
- **[NOT a defect]** This analyst's own exploratory attempt to create a
  disposable pipeline via a direct cross-origin `fetch()` from the
  browser page context (`https://dev.elitea.ai/api/v2/...` called
  directly from `localhost:5173`, bypassing the Vite dev proxy) failed
  with a CORS preflight error (`net::ERR_FAILED`, "Redirect is not
  allowed for a preflight request"). This is expected — the app's own
  code always calls same-origin (`http://localhost:5173/api/v2/...`),
  which the dev server proxies through; this analyst's probe simply
  didn't use that proxy. Not a product defect; not part of the case's
  own flow. Recorded so a future analyst doesn't waste time re-diagnosing
  the same non-issue — reuse the UI-driven pipeline-creation flow (as
  ELITEA-2017's AFS does) or drive an existing disposable pipeline
  instead of a raw cross-origin fetch.
- No functional product defect found.

## Blocked Steps
None. All 7 case steps were traced end-to-end — 4 already satisfied by
the covering spec (reconfirmed live), 3 filled by new gap assertions
(also confirmed live this session, not merely proposed).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Insert the Step 2 gap assertions (button-visible + default-model-
  captured) immediately before the covering spec's existing "Step 2 —
  Select a model..." `allure.step` block; insert the Step 7 gap assertion
  (`answer_model_chip` contains `MODEL_DISPLAY_NAME`) immediately after
  the existing "Step 5 — Verify the final response..." block, before
  Step 6's error checks. Renumber/re-word the existing `allure.step`
  labels only as needed to keep them accurate (e.g. the existing "Step 2"
  becomes "Step 2 — Select a model..." preceded by a new "Step 2a" or
  folded into an expanded "Step 2" that first asserts the button/default,
  then selects) — implementer's call, as long as every step still reaches
  the Allure report per `.agents/testing.md` § Step reporting.
- The new `answer_model_chip` field/getter belongs on `PipelineDetailPage`
  near the existing model-selector methods (`pipeline_detail_page.py`
  around line 6260) — mirror `ChatPage.answer_model_chip` exactly, do not
  invent a new pattern.
- No new `add-data-testid` work required — both testids the gap
  assertions need already exist on `automation/testids` (see § Extension
  target provenance table).
- Wait strategy: condition-based only, never a fixed `sleep()`. The chip
  assertion should read `answer_model_chip` only after the existing
  `wait_for_embedded_chat_response()` call (Step 5) has already confirmed
  the response is stable — reading it earlier risks the chip not having
  rendered yet mid-stream.
