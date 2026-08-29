# Test Case: Change the default TTS model

## Metadata
- **TMS ID**: ELITEA-2407
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; folder mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (`auth_state` fixture)
- **Analyst**: qa-engineer (analyst slot), 2026-08-30, batch `settings-w11`
- **Status**: **ready-for-automation** (with a declared **transit** substitution — § Fidelity Declaration)
- **Why this is NOT in the ELITEA-2403/2405 family**: the case *text* is identical, but
  the TTS section holds **one** model live, so the case's step 3 ("select a **different**
  model") is unsatisfiable without first creating a second configuration — and creating
  one drags in a create flow, a delete teardown, and a default-restore the other two
  rows do not have. That is a difference in **steps**, not data ⇒ its own spec.
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## ⚠️ WRITE-HEAVY — this test creates, mutates and deletes shared project state

Three separate mutations, each fully restored: a TTS configuration is **created**, the
project's **default TTS model** is moved twice, and the configuration is **deleted**.
`.agents/testing.md` § Teardown-guard ordering is binding; see § Cleanup.

## Case-identity note (pre-existing, NOT re-filed)

The case says **"Settings → AI Configuration → Text to Speech (TTS) section"**. There is
no such page; the section lives on **Settings → AI Providers** (`/settings/ai-providers`).
Already filed as EliteaAI/elitea-testing-public#1250 (ELITEA-2392); re-confirmed live.
Asserting the live contract per the reverse-masking guard; **not re-filed**.

Same as its two siblings, step 1 also lands on a **collapsed** accordion (only LLMs
auto-expands), whose content — including the real Default combobox — unmounts while
collapsed. The expand is folded into step 1 below; folded into #1250, not filed
separately.

## Fidelity Declaration (`.agents/testing.md` § Fidelity policy)

| What is substituted | Transit or terminal | Authority |
|---|---|---|
| The **second TTS configuration** the case needs in order to have "a different model" to select | **TRANSIT ONLY** | The case's step 3 says *"select a different model"*, which is unsatisfiable with the single TTS model the project has. The transit configuration is created **through the same UI create form a real user would use** (`/settings/create-ai-provider/tts_model`), not injected, seeded via API, or fabricated. Every observable the case actually asserts — the combobox label (step 4), the badge appearing (step 5), the badge disappearing (step 6), and the `POST` that persists it — is produced by the **product**. Nothing is mocked, stubbed, routed or evaluated into place. |
| The **pre-existing default is put back before the case's step 3** | **TRANSIT ONLY** (setup) | Creating a TTS configuration **auto-assigns it as the section default** — measured live this session (see § Live contract below). Without restoring `gpt-4o-mini-tts` first, the case's "select a different model" would select what is *already* selected, fire no request at all, and the whole case would pass vacuously. This is the exact half-transit ELITEA-2401 documents for Vector Storage. |

**Nothing here is terminal.** There is no `route.fulfill`, no `page.evaluate`-injected
state, no monkeypatched client. This is the ELITEA-2401 precedent, which is merged.

## Live contract measured this session — **creating a TTS configuration makes it the default**

Directly measured, and it is the single most load-bearing fact in this AFS:

- Before: TTS section count **1** (`gpt-4o-mini-tts`), default `gpt-4o-mini-tts`.
- Created `Autotest TTS Probe` (model name `tts-1-probe`) via the UI create form.
- Straight after the save, **with no selection made**, the Default combobox read
  **`Autotest TTS Probe`** and that card carried the `Default` badge.

This matches the **Vector Storage** behaviour (`_surface.md`, ELITEA-2399) and is the
**opposite** of the **LLMs** section, where a newly created model must be assigned
explicitly (ELITEA-2395). Two consequences the implementer must not rediscover the hard
way:

1. Setup owes a **restore-before-the-case** (see § Fidelity Declaration row 2).
2. Teardown owes a **restore-before-the-delete** — while the transit configuration is
   the default, deleting it would leave the project pointing at a configuration that no
   longer exists.

## Preconditions

- Logged in as `${TEST_USER}` (`auth_state`).
- The TTS section holds **≥ 1** configuration **and has a default assigned** — read from
  the product's own `GET …&section=tts` (`total >= 1`, `default_model_name` non-empty)
  and fail loudly otherwise. There is **no blank/"None" option** in the selector
  (live-confirmed), so a section starting with no default could not be restored, and the
  spec must refuse rather than create an unrestorable mutation.
- **TTS is NOT a protected section.** `CredentialsControls.jsx`'s `isLastInSection`
  guard covers only `vectorstorage` and `embedding`, so the transit TTS configuration is
  freely deletable — verified live end to end (created id 77, deleted it, section count
  returned to 1). This is why a transit-create is safe here and would **not** be safe in
  Vector Storage.
