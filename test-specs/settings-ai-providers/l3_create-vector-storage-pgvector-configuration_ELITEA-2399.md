# Test Case: Create a new Vector Storage (PGVector) configuration

## Metadata
- **TMS ID**: ELITEA-2399
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; folder mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` @ `a64d3308`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (`auth_state` fixture)
- **Analyst**: qa-engineer (analyst slot), 2026-08-29, batch `settings-w10`
- **Status**: ready-for-automation
- **Clarification**: EliteaAI/elitea-testing-public#1988 (filed this session)
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## Case-identity + case-text drift (read first — filed as #1988)

- "Settings → AI Configuration" is **AI Providers** (`/settings/ai-providers`) — page
  identity already filed as #1250, not re-filed.
- **Steps 2-3 are one step, not two.** The case says *"Click '+' → select 'Vector
  Storage'"* then *"Select provider: PGVector"*. Live, `sidebar-create-button` opens a
  **flat 12-card type picker with no 'Vector Storage' entry**; the card is
  **"PgVector"** (`toolkit-type-card-pgvector`) and one click lands on
  `/settings/create-ai-provider/pgvector`. "Vector Storage" is the name of the
  **accordion section on the list page**, not a picker entry.
- **Step 9's dropdown shows the `elitea_title`, not the Display Name.** The Vector
  Storage Default selector labels its options with the configuration **ID**
  (`autotest_pgvector`), unlike every other section which shows a display name. This
  is a consequence of pgvector configurations carrying no `data.name` (see #1987).
- Per the reverse-masking guard this AFS asserts the **live** contract.

## Preconditions
- `auth_state` fixture.
- **The project must already have ≥1 Vector Storage configuration** before this test
  runs — see § Known constraints. On project 400 this session established the seed
  **`Autotest PGVector Seed`** (`autotest_pgvector_seed`) for exactly this purpose.
  ⚠️ **Amended (implementation):** the automation does NOT land on project 400 — the
  acting user's default project is 399 (`Private`), whose Vector Storage section is
  EMPTY (confirmed live from the product's own `section=vectorstorage` response: 399 →
  `total: 0`, 400 → `total: 1`). The spec therefore switches to the seeded project
  through the sidebar project selector — a real user action, and the same
  `settings.ai_providers_seeded_project_id` mechanism several merged specs already use
  for project-specific preconditions.
- **This test MUTATES shared, live project configuration.** § Cleanup is mandatory.

## Known constraints — the first Vector Storage in a project is UNDELETABLE

`CredentialsControls.jsx:51,63` —
```js
const isProtectedSection = section === 'vectorstorage' || section === 'embedding';
const isLastInSection = isProtectedSection && totalAvailable <= 1;
// delete menu item: disabled: isDeleting || !credentialDetails?.id || isLastInSection
```
tooltip: *"Cannot delete the only pgVector configuration. At least one is required for
the project."* `totalAvailable` = own total + **shared** total.

Vector Storage has **no shared configurations** (Embedding has 3, which is why
ELITEA-2398's cleanup is unconditionally safe). So a project going 0 → 1 vector
storages **cannot go back to 0 through the UI**. Verified live this session: with one
configuration left, `delete-credentials-menuitem` renders `aria-disabled="true"`; after
creating a second, it became clickable immediately.

**Consequence for this spec:** it must run against a project that already has ≥1
vector storage, so the one it creates is never last-in-section and cleanup always
succeeds. Guard it explicitly rather than assuming — if the section is absent/empty at
test start, **fail loudly** with a clear message instead of creating an
unremovable artifact. (Routed to a human on #1988 § 4.)

## Test Data

| Field | Value | Note |
|---|---|---|
| Display Name | `Autotest PGVector` | the case's own value; 17 chars — keep any per-run suffix inside `maxlength="32"` |
| Connection String | `postgresql://autotest:autotest@localhost:5432/autotest` | the case asks for "a valid PostgreSQL connection string". **Nothing connects to it** — `has_test_connection: false` for pgvector and the Test-connection button stays disabled, so it is never dialled. Any well-formed URI works |

