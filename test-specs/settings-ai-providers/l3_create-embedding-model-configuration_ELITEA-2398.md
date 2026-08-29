# Test Case: Create a new Embedding Model configuration

## Metadata
- **TMS ID**: ELITEA-2398
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; folder mapping — ELITEA-2392/2395/2397)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` @ `a64d3308`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (via `auth_state` — `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (analyst slot), 2026-08-29, batch `settings-w10`
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## Case-identity note (read first)

The case says "Settings → AI Configuration". **No such page or nav item exists** —
already filed as EliteaAI/elitea-testing-public#1250 and not re-filed. The real page
is **AI Providers** (`/settings/ai-providers`); its **Embedding Models** accordion is
what this case exercises. The type-picker card is labelled **"Embedding model"**
(lowercase `m`) — cosmetic, folded into #1250.

## Preconditions
- `auth_state` fixture (localhost dev-token bypass).
- Active project has ≥1 usable **AI Credential**. Verified live: the shared **`ELPS`**
  credential (`elitea_title` = `elps`) is visible in every non-public project
  (`include_shared=true`). Pick it by `elitea_title`, never by list position.
- **This test MUTATES shared, live project configuration** — it creates a real
  embedding-model configuration in the active project. § Cleanup is mandatory.
- Cleanup is *safe here*: the Embedding Models section already holds **3 shared**
  configurations, so the created one is never "last in section" and the delete control
  stays enabled (see § Known constraints — this is NOT true for Vector Storage).

## Test Data

| Field | Value | Note |
|---|---|---|
| Display Name | `Autotest Embedding Model` | the case's own value; 24 chars — **`toolkit-field-label-input` has `maxlength="32"` and truncates silently**, so any per-run suffix must keep the total ≤32 |
| Name (model identifier) | `text-embedding-3-small` | the case's own value. It **collides by name** with an existing shared model, but NOT by option testid — see § Automation Hints |
| Ai Credentials | saved credential `elps` (displayed `ELPS`) | |

## Test Steps

| # | Action | Expected (verified live 2026-08-29) |
|---|---|---|
| 1 | `goto /settings/ai-providers`; expand **Embedding Models**; capture the card count | `ai-providers-page-title` == `AI Providers`; `ai-providers-section-embedding-models` present; **3** cards in this session (`amazon.titan-embed-text-v2:0`, `text-embedding-3-small`, `text-embedding-ada-002`) |
| 2 | Click `sidebar-create-button` | URL → `/settings/create-ai-provider?viewMode=owner&from=ai-providers`; a **12-card** type picker renders |
| 3 | Click `toolkit-type-card-embedding_model` | URL → `/settings/create-ai-provider/embedding_model?viewMode=owner&from=ai-providers`; form mounts with `toolkit-field-label-input`; `credential-form-save-button` `disabled: true` on the pristine form |
| 4-5 | Fill **Display Name** = `Autotest Embedding Model` | `toolkit-field-label-input` holds it; `toolkit-field-elitea_title-input` auto-fills `autotest_embedding_model` and stays **`disabled`** |
| 6a | Fill **Name** = `text-embedding-3-small` | `toolkit-field-name-input` holds it; Save is **still `disabled`** (the credential is the last gate — positive control) |
| 6b | Open `toolkit-credential-select--combobox`, pick the saved `ELPS` option | combobox text becomes `ELPS`; `credential-form-save-button` flips to **enabled** |
| 7 | Click `credential-form-save-button` | POST succeeds; the app navigates itself back to `/settings/ai-providers` |
| 8 | Find the new card in the Embedding Models section | count **3 → 4**; a card whose `ai-provider-configuration-card-name` equals `Autotest Embedding Model` exists; its concatenated text is `Autotest Embedding ModelOK • Local` |
| 9 | Open `ai-providers-section-embedding-models-default-selector-combobox` and read the options | an option `select-option-text-embedding-3-small<<>>400` exists, **labelled `Autotest Embedding Model`**, `aria-selected="false"` (the project default is unchanged) |

**Step 9 asserts inclusion only — the case does NOT ask to select it.** Do not
mutate the project's default embedding model; that keeps this test read-only with
respect to every other suite that reads it.

## Expected Results
1. An Embedding Model configuration is created from the "+" → Embedding model flow
   with Display Name + Name + an existing AI Credential.
2. The card appears in the **Embedding Models** section with the Display Name and an
   `OK • Local` status.
3. The new model is offered by the section's **Default** selector, keyed by its own
   `name` and the **active project's** id, and labelled with its Display Name.

## Coverage Map