- **An AI Credential must exist** for the create form's required `Ai Credentials *`
  field. Live, the shared **`ELPS`** credential is present on every non-public project
  (`_surface.md`, ELITEA-2417), and it is what this analysis used. Assert it is
  selectable and fail loudly if not — do not create a credential as a second transit.

## Test Data

| Field | Value | Note |
|---|---|---|
| Transit Display Name | `Autotest TTS Probe <run-suffix>` | `maxlength="32"` on this field with **silent truncation** (`_surface.md`) — `"Autotest TTS Probe "` is 19 chars, so a 5-digit suffix fits. Keep it unique per run. |
| Transit `Name` (model id) | `tts-1-probe` | This is the field the option key is built from — the option testid becomes `select-option-tts-1-probe<<>>{project_id}`, **labelled with the Display Name**. Verified live: `select-option-tts-1-probe<<>>400` labelled `Autotest TTS Probe`. |
| Transit credential | saved credential `ELPS` | option testid `select-option-{"kind":"saved","elitea_title":"elps","private":false}` |
| Pre-existing default | `gpt-4o-mini-tts` (`gpt-4o-mini-tts<<>>1`) | **Read it from the API, do not hardcode** — shared project-1 model, mutable |

**The transit model name is never called.** No TTS request is ever issued against
`tts-1-probe`; the configuration exists only to be a selectable option. The case asserts
nothing about the model working.

## Test Steps

| # | Action | Expected result (observed live) |
|---|---|---|
| 0a | *(transit)* Navigate to `/settings/ai-providers`, capture `GET …&section=tts`; assert `total >= 1` and a non-empty default; record it as `original_option_value` | 200; live `total: 1`, default `gpt-4o-mini-tts` |
| 0b | *(transit)* Create a second TTS configuration through the UI create form: Display Name, `Name`, saved credential `ELPS`, Save | Returns to `/settings/ai-providers`; TTS count **1 → 2** |
| 0c | *(transit)* Read the default back; it is now the **new** configuration — re-select `original_option_value` so the case's step 3 is a genuine change | combobox returns to `gpt-4o-mini-tts` |
| 1 | Navigate to `/settings/ai-providers` and **expand** the TTS accordion | `aria-expanded` `false` → `true`; combobox mounts |
| 2 | Note the currently selected default TTS model | combobox text == API default (`gpt-4o-mini-tts`); that card carries the `Default` badge and **no other card does** |
| 3 | Open the `Default TTS model` dropdown and select a different model | listbox lists **2** options; clicking the transit option fires `POST /api/v2/configurations/models/{project_id}` → **200** |
| 4 | Verify the selector updates | combobox text == `Autotest TTS Probe …` (the **Display Name**, not the model id) |
| 5 | Verify the selected model's card gains a `Default` badge | that card's `ai-provider-configuration-badge` reads `Default` |
| 6 | Verify the previously default card no longer shows the badge | the `gpt-4o-mini-tts` card has **0** badges |

No reload is needed between 3 and 4–6 — all three landed in one render pass off the
app's own post-POST refetch. Confirmed live.

## Expected Results

- With two TTS configurations present, the default moves, persists, and both badges move
  with it in a single render.
- **0 console errors** across steps 1–6.
- After teardown the project reads back **exactly as found**: TTS count 1, default
  `gpt-4o-mini-tts`, no `Autotest TTS Probe` card.

## Coverage Map

