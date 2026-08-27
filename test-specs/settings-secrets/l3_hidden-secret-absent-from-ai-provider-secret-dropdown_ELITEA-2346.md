# Test Case: Hidden secret does not appear in the secret selection dropdown for new AI-provider configurations

## Metadata
- **TMS ID**: ELITEA-2346
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2346.md`
- **Linked Story**: none · **Tracking issue**: settings-w05 batch · **Filed this session**: #1906 (clarification)
- **Priority**: l3 (medium, per case frontmatter `priority: medium`). **pytest marker:
  `@pytest.mark.p2`** — medium→l3→p2, per
  `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend), project `Private` / `${ELITEA_PROJECT_ID}` = **399**
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot — cluster session with ELITEA-2345, 2026-08-27
- **Status**: ready-for-automation
- **Surface key**: `secret-visibility-and-consumers`

## Relationship to ELITEA-2345 (why these are two specs, not one)
Both cases end on "a hidden secret is absent from a secret-selection dropdown", but they
differ in **steps**, not merely in data: ELITEA-2345 additionally builds a credential that
*references* the secret and asserts the credential survives the hide, and it checks the
**Credentials** create/edit forms; this case checks a different surface entirely
(**Settings → AI Providers → New AI Provider**) reached through a different route and a
type-picker step that has no analogue in 2345. Merging them would make one case's
assertions stand in for the other's. They share page objects and the secrets fixtures.

## Preconditions
- User is logged in; active project `${ELITEA_PROJECT_ID}` (399, "Private").
- **The case names a literal secret `"autotest_secret"` — do NOT use it.** Hiding is
  **irreversible via the UI** (no unhide affordance exists). A fixed literal works
  exactly once and then permanently occupies that name in the shared project. The test
  MUST create its own run-unique secret and hide THAT one. Recorded as a case-text
  clarification — `EliteaAI/elitea-testing-public#1906`.
- A freshly created secret is never `isDefault`, so its three-dot menu items are enabled.

## Test Data
### generated-per-run
- Secret name: `f"autotest_hidden_{uuid4().hex[:8]}"`. Confirmed live with
  `autotest_hidden_d4e5f6`.
- Secret value: any non-empty ASCII string, e.g. `"hidden-secret-value-456"`.
- A **second, NOT hidden** run-unique secret (or any known-visible secret) is needed for
  the control assertion in step 6.
- AI-provider type: **`open_ai`** (`toolkit-type-card-open_ai`) — chosen because its form
  is two text fields plus the `api_key` `SecretField`. Confirmed live.

## Test Steps

1. Navigate to `${BASE_URL}/settings/secrets` and create the run-unique secret via the
   inline "+" flow (`secrets-add-button` → `secret-name-input` / `secret-value-input` →
   `secret-row-save-button`).
   - **Verify**: `POST /api/v2/secrets/secrets/default/399` resolves **201 Created**.

2. Filter with `secrets-search-input` on the generated name, open the row's three-dot
   menu (`secret-row-actions-button`), click `secret-actions-menu-hide`, and confirm via
   `alert-dialog-confirm-button`.
   - **Verify**: `alert-dialog-content` reads
     `Are you sure to hide the secret "<name>"? Once hidden, the secret will no longer be
     visible.` (confirmed live verbatim).
   - **Verify**: `POST /api/v2/secrets/hide/default/399/<name>` resolves **200 OK**, and
     the filtered `secret-row` count drops to **0** (confirmed live).
   - **INHERITED DECLARED IMPROVISATION — keep it.** The three-dot button needs
     `secrets_page.open_row_actions_menu()`'s React-`onClick` workaround; a plain
     `.click()` failed again this session (`EliteaAI/elitea-testing-public#1222`).
   *(Case step 1.)*

3. Navigate to `${BASE_URL}/settings/ai-providers` and click the page's "+" create
   control, `sidebar-create-button` (its label reads **"AI Provider"** on this route).
   - **Verify**: the app routes to `/settings/create-ai-provider?viewMode=owner&from=ai-providers`
     and the type picker renders ("Select the AI Provider Type").
   - **NOTE — case-text drift (clarification, not a defect):** the case says
     *"Settings → AI Configuration → click '+' to create a new model configuration"*. The
     live settings section is named **AI Providers** (`settings-nav-item-ai-providers`,
     route `/settings/ai-providers`, title testid `ai-providers-page-title`), and the "+"
     creates an **AI Provider**, not a "model configuration". Assert the live names.
   - ⚠️ The AI-providers page renders `ai-providers-section-*-loading` placeholders first
     and only then the real `ai-providers-section-*` testids — wait on a real section
     testid (or on `sidebar-create-button`), never on a fixed delay.
   *(Case step 2, first half.)*

