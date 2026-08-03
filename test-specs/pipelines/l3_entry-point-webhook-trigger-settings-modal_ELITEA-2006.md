# Test Case: Entry Point Node — Webhook Trigger Settings Modal

## Metadata
- **TMS ID**: ELITEA-2006
- **Priority**: l3 (medium — see ELITEA-2005 AFS Metadata for the medium→p2 convention citation)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-03 (cluster dispatch with ELITEA-2005/2007/2008)
- **Status**: ready-for-automation
- **surface_key**: `pipeline-entry-point-trigger`

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline exists with an entry point node and no HITL/Printer/interrupts — satisfied by the
  existing `pipeline_with_llm_id` fixture (same as ELITEA-2005; see that AFS for the seeding
  gotcha re: why the multi-node helper must NOT be used).

## Test Data
| Field | Value |
|-------|-------|
| Webhook types | GitHub, GitLab, Custom |

## Test Steps

1. Use `pipeline_with_llm_id` (single LLM-node pipeline). Navigate to the detail page, wait for
   canvas, click the "LLM 1" node.
   - **Verify**: pipeline ready with a single entry point node (same as ELITEA-2005 step 1/2).
2. Select "Webhook" from the Trigger dropdown (see ELITEA-2005 § Concrete Handles for the
   combobox/option locators — identical mechanism, reused here).
   - **Verify**: Trigger dropdown updates to "Webhook" (eventually — see § Quirks re: the
     immediate-read staleness already documented in the ELITEA-2005 AFS).
3. Verify the "Webhook settings" modal (`role="dialog"`) opens with all of: Webhook Type radio
   buttons (GitHub, GitLab, Custom) with GitHub selected by default; Description text; Webhook
   URL read-only field with copy button; Secret Value masked field with eye/copy/refresh buttons
   and helper text; Payload Format description; Example Request code block with copy button;
   Cancel/Apply buttons.
   - **CRITICAL TIMING NOTE, confirmed live and reproducible every run**: the modal renders
     IMMEDIATELY on selection (before its own data has loaded) showing ONLY "Webhook Type" radios
     + description + "Payload Format" text + Cancel/Apply — the "Webhook URL", "Secret Value", and
     "Example Request" sections are **entirely ABSENT from the DOM** at this point (not hidden,
     not loading-skeletoned — simply not rendered, because `PipelineWebhookModal.jsx` conditionally
     renders them only `if (webhookUrl)` / `if (secretValue)`, and those props are sourced from
     `useGetPipelineTriggerQuery`'s cached data, which has not yet refetched with the fresh
     webhook config the immediately-preceding `PUT .../trigger` just created). Confirmed live: the
     3 missing sections consistently appear within ~1.5–4.5s (repeated 3× this session, all
     resolved within that window) once the GET completes. **This is a real, reproducible product
     timing gap — the modal shows no loading indicator for the missing sections, they just
     silently pop in** — but it is NOT classified as a defect against this case, because the case's
     own Pass/Fail criteria ("the modal contains all required elements") does not specify a time
     bound, and the elements DO appear correctly, just after a short delay. **Automation MUST
     wait for the "Webhook URL" text (or its testid once added) to appear before asserting the
     full field inventory** — asserting immediately after modal-open WILL flake/fail intermittently
     depending on backend GET latency. See § Known Defects for the CLARIFICATION filed on this.
   - **Verify (once settled)**: all 6 named element groups present. GitHub radio checked by
     default (`aria-checked`/MUI-checked-icon state). Description reads "Uses x-hub-signature-256
     header with HMAC-SHA256 signature" for GitHub. Webhook URL input value:
     `{origin}/api/v2/elitea_core/webhook/prompt_lib/{project_id}/{pipeline_id}/github` (confirmed
     exact live value: `http://localhost:5173/api/v2/elitea_core/webhook/prompt_lib/399/{id}/github`).
     Secret Value input shows masked dots (`•` × secret length) by default, with adjacent
     eye/copy/refresh icon buttons.
4. Switch Webhook Type to "GitLab".
   - **Verify**: URL updates to `.../gitlab` (confirmed live: exact suffix swap, everything else
     of the URL unchanged); description updates to "Uses x-gitlab-token header with secret token"
     (confirmed live via full modal text dump).
