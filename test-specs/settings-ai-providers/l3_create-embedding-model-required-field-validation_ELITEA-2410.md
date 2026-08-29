# Test Case: Create Embedding Model — Display Name and Name are required

## Metadata
- **TMS ID**: ELITEA-2410
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; folder mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` @ `a64d3308`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (`auth_state` fixture)
- **Analyst**: qa-engineer (analyst slot), 2026-08-29, batch `settings-w10`
- **Status**: **ready-for-automation (sanctioned-RED)** — see § Classification note
- **Defect**: EliteaAI/elitea-testing-public#1984 (OPEN — new occurrence recorded on it
  this session; the issue was filed for `llm_model`, the embedding form is identical)
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## Classification note — declared improvisation (`.agents/testing.md` § Merge gate, *Analysis-time entry*)

Param A (**Display Name** empty) **passes**. Param B (the same check for **Name**)
**fails on a real product defect**: Save is not disabled and the configuration IS
created. Verified live this session on the embedding form:
`credential-form-save-button.disabled == false` with Name empty, and clicking it took
the Embedding Models count **3 → 4**.

The defect is deterministic, single-cause (one missing validation walk — root cause in
#1984: `validateRequiredFields`, `toolBase.helpers.js:146`, walks only the top-level
`schema.required` and never the nested `data.required`), linked to an OPEN issue, and
does **not** block exploration. Therefore, per `.agents/testing.md` § Merge gate →
*Analysis-time entry (2026-07-23, #557/ELITEA-1965)*, this AFS is
`ready-for-automation`, **not** `defect-found`, and the implementer writes the
Name-half assertions as the **correct expected behaviour** using `expect.soft()` +
`# Known defect: #1984`. Param A's coverage is preserved and the spec flips green when
the product is fixed.

⚠️ A soft-assert failure **is** a pytest FAILURE (`.agents/testing.md`, verified
in-venv 2026-08-22): this spec is sanctioned-RED, owes a closure-record entry, and its
case status stays `blocked-on-#1984` rather than `automated`.

**This is the second surface for #1984, not a second defect** — same form component
(`ToolBase.jsx` → `validateRequiredFields`), same route family, one `type` path-param
apart. Per `.agents/profile.md` § Bug filing it was consolidated as a comment on
#1984 rather than filed again ("not filed — already tracked as #1984").

## Case-identity note
"Settings → AI Configuration → click '+' → select 'Embedding Model'" =
`/settings/ai-providers` → `sidebar-create-button` →
`toolkit-type-card-embedding_model` (label: **"Embedding model"**). Page-identity
drift already filed as EliteaAI/elitea-testing-public#1250; not re-filed.

## Preconditions
- `auth_state` fixture.
- A usable AI Credential exists (shared `ELPS`, `elitea_title` = `elps`).
- **Read-mostly.** The only mutation is param B's Save, which currently succeeds — see
  § Cleanup. Cleanup is safe because Embedding Models holds 3 shared configurations,
  so the created one is never last-in-section.

## Test Data

| Param | Field under test (left empty) | Other required fields | Expected Save state | Live (2026-08-29) |
|---|---|---|---|---|
| A | **Display Name** (`toolkit-field-label-input`) | Name = `text-embedding-3-small`, credential = `ELPS` | **disabled** | ✅ `disabled: true` — matches |
| B | **Name** (`toolkit-field-name-input`) | Display Name = `Autotest Emb 2410`, credential = `ELPS` | **disabled** | ❌ `disabled: false`, and Save **creates** the configuration — #1984 |

## Test Steps

| # | Action | Expected | Live (2026-08-29) |
|---|---|---|---|
| 1 | `/settings/ai-providers` → `sidebar-create-button` → `toolkit-type-card-embedding_model` | create form renders | ✅ form present; Save `disabled: true` on a pristine form |
| 2A | Fill **Name**, pick the credential; leave **Display Name** empty | — | ✅ `label: ""`, `name: "text-embedding-3-small"`, `cred: "ELPS"` |
| 3A | Read `credential-form-save-button` `disabled` | **True** | ✅ `True` |
| 2B | On a **fresh** form: fill **Display Name**, pick the credential, leave **Name** empty | — | ✅ |
| 3B | Read `credential-form-save-button` `disabled` | **True** | ❌ **`False`** — #1984 (`expect.soft`) |
| 4B | Click Save; assert **no configuration is created** | Embedding Models count unchanged | ❌ configuration created, count 3 → 4 — #1984 (`expect.soft`) |

Param A must run **before** param B in a single spec, or as two tests in a class where
A is not skipped by B's failure — the working half must keep reporting.

## Expected Results
1. With a required field empty, `credential-form-save-button` is disabled.
2. With a required field empty, no Embedding Model configuration is created.