## Test Steps

| # | Action | Expected (verified live 2026-08-29) |
|---|---|---|
| 1 | `goto /settings/ai-providers`; expand **Vector Storage**; capture the card count | `ai-providers-section-vector-storage` present (precondition guard); N cards |
| 2 | Click `sidebar-create-button` | URL → `/settings/create-ai-provider?viewMode=owner&from=ai-providers`; 12-card picker |
| 3 | Click `toolkit-type-card-pgvector` | URL → `/settings/create-ai-provider/pgvector?viewMode=owner&from=ai-providers`; form mounts with `toolkit-field-label-input`; Save `disabled: true` on the pristine form. **There is no provider sub-picker** — case step 3 is satisfied by this same click |
| 4-5 | Fill **Display Name** = `Autotest PGVector` | `toolkit-field-label-input` holds it; `toolkit-field-elitea_title-input` auto-fills `autotest_pgvector`, stays `disabled` |
| 6 | Fill **Connection String** into `toolkit-field-connection_string-input-field` | value length matches what was typed; the native input's `type` is **`password`** (a secret field, `writeOnly` in the schema) |
| 7 | Click `credential-form-save-button` | POST succeeds; the app navigates itself back to `/settings/ai-providers` |
| 8 | Find the new card in the Vector Storage section | count N → **N+1**; a card whose `ai-provider-configuration-card-name` equals `Autotest PGVector`; concatenated text `Autotest PGVectorOK • Local` |
| 9 | Open `ai-providers-section-vector-storage-default-selector-combobox` and read the options | an option `select-option-autotest_pgvector<<>>400` exists, **labelled `autotest_pgvector`** (the ID, not the Display Name), and it is **`aria-selected="true"`** — the product ASSIGNS a newly created vector storage as the section default (amended, see § Implementation amendment) |

**Step 9 asserts inclusion only** — the case does not ask to select it. Selecting is
ELITEA-2401's subject.

## Expected Results
1. A PGVector Vector Storage configuration is created from the "+" → PgVector flow
   with a Display Name and a Connection String.
2. The card appears in the **Vector Storage** section with the Display Name and an
   `OK • Local` status.
3. The new configuration is offered by the section's **Default** selector, keyed by
   `{elitea_title}<<>>{project_id}`.

## Coverage Map