5. Switch to "Custom".
   - **Verify**: URL updates to `.../custom` (confirmed live); description updates to "Uses
     X-Webhook-Token header with secret token" (confirmed live).
6. Click "Apply".
   - **Verify**: modal closes (`role="dialog"` count → 0); Trigger combobox shows "Webhook"
     (confirmed live, immediate read after Apply is reliable — unlike after Cancel, Apply fires
     its own fresh `updateTrigger` mutation with the currently-selected webhook type, so the
     resulting state is not dependent on the earlier GET's timing the way step 3's field
     population was).
7. Save pipeline — reload — verify Webhook trigger persists.
   - **CLARIFICATION (reverse-masking guard, same as ELITEA-2005 row 5/7)**: there is no
     meaningful "Save pipeline" action for trigger state — the pipeline-level Save button stays
     disabled after a trigger change (trigger persists via its own endpoint on selection/Apply,
     confirmed live). Reload directly.
   - **Verify**: after reload, Trigger combobox reads "Webhook" — confirmed live,
     `TRIGGER_AFTER_APPLY` → `TRIGGER_AFTER_RELOAD` both read "Webhook" in a clean run (no Cancel
     involved, so no staleness).

## Expected Results
- The Webhook settings modal contains all case-listed elements, but populates them in TWO waves:
  an immediate wave (Webhook Type radios, description, Payload Format, Cancel/Apply) and a
  delayed wave (~1.5–4.5s later: Webhook URL, Secret Value, Example Request) as a secondary GET
  resolves. Automation must wait for the delayed wave before asserting the full inventory.
- Switching Webhook Type updates both the URL (path suffix swap: `/github` ↔ `/gitlab` ↔
  `/custom`) and the description text, live, with no additional network round-trip (both are
  derived client-side from `selectedWebhookType` + the already-fetched `webhookUrl` base).
- Apply persists the selected webhook type/sub-type; the change survives a full page reload.
- The pipeline-level Save button is NOT involved in trigger persistence at all.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: pipeline with entry point, no HITL/Printer/interrupts | setup exists | step 1 | step 1 | asserted |
| 1 Create pipeline with entry point node | Pipeline ready | step 1 | step 1 | asserted — via fixture, not raw UI create |
| 2 Select "Webhook" from Trigger dropdown | Dropdown updates to Webhook | step 2 | step 2 | asserted |
| 3 Verify Webhook settings modal opens with all listed elements | All elements present | step 3 | step 3: full field inventory after settle-wait | asserted — **CLARIFICATION: elements render in two timing waves, not all-at-once; case text implies instantaneous full presence. Automation must wait for the second wave. Not classified as a product defect against this case's Pass/Fail criteria (elements DO eventually appear correctly) — filed as a lower-severity CLARIFICATION so the timing gap is on record (see § Known Defects) since it IS a real, reproducible UX rough edge (no loading indicator) even though it doesn't fail this case.** |
| 4 Switch to GitLab — URL/description update | URL and description reflect GitLab | step 4 | step 4: input value + text | asserted |
| 5 Switch to Custom — URL updates | URL reflects Custom | step 5 | step 5: input value + text | asserted |
| 6 Click Apply — modal closes, Trigger shows Webhook | Modal closes, Webhook shown | step 6 | step 6 | asserted |
| 7 Save — reload — Webhook trigger persists | Trigger persists | step 7 | step 7: post-reload combobox text | asserted — same "Save" clarification as ELITEA-2005 |
| Expected Final State: modal fully functional, type switching updates URL/description, persists after reload | — | steps 3–7 | steps 3–7 | asserted |
| Pass/Fail: all steps complete without errors; modal has all elements, type switching works, persists | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 3 adds an explicit two-wave timing model (immediate fields vs delayed fields) that the
  case text does not distinguish — *added because a naive automated implementation that asserts
  the full field inventory right after the dialog becomes visible WILL be flaky (confirmed: the
  gap is consistently 1.5–4.5s across 3 repeated live runs this session, well beyond typical
  Playwright default-timeout margins if the assertion race loses), and because this timing gap
  is itself worth a CLARIFICATION filing per § Known Defects — leaving it undocumented would mean
  the next person to touch this area rediscovers the same flake from scratch.*
