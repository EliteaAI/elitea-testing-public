# Test Case: Set a Vector Storage as default

## Metadata
- **TMS ID**: ELITEA-2401
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; folder mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` @ `a64d3308`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (`auth_state` fixture)
- **Analyst**: qa-engineer (analyst slot), 2026-08-29, batch `settings-w10`
- **Status**: **ready-for-automation (sanctioned-RED)** — see § Classification note
- **Defect**: EliteaAI/elitea-testing-public#1987 (OPEN, filed this session)
- **Clarification**: EliteaAI/elitea-testing-public#1988 § 3-4
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## Classification note — declared improvisation (`.agents/testing.md` § Merge gate, *Analysis-time entry*)

Steps 1-4 **pass**: the Default selector opens, a different configuration can be
selected, the selection persists (`POST /configurations/models/{project_id}` → 200) and
the combobox label updates. Step 5 — *"Verify the selected card gains a 'Default'
badge"* — **fails on a real product defect**: no Vector Storage card ever renders an
`ai-provider-configuration-badge`.

The defect is deterministic (reproduced on every observation, including after cleanup
with a single configuration that *is* the default), single-cause (one key-derivation
mismatch, root-caused below and in #1987), linked to an OPEN issue, and does **not**
block exploration. Therefore, per `.agents/testing.md` § Merge gate → *Analysis-time
entry (2026-07-23, #557/ELITEA-1965)*, this AFS is `ready-for-automation`, **not**
`defect-found`, and the implementer writes step 5 as the **correct expected
behaviour** using `expect.soft()` + `# Known defect: #1987`. Steps 1-4 keep reporting
and the spec flips green when the product is fixed.

⚠️ A soft-assert failure **is** a pytest FAILURE (`.agents/testing.md`, verified
in-venv 2026-08-22): this spec is sanctioned-RED, owes a closure-record entry, and its
case status stays `blocked-on-#1987` rather than `automated`.

**Root cause** (`ConfigurationSection.jsx:212`, the non-grouped branch Vector Storage
uses):
```js
const configKey = `${configuration.data?.name || configuration.label}<<>>${configuration.project_id}`;
isDefault={defaultSettingValue === configKey}
```
A pgvector configuration has **no `data.name`** (its schema declares only
`connection_string`; the API returns `"name": null`), so `configKey` falls back to the
**label** — `Autotest PGVector Seed<<>>400`. But `defaultSettingValue` comes from the
models API, which keys vector storages by **`elitea_title`** —
`autotest_pgvector_seed<<>>400`. They can never be equal. Every other section supplies
`data.name` and renders the badge correctly.

