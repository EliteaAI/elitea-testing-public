# Test Case: Edit an existing Vector Storage configuration

## Metadata
- **TMS ID**: ELITEA-2400
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; folder mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` @ `a64d3308`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (`auth_state` fixture)
- **Analyst**: qa-engineer (analyst slot), 2026-08-29, batch `settings-w10`
- **Status**: ready-for-automation
- **Clarification**: EliteaAI/elitea-testing-public#1988 § 4 (precondition + irreversibility)
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## Case-identity note
"Settings → AI Configuration → Vector Storage section" = `/settings/ai-providers` →
the **Vector Storage** accordion. Page-identity drift already filed as #1250.

## Preconditions
- `auth_state` fixture.
- **The case's "an existing vector storage card" does not exist by default.** On the
  shared test projects the Vector Storage section is empty and therefore renders
  *nothing at all* (`ConfigurationSection.jsx` returns `null` for a zero-item section).
  The spec must **create the configuration it edits**, in the same UI, as declared
  transit — that is the identical interface the case's own subject uses, so no
  fidelity concern arises (`.agents/testing.md` § Fidelity policy: transit only, the
  case's own observable — the renamed card — is still produced by the system).
- **The project must already hold ≥1 OTHER vector storage** so the transit
  configuration can be deleted at teardown. Project 400 carries the seed
  **`Autotest PGVector Seed`** for this. See ELITEA-2399 § Known constraints for why
  (the `isLastInSection` delete guard). Guard it and **fail loudly** if the section is
  empty at test start.
- **This test MUTATES shared, live project configuration.** § Cleanup is mandatory.

## Test Data

| Field | Value | Note |
|---|---|---|
| Display Name (before) | `Autotest PGVector` | created as transit |
| Display Name (after) | `Autotest PGVector Edited` | the case's own value; 24 chars — **`maxlength="32"`, silent truncation**, so a per-run suffix must keep the LONGEST name ≤32 |
| Connection String | `postgresql://autotest:autotest@localhost:5432/autotest` | supplied at create time; **not re-asserted after edit** (see § Automation Hints) |

## Test Steps

| # | Action | Expected (verified live 2026-08-29) |
|---|---|---|
| 0 | *(transit)* Create a PGVector configuration named `Autotest PGVector` via "+" → `toolkit-type-card-pgvector` | card present in the Vector Storage section; count captured |
| 1 | `goto /settings/ai-providers`; expand the **Vector Storage** section | `ai-providers-section-vector-storage` present, `aria-expanded="true"` after the click |
| 2 | Click the `Autotest PGVector` card | URL → `/settings/edit-ai-provider/{id}?from=ai-providers` (live: `/39`) |
| 3 | Read the edit form's pre-populated values | `toolkit-field-label-input` == `Autotest PGVector`; `toolkit-field-elitea_title-input` == `autotest_pgvector` and **`disabled: true`**; `toolkit-field-connection_string-input-field` holds a **masked 32-hex placeholder**, `type="password"`; `credential-form-save-button` **and** `credential-form-discard-button` both `disabled: true` (pristine) |
| 4 | Replace Display Name with `Autotest PGVector Edited` | field holds it; Save **and** Discard both flip to `disabled: false`; the disabled ID field **re-derives** to `autotest_pgvector_edited` |
| 5 | Click `credential-form-save-button` | PUT succeeds; the app navigates itself back to `/settings/ai-providers` |
| 6 | Read the Vector Storage section | the card's `ai-provider-configuration-card-name` == `Autotest PGVector Edited`; **the card count is UNCHANGED** (update, not create); no card named `Autotest PGVector` remains |

## Expected Results
1. Clicking a Vector Storage card opens its edit form pre-populated with the stored
   values, in a pristine (Save/Discard disabled) state.
2. Changing the Display Name enables Save.
3. Saving updates the existing record in place — the card reflects the new Display
   Name and the section's card count does not change.

## Coverage Map

### Axis 1 — every case element
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | covered (setup) |
| Precondition (implicit): "an existing vector storage configuration" | exists | step 0 (declared transit) + the non-empty-section guard | card present before step 1 | covered — the case never states how it comes to exist; #1988 § 4 |
| 1. Navigate → Vector Storage section | section loads | step 1 | `ai-providers-section-vector-storage` visible | covered |
| 2. Click on an existing vector storage card | next state shown | step 2 | URL matches `/settings/edit-ai-provider/(\d+)` | covered |
| 3. Edit form opens with pre-populated values | holds | step 3 | label + ID values; both tab-bar buttons `disabled` | covered |
| 4. Update Display Name to `Autotest PGVector Edited` | accepted | step 4 | `toolkit-field-label-input` value | covered |
| 5. Click Save | next state shown | step 5 | URL back at `/settings/ai-providers` | covered |
| 6. Card reflects the updated Display Name | holds | step 6 | card-name node == the new name | covered |