- Step 6's Apply-vs-Cancel reliability distinction is called out explicitly (Apply's resulting
  combobox read is immediately reliable; Cancel's is not, per the ELITEA-2005 AFS's shared
  Quirks) — *added so the implementer doesn't accidentally copy an assertion pattern from a
  Cancel-flow test (if one exists) onto this Apply-flow test and get confused by the different
  reliability characteristics.*

## Cleanup

1. All pipelines created via `pipeline_with_llm_id` (function-scoped, auto-deletes in teardown).
   No manual cleanup needed — confirmed clean teardown across every run this session.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| Trigger combobox | see ELITEA-2005 § Concrete Handles (shared) | same |
| Webhook Type radio group (GitHub/GitLab/Custom) | `dialog.locator('input[type="radio"]')` — 3 elements, `value="github"/"gitlab"/"custom"` on the native `<input type="radio">`, DOM order matches display order | **NO `data-testid` — flag to `add-data-testid`.** The underlying `Checkbox.RadioButtonGroup` component (`EliteaUI/src/[fsd]/shared/ui/checkbox/RadioButtonGroup.jsx`) ALREADY accepts a `testId` prop that auto-derives PER-ITEM testids as `${testId}-${item.value.toLowerCase()}` (e.g. `pipeline-webhook-type-radio-github`) — confirmed via source read, zero new component code, just pass `testId="pipeline-webhook-type-radio"` at the `<Checkbox.RadioButtonGroup .../>` call site in `PipelineWebhookModal.jsx`. |
| Webhook URL input | `dialog.locator('input[type="text"]').nth(0)` (first non-radio text input, once the delayed field wave has rendered) — **NOT `dialog.locator("input").first`**, which resolves to the FIRST radio input instead (confirmed live — a naive `.first` selector silently reads a radio's `value` attribute, e.g. `"github"`, instead of the URL) | **NO `data-testid` on the actual `<input>` element — flag to `add-data-testid`.** `FormInput` (`EliteaUI/src/components/FormInput.jsx`) spreads `...props` onto MUI `TextField`, and a bare `data-testid` prop on `TextField` lands on the OUTER wrapper div, not the inner `<input>` (standard MUI behavior) — the call site needs `inputProps={{ 'data-testid': 'pipeline-webhook-url-input' }}`, same pattern already used for `InputMappingItem.jsx` per the `_surface.md` digest, NOT a bare `data-testid` prop. |
| Webhook URL copy button | icon-only `IconButton` next to the URL field, `<ContentCopyIcon>` inside | **NO `data-testid`.** Recommended: `pipeline-webhook-url-copy-button`. Plain MUI `IconButton` — `data-testid` prop lands correctly since `IconButton` (unlike `TextField`) forwards it straight to the underlying `<button>`. |
| Secret Value input | `dialog.locator('input[type="text"]').nth(1)` (second non-radio text input, once rendered) — value is masked dots by default | **NO `data-testid`.** Same `inputProps={{'data-testid': ...}}` fix as the URL field. Recommended: `pipeline-webhook-secret-input`. |
| Secret Value eye/copy/refresh buttons | 3 `IconButton`s in DOM order after the Secret input: `VisibilityIcon`/`VisibilityOffIcon` (toggle), `ContentCopyIcon` (copy), `RefreshIcon` (regenerate) | **NO `data-testid` on any of the 3.** Recommended: `pipeline-webhook-secret-toggle-button`, `pipeline-webhook-secret-copy-button`, `pipeline-webhook-secret-regenerate-button`. |
| Example Request code block + copy button | `dialog.locator('pre')` for the code text; adjacent `IconButton` with `ContentCopyIcon` for copy | **NO `data-testid` on either.** Recommended: `pipeline-webhook-example-request-block`, `pipeline-webhook-example-request-copy-button`. |
| Cancel / Apply buttons | `dialog.get_by_role("button", name="Cancel"/"Apply")` — confirmed reliable by visible text | `Modal.BaseModal` (`EliteaUI/src/[fsd]/shared/ui/modal/BaseModal.jsx`) already accepts `cancelButtonTestId`/`confirmButtonTestId` props (confirmed via source read) — recommend wiring `pipeline-webhook-modal-cancel-button`/`pipeline-webhook-modal-apply-button` at the call site rather than relying on visible-text role queries long-term, though the text-based query is a safe interim fallback (button labels are static, not i18n-variable in this codebase today). |
| Modal root | `[role="dialog"]` — confirmed unique (only one dialog open at a time in this flow) | `Modal.BaseModal` already accepts a top-level `data-testid` prop (confirmed via source read) — recommend `pipeline-webhook-settings-modal`. |

## Network Behavior

- `PUT .../pipeline_trigger/.../trigger` (body `type: "webhook"`, `webhook_type: "github"`) —
  fires on initial Webhook selection, BEFORE the modal's data has settled. Response body already
  contains the correct `webhook_url`/`secret_value` at this point (confirmed via response-body
  capture) — the delay in § Test Steps step 3 is a FRONTEND cache-population lag, not a backend
  data-availability lag; the backend has the right data immediately.
- `GET .../pipeline_trigger/.../trigger` — fires shortly after the PUT above; ITS response is what
  actually populates the modal's `webhookUrl`/`secretValue` props (via `useGetPipelineTriggerQuery`).
  This is the request automation should wait for (or wait for the "Webhook URL" text to appear) before
  asserting the full field inventory.
- Switching Webhook Type (GitHub→GitLab→Custom) triggers NO network request — confirmed live,
  purely a client-side re-derivation of the displayed URL/description from already-fetched data.
- Apply fires a SECOND `PUT .../trigger` with the finally-selected `webhook_type` (and, if the
  user regenerated the secret, a `webhook_secret_value` field) — confirmed via the code read
  (`handleWebhookSubmit` in `TriggerTypeSelector.jsx`).

## Known Defects Found During Exploration

**None filed as `bug`.** All case steps produced the expected final observable — the modal's
complete field set IS present and correct (GitHub/GitLab/Custom description + URL text all
verified byte-accurate), type switching works, and Apply persists through reload. Zero console
errors observed. Zero failed (≥400) network requests observed.

**One CLARIFICATION worth filing** (per `.agents/profile.md` § Bug filing routing — light UX
timing gap, not a functional defect): the Webhook settings modal opens with 3 of its 6
element-groups (Webhook URL, Secret Value, Example Request) entirely absent from the DOM for
~1.5–4.5s while a secondary GET populates them, with no loading indicator shown for the gap. This
does not fail the case (the elements DO appear correctly) but is a real, reproducible (3/3 runs
this session) rough edge worth the team's awareness, since a human tester clicking through quickly
could plausibly perceive the modal as broken/incomplete during that window. Filed as issue —
see PR/issue reference once created by the orchestrator per the seeded bug-filing policy (this
analyst session did not file it directly — see notes for routing).

## Blocked Steps

None. All 7 case steps were executed to completion against the live local environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. **Requires `add-data-testid`
  work** — see § Concrete Handles for the full list (Webhook Type radios via existing `testId`
  prop plumbing on `Checkbox.RadioButtonGroup`; URL/Secret inputs via `inputProps={{'data-testid':
  ...}}`; copy/eye/refresh `IconButton`s via a bare `data-testid` prop each; modal root + Cancel/
  Apply via `Modal.BaseModal`'s already-existing `data-testid`/`cancelButtonTestId`/
  `confirmButtonTestId` props).
- **Wait strategy is the load-bearing detail for this case**: wait for `dialog.get_by_text("Webhook
  URL")` (or its testid once added) to become visible before asserting the full field inventory —
  do NOT use a fixed short timeout (confirmed flaky below ~1.5s, confirmed reliable by ~4.5s across
  3 runs — recommend an explicit `wait_for(state="visible", timeout=8000)` on the URL field/testid
  as the settle signal, not a sleep).
- Use `pipeline_with_llm_id` (existing fixture). No new fixture needed.
- Suggested pytest markers: `@pytest.mark.p2`, `@pytest.mark.pipelines`, `@pytest.mark.regression`.
- This case's modal-open mechanics (select Webhook → wait for settle) are identical to ELITEA-2005
  step 4 — consider extracting a shared `open_webhook_modal_settled(page, node)` helper used by
  both this test and ELITEA-2005's, rather than duplicating the wait logic.