## Case-identity note
"Settings → AI Configuration" = `/settings/ai-providers` (#1250). The *"Default vector
storage" dropdown* is `ai-providers-section-vector-storage-default-selector-combobox`,
inside the **Vector Storage** accordion (which must be expanded first — accordion
content unmounts on collapse).

## Preconditions
- `auth_state` fixture.
- **The project must hold ≥2 Vector Storage configurations** — step 3 says *"Select a
  **different** vector storage configuration"*, which is unsatisfiable with one. On
  the shared projects the section starts **empty**, so the spec must create what it
  needs (declared transit, same UI interface — `.agents/testing.md` § Fidelity policy:
  the case's own observables, the combobox label and the badge, are still produced by
  the system).
- Project 400 carries a permanent seed **`Autotest PGVector Seed`**
  (`autotest_pgvector_seed`); the spec creates **one** more and selects between them.
  See ELITEA-2399 § Known constraints for why the seed cannot be removed.
- **This test MUTATES the project's default vector storage**, which is shared state.
  § Cleanup is mandatory.

## Test Data

| Field | Value | Note |
|---|---|---|
| Transit configuration Display Name | `Autotest PGVector Alt <suffix>` | keep ≤32 chars (`maxlength`, silent truncation) |
| Transit Connection String | `postgresql://autotest:autotest@localhost:5432/autotest` | never dialled (`has_test_connection: false`) |

## Test Steps

| # | Action | Expected (verified live 2026-08-29) |
|---|---|---|
| 0 | *(transit)* Ensure ≥2 vector storages: create one via "+" → `toolkit-type-card-pgvector` if needed | Vector Storage section holds ≥2 cards |
| 1 | `goto /settings/ai-providers`; expand **Vector Storage**; **capture the current default** from `GET …&section=vectorstorage`'s `default_model_name` | section renders; combobox label == the current default's `elitea_title` (live: `autotest_pgvector`) |
| 2 | Click `ai-providers-section-vector-storage-default-selector-combobox` | a `listbox` opens with one `select-option-{elitea_title}<<>>{project_id}` per configuration; the current default carries `aria-selected="true"` |
| 3 | Click the option for a **different** configuration | `POST /api/v2/configurations/models/{project_id}` → **200**; the list refetches |
| 4 | Read the combobox label | updates to the newly selected configuration's **`elitea_title`** (live: `autotest_pgvector` → `autotest_pgvector_2411`) ✅ |
| 4b | Read `GET …&section=vectorstorage` after the POST | the selected item has `"default": true` and `default_model_name` == its `elitea_title` — the honest, product-produced proof the assignment persisted ✅ |
| 5 | Read the selected configuration's card for an `ai-provider-configuration-badge` reading `Default` | **badge expected; live there is NO badge on any Vector Storage card** ❌ — `expect.soft()` + `# Known defect: #1987` |

## Expected Results
1. The Default vector storage dropdown lists every configured vector storage, with the
   current default marked selected.
2. Selecting a different one persists immediately (no separate Save) and the dropdown
   label updates.
3. The selected configuration's card gains a `Default` badge. **(Currently violated —
   #1987.)**

## Coverage Map

### Axis 1 — every case element
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | covered (setup) |
| Precondition (implicit): ≥2 vector storages exist | — | step 0 (declared transit) | card count ≥2 before step 1 | covered — the case never states it; #1988 § 4 |
| 1. Navigate Settings → AI Configuration | page loads | step 1 | `ai-providers-page-title` == `AI Providers`; VS section present | covered (identity drift, #1250) |
| 2. Click the "Default vector storage" dropdown | control responds | step 2 | `listbox` visible with ≥2 `select-option-*` nodes | covered |
| 3. Select a different vector storage configuration | control responds | step 3 | POST status 200 | covered |
| 4. Dropdown updates to show the selected configuration | holds | steps 4 + 4b | combobox text == the selected `elitea_title`; API `default_model_name` matches | covered — shows the **ID**, not the Display Name; drift #1988 § 3 |
| 5. The selected card gains a "Default" badge | holds | step 5 | `ai-provider-configuration-badge` with text `Default`, scoped inside the selected card | covered — **fails, #1987**, `expect.soft()` + `# Known defect: #1987` |

### Axis 2 — asserted beyond the case
| Extra observable | Why (grounded) |
|---|---|
| The POST's 200 **and** the follow-up GET's `default: true` (step 4b) | separates "the UI label changed" from "the setting persisted". Without it, step 5's failure is ambiguous — this is exactly what let #1987 be root-caused as *display-only* rather than reported as data loss |
| The previously-default configuration is `"default": false` in the same GET | a default is exclusive; asserting only the new one would pass against a bug that marks two |
| The pre-change default, captured from the API before step 3 | the § Cleanup obligation; asserting the restore is what makes the mutation safe for the rest of the suite |
| The option set matches the section's card set one-for-one | proves the dropdown is fed by the same configurations the cards render, which is the invariant #1987 breaks on the *card* side |
| No console errors on the list page across the selection | verified live: 0 errors |

## Implementation amendment (2026-08-29, test-automation-engineer)

1. **The automation does not land on project 400.** The acting user's default project
   is 399 (`Private`), whose Vector Storage section is EMPTY (confirmed live: 399 →
   `total: 0`, 400 → `total: 1`). The spec switches to the seeded project through the
   sidebar project selector, via `settings.ai_providers_seeded_project_id`.
2. **Step 0's transit create must be followed by a default RESTORE — otherwise the
   case's step 3 is a no-op.** Creating a Vector Storage configuration ASSIGNS it as
   the section default (measured: the first implementation run failed on
   `The transit configuration is ALREADY the default`). Setup therefore re-selects the
   PRE-EXISTING default after creating the transit configuration, so the selection the
   case asks for is a genuine change the product has to perform. Step 1's assertion
   that the default equals the pre-transit one is what proves setup did so.
3. Step 5's `Default` badge assertion is unchanged and remains sanctioned-RED on #1987.

## Cleanup (MANDATORY — this test mutates shared project state)

1. **Restore the default vector storage** captured in step 1 by re-selecting its
   option. Verified live: the round trip is lossless
   (`autotest_pgvector` → `autotest_pgvector_2411` → `autotest_pgvector_seed`),
   and the API reflects each change.
   ⚠️ There is **no "unset"/blank option** in these selectors (`_surface.md`). If the
   section had no default at test start, do **not** set one — fail loudly rather than
   leave the project altered.
2. **Delete the transit configuration** created in step 0: card →
   `controls-menu-button` → `delete-credentials-menuitem` → type its Display Name into
   the **inner `input`** of `delete-confirm-name-input` → `delete-confirm-button`.
   ⚠️ **Restore the default FIRST.** Deletion is blocked while only one configuration
   remains (`isLastInSection`, ELITEA-2399 § Known constraints), and the seed must be
   the survivor.
3. Run cleanup in a `finally` so a mid-test failure still tears down.

⚠️ Assert the console-error axis **before** teardown (post-delete 404 refetch).

## Concrete Handles (discovered live; **testid-only**)

| Purpose | Handle | Provenance (fresh `git fetch origin`, 2026-08-29) |
|---|---|---|
| Vector Storage section root | `ai-providers-section-vector-storage` | on-main ✓ — only renders with ≥1 item; expand it before the selector exists |
| Default selector (clickable) | `ai-providers-section-vector-storage-default-selector-combobox` | on-main ✓ (`{sectionTestId}-default-selector` + the shared `Select.SingleSelect` `-combobox` suffix) |
| Default selector (FormControl wrapper) | `ai-providers-section-vector-storage-default-selector` | on-main ✓ |
| Dropdown option | `[data-testid="select-option-{elitea_title}<<>>{project_id}"]` — live `select-option-autotest_pgvector_seed<<>>400` | on-main ✓ — **keyed by `elitea_title`, NOT by a model name or the Display Name** |
| Card / card name | `ai-provider-configuration-card` / `-card-name` | on-main ✓ |
| **Default badge (the failing assertion)** | `ai-provider-configuration-badge`, text `Default`, scoped inside the card locator | on-main ✓ — the testid exists and works on other sections; it is the `isDefault` prop that is never true here |
| Delete flow | `controls-menu-button` → `delete-credentials-menuitem` → `delete-confirm-name-input` → `delete-confirm-button` | on-main ✓ |

**No new testid is required for this case** — #1987 is a JSX logic bug, not a missing
handle. Do **not** work around it by adding a state-flavoured testid; that would be a
state-switched testid, outlawed by `.agents/testing.md` § Locator policy.

## Network Behavior
- `POST /api/v2/configurations/models/{project_id}` fires on every selection — **no
  separate Save action** — returning 200; the section then refetches
  `GET …?include_shared=true&section=vectorstorage`.
- That GET is the honest oracle. Live after the change:
  ```json
  {"total": 2,
   "items": [{"name": "autotest_pgvector", "project_id": 400, "shared": false, "default": false},
             {"name": "autotest_pgvector_2411", "project_id": 400, "shared": false, "default": true}],
   "default_model_name": "autotest_pgvector_2411", "default_model_project_id": 400}
  ```
  Note `items[].name` is the **elitea_title** for this section.
- Never hardcode `400` — read it from the `{project_id}` path segment.

## Known Defects Found During Exploration
- **EliteaAI/elitea-testing-public#1987** — the subject of step 5. Root cause above.
- **#1988 § 3** — the selector shows the ID rather than the Display Name (case-text
  drift, asserted as the live contract here).
- Post-delete 404 console error (cleanup-only, cosmetic).

## Blocked Steps
None — #1987 is isolable to step 5 and does not prevent reaching it or anything after.

## Automation Hints
- `AIProvidersPage.select_tier_model(combobox, option_value)` already implements
  "open the combobox, click `select-option-{value}`, wait for the POST response" and
  returns the `Response` — reuse it; only the combobox descriptor is new.
- Extend `AIProvidersPage` with `vector_storage_default_selector_combobox` (the class
  has `vector_storage_section_header` but no selector descriptors — the section was
  empty on every project when it was written).
- `AIProvidersPage.card_tier_badge(display_name, "Default")` is the existing shape for
  step 5 — it scopes the badge inside `card_for_model()`, which is correct here.
- **Derive option values from the API response, not the DOM** — the `section=vectorstorage`
  GET body gives every `items[].name` plus the current `default_model_name`, which is
  enough to construct any option testid and to pick "a different one" deterministically
  (the same technique ELITEA-2397 established for LLM tiers).
- **Expand the accordion before touching the selector** — Vector Storage starts
  collapsed (only LLMs auto-expands) and the selector does not exist until then.
- `delete-confirm-name-input`'s testid is on a DIV wrapper — click first, then
  `press_sequentially`.
- Console: `collect_console_errors()` + the `#1971` URL filter.
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
