# Test Case: Test connection reports an error for an invalid credential, then success once corrected

## Metadata
- **TMS ID**: ELITEA-2415
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `high`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` -> DEV backend `https://dev.elitea.ai/api/v2`), project
  `Private` (399)
- **User set**: `${TEST_USER}` (`auth_state` is a no-op on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w11`, 2026-08-30
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`
- **Cluster**: dispatched with ELITEA-2416. Shared surface (the AI-provider
  credential form), **separate specs** — the two differ in STEPS, not in data
  (2415 never saves anything; 2416 saves a credential + a model and drives chat).

---

## Case-identity note — "Settings -> Credentials" is Settings -> **AI Providers**

There is no `Credentials` item in the settings drawer (its PROJECT group is
General / AI Providers / Project Context / Secrets / Users / Analytics / Usage).
The case's module is `settings-ai-configuration` and its sibling ELITEA-2416
consumes the created credential from an **LLM model**, so "Settings -> Credentials"
resolves to the **AI Credentials** half of Settings -> AI Providers, whose `+`
flow is `/settings/create-ai-provider/{type}`:

| Case wording | Live route |
|---|---|
| Settings -> Credentials | `/settings/ai-providers` (section **AI Credentials**) |
| Click "+" to create a new credential | `sidebar-create-button` -> `/settings/create-ai-provider?viewMode=owner&from=ai-providers` -> a 12-card type picker (`ai_dial`, `amazon_bedrock`, `azure_open_ai`, `embedding_model`, `image_generation_model`, `llm_model`, `ollama`, **`open_ai`**, `pgvector`, `asr_model`, `tts_model`, `vertex_ai`) |
| The credential form | `/settings/create-ai-provider/open_ai` — the SAME `CredentialForm.jsx` the toolkit-credentials page uses (`CreateCredentialFromMain`, `title="New AI Provider"`) |

Same nonexistent-"AI Configuration"-page drift already tracked by #1250 / #1772 /
#1906 / #1982 — **not re-filed**, this AFS records the resolution.

## Case-text divergence (non-blocking) — the error message text

The case says the message should be *"e.g. 'Connection failed' or 'Invalid API
key'"*. The product renders the **backend's own** message verbatim:

```
Authentication failed: Invalid or expired api_key - Authentication Error,
Invalid proxy server token passed. Received API Key = sk-...2415, Key Hash (Token) =c353...
```

The case says "e.g.", so this is an example, not a contract. The spec asserts the
**carry-through invariant** (the inline text equals the failing response body's own
`message`) plus a category regex `authentication failed`, exactly as ELITEA-1970 /
ELITEA-1980 already do on the toolkit-credentials vehicle. Never pin a literal.

## Relationship to the merged credential specs — why this is a NEW spec

| ELITEA-2415 asks for | Already proven? |
|---|---|
| Test connection on the **AI-provider** credential form (`open_ai`) | **no** — 1970 is Jira/detail-page, 1980 is Github/create-form; neither touches Settings -> AI Providers |
| the form **stays open** after a failed test (no redirect) | **no** — neither existing spec asserts it |
| a failure **recovering to success in the same form session** (error indicators CLEAR) | **no** — 1970 runs the opposite direction (success then failure) and never re-tests after a fix |

`already-covered` / `extend-existing` were both rejected: folding an AI-provider
vehicle plus a recovery direction into `test_credential_test_connection.py` would
be a near-rewrite of a spec whose whole subject is one type's success->failure
contrast.

## Preconditions
- User authenticated (`auth_state`, no-op on localhost).
- `.env.test` carries `ELITEA_API_TOKEN` (already required by the suite). The spec
  `pytest.skip`s when it is unset — the suite's established test-data pattern.
- **Nothing is created and nothing is saved** — the case ends at step 8 with the
  form still unsaved, so there is **no teardown and no shared-state pollution**.
  (Verified: the case's own steps never click Save.)

## Test Data (ONE module-level block, per the ELITEA-1970 convention)

| Key | Value | Note |
|---|---|---|
| Credential type | `open_ai` | route segment + `check_connection` path segment |
| Display Name | `autotest_2415_conn_{ts}` | keep <= 32 chars — the field's real `maxLength` silently truncates (`MAX_NAME_LENGTH`, `EliteaUI/src/common/constants.js`) |
| ID (`elitea_title`) | auto-derived from Display Name | **verified live**: typing the Display Name auto-fills the ID field |
| `api_base` | `https://dev.elitea.ai/llm/v1` | Elitea's own OpenAI-compatible endpoint — the app's `OpenAI-BaseURL` (see `test-specs/settings-ai-configurations/_surface.md`) |
| Invalid `api_key` | `sk-invalid-key-xyz-2415` | literal, no external service needed |
| Valid `api_key` | `settings.elitea_api_token` | **real, already-present test data**; never logged, never asserted on, only typed |

**Why this vehicle (fidelity, not convenience).** The valid half of the case needs a
credential that genuinely authenticates. `.env.test` has no OpenAI key — but Elitea
exposes an OpenAI-compatible endpoint that `ELITEA_API_TOKEN` authenticates against.
Verified independently of the UI before specifying it:

```
GET https://dev.elitea.ai/llm/v1/models   Authorization: Bearer $ELITEA_API_TOKEN  -> 200
GET https://dev.elitea.ai/llm/v1/models   Authorization: Bearer sk-bogus-xyz       -> 401
```

Both halves of the case are therefore produced by the real system against a real
service. **No substitution of any kind** — see § Fidelity Declaration.

## Test Steps (all executed live 2026-08-30; observations are actual, not expected)

1. **Navigate to Settings -> AI Providers** (`/settings/ai-providers`).
   - Verify: `ai-providers-section-ai-credentials` renders; the settings nav item
     `settings-nav-item-ai-providers` carries `data-active`.
2. **Click "+" and choose the OpenAI provider type.**
   - Verify: `sidebar-create-button` navigates to `/settings/create-ai-provider…`;
     the picker renders `toolkit-type-card-open_ai`; clicking it lands on
     `/settings/create-ai-provider/open_ai` and the form renders
     `toolkit-field-api_key-input-field`.
   - **Wait on the form's own fields, not on `networkidle`** (#1847).
3. **Fill Display Name, Api Base, and an INVALID Api Key.**
   - Verify: `toolkit-field-label-input` reads the full name back (truncation guard);
     `toolkit-field-elitea_title-input` auto-filled to the same value;
     `toolkit-field-api_base-input` reads the base url;
     `toolkit-field-api_key-input-field` reads the invalid key;
     `credential-form-save-button` becomes enabled.
4. **Click Test connection.**
   - Verify: `credential-form-test-connection-button` is enabled before the click;
     `POST {api}/configurations/check_connection/{project}/open_ai` -> **400**,
     body `success == false` with a non-empty `message`.
5. **Verify the user-facing error.**
   - Verify: `toolkit-field-api_key-input-helper-text` **and**
     `toolkit-field-api_base-input-helper-text` are visible and each has text
     **equal to** the response body's `message`; both fields carry
     `aria-invalid="true"`; the message matches `/authentication failed/i`;
     **no success toast** (`toast-alert[data-severity="success"]` count 0);
     the global `credential-form-api-error-message` stays **absent**.
   - Observed live: `Authentication failed: Invalid or expired api_key - ...
     Received API Key = sk-inval***********2415 ...`.
6. **Verify the form remains open for correction.**
   - Verify: `page.url` is unchanged (still `/settings/create-ai-provider/open_ai…`);
     `credential-form-save-button` and `credential-form-discard-button` are still
     rendered; `toolkit-field-api_key-input-field` still holds the typed value.
7. **Correct the Api Key to the valid token and click Test connection again.**
   - Verify: the secret field's value length changes (never assert the value);
     `POST …/check_connection/{project}/open_ai` -> **200**, body `{"success": true}`.
8. **Verify the success indicator, and that the failure indicators cleared.**
   - Verify: `toast-alert[data-severity="success"]` is visible and its
     `toast-message` text is exactly `The connection is OK!`;
     `toolkit-field-api_key-input-helper-text` and
     `toolkit-field-api_base-input-helper-text` are **gone** (count 0);
     neither field carries `aria-invalid="true"` any more;
     `credential-form-api-error-message` still absent.

## Expected Results
Test connection reports the truth from the target service on the AI-provider form:
an inline, field-level error carrying the service's own reason for a broken
credential, with the form left open and editable; and, once the credential is
corrected in the same session, a success toast **and** a full clearing of the
previous failure indicators.

## Fidelity Declaration
**No substitutions of any kind.** No `page.route`, no `route.fulfill`, no
`page.evaluate` writing app state, no monkeypatch, no seeded-by-API precondition.
Both `check_connection` round trips are real calls to the real backend, which really
calls the real LLM gateway; every asserted string is read off the response body that
produced it. The valid secret is real environment test data, verified out-of-band
(above) before use.

## Coverage Map

### Axis 1 — Case coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | setup | precondition |
| Step 1 — Settings -> Credentials | page/section loads | Step 1 (resolved to Settings -> AI Providers, § Case-identity note) | `ai-providers-section-ai-credentials` visible | asserted |
| Step 2 — click "+" to create a credential | control responds, next state shown | Step 2 | type picker renders `toolkit-type-card-open_ai`; form route reached | asserted |
| Step 3 — fill invalid/expired values | field accepts + displays input | Step 3 | four input-value read-backs + Save enabled | asserted |
| Step 4 — click Test Connection | control responds | Step 4 | button enabled + `check_connection` 400 observed | asserted |
| Step 5 — user-friendly error shown | condition holds | Step 5 | helper text == body `message`, `aria-invalid="true"`, category regex, no success toast | asserted |
| Step 6 — form remains open, no redirect | condition holds | Step 6 | URL unchanged + Save/Cancel still rendered + typed value retained | asserted |
| Step 7 — correct values, Test Connection again | completes without error | Step 7 | `check_connection` 200 `{"success": true}` | asserted |
| Step 8 / Expected Final State — success indicator | condition holds | Step 8 | success toast `The connection is OK!` **and** both helper texts gone, `aria-invalid` cleared | asserted |
| Fail criterion — success feedback for an invalid credential | must not happen | Step 5 | success-toast count 0 at the failing click | asserted |

### Axis 2 — Analyst additions
| Addition | Why grounded |
|---|---|
| The inline text **equals the response body's `message`** | Honest oracle for a backend-authored string — catches the UI dropping/mangling the reason without pinning a wording (same shape as merged ELITEA-1970/1980) |
| Failure indicators must **CLEAR** on the successful retry, not merely be joined by a toast | The case's step 8 says the test "now succeeds"; a stale inline error next to a success toast would be a contradictory UI and is exactly what a recovery flow regresses into |
| The error is asserted on **both** `api_key` and `api_base` helper texts | Live-observed: `extractInformationFromCredentialError` maps an `authentication` message to the secret key AND falls back to every `*url*` key, so both light up. Pinning only one would pass while the other silently changed |
| The rendered error must **not contain the full typed key** | Live-observed masking (`sk-inval***********2415`); a regression that echoes the raw secret into the DOM is a real leak this assertion catches |
| `credential-form-api-error-message` asserted ABSENT | Distinguishes the case's inline field error from the other error surface the same handler can take |

## Cleanup
**None required** — the case never saves. Nothing is created, so nothing is deleted
and no shared project state moves. (Contrast ELITEA-2416, which does create.)

## Concrete Handles (verified live 2026-08-30; provenance via `git fetch origin` in `../EliteaUI`)

| Element | Handle (testid-only) | on `main` | on `automation/testids` |
|---|---|---|---|
| Settings nav item | `settings-nav-item-ai-providers` (+ `data-active`) | no | YES |
| Create button | `sidebar-create-button` | YES | YES |
| Provider type card | `toolkit-type-card-open_ai` (dynamic: `toolkit-type-card-{type}`) | YES | YES |
| AI Credentials section | `ai-providers-section-ai-credentials` | YES | YES |
| Display Name input | `toolkit-field-label-input` | YES (composed `toolkit-field-${k}-input`, `ToolBaseProperty.jsx:294`) | YES |
| ID input | `toolkit-field-elitea_title-input` | YES (same composition) | YES |
| Api Base input | `toolkit-field-api_base-input` | YES (same composition) | YES |
| Api Key wrapper | `toolkit-field-api_key-input` | YES (same composition) | YES |
| Api Key native `<input type=password>` | `toolkit-field-api_key-input-field` | YES (derived in `SecretField.jsx`) | YES |
| Api Key inline error | `toolkit-field-api_key-input-helper-text` | **no** | YES (`SecretField.jsx:88,301`, EliteaAI/EliteaUI@58955184) |
| Api Base inline error | `toolkit-field-api_base-input-helper-text` | **no** | YES (`ToolBaseProperty.jsx:623` -> `InputBase.jsx:101,270`) |
| Test connection button | `credential-form-test-connection-button` | **no** | YES (EliteaAI/EliteaUI@5892ae48, added for ELITEA-1967) |
| Save / Cancel | `credential-form-save-button` / `credential-form-discard-button` | YES | YES |
| Global API error (asserted ABSENT) | `credential-form-api-error-message` | YES | YES |
| Toast + severity | `toast-alert` + `data-severity="success"` | YES | YES |
| Toast text | `toast-message` | YES | YES |

**No new testid is needed for this case** — every element it touches already has one.
Three of them live only on `automation/testids`, so the spec is localhost-green and
**not deployed-env-promotable** until a human cherry-picks them to `main`.

## Network Behavior
- `POST {api}/configurations/check_connection/{project_id}/open_ai`
  - invalid key -> **400** `{"success": false, "message": "<gateway reason>"}`
  - valid key -> **200** `{"success": true}`
  - round trip observed at ~1-3 s; use `page.expect_response` around BOTH clicks.
- No other request fires from the two clicks. `networkidle` is **not** a usable
  settle condition on this route (#1847) — wait on the form's own nodes.
- The project id in the path is the honest oracle for which project the form is
  scoped to; read it from the request rather than hardcoding.

## Known Defects Found During Exploration
**None on this case's path.** The invalid-credential error is masked
(`sk-inval***********2415`), inline, and the form is left intact.

*(The sibling case ELITEA-2416 DID find one — issue **#1993** — but it is on the chat
surface, not this form.)*

## Blocked Steps
None — all 8 steps executed live end to end, both directions.

## Automation Hints
- `pytestmark`: `ui`, `credentials`, `p1`, `regression`, `new` (feature marker per
  `pytest.ini` — `admin`/`credentials` as the settings-suite neighbours use).
- Lives naturally in `automation/tests/ui/settings/`; the form handles are the same
  `CredentialFormFieldsMixin` the toolkit-credentials page objects already share, so
  extend that mixin / `AIProvidersPage` rather than duplicating testids.
- **`fill()` does NOT register with these MUI controlled inputs** — a `fill()`ed
  Display Name and Api Base reached the backend as EMPTY (`"api_base is required"`,
  400) while the field looked populated. Use click -> `ControlOrMeta+a` ->
  `Backspace` -> `press_sequentially`, then **read the value back** before
  continuing. Cost this analysis two runs.
- **Let the form settle (~2 s) after it renders before typing the first field** — a
  write into `toolkit-field-label-input` immediately after `wait_for_selector` was
  silently lost to a re-render (Save stayed disabled, ID never auto-filled). The
  read-back-and-retry helper above is the robust shape.
- Read the success toast INSIDE step 8 — MUI auto-hides it.
- Never assert on, log, or screenshot the valid token; assert its effect (200 /
  `{"success": true}`), not its value.