4. Choose the provider type — click `toolkit-type-card-open_ai`.
   - **Verify**: the app routes to `/settings/create-ai-provider/open_ai?...` and the
     configuration form renders (`toolkit-field-label-input`,
     `toolkit-field-api_base-input`, `toolkit-field-api_key-input`).
   - **This step has no counterpart in the case text** — the case's "+ → new model
     configuration" is a two-hop flow in the live product (create → type picker → form).
     Decomposed, see § Coverage Map.
   *(Case step 2, second half.)*

5. Open the secret-selection dropdown on the `api_key` field:
   - click `toolkit-field-api_key-input-toggle-secret` — **required; the field defaults
     to Password mode and the dropdown does not exist until this toggle is clicked**
     (confirmed live; the case's step 3 omits this hop);
   - click `toolkit-field-api_key-input-combobox`;
   - wait for `select-group-header-Saved Secrets` **and the first saved option** — the
     vault `GET` is `skip`-gated on the field's mode (`SecretField.jsx:118`), so the menu
     opens before the list resolves and waiting on the header alone yields an
     open-but-empty dropdown (already handled by
     `credential_create_page.open_secret_dropdown()`).
   - **Verify**: both group headers render — `select-group-header-Create` and
     `select-group-header-Saved Secrets` (confirmed live).
   *(Case step 3.)*

6. **Verify the hidden secret does NOT appear in the dropdown.**
   - **Verify**: `select-option-{{secret.<hidden name>}}` has **count 0** (confirmed
     live).
   - **Control (do include it):** a known-visible secret IS present in the same open
     dropdown, and `saved_secret_options` count is > 0 (confirmed live: 121 options
     rendered, the hidden one absent). Without the control, a dropdown that failed to
     load would pass the absence assertion silently.
   - **Baseline (assert it BEFORE step 2's hide, or accept the count delta):** the
     secret was present in the same dropdown while visible — confirmed live at 123
     options with it present, 121–122 after hiding. The implementer may either open the
     dropdown once before hiding (stronger, one extra navigation) or assert the
     known-visible control only (cheaper). **Prefer the pre-hide baseline** — it is the
     only thing that proves the absence was caused by the hide.
   *(Case step 4 and the case's Expected Final State.)*

## Expected Results
- Secret creates (201) and hides (200); it leaves the Secrets table immediately.
- `/settings/ai-providers` → "+" → `/settings/create-ai-provider` type picker →
  `toolkit-type-card-open_ai` → the OpenAI configuration form.
- The `api_key` field starts in Password mode; the Secret toggle swaps it for the vault
  combobox.
- The open vault dropdown renders the Create and Saved Secrets groups and a non-empty
  saved-secret list that **excludes** the hidden secret while including still-visible
  ones.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Secrets and hide a secret (e.g. "autotest_secret") | page loads | steps 1–2 | 201 create; dialog copy; `POST .../hide/...` → 200; filtered row count 0 | asserted *(secret name changed to a run-unique value — the literal is unusable because hiding is irreversible; clarification filed)* |
| 2 Navigate to Settings → AI Configuration → click "+" to create a new model configuration | page loads | steps 3–4 | route + type picker asserted, then `toolkit-type-card-open_ai` + the rendered form's field testids | asserted *(decomposed into two hops — the live flow has a type picker; section renamed "AI Providers", entity renamed "AI Provider"; clarification filed)* |
| 3 Open the secret/credentials selection dropdown | page/section loads | step 5 | both group headers visible + first saved option visible | asserted *(one hop added — the field must be switched to Secret mode first; the case omits it)* |
| 4 Verify "autotest_secret" does NOT appear in the dropdown list | condition holds | step 6 | `select-option-{{secret.<name>}}` count 0 | asserted |
| Expected Final State (same as 4) | condition holds | step 6 | as above | asserted |

**Axis 2 — Analyst additions:**
- Step 5 asserts both group headers render — *added: cheap positive proof the dropdown
  actually opened, so the step-6 absence assertion is not read off a closed menu.*
- Step 6's control assertion on a still-visible secret + non-empty option count —
  *added: an absence assertion passes trivially against an empty list; the control is
  what distinguishes "hidden" from "nothing loaded".*
- Step 6's pre-hide baseline — *added: without it the test cannot attribute the absence
  to the hide rather than to the secret never having been listed.*
- Step 3 asserts the live section/entity names — *added/corrected: the case's "AI
  Configuration" / "model configuration" wording does not match the product; asserting
  the stale text would make the test lie (reverse-masking guard).*

## Cleanup
- Nothing to delete: the AI-provider form is **never saved** (the case only opens the
  dropdown), and the secret cannot be un-hidden.
- The hidden secret leaves one invisible, run-unique row server-side per run —
  inherent to the case, which is why the name must be run-unique. Do not "clean up" by
  reusing a fixed name.
- **Do not save the AI-provider form.** A saved provider configuration is real project
  data on a shared DEV project, and this case never asks for one.
- ⚠️ Leaving a dirtied form (the Secret-mode toggle dirties it) raises a native
  `beforeunload` dialog that hangs a bare `page.goto()`. Register
  `page.on("dialog", lambda d: d.accept())`, or press Escape and use the form's own
  discard control before navigating away.

## Concrete Handles (discovered/confirmed during exploration)

Provenance verified 2026-08-27 after `cd ../EliteaUI && git fetch origin`.

| Element | Testid | Provenance |
|---|---|---|
| Secrets page title | `secrets-page-title` | on-main ✓ |
| Secrets "+" add button | `secrets-add-button` | on-main ✓ |
| Secret name / value inputs | `secret-name-input` / `secret-value-input` | on-main ✓ |
| Secret row save (✓) | `secret-row-save-button` | on-main ✓ |
| Secrets search input | `secrets-search-input` | **on `automation/testids` only** (awaiting human cherry-pick to main) |
| Secret row | `secret-row` | on-main ✓ |
| Three-dot actions button | `secret-row-actions-button` | on-main ✓ |
| "Hide" menu item | `secret-actions-menu-hide` | on-main ✓ |
| Hide dialog body / confirm | `alert-dialog-content` / `alert-dialog-confirm-button` | on-main ✓ |
| Settings nav item | `settings-nav-item-ai-providers` | on-main ✓ |
| AI Providers page title | `ai-providers-page-title` | on-main ✓ |
| AI Providers "+" create control | `sidebar-create-button` | on-main ✓ (generic sidebar create button; its label is route-contextual — "AI Provider" here) |
| Provider type card | `toolkit-type-card-open_ai` | template `toolkit-type-card-{type}` — on-main ✓ (same family the credentials type picker uses) |
| Provider display name / api_base | `toolkit-field-label-input` / `toolkit-field-api_base-input` | runtime-composed by `ToolBaseProperty.jsx` — on-main ✓ |
| api_key SecretField wrapper | `toolkit-field-api_key-input` | on-main ✓ |
| api_key native password input | `toolkit-field-api_key-input-field` | derived by `SecretField.jsx` (`nativeInputTestId`) — on-main ✓ |
| api_key Secret / Password toggles | `toolkit-field-api_key-input-toggle-secret` / `-toggle-password` | derived by `SecretField.jsx` `testIdPrefix` (line 342) — **on `automation/testids` only**; `origin/main`'s SecretField has no `testIdPrefix` |
| api_key vault combobox | `toolkit-field-api_key-input-combobox` | derived by `SingleSelect.jsx:662` — on-main ✓ |
| Saved-secret option | `select-option-{{secret.<name>}}` | on-main ✓ |
| Group headers | `select-group-header-Create` / `select-group-header-Saved Secrets` | on-main ✓ |
| AI-providers section (load gate) | `ai-providers-section-llms` (+ `-loading` variant) | on-main ✓ |

**Provenance note:** the `toolkit-field-*` and `toolkit-type-card-*` families are
**runtime-composed** — a bare `git grep` for the literal string finds nothing on either
ref. Verified at the composition sites (`ToolBaseProperty.jsx`, `SecretField.jsx`,
`SingleSelect.jsx`) plus live DOM read. Do not read "no grep hit" as "not on main" here.

**No new testid is needed by this case.**

## Network Behavior
- `POST /api/v2/secrets/secrets/default/399` — create, **201**.
- `POST /api/v2/secrets/hide/default/399/<name>` — hide, **200**, then a list `GET`.
- `GET /api/v2/configurations/available/?section=…` — the AI-provider type schema; the
  form renders only after it resolves. Settle on the rendered form's Display Name field,
  **not** on `networkidle` (these routes do not reach it — see `#1847`).
- `GET /api/v2/secrets/secrets/default/399` — the vault list behind the dropdown,
  `skip`-gated on the field's mode.
- **No mutation is issued by this case beyond the secret create + hide.**

## Known Defects Found During Exploration
- **No product defect blocks this case.**
- **Case-text clarifications filed — `EliteaAI/elitea-testing-public#1906`** (reverse-masking guard — assert the live product):
  1. "Settings → **AI Configuration**" → the section is **AI Providers**
     (`/settings/ai-providers`); the created entity is an **AI Provider**, not a
     "model configuration".
  2. Step 2's "+" is a **two-hop** flow: create → type picker → type-specific form.
  3. Step 3's dropdown requires first switching the `api_key` field to **Secret** mode;
     it defaults to Password mode.
  4. The literal secret name `"autotest_secret"` must be replaced by a run-unique value —
     the hide is irreversible, so a fixed literal is usable exactly once.
- `EliteaAI/elitea-testing-public#1203` (Secrets-page "Maximum update depth exceeded")
  was **not** observed this session. Implementer: check the run's own console.
- `EliteaAI/elitea-testing-public#656` (React "unique key prop" in `CategorySection.jsx`)
  fires on the **credentials** type picker, not on this case's AI-provider picker — the
  one console error captured this session came from the ELITEA-2345 leg. Still, if a
  console-error assertion is added here, verify against the run's own output.
- `EliteaAI/elitea-testing-public#1222` (three-dot menu React-`onClick` workaround) —
  reproduced again, see step 2.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest. Markers: `@pytest.mark.p2`, `@pytest.mark.regression`,
  feature marker matching the other secrets specs; file alongside them in
  `automation/tests/ui/admin/` (e.g.
  `test_hidden_secret_absent_from_ai_provider_dropdown.py`).
- Page objects — mostly reuse:
  - `automation/pages/secrets_page.py` — create + search + hide, exactly as ELITEA-2344.
  - `automation/pages/credential_create_page.py` — `secret_toggle()`,
    `open_secret_dropdown("api_key")`, `saved_secret_option()`, `saved_secret_options`,
    `secret_create_group_header`, `secret_saved_group_header`. These are **not
    credential-specific**: the AI-provider form renders the same shared `SecretField`
    with the same derived testids (confirmed live). Consider promoting the secret-vault
    block to a small shared component object (e.g.
    `automation/components/secret_field.py`) rather than importing
    `CredentialCreatePage` on an AI-providers spec — flag to the lead if that refactor
    is wanted; either way do NOT duplicate the selectors.
  - `automation/pages/ai_providers_page.py` — `navigate()` + the section testids for the
    step-3 load gate. It has **no create-button locator today**; add
    `sidebar-create-button` (pre-existing testid) and a `create-ai-provider` navigation
    method there, plus a `toolkit-type-card-{type}` class-constant template for step 4.
- Waits: `page.expect_response()` on the create (201) and hide (200); settle the
  AI-provider form on its Display Name field. No sleeps.
- Wrap every step in `with allure.step("Step N — …"):`.
- Register the `beforeunload` dialog handler before navigating away from the dirtied
  AI-provider form.

## Implementation notes (shipped — amended by the implementer, 2026-08-28)

Spec: `automation/tests/ui/admin/test_hidden_secret_absent_from_ai_provider_dropdown.py`
(green first run, 50.24 s, 0 reruns). Every assertion above shipped as
specified, including the **preferred pre-hide baseline** (the dropdown is
opened once on a new AI-provider form BEFORE the hide and both secrets are
asserted present). Deltas in the *how*:

1. **`ai_providers_page.py` gained, additively:** `create_button`
   (`sidebar-create-button`), the `TYPE_CARD_SELECTOR` /
   `TYPE_CARD_PREFIX_SELECTOR` class-constant templates, `type_card()`,
   `type_cards`, `click_create()` and `click_type_card()`. `click_type_card()`
   settles on the type picker unmounting and deliberately does NOT re-declare
   `toolkit-field-label-input` — that testid already lives in
   `CredentialFormFieldsMixin`, and the caller asserts the rendered form
   through it.
2. **The shared secret-vault block is reused, not duplicated:** the spec drives
   the AI-provider form's `api_key` field through `CredentialCreatePage`, whose
   methods already own those derived testids. The `components/secret_field.py`
   extraction this file suggests is the cleaner end state but is a non-additive
   refactor of a ~20-caller page object — raised to the lead, not done here.
3. **A second, run-unique CONTROL secret is created and deleted**, so the
   "other secrets are still selectable" control is owned by the run.
4. **No console-error assertion** was added — outside this case's Coverage Map,
   and the AFS's own §Known Defects records two environment-dependent
   signatures around this flow.
