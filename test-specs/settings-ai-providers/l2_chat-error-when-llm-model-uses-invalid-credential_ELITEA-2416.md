# Test Case: Chat reports a meaningful error when the assigned LLM model uses an invalid credential

## Metadata
- **TMS ID**: ELITEA-2416
- **Linked Story**: none
- **Priority**: l2 (case frontmatter: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` -> DEV backend `https://dev.elitea.ai/api/v2`), project
  `Private` (399)
- **User set**: `${TEST_USER}` (`auth_state` is a no-op on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w11`, 2026-08-30
- **Status**: **ready-for-automation** — with a **sanctioned-RED** step (see
  § Known Defects). Rationale: `.agents/testing.md` § Merge gate, *Analysis-time
  entry* bullet — the defect is deterministic, single-cause, linked to an OPEN
  issue, and does **not** block reaching any later step, so the case is automated
  with the affected assertion written as the CORRECT expected behaviour under
  `expect.soft()` + `# Known defect: #1993`.
- **Filed**: product bug **EliteaAI/elitea-testing-public#1993**
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`
- **Cluster**: dispatched with ELITEA-2415, same surface for its first half.
  **Separate specs** — the two differ in STEPS, not data.

---

## Case-identity note

Same resolution as ELITEA-2415: "Settings -> Credentials" and "Settings -> AI
Configuration" are both **Settings -> AI Providers** (`/settings/ai-providers`),
whose `+` flow is `/settings/create-ai-provider/{type}`. Step 1 creates an
`open_ai` **AI Credential**; step 2 creates an **`llm_model`** configuration that
references it. Both use the same `CredentialForm.jsx`.

## What actually happened, step by step (executed live 2026-08-30)

| Case step | Live observation |
|---|---|
| 1 — create a credential with an invalid API key | `open_ai`, `api_base=https://dev.elitea.ai/llm/v1`, `api_key=sk-invalid-2416-xyz`. `POST /configurations/configurations/399` -> **200**, id `3553`. |
| 2 — "+" -> create a new LLM model using the invalid credential | `/settings/create-ai-provider/llm_model`. Fields: Display Name, ID, **Name** (the model identifier), Context Window, Max Output Tokens, 5 checkboxes, **Ai Credentials** (a select). The select lists `SAVED CREDENTIALS` -> the credential from step 1. |
| 3 — save the LLM model | `POST /configurations/configurations/399` -> **200**, id `3554`. |
| 4-5 — open a chat that uses that model | `/chat` -> model selector -> the new model appears by its **display label**; selecting it sets `model-selector-name` to that label. |
| 6 — send any message | `Hello, reply with one word.` — the turn runs. |
| 7 — chat does not hang / go blank | **PASSES.** An error surfaces in **~8 s**; no spinner-forever, no blank bubble. |
| 8 — a user-friendly error is displayed | **PARTIAL.** An error *card* IS rendered (so the user is told something went wrong), but its content is the raw backend exception, not a user-facing sentence. |
| 9 — no raw stack trace or internal error details exposed | **FAILS — product defect #1993.** |

### The step-9 failure, verbatim

The chat renders a thought-step chip `toolkit: Agent Exception Stacktrace` plus an
error card whose DOM text contains:

```
Traceback (most recent call last):
  File "/data/plugins/indexer_worker/methods/indexer_predict_agent.py", line 472, in _indexer_predict_agent_task_inner
    raise elitea_callback.llm_error
plugins.indexer_worker.utils.exceptions.InternalSDKError: status code: 401, message: AuthenticationError:
OpenAIException - Authentication Error, Invalid proxy server token passed. Received API Key = sk-...-xyz,
Key Hash (Token) =625ba5bf137fecb2b9186e41766405588994eed0679ec3a047e4131a9f00e3eb.
Unable to find token in cache or `LiteLLM_VerificationTokenTable`
No fallback model group found for original model_group=399_gpt-5.6-luna. Fallbacks=[] ...
```

Leaked: a server file path + line number, an internal exception class, a LiteLLM
table name, the internal model-group naming scheme, and a **key hash**.
Evidence: `test-results/screenshots/ELITEA-2416-step-06-chat-invalid-model.png`
(uploaded and embedded on #1993).

**Notable contrast, and why this is a narrow product bug rather than a case-text
problem:** the *same* invalid credential produces a clean, masked, user-appropriate
message two screens away on the credential form's Test connection
(`Authentication failed: Invalid or expired api_key ...`, key masked as
`sk-inval***********2415` — see ELITEA-2415). The sanitisation exists; it is
missing on the chat surface.

## Preconditions
- User authenticated (`auth_state`, no-op on localhost).
- Project id from `settings.elitea_project_id` (the form's own request path is the
  honest oracle for which project the configs land in).
- No external service or new secret is needed: the invalid key is a literal.

## Test Data (ONE module-level block)

| Key | Value |
|---|---|
| Credential type | `open_ai` |
| Credential Display Name | `autotest_2416_cred_{ts}` (<= 32 chars) |
| `api_base` | `https://dev.elitea.ai/llm/v1` |
| Invalid `api_key` | `sk-invalid-2416-xyz` |
| Model type | `llm_model` |
| Model Display Name | `autotest_2416_model_{ts}` (<= 32 chars) |
| Model `name` | `autotest-2416-badcred` — **deliberately NOT a real model name**, see § Automation Hints |
| Chat message | `Hello, reply with one word.` |

## Test Steps

1. **Create the invalid AI credential** via `/settings/create-ai-provider/open_ai`.
   - Verify: `POST {api}/configurations/configurations/{project}` -> **200**, body
     carries a numeric `id` and `label == elitea_title == <display name>`.
   - **Set the teardown flag for the credential IMMEDIATELY BEFORE this click**
     (`.agents/testing.md` § Teardown-guard ordering — this spec is write-heavy).
2. **Create the LLM model** via `/settings/create-ai-provider/llm_model`: Display
   Name, Name, then open `toolkit-credential-select--combobox` and pick the
   credential created in step 1.
   - Verify: the dropdown's `SAVED CREDENTIALS` group contains an option whose
     `data-testid` is `select-option-{"kind":"saved","elitea_title":"<id>","private":true}`;
     `credential-form-save-button` becomes enabled only after the credential is
     chosen (`Ai Credentials` is a required field).
3. **Save the model.**
   - Verify: `POST {api}/configurations/configurations/{project}` -> **200** with a
     numeric `id`; set the model's teardown flag immediately before this click.
   - **Do NOT tick `Low Tier` / `High Tier`, and never make it the project default** —
     that would move a project-level default and damage every later spec.
4. **Open `/chat`, open the model selector, select the new model.**
   - Verify: `model-selector-name` reads the model's display label after selection.
5. **Send the message.**
   - Verify: the turn is accepted (the user bubble renders the sent text).
6. **Verify the chat does not hang or go blank (case step 7).**
   - Verify: within a bounded wait, an assistant turn resolves to an **error**
     state — assert the arrival of the backend's error rather than a fixed sleep.
     Oracle: a Socket.IO `chat_message_sync` frame whose `meta.error` is non-empty
     (`automation/utils/websocket_frames.py` — `ChatPage.capture_websocket_frames()`).
     Observed at ~8 s. Assert on the **frame's field**, never on its text.
7. **Verify an error is surfaced to the user (case step 8).**
   - Verify: the error card is visible in the message list and its text is non-empty.
8. **Verify no raw stack trace / internal detail is exposed (case step 9).**
   - **`expect.soft()` + `# Known defect: #1993`** — write it as the CORRECT
     behaviour, so it flips green when the fix ships:
     the rendered error text must NOT match
     `/Traceback \(most recent call last\)|File "\/data\/|InternalSDKError|LiteLLM_VerificationTokenTable|Key Hash/`.
   - Also soft-assert the `toolkit: Agent Exception Stacktrace` thought-step chip is
     absent — it is the same leak, surfaced as a tool label.

## Expected Results
A chat turn against a model whose credential cannot authenticate fails **fast and
visibly** (no hang, no blank bubble) with a message aimed at a user, and never
exposes server internals. Today the first two hold and the third does not (#1993).

## Fidelity Declaration
**No substitutions.** Every artifact is created through the real UI form against the
real backend; the failure is produced by the real LLM gateway rejecting a real
(invalid) key; every asserted value is read off the product's own response/frames.
No `route.fulfill`, no `page.evaluate` writing state, no API-seeded precondition for
a step the case performs in the UI. The API is used **only in teardown** (below),
which asserts nothing.

## Cleanup — mandatory, and order-sensitive
- Delete BOTH configurations:
  `DELETE {api}/configurations/configuration/{project}/{id}` -> **204**
  (verified live for both the credential and the model).
  Delete the **model first**, then the credential (the model references it).
- Delete the conversation the chat step creates (`ConversationAPI`) — the chat list
  on this shared user is already heavily polluted (`#1082` class); do not add to it.
- **Teardown-guard ordering is non-negotiable here** (`.agents/testing.md`): each
  `created_*_id` is recorded from the create response and its guard flag set
  *before* the mutating click, so a mid-flow failure still cleans up. A green spec
  that leaves an orphan LLM model behind is exactly the failure the merge gate
  cannot see — an orphan model shows up in every model selector in the project.

## Coverage Map

### Axis 1 — Case coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` | setup | precondition |
| Step 1 — create credential with an invalid API key | page/section loads, credential created | Step 1 | create `POST` 200 + id/label | asserted |
| Step 2 — "+" -> create LLM model using that credential | page loads | Step 2 | model form renders; credential option present + selected; Save gated on it | asserted |
| Step 3 — save the LLM model | operation completes, confirmation | Step 3 | create `POST` 200 + id | asserted |
| Step 4 — open/create an agent using the model | page loads | Steps 4 (adapted — see note) | model selected in the chat session; `model-selector-name` reads the label | asserted (adapted) |
| Step 5 — open a chat session | page loads | Step 4 | `/chat` composer ready | asserted |
| Step 6 — send any message | completes, expected UI state | Step 5 | user bubble renders the sent text | asserted |
| Step 7 — chat does not hang / blank | condition holds | Step 6 | bounded wait on a real error frame (`meta.error` non-empty), ~8 s live | asserted |
| Step 8 — user-friendly error displayed | condition holds | Step 7 | error card visible + non-empty | asserted |
| Step 9 / Expected Final State — no raw stack trace or internal details | condition holds | Step 8 | negative regex on the rendered text + absent stacktrace chip | **asserted, currently RED — `expect.soft()` + `# Known defect: #1993`** |

**Step-4 adaptation, declared.** The case says "open or create an agent that uses
the newly created invalid LLM model". Live, the model is bound to the turn through
the **same `model-selector-*` control** in both the plain `/chat` composer and an
agent's embedded chat panel (`AgentDetailPage.open_model_selector` /
`select_llm_model` already drive it), and the failure originates in the predict
path, not in the agent wrapper. The spec therefore selects the model directly in
the chat session rather than creating and deleting a throwaway agent — one fewer
shared-project object to create and orphan, with the same observable. This is a
declared improvisation under `.agents/role-overrides.md` § Declared-improvisation
protocol; it changes the *vehicle*, not *what is verified*. If the lead prefers the
literal agent path, the same steps apply with `AgentDetailPage` in place of the
chat composer.

### Axis 2 — Analyst additions
| Addition | Why grounded |
|---|---|
| Wait for a real `chat_message_sync` frame with non-empty `meta.error`, not a sleep | On this stack a failing turn's truth lives in the Socket.IO frames (`.agents/testing.md` — the HITL root-cause entry). It also makes "does not hang" a positive, bounded statement instead of an absence |
| Assert on the frame's `meta.error` **field**, never its text | The message is backend-authored and will change when #1993 is fixed; the field is the stable contract |
| Soft-assert the absence of the `Agent Exception Stacktrace` chip as well as the text | Same leak, second surface — a fix that only trims the card text would still expose the trace behind the chip |
| Assert Save is gated on `Ai Credentials` | Live-observed: the model form's Save stays disabled until a credential is chosen — that gate is what makes "the model uses THIS credential" true rather than assumed |

## Known Defects Found During Exploration
- **EliteaAI/elitea-testing-public#1993** (`bug`, OPEN) — chat exposes a raw Python
  traceback and internal LiteLLM details (incl. a credential key hash) when the
  assigned LLM model's credential is invalid. Deterministic, single-cause, and
  isolated to case step 9. It does not block steps 1-8, so per
  `.agents/testing.md` § Merge gate (*Analysis-time entry*) this case is
  `ready-for-automation` with that one assertion soft + linked, and the spec is a
  **sanctioned-RED** merge candidate. Record it in the closure record.
- **Testid wart (not a product defect, no issue filed):** the LLM-model form's
  credential select renders `data-testid="toolkit-credential-select-"` and
  `toolkit-credential-select--combobox` — a composed testid with an **empty key
  segment**, i.e. a double dash. It is stable and usable today, but it is not the
  `{section}-{element}-{type}` grammar and a future non-empty key would change it.
  Flagged to the lead; the implementer should use it as-is and not "fix" it inline.

## Blocked Steps
None — all 9 steps were reached and observed live.

## Concrete Handles (verified live 2026-08-30; provenance via `git fetch origin`)

| Element | Handle (testid-only) | on `main` | on `automation/testids` |
|---|---|---|---|
| Create button / provider type card | `sidebar-create-button` / `toolkit-type-card-{open_ai,llm_model}` | YES | YES |
| Credential + model form fields | `toolkit-field-{label,elitea_title,api_base,api_key,name}-input` (composed, `ToolBaseProperty.jsx:294`) | YES | YES |
| Api Key native input | `toolkit-field-api_key-input-field` | YES | YES |
| Model-form credential select | `toolkit-credential-select-` / `toolkit-credential-select--combobox` | YES | YES |
| A saved-credential option | `select-option-{"kind":"saved","elitea_title":"<id>","private":true}` (dynamic; JSON payload is the suffix) | YES | YES |
| Save / Cancel | `credential-form-save-button` / `credential-form-discard-button` | YES | YES |
| Chat model selector | `model-selector-button` (group) / `model-selector-name` (the clickable button) | YES | YES |
| Model option | `model-selector-option-{model name}` — **select by rendered display text**, see hints | YES | YES |
| Chat composer | `chat-input` (wrapper; the editable node is its inner `textarea`) | YES | YES |

**No new testid is needed.** (The error card / stacktrace chip are asserted through
the chat message list the existing `ChatPage` already exposes; if the implementer
finds the error card lacks a handle, that IS `add-data-testid` work — do not rung
down to text matching for the positive "an error card is visible" assertion.)

## Network / transport behaviour
- Create (both objects): `POST {api}/configurations/configurations/{project}` -> 200.
- Delete (teardown): `DELETE {api}/configurations/configuration/{project}/{id}` -> 204.
- The failing turn produces **no failed HTTP request and no console error** — the
  error arrives only over Socket.IO (`chat_message_sync`, `meta.error`). Do not
  classify this flow by console/HTTP silence (the documented lesson from the HITL
  investigation in `.agents/testing.md`).
- `page.wait_for_timeout` (not `time.sleep`) must be used when pumping for frames —
  the sync API only dispatches WS events while inside a Playwright call.

## Automation Hints
- `pytestmark`: `ui`, `admin` (settings surface) + `chat`, `p2`, `regression`, `new`.
- **Give the model a `name` that no shared model uses.** The option testid is
  `model-selector-option-{name}`, so reusing a real name (`gpt-5.6-luna`, as this
  analysis first did) collides with the shared model's option. Select the option by
  **rendered display text** (`AgentDetailPage.select_llm_model`'s `filter(has_text=…)`
  shape) and keep the model `name` unique to this spec.
- **`fill()` does not register with these MUI controlled inputs** — use click ->
  `ControlOrMeta+a` -> `Backspace` -> `press_sequentially`, then read the value back.
  Also let the form settle ~2 s after render before the first keystroke (a lost
  first write cost this analysis two runs).
  *(Amended at implementation, 2026-08-30: on the `llm_model` form this is not a
  settle-time problem and `wait_for_schema_field()` does not close it either — the
  Display Name arrived as `043574` with the schema-only `name` field already
  visible. Shipped shape: `AiProviderFormPage.set_display_name_verified()` /
  `.set_schema_field_verified()` — type, read back, re-type what the form's own
  re-render discarded, final attempt still asserted — plus a settle assertion on
  the schema default `context_window == "128000"`.)*
- `model-selector-button` is a `role="group"` wrapper — clicking it does nothing.
  Click `model-selector-name` (the actual `<button>`), and wait for
  `[data-testid^="model-selector-option-"]` to be visible rather than a fixed pause.
- `chat-input` is a `MuiFormControl` wrapper — type into `[data-testid="chat-input"] textarea`.
- Use the URL-keyed `#1971` console filter if the spec asserts console cleanliness —
  it drives project-scoped settings navigation, #1971's documented trigger.