Both hold for **Display Name**. Both are violated for **Name**, whose required-ness is
declared by the toolkit schema and rendered with the required asterisk (`Name * *` in
the DOM's label). **The case text is correct; the product is wrong** — a defect, not
case-text drift.

## Coverage Map

### Axis 1 — every case element
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` | fixture | covered (setup) |
| 1. Navigate → "+" → Embedding Model | page/section loads | step 1 | URL + `toolkit-field-label-input` present | covered |
| 2. Leave Display Name empty — Save disabled or validation error | holds | steps 2A/3A | `save_button` `disabled` is `True` | covered — **passes** |
| 3. Fill Display Name, leave Name empty — Save disabled or validation error | holds | steps 2B/3B | `save_button` `disabled` | covered — **fails, #1984**, `expect.soft()` + `# Known defect: #1984` |
| 4. Verify no model is created in either case | holds | step 3A (Save unclickable) + step 4B (count) | Embedding Models card count | covered — A passes, B **fails, #1984**, `expect.soft()` |

### Axis 2 — asserted beyond the case
| Extra observable | Why (grounded) |
|---|---|
| Save is **enabled** once every required field is filled (positive control) | without it, a spec asserting "disabled" passes trivially against a form that is broken *shut*. Verified live: Display Name + Name + credential ⇒ `disabled: False` |
| Save is still **disabled** with Display Name + Name filled but NO credential | pins that the credential select DOES gate Save on this form, i.e. #1984 is narrow to `name` — the same narrowing ELITEA-2395 established for `llm_model`. Prevents a future "fix" that over-corrects |
| `aria-invalid` and helper-text absence on the empty Name field | records that there is no *inline* validation either (`aria-invalid: "false"`, no `toolkit-field-name-input-helper-text` node), so the fix can be verified as complete rather than partial |
| Embedding Models card count before/after step 4B | the case's "no model is created" half. Asserting only the button state would miss that the record is actually **persisted** — the severe part of #1984 |

## Cleanup (MANDATORY while #1984 is open)
Step 4B **creates a real configuration**. Delete it in a `finally`: card →
`controls-menu-button` → `delete-credentials-menuitem` → type the Display Name into
the **inner `input`** of `delete-confirm-name-input` → `delete-confirm-button`.
Verified live; the count returns to 3.

Use a **per-run suffix** on the Display Name (keeping the total ≤32 chars —
`toolkit-field-label-input` has `maxlength="32"` and truncates silently) so cleanup can
never delete someone else's configuration. When #1984 is fixed, step 4B creates
nothing and cleanup becomes a no-op — **write it tolerant of the record being absent.**

⚠️ Assert the console-error axis **before** teardown (the post-delete refetch logs a
404).

## Concrete Handles
Same inventory as
`test-specs/settings-ai-providers/l3_create-embedding-model-configuration_ELITEA-2398.md`
§ Concrete Handles (fresh fetch 2026-08-29). Specific to this case:

| Purpose | Handle | Provenance |
|---|---|---|
| Save gate | `credential-form-save-button` — assert the `disabled` **property**, never a CSS class | on-main ✓ |
| Empty-field inline error | `[data-testid="toolkit-field-{}-input-helper-text"]` (`CredentialFormFieldsMixin.FIELD_HELPER_TEXT`) — asserted **absent** | on-main ✓ |
| Card count | `ai-provider-configuration-card` scoped to the embedding accordion (`AIProvidersPage.get_configuration_card_count()` counts the WHOLE page — scope it, or capture a before/after delta) | on-main ✓ |

**No new testid is required for this case.**

## Network Behavior
Step 4B fires the create POST (2xx) followed by the list refetch. When #1984 is fixed,
**no request should fire at all** — that is the cleanest post-fix assertion.

## Known Defects Found During Exploration
- **EliteaAI/elitea-testing-public#1984** — required `Name` does not gate Save on the
  AI-provider create form; the record is persisted. Confirmed on `embedding_model`
  this session (comment added to the issue rather than a duplicate ticket). Siblings
  already cross-linked on #1984: #1004, #1903, #633 — same pattern, different surfaces.

## Blocked Steps
None — the defect is isolable to the Name half and does not prevent reaching any later
step.

## Automation Hints
- Reuse `CredentialFormFieldsMixin.is_save_enabled()` and
  `AiProviderFormPage.clear_display_name()`.
- **Get a fresh form per param.** A `page.reload()` mid-edit raises the native
  `beforeunload` dialog; register `page.on("dialog", lambda d: d.accept())` and
  navigate through the app.
- **Clearing a field must go through real key events** — MUI does not commit React
  `onChange` on a bare `fill("")`. Live this session, clearing Name via
  focus + select + `Backspace` worked; `clear_display_name()` is the existing shape.
- **Clearing Display Name also clears the auto-derived ID field.** Do not assert a
  stale ID value after clearing.
- Console: `utils/console_errors.collect_console_errors()` + the `#1971` URL filter;
  expect the `#656` React `key` error only if the spec walks the type picker.
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