### Axis 1 — every case element
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | covered (setup) |
| 1. Navigate Settings → AI Configuration | page loads | step 1 | `ai-providers-page-title` == `AI Providers` | covered (identity drift, #1250) |
| 2. Click "+" → select "Embedding Model" | next state shown | steps 2-3 | URL assertions + form present | covered (decomposed into the two real clicks) |
| 3. Fill in required fields | fields accept input | steps 4-6b | per-field value assertions | covered (decomposed) |
| 4. Display Name `Autotest Embedding Model` | accepted | step 4-5 | `toolkit-field-label-input` value | covered |
| 5. Name `text-embedding-3-small` | accepted | step 6a | `toolkit-field-name-input` value | covered |
| 6. Credentials: select an existing credential | accepted | step 6b | combobox text == `ELPS` | covered |
| 7. Click Save | next state shown | step 7 | URL back at `/settings/ai-providers` | covered |
| 8. New model card appears in Embedding Models | holds | step 8 | card-name node exists inside the embedding-models accordion; count 3 → 4 | covered |
| 9. Default embedding model dropdown includes the new model | holds | step 9 | `select-option-text-embedding-3-small<<>>{project_id}` present, labelled with the Display Name | covered |

### Axis 2 — asserted beyond the case
| Extra observable | Why (grounded) |
|---|---|
| Embedding card count 3 → 4 | proves a **create**, not a silent overwrite of the same-named shared model — the `name` deliberately duplicates an existing model, so identity has to be proven, not assumed |
| Save `disabled` before the credential is picked, enabled after | the credential is the last required gate; the transition is the honest proof the form knows the record is complete. Without it, "Save was clickable" proves nothing (cf. #1984, where a required field does NOT gate) |
| The `elitea_title` auto-derives to `autotest_embedding_model` and the ID field is `disabled` | the live read-only-ID contract already pinned by ELITEA-2409 for `llm_model`; asserting it here proves it is form-wide, not type-specific |
| The new option's `aria-selected` is `"false"` and the combobox label is unchanged | proves creation does **not** silently reassign the project default — a real regression risk this case would otherwise miss |
| No console errors on `/settings/ai-providers` and on the create form | verified live: a clean `goto` of each logs **0** errors. See § Automation Hints for the two expected exceptions |

## Cleanup (MANDATORY — this test mutates a shared project)

Delete the created configuration in a `finally`:
card → `controls-menu-button` → `delete-credentials-menuitem` → type the Display Name
into the **inner `input`** of `delete-confirm-name-input` → `delete-confirm-button`.
Verified live end to end; the Embedding Models count returns to 3.

⚠️ **Assert the console-error axis BEFORE teardown** — immediately after a delete the
app GETs the deleted record (`/api/v2/configurations/configuration/{project}/{id}`)
and logs a **404** console error (observed again this session).

## Concrete Handles (discovered live; **testid-only**, `.agents/testing.md` § Locator policy)

| Purpose | Handle | Provenance (fresh `git fetch origin`, 2026-08-29) |
|---|---|---|
| Page title | `ai-providers-page-title` | on-main ✓ |
| "+" create button | `sidebar-create-button` | on-main ✓ |
| Embedding-model type card | `toolkit-type-card-embedding_model` (dynamic `toolkit-type-card-{}`) | on-main ✓ |
| Display Name input | `toolkit-field-label-input` | on-main ✓ (template `testId={\`toolkit-field-${k}-input\`}`, `ToolBaseProperty.jsx`) |
| ID input (read-only) | `toolkit-field-elitea_title-input` | on-main ✓ (same template) |
| Name input | `toolkit-field-name-input` | on-main ✓ (same template) |
| Ai Credentials select | `toolkit-credential-select-` / clickable `toolkit-credential-select--combobox` | on-main ✓ — **the trailing dash is real** (`toolkit-credential-select-${type}` with an empty `type`) |
| Saved-credential option | `[data-testid='select-option-{{"kind":"saved","elitea_title":"{}","private":false}}']` | on-main ✓ (shared `Select` convention) |
| Save / Cancel | `credential-form-save-button` / `credential-form-discard-button` | on-main ✓ |
| Embedding Models section root | `ai-providers-section-embedding-models` | on-main ✓ |
| Embedding Models Default selector | `ai-providers-section-embedding-models-default-selector-combobox` | on-main ✓ |
| Default-selector option | `[data-testid="select-option-{name}<<>>{project_id}"]` — live `select-option-text-embedding-3-small<<>>400` | on-main ✓ |
| Card / card name | `ai-provider-configuration-card` / `-card-name` | on-main ✓ — use `AIProvidersPage.card_for_model()` (`.filter(has=…)`, never `has_text` on the outer card) |
| Delete flow | `controls-menu-button` → `delete-credentials-menuitem` → `delete-confirm-name-input` → `delete-confirm-button` | on-main ✓ (`delete-credentials-menuitem` is composed by `DotMenu.jsx:58` from `key: 'delete-credentials'`, present on `origin/main`; `delete-confirm-entity-name` is on `automation/testids` only and is not required by this case) |

**No new testid is required for this case.** The whole flow reuses handles the
ELITEA-2395/2396/2408/2409 wave already exercised.

## Network Behavior
- Page load fires the three GET shapes in `_surface.md` § Network.
- Save issues the create POST, then the app refetches
  `GET /api/v2/configurations/configurations/{project_id}?…` — the list re-renders
  from the refetch; **no manual reload**.
- `GET /api/v2/configurations/models/{project_id}?include_shared=true&section=embedding`
  is the honest oracle for both the starting card set and the default:
  observed `{"total": 3, …, "default_model_name": "text-embedding-3-small",
  "default_model_project_id": 1}`. Its `{project_id}` path segment is the honest
  oracle for the active project — **never hardcode `400`**.

## Known Defects Found During Exploration
- **EliteaAI/elitea-testing-public#1984** — required `Name` does not gate Save on this
  very form (recorded as a new occurrence in a comment this session; the issue was
  filed for `llm_model`, and the embedding form behaves identically). It does **not**
  affect this case, which fills Name. It is ELITEA-2410's subject.
- Post-delete 404 console error (above) — cosmetic refetch race, cleanup-only.

## Blocked Steps
None.

## Automation Hints
- Page objects already exist: `AIProvidersPage`
  (`automation/pages/ai_providers_page.py` — owns `create_button`, `click_type_card`,
  `card_for_model`, `configuration_cards`, `expand_section`,
  `embedding_models_section_header`, `embedding_models_default_selector`) and
  `AiProviderFormPage` (`automation/pages/ai_provider_form_page.py` — owns
  `navigate_to_create(provider_type)`, `select_saved_credential`,
  `save_and_return_to_list`, `delete_current_configuration`). **Extend, do not
  re-derive.** The only gap is a combobox descriptor for the embedding Default
  selector (`ai-providers-section-embedding-models-default-selector-combobox`) —
  the existing `embedding_models_default_selector` targets the FormControl wrapper,
  not the clickable node.
- **Name-collision is safe, and this is the subtle part.** The case's `Name`
  (`text-embedding-3-small`) equals an existing SHARED model's name, but every
  existing embedding model lives in **project 1** while the new one lives in the
  active project, and the option testid is
  `select-option-{name}<<>>{project_id}`. Live: `…<<>>1` (shared, selected) and
  `…<<>>400` (new) coexist as distinct options. Assert the **project-scoped** one —
  a bare `select-option-text-embedding-3-small` substring match would hit the wrong
  node and pass vacuously.
- **Do not `goto` the create route directly and `fill()` immediately** — the form is
  schema-driven and remounts after `GET /configurations/available/?section=…`
  resolves. Live this session: a `fill()` on `toolkit-field-label-input` seconds after
  a direct `goto` was **silently wiped** by the remount (the value read back empty and
  Save stayed disabled). `AiProviderFormPage.navigate_to_create()` already waits on
  the field; if a value still reads back empty, re-fill rather than assume a typo.
- **A dirty create form arms a native `beforeunload` dialog.** Register
  `page.on("dialog", lambda d: d.accept())` before touching the form (the pattern the
  four ELITEA-2395/… specs already use).
- **The delete dialog's `delete-confirm-name-input` testid is on a DIV wrapper**, not
  the native `<input>`. `AiProviderFormPage.delete_current_configuration()` handles
  this correctly by clicking the wrapper first (which focuses the inner input) and
  then `press_sequentially`. A bare `fill()`/`press_sequentially` without the click
  types nowhere and leaves the Delete button disabled — cost a turn this session.
- Console: `utils/console_errors.collect_console_errors()` (URL-bearing) plus the
  `#1971` URL-keyed filter (this flow drives project-scoped navigation). Walking the
  **type picker** logs exactly one React `key` `console.error` — **#656**; a direct
  `goto` of the typed create route avoids it, but this case's step 2 requires the
  picker, so filter #656 by its URL or assert the console axis on the list page only.
- Steps wrapped in `with allure.step("Step N — …")`. **Markers:** `ui`, `settings`,
  `p2`, `regression`, `new` (this folder maps l3 → `p2`).
