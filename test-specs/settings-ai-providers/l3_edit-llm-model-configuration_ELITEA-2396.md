# Test Case: Edit an existing LLM model configuration

## Metadata
- **TMS ID**: ELITEA-2396
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; folder mapping — ELITEA-2392/2397)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` @ `7418c06f`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (`auth_state` fixture)
- **Analyst**: qa-engineer (analyst slot), 2026-08-29, batch `settings-w10`
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## Case-identity note
"Settings → AI Configuration → LLM Models section" = **Settings → AI Providers**
(`/settings/ai-providers`) → the **LLMs** accordion. Page-identity drift already
filed as EliteaAI/elitea-testing-public#1250 (ELITEA-2392); not re-filed here.

## Preconditions
- `auth_state` fixture.
- **The test edits a model IT CREATED, not "any existing card".** The case says
  "any existing LLM model card"; renaming a shared, live model (e.g. the project
  Default `GPT-5.6 Luna`) would alter what every other UI test reads. The
  behaviour under test — *editing an existing configuration* — is identical, and
  a self-created subject makes the case safely repeatable. Declared deviation.
- Requires a usable AI Credential (shared `ELPS`, see ELITEA-2395 § Preconditions).

## Test Data

| Field | Value |
|---|---|
| Seed model Display Name | `Autotest LLM Model <run-suffix>` |
| Seed model Name | `gpt-4o` |
| Seed credential | saved `elps` |
| Edited Display Name | `Autotest LLM Model Edited <run-suffix>` (case: `Autotest LLM Model Edited`) |

## Test Steps

| # | Action | Expected (verified live 2026-08-29) |
|---|---|---|
| 0 | **Setup** — create the seed model through the UI ("+" → LLM Model → fill → Save), as ELITEA-2395 step 2-10 | card present in the LLMs section |
| 1 | Be on `/settings/ai-providers` with the LLMs section rendered | `ai-providers-section-llms` present; the seed card exists |
| 2 | Click the seed model's `ai-provider-configuration-card` | navigates to `/settings/edit-ai-provider/{id}?from=ai-providers` |
| 3 | Read every form field | **pre-populated**: `toolkit-field-label-input` = seed Display Name, `toolkit-field-elitea_title-input` = `autotest_llm_model…` (disabled), `toolkit-field-name-input` = `gpt-4o`, `toolkit-field-context_window-input` = `128000`, `toolkit-field-max_output_tokens-input` = `16000`, credential combobox = `ELPS`. `credential-form-save-button` is **disabled while pristine**; `credential-form-discard-button` likewise |
| 4 | Fill `toolkit-field-label-input` with the edited Display Name | value updates; Save + Discard become **enabled**; the read-only ID field **re-derives** to `autotest_llm_model_edited…` (see § Known Defects) |
| 5 | Click `credential-form-save-button` | PUT succeeds; app navigates back to `/settings/ai-providers` |
| 6 | Re-read the LLMs section | a card named with the **edited** Display Name exists; **no** card with the old Display Name remains; **the card count is unchanged** |

## Expected Results
1. Clicking a configuration card opens its edit form at
   `/settings/edit-ai-provider/{id}`, pre-populated with the stored values.
2. Save is inert until the form is dirtied.
3. Saving a changed Display Name updates the existing record in place — the card
   in the LLMs section reflects the new name and the section count does not grow.

## Coverage Map

### Axis 1 — every case element
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` | fixture | covered (setup) |
| 1. Navigate to the LLM Models section | loads | step 1 | `ai-providers-section-llms` visible | covered (identity drift #1250) |
| 2. Click any existing LLM model card | responds | step 2 | URL matches `/settings/edit-ai-provider/\d+` | covered (subject is self-created — see § Preconditions) |
| 3. Edit form opens pre-populated with current values | holds | step 3 | all six field values + credential label | covered (decomposed per field) |
| 4. Change Display Name to `Autotest LLM Model Edited` | accepted | step 4 | input value; Save transitions disabled→enabled | covered |
| 5. Click Save | responds | step 5 | URL back at `/settings/ai-providers` | covered |
| 6. Card reflects the updated Display Name | holds | step 6 | card-name present for new, absent for old | covered |

### Axis 2 — asserted beyond the case
| Extra observable | Why (grounded) |
|---|---|
| Card count unchanged across the edit | proves an **update**, not a create-and-orphan. Live count stayed 13 — without this, a regression that creates a duplicate passes step 6 |
| Old Display Name is **absent** afterwards | the complement of the above; an absence assertion is a first-class reference (`.agents/testing.md`, #511 extension) |
| Save/Discard disabled while pristine | the dirty-state contract; the case's step 5 is meaningless if Save was always clickable |
| No console errors up to (not after) teardown | the post-delete 404 refetch is a teardown-only artifact — see ELITEA-2395 § Known Defects |

## Cleanup (MANDATORY)
Delete the edited model: card → `controls-menu-button` →
`delete-credentials-menuitem` → type the **current** (edited) Display Name into
`delete-confirm-name-input` → `delete-confirm-button`. In a `finally`; the
cleanup must look up the name it is deleting rather than assume which of the two
names is live, so a failure between steps 4 and 6 still tears down.

## Concrete Handles
Same inventory as
`test-specs/settings-ai-providers/l3_create-llm-model-configuration_ELITEA-2395.md`
§ Concrete Handles (all **on-main ✓**, verified with a fresh `git fetch origin`
2026-08-29). Additional to that list:

| Purpose | Handle | Provenance |
|---|---|---|
| Edit route | URL `/settings/edit-ai-provider/{configuration_id}?from=ai-providers` | n/a (URL, not a locator) |
| Pristine-state gate | `credential-form-save-button` / `credential-form-discard-button` `disabled` property | on-main ✓ |

**No new testid is required for this case.**

## Network Behavior
- Card click is a client-side route change plus a
  `GET /api/v2/configurations/configuration/{project_id}/{id}` for the record.
- Save issues the update request, then the list refetch documented in
  `_surface.md` § Network drives the re-render — no reload needed.

## Known Defects Found During Exploration
- **Observation, not filed — the ID (`elitea_title`) re-derives on rename.**
  Editing the Display Name silently rewrites the read-only ID field
  (`autotest_llm_model` → `autotest_llm_model_edited`), even though the input is
  `disabled`. An identifier that changes when a *display* label changes is
  suspicious, but nothing observable in this case's scope broke, and the AFS does
  not know what consumes `elitea_title`. **Recorded here rather than filed** —
  raise it to the lead if a later case shows a stale reference after a rename.
  The test should assert the ID field's live behaviour (it mirrors the label),
  not a guess about what it *ought* to do.
- ELITEA-2408's defect (#1984) lives on the create form; it does not gate this case.

## Blocked Steps
None.

## Automation Hints
- Reuse `AIProvidersPage.card_for_model()` — the outer card's concatenated text
  is `"<name>OK • Local"` with no separator, so `has_text` on the card never
  matches; filter by the `-card-name` child (`_surface.md`).
- The seed step is UI-driven on purpose: seeding via API would be a
  wrong-interface precondition for a case whose subject is the UI edit of a
  UI-created record. It is transit only — the case's own observable (the renamed
  card) still comes from the product.
- Same `beforeunload` and slow-form-mount cautions as ELITEA-2395 § Automation Hints.
- `with allure.step("Step N — …")` per step; markers `p3`, `regression`, settings.