### Axis 1 — every case element
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | covered (setup) |
| 1. Navigate Settings → AI Configuration | page loads | step 1 | `ai-providers-page-title` == `AI Providers` | covered (identity drift, #1250) |
| 2. Click "+" → select "Vector Storage" | next state shown | steps 2-3 | URL assertions | covered — **live has no "Vector Storage" card**; drift #1988 § 2 |
| 3. Select provider: PGVector | next state shown | step 3 | URL == `/settings/create-ai-provider/pgvector?…` | covered — same single click as the row above; drift #1988 § 2 |
| 4. Fill in required fields | fields accept input | steps 4-6 | per-field value assertions | covered (decomposed) |
| 5. Display Name `Autotest PGVector` | accepted | step 4-5 | `toolkit-field-label-input` value | covered |
| 6. Connection String: valid PostgreSQL string | accepted | step 6 | value length on the native secret input | covered — the value itself cannot be read back (`writeOnly`), see § Automation Hints |
| 7. Click Save | next state shown | step 7 | URL back at `/settings/ai-providers` | covered |
| 8. New vector storage card appears in Vector Storage | holds | step 8 | card-name node inside the vector-storage accordion; count N → N+1 | covered |
| 9. Default vector storage dropdown includes the new configuration | holds | step 9 | `select-option-autotest_pgvector<<>>{project_id}` present | covered — label is the **ID**, drift #1988 § 3 |

### Axis 2 — asserted beyond the case
| Extra observable | Why (grounded) |
|---|---|
| Vector Storage card count N → N+1 | proves a **create**, not an in-place update of an existing configuration — ELITEA-2400 exercises the update path and the two must stay distinguishable |
| Save `disabled` on the pristine form, enabled after Display Name is typed | the honest gate proof. Note it becomes enabled on Display Name **alone** — Connection String does not gate it (schema-optional, ELITEA-2411/#1988 § 1) |
| The native Connection String input's `type == "password"` | pins the secret handling; a regression that renders it as plain text would leak a DB URI into screenshots and DOM dumps |
| The new option's `aria-selected` is `"true"`, the combobox label is the new `elitea_title`, and the PREVIOUS default is still offered with `aria-selected="false"` | **amended — see § Implementation amendment.** Creation DOES reassign the section default here. Asserting it (plus the previous default's continued presence and de-selection) pins the exclusivity contract and makes the mutation visible instead of silent |
| Precondition guard: the Vector Storage section is non-empty at test start | not decorative — without it the spec can create a permanently unremovable configuration (§ Known constraints) |
| No console errors on the list page | verified live: clean `goto` logs **0** errors |

## Implementation amendment (2026-08-29, test-automation-engineer)

**Creating a Vector Storage configuration ASSIGNS it as the section's default.**
Measured live during implementation: with `autotest_pgvector_seed` the default before
the create, the combobox read `autotest_pgvector_<run>` immediately after, with no
selection made. This contradicts the Axis-2 row this AFS originally carried
("creation does not silently reassign the project default"), which was written from
the analyst's `aria-selected` reading of a different moment.

Consequences, all applied to the spec:
1. Step 9 asserts the LIVE contract (`aria-selected="true"` on the new option, the
   combobox showing its `elitea_title`) per the reverse-masking guard.
2. **§ Cleanup gains a restore step:** the pre-existing default is captured from the
   product's own `section=vectorstorage` response at step 1 and re-selected BEFORE the
   delete. Without it the spec silently mutates state the rest of the suite reads.
3. The spec **refuses to run when the section has no default at start** — the selector
   offers no blank option, so that state could not be restored.
4. This differs from the LLMs section, where ELITEA-2395 must assign the new model
   explicitly. Recorded as an observation, not filed: no case asserts it either way.

## Cleanup (MANDATORY — this test mutates a shared project)

**Restore the section's original default FIRST** (captured at step 1), then delete the
created configuration in a `finally`: card → `controls-menu-button` →
`delete-credentials-menuitem` → type the Display Name into the **inner `input`** of
`delete-confirm-name-input` → `delete-confirm-button`. Verified live; the count
returns to N.

⚠️ **Cleanup can only succeed while another vector storage exists** (§ Known
constraints). If the delete menu item is disabled, the precondition guard was skipped
— surface that as a failure with the tooltip text, do not swallow it.

⚠️ Assert the console-error axis **before** teardown (post-delete 404 refetch).

## Concrete Handles (discovered live; **testid-only**)

| Purpose | Handle | Provenance (fresh `git fetch origin`, 2026-08-29) |
|---|---|---|
| Page title / "+" button | `ai-providers-page-title` / `sidebar-create-button` | on-main ✓ |
| PgVector type card | `toolkit-type-card-pgvector` (dynamic `toolkit-type-card-{}`) | on-main ✓ |
| Display Name / ID inputs | `toolkit-field-label-input` / `toolkit-field-elitea_title-input` | on-main ✓ (`ToolBaseProperty.jsx` template) |
| Connection String — outer wrapper | `toolkit-field-connection_string-input` (a **DIV**, the MUI TextField root) | on-main ✓ (same template) |
| Connection String — **native input (use this to type)** | `toolkit-field-connection_string-input-field` | on-main ✓ — derived by `SecretField.jsx:77` (`\`${inputProps['data-testid']}-field\``) |
| Connection String inline error | `toolkit-field-connection_string-input-helper-text` | on-main ✓ (`SecretField.jsx:88`, same derivation) |
| Secret/Password toggles | `toolkit-field-connection_string-input-toggle-secret` / `-toggle-password` | **on `automation/testids` only** (`SecretField.jsx:342` `testIdPrefix`) — not needed by this case |
| Save / Cancel / Test connection | `credential-form-save-button` / `-discard-button` / `-test-connection-button` | first two on-main ✓; **`-test-connection-button` on `automation/testids` only** — not needed (pgvector's `has_test_connection` is `false`, the button stays disabled) |
| Vector Storage section root | `ai-providers-section-vector-storage` | on-main ✓ — **only renders when the section has ≥1 item** |
| Vector Storage Default selector | `ai-providers-section-vector-storage-default-selector-combobox` | on-main ✓ (derived from the threaded `sectionTestId`) |
| Default-selector option | `[data-testid="select-option-{elitea_title}<<>>{project_id}"]` — live `select-option-autotest_pgvector<<>>400` | on-main ✓ |
| Card / card name | `ai-provider-configuration-card` / `-card-name` | on-main ✓ |
| Delete flow | `controls-menu-button` → `delete-credentials-menuitem` → `delete-confirm-name-input` → `delete-confirm-button` | on-main ✓ |

**No new testid is required for this case.**

## Network Behavior
- `GET /api/v2/configurations/available/?section=vectorstorage` returns the pgvector
  schema — the honest oracle for which fields exist and which are required. Observed
  `config_schema.properties.data.properties == {connection_string}` with **no
  `data.required` array**, and top-level `required == ["elitea_title","label","type","data"]`.
- `GET /api/v2/configurations/models/{project_id}?include_shared=true&section=vectorstorage`
  is the oracle for the section's contents and current default. After this create,
  observed `{"total": 2, "items": [{"name": "autotest_pgvector", "project_id": 400,
  "shared": false, "default": false}, …]}` — note `name` here is the **elitea_title**.
- Save issues the create POST; the app refetches the combined configurations GET and
  re-renders. No manual reload.
- Never hardcode `400` — read it from the `{project_id}` path segment.

## Known Defects Found During Exploration
- **EliteaAI/elitea-testing-public#1987** — a Vector Storage card never gets the
  `Default` badge (configKey/selector-key mismatch). Does not affect this case, which
  only asserts dropdown **inclusion**. It is ELITEA-2401's subject.
- **#1988 § 1** — Connection String is not schema-required; ELITEA-2411's premise.
  Does not affect this case, which supplies one.
- Post-delete 404 console error (cleanup-only, cosmetic).

## Blocked Steps
None.

## Automation Hints
- Reuse `AiProviderFormPage.navigate_to_create("pgvector")` — it already waits on
  `toolkit-field-label-input` rather than on navigation/`networkidle`.
- **Type into `toolkit-field-connection_string-input-field`, never the wrapper.** The
  `toolkit-field-connection_string-input` testid is on the MUI TextField root DIV; a
  `fill()` on it fails or types nowhere. The `-field` suffix is `SecretField`'s own
  derived handle for the native input — this is the sanctioned testid-only shape, no
  raw-CSS chain needed.
- **The value cannot be read back after save.** Re-opening the record shows a masked
  32-hex placeholder (observed `62ac1990453041258fcbeea7a0bafe8a`), not the typed URI
  (`writeOnly: true`). Assert the typed length/value only **before** Save; never assert
  a round-trip.
- **Do not `goto` the create route and `fill()` immediately.** The schema-driven form
  remounts and silently wipes an early value — hit live this session (the Display Name
  read back empty and Save stayed disabled). Wait on the field, and if a value reads
  back empty, re-fill.
- Register `page.on("dialog", lambda d: d.accept())` for the `beforeunload` trap.
- `delete-confirm-name-input`'s testid is on a DIV wrapper — click it first, then
  `press_sequentially` (`AiProviderFormPage.delete_current_configuration()` already
  does this correctly).
- Page objects: extend `AIProvidersPage` with a `vector_storage_default_selector_combobox`
  descriptor (only `vector_storage_section_header` exists today — the section was empty
  on every project when that page object was written, so its selector was never
  observed).
- Console: `collect_console_errors()` + the `#1971` URL filter; `#656` fires only via
  the type picker, which step 2 requires.
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