### Axis 1 — every case element

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — navigate to Settings → AI Configuration → TTS section | page/section loads | Step 1 (**decomposed**: route corrected per #1250 **+** expand) | GET 200 + `aria-expanded` true | covered (clarified) |
| Step 2 — note the current default TTS model | completes without error | Step 2 | combobox text == API default; exactly one `Default` badge | covered |
| Step 3 — open dropdown, select a different model | control responds | Step 3 (**enabled by transit 0a–0c**) | 2 options listed; POST 200 | covered — see § Fidelity Declaration |
| Step 4 — selector updates | condition holds | Step 4 | combobox text == transit Display Name | covered |
| Step 5 — selected card gains `Default` badge | condition holds | Step 5 | badge `Default` on the transit card | covered |
| Step 6 — previous card loses the badge | condition holds | Step 6 | `gpt-4o-mini-tts` card badge count 0 | covered |
| Expected Final State | previous card no longer `Default` | Step 6 | same | covered |
| Precondition — user logged in | — | `auth_state` | — | covered (setup) |

### Axis 2 — asserted beyond the case

| Extra assertion | Why it is grounded |
|---|---|
| The mutation **persisted server-side** (`POST …` → 200) | Steps 4–6 are all DOM reads; an optimistic UI update would satisfy every one while the server rejected the change. The POST is the product's own response, not a fabricated one. |
| Exactly **one** card carries a `Default` badge, before and after | The case checks the gain (5) and the loss (6) but never that no *third* card has one. "Exactly one" is the invariant that catches a badge-keying regression — the defect class behind #1987 in Vector Storage. |
| The transit precondition reads (`total >= 1`, default non-empty, `ELPS` selectable) | Without them the spec silently degrades into a no-op or leaves unrestorable state. All read from the product's own responses. |
| **The default is put back BEFORE the case's step 3** (0c), verified by read-back | Not defensive: creating the configuration auto-assigns it, so without 0c step 3 re-selects an already-selected option, **fires no request at all**, and the case passes proving nothing. |
| **0 console errors** over steps 1–6 | Verified live. Use `utils/console_errors.collect_console_errors()`. **Capture before teardown** — see § Known Defects. |
| Teardown read-back: TTS count 1, default original, transit card absent | A green-but-damaging spec is exactly what N×-green cannot catch (`.agents/testing.md` § Teardown-guard ordering). Prove the restore. |

## Cleanup (MANDATORY — ordering is load-bearing)

**Teardown-guard ordering (`.agents/testing.md`, AUTHORITATIVE):** each flag is set
**immediately BEFORE** the mutation it guards.

```python
# RIGHT — flags can only be wrong in the safe (restore-runs-needlessly) direction
self.config_created = True
form.save_and_return_to_list()
...
self.default_changed = True
providers_page.select_default_configuration(tts_combobox, transit_option_value)
```

`finally`, **in this exact order**:

1. **Restore the default first** — re-select `original_option_value`
   (`utils/ai_provider_teardown.restore_section_default()`), and **read it back**.
2. **Then delete** the transit configuration
   (`utils/ai_provider_teardown.delete_configurations_if_present()`), passing the run's
   Display Name.
3. Assert the section reads back at its original count with its original default.

**Order 1-before-2 is not stylistic.** Deleting a configuration that the project default
still points at leaves the project pointing at something gone — a state no later spec
expects, from a spec that still reports green. This is the exact hazard
`restore_section_default`'s docstring was written for.

⚠️ **Re-selecting an already-selected option fires NO request** (live-confirmed). A
restore that waits on the POST hangs its full timeout when the test failed before it
changed anything. Read the persisted default first; only re-select when it moved.

### The delete flow, verified live end to end

card → **`controls-menu-button`** (on the *edit* page the card navigates to) →
`delete-credentials-menuitem` → `delete-confirm-dialog` → type the **Display Name** →
`delete-confirm-button`.

⚠️ **`delete-confirm-name-input` is NOT the `<input>`** — it is the MUI wrapper `div`.
Typing into it silently does nothing and the Delete button stays **disabled**; the
scoped inner node is required. This cost a retry during analysis. `AiProviderFormPage`
already handles it — use `delete_current_configuration()` and do **not** re-derive the
locator.

## Concrete Handles (discovered live; **testid-only**)

| Handle | Testid | Provenance (verified `git fetch origin`, 2026-08-30) | Notes |
|---|---|---|---|
| TTS section header | `ai-providers-section-tts` | on-main ✓ | `AIProvidersPage.tts_section_header` |
| TTS default combobox | `ai-providers-section-tts-default-selector-combobox` | on-main ✓ | **page-object gap only** — testid exists in JSX, resolved live; add the `LocatorDescriptor` field mirroring `embedding_models_default_selector_combobox` |
| Dropdown option | `select-option-{name}<<>>{project_id}` | pre-existing shared `SingleSelect` convention | `SELECT_OPTION` template. Live: `select-option-gpt-4o-mini-tts<<>>1` and `select-option-tts-1-probe<<>>400` — **the two halves differ in project id**; take the whole value from the response body |
| Option SET | `SELECT_OPTION_PREFIX_SELECTOR` | — | the bare prefix also matches `select-option-selected-icon` |
| Configuration card | `ai-provider-configuration-card` | on-main ✓ | `CONFIGURATION_CARD_SELECTOR` |
| Card display name | `ai-provider-configuration-card-name` | on-main ✓ | `CARD_NAME_SELECTOR` |
| `Default` badge | `ai-provider-configuration-badge` | on-main ✓ | `card_tier_badge(name, "Default")` |
| Create-form Display Name | `toolkit-field-label-input` | on-main ✓ | `AiProviderFormPage.set_display_name()` |
| Create-form ID (read-only) | `toolkit-field-elitea_title-input` | on-main ✓ | auto-derived from Display Name |
| Create-form model `Name` | `toolkit-field-name-input` | on-main ✓ | use `set_schema_field()` — `press_sequentially` can drop the first keystroke on a freshly-mounted MUI input (`_surface.md`) |
| Create-form credential select | `toolkit-credential-select--combobox` | on-main ✓ | note the **double dash** — the dynamic suffix is empty on this form. `select_saved_credential` covers it |
| Save | `credential-form-save-button` | on-main ✓ | |
| Delete menu | `controls-menu-button` → `delete-credentials-menuitem` | on-main ✓ | |
| Delete dialog | `delete-confirm-dialog` / `delete-confirm-name-input` / `delete-confirm-button` | on-main ✓ | input is the wrapper — see the warning above |

**No new testid is needed for this case.** Every handle above resolved live.

⚠️ **Wait for a schema-render-only field before typing.** `wait_for_form()` settles on
`toolkit-field-label-input`, which the form renders in its **pre-schema** pass too, so
the schema re-render can wipe an already-typed and already-asserted value
(`_surface.md`, measured on ELITEA-2399). Wait on `toolkit-field-name-input` —
`AiProviderFormPage.wait_for_schema_field("name")`.

## Network Behavior

- Per page load: summary GET, one `…&section={param}` GET per section, combined
  `configurations/…` listing — all 200.
- **Selecting an option**: `POST /api/v2/configurations/models/{project_id}` → 200, then
  a refetch of the summary and of **every** section's models GET.
- **Expanding an accordion and opening a dropdown fire NO request.** Wait on the target
  testid, never on network, after those.
- **Deleting**: `DELETE /api/v2/configurations/configuration/{project_id}/{id}` succeeds,
  then the app re-fetches the deleted id and gets a **404** — see § Known Defects.

## Known Defects Found During Exploration

**One, pre-existing, NOT filed (real duplicate).** After the transit configuration is
deleted, the app re-requests it and logs a console error:

```
[ERROR] Failed to load resource: the server responded with a status of 404 (Not Found)
        @ http://localhost:5173/api/v2/configurations/configuration/400/77
```

Same object family (`/configurations/configuration/{project}/{id}`), same trigger
(three-dot → Delete → type-to-confirm), same expected/actual as the **OPEN**
EliteaAI/elitea-testing-public#1666. Per `.agents/profile.md` § Bug filing, a real
duplicate found before filing is **commented, not re-filed** — the new occurrence is
recorded on #1666 (comment posted 2026-08-30).

**Automation consequence:** capture the console assertion **before teardown runs**. It
naturally is — teardown lives in `finally`, after the assertions — so **no console
filter is needed**. Do not add one: the case's own steps 1–6 produce **0** console
errors (verified live), and a filter that swallowed this 404 would also swallow a real
one.

**No defect in the case's own flow.** Steps 1–6 executed clean: badges moved correctly,
the POST persisted, and the section restored exactly.

## Blocked Steps

None. All 6 steps executed end-to-end against the live system, including the transit
create, the default restore and the delete.

## Automation Hints

- One spec, `automation/tests/ui/settings/test_change_default_tts_model.py`. **Not
  parameterized** — it is a single case with a transit the other two rows don't have.
- **`isolate_section()` before every card count.** `ai-providers-section-tts` is on the
  accordion **summary button**, so cards are not its descendants; a whole-page card query
  mixes in every other expanded section's cards (live: the Vector Storage seed card kept
  surfacing in TTS queries).
- Reuse `utils/ai_provider_teardown` for both halves — `restore_section_default()` then
  `delete_configurations_if_present()`. Both are section-agnostic and already prove the
  ordering.
- A **direct route to the create form** skips the "+" type picker (whose own React
  "unique key" console error, #656, is unrelated to this case):
  `/settings/create-ai-provider/tts_model?viewMode=owner&from=ai-providers` —
  `AiProviderFormPage.navigate_to_create("tts_model")`.
- **Do not run in parallel** with any other AI-Providers spec — this one creates,
  reassigns and deletes shared project state. Serial only.
- Markers: `ui, settings, p2, regression, new`.
- Wrap each step in `with allure.step("Step N — …"):`; the transit steps get their own
  `Step 0a/0b/0c` blocks so a setup failure is legible in the report.
- Docstring must state (a) that the spec creates, reassigns and deletes shared project
  state and restores all three, and (b) the transit declaration in one line: *"the second
  TTS configuration is created through the real UI create form because the project has
  only one TTS model — transit only; every asserted observable is produced by the
  product."*