### Axis 2 — asserted beyond the case
| Extra observable | Why (grounded) |
|---|---|
| Vector Storage card count is **unchanged** across the edit | the case's "edit" claim is only meaningful if it is an in-place update. Without this, a bug that saved a *copy* would still show "a card with the updated name" and pass |
| No card named `Autotest PGVector` (the OLD name) remains | the other half of the same proof, and it is the assertion a copy-on-save bug actually trips |
| Save **and** Discard are both `disabled` on the pristine form, and both enable on the first edit | pins the dirty-tracking contract. It is also the anti-flake guard: asserting "Save enabled" without first proving it was disabled cannot distinguish a real edit from a form that is always enabled (cf. #633 on the MCP form) |
| The disabled ID re-derives `autotest_pgvector` → `autotest_pgvector_edited` | live-observed client-side behaviour, and it is **not cosmetic** — see § Observations: the identity key really does change on the server, which changes the Default-selector option testid |
| The pre-populated Connection String is a **masked placeholder**, `type="password"` | records that the stored secret is never echoed back, so nobody later writes a round-trip assertion that would either fail or (worse) pass by leaking |
| No console errors on the edit form and the list page | verified live: 0 errors on both |

## Observations (not defects — recorded so nobody re-derives them)

- **Renaming a vector storage changes its `elitea_title` too.** Live, after step 5 the
  configurations API returned
  `{"id": 39, "label": "Autotest PGVector Edited", "elitea_title": "autotest_pgvector_edited", "type": "pgvector"}`.
  Because the Vector Storage Default selector keys its options by `elitea_title`
  (#1988 § 3), a rename **changes that option's testid**. A spec that captures an
  option testid before an edit and reuses it after will miss. Not filed — the ID field
  is documented as read-only-but-derived (#1985), and this is the consistent
  consequence.
- The edit form for pgvector has **no Ai Credentials picker** (unlike llm_model /
  embedding_model) — its schema declares only `connection_string`.

## Implementation amendment (2026-08-29, test-automation-engineer)

1. **The automation does not land on project 400.** The acting user's default project
   is 399 (`Private`), whose Vector Storage section is EMPTY (confirmed live from the
   product's own `section=vectorstorage` response: 399 → `total: 0`, 400 → `total: 1`).
   The spec switches to the seeded project through the sidebar project selector — a
   real user action, via `settings.ai_providers_seeded_project_id`.
2. **The transit create also assigns the section default.** Creating a Vector Storage
   configuration makes it the section's default (measured during ELITEA-2399's
   implementation). So this spec's step 0 mutates the default even though the case
   never mentions it; the pre-existing default is captured before the create and
   restored in the `finally`, before the delete.
3. **Card counts are section-scoped.** A whole-page `ai-provider-configuration-card`
   count is not comparable across the app's own navigation back from a Save (the LLMs
   accordion auto-expands only on a fresh page load — measured 15 before / 4 after).
   `AIProvidersPage.isolate_section()` collapses every section and expands one.

## Cleanup (MANDATORY — this test mutates a shared project)

Delete the (renamed) configuration in a `finally`, **using the name it has at teardown
time**: card → `controls-menu-button` → `delete-credentials-menuitem` → type
`Autotest PGVector Edited` into the **inner `input`** of `delete-confirm-name-input` →
`delete-confirm-button`. Verified live.

⚠️ The confirm dialog requires the **current** Display Name. A `finally` that always
types the pre-edit name will fail whenever the test got past step 5 — track the name
in a variable that step 4 updates, and make the teardown tolerant of either.

⚠️ Deletion only succeeds while another vector storage exists (§ Preconditions).

⚠️ **The `default_changed` guard is raised on the line immediately after the transit
create**, before any assertion about it. Anything in between is a path on which a flake
skips `restore_section_default(...)` while the `finally` still deletes the configuration
that is now the default — leaving the shared seeded project with NO default, which makes
the sibling specs (ELITEA-2399/2401) refuse to run. Pinned by
`tests/unit/test_default_changed_guard_is_set_at_the_mutation.py` (PR #1989 review).

⚠️ Assert the console-error axis **before** teardown (post-delete 404 refetch).

## Concrete Handles (discovered live; **testid-only**)

| Purpose | Handle | Provenance (fresh `git fetch origin`, 2026-08-29) |
|---|---|---|
| Vector Storage section root | `ai-providers-section-vector-storage` | on-main ✓ |
| Card / card name | `ai-provider-configuration-card` / `-card-name` | on-main ✓ — identify via `AIProvidersPage.card_for_model()`'s `.filter(has=…)` shape, never `has_text` on the outer card (its text concatenates name+status with no separator) |
| Edit route | URL pattern `/settings/edit-ai-provider/(\d+)` (`AiProviderFormPage.EDIT_URL_PATTERN`) | n/a (route) |
| Display Name / ID inputs | `toolkit-field-label-input` / `toolkit-field-elitea_title-input` | on-main ✓ |
| Connection String native input | `toolkit-field-connection_string-input-field` | on-main ✓ (`SecretField.jsx:77`) |
| Save / Discard | `credential-form-save-button` / `credential-form-discard-button` | on-main ✓ |
| Delete flow | `controls-menu-button` → `delete-credentials-menuitem` → `delete-confirm-name-input` → `delete-confirm-button` | on-main ✓ |
| Delete-dialog entity name (optional cross-check) | `delete-confirm-entity-name` | **on `automation/testids` only** — live it read `Autotest PGVector Edited`, a cheap extra confirmation that the right record is being deleted |

**No new testid is required for this case.**

## Network Behavior
- Clicking the card fires `GET /api/v2/configurations/configuration/{project_id}/{id}`
  — the record that pre-populates the form.
- Save issues the update, then the app refetches the combined configurations GET and
  re-renders in place. No manual reload.
- `GET /api/v2/configurations/configurations/{project_id}?section=vectorstorage&…` is
  the honest oracle for the persisted `label`/`elitea_title` pair if the spec wants to
  prove the update server-side rather than only in the DOM.

## Known Defects Found During Exploration
- **#1987** (Vector Storage cards never show the `Default` badge) — visible on this
  page but not asserted by this case.
- Post-delete 404 console error (cleanup-only, cosmetic).

## Blocked Steps
None.

## Automation Hints
- Reuse `AIProvidersPage.open_model_card()` (clicks a card by display name) and
  `AiProviderFormPage.wait_for_form()` / `configuration_id_from_url()` /
  `save_and_return_to_list()` / `delete_current_configuration()`.
- **Do not assert the Connection String after the edit.** It comes back masked
  (`writeOnly`), so any equality against the typed URI fails, and any equality against
  the placeholder pins a value that is regenerated.
- Register `page.on("dialog", lambda d: d.accept())` — the edit form is dirty from
  step 4 onward and arms `beforeunload`.
- `delete-confirm-name-input`'s testid is on a DIV wrapper — click first, then
  `press_sequentially`.
- Keep the longest Display Name ≤ 32 characters (`maxlength`, silent truncation) —
  `Autotest PGVector Edited` is 24, leaving 8 for a run suffix.
- Console: `collect_console_errors()` + the `#1971` URL filter. A direct `goto` of the
  create route (step 0) avoids the type picker's `#656` error entirely.
- `with allure.step("Step N — …")`. **Markers:** `ui`, `settings`, `p2`, `regression`,
  `new`.

### Page-object work shipped by this implementation (2026-08-29)

Additive only; every existing method kept its merged callers unchanged.

| Where | What | Why |
|---|---|---|
| `AIProvidersPage` | `embedding_models_default_selector_combobox`, `vector_storage_default_selector_combobox` | the clickable/readable `-combobox` node; the pre-existing `*_default_selector` fields target the FormControl wrapper |
| `AIProvidersPage` | `isolate_section()` / `collapse_section()` / `all_section_headers()` | a section-scoped card count. `get_configuration_card_count()` counts the WHOLE page, and the whole-page total is NOT comparable across the app's own navigation back from a Save (LLMs auto-expands only on a fresh load — measured 15 before / 4 after) |
| `AIProvidersPage` | `select_option()`, `open_select_options`, `close_open_dropdown()`, `SELECT_OPTION_PREFIX_SELECTOR` | inspect a dropdown's option set without selecting. ⚠️ the bare `select-option-` prefix ALSO matches the shared `SingleSelect`'s `select-option-selected-icon` checkmark — the constant excludes it |
| `AIProvidersPage` | `navigate_and_capture_section_models_response(section)`, `project_id_from_models_response()`, `select_default_configuration()` | section-agnostic siblings of the ELITEA-2397 LLM-specific helpers; the project id is read from the product's own request URL, never hardcoded |
| `AiProviderFormPage` | `wait_for_schema_field(field_key)` | `wait_for_form()` settles on the PRE-schema shell, so the schema-driven re-render wipes anything typed in the gap — measured: Display Name typed AND asserted, Save observed enabled, still disabled 10 s later at the click |
| `AiProviderFormPage` | `set_schema_field()`, `fill_secret_field()` | focus-confirmed typing (`press_sequentially` could start before the click's focus settled and drop the first keystroke — `text-embedding-3-small` arrived as `ext-embedding-3-small`) and a blur after a secret field (MUI commits some schema-typed fields only on blur) |
| `BasePage` | `ensure_project_selected()` | `switch_project()` settles on `networkidle` + a fixed 1 s pause, which is the `#1847` mechanism. This waits on the two project-scoped GETs a switch actually fires — the shape `AdminUsersPage.ensure_team_project_selected` proved live in settings-w09 |
| `utils/ai_provider_teardown.py` | `delete_configurations_if_present()`, `restore_section_default()` | the same `finally` was about to be copied a 4th time (Hard Rule 7) |
