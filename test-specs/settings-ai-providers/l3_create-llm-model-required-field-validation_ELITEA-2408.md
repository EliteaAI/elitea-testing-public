# Test Case: Create LLM Model — Display Name is required

## Metadata
- **TMS ID**: ELITEA-2408
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; folder mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` @ `7418c06f`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (`auth_state` fixture)
- **Analyst**: qa-engineer (analyst slot), 2026-08-29, batch `settings-w10`
- **Status**: **ready-for-automation (sanctioned-RED)** — see § Classification note
- **Defect**: EliteaAI/elitea-testing-public#1984 (OPEN, filed this session)
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## Classification note — declared improvisation (`.agents/testing.md` § Merge gate, *Analysis-time entry*)

Step 3 (Display Name) **passes**. Step 4 (the same check for `Name`) **fails on a
real product defect**: Save is not disabled and the model IS created. The defect
is deterministic (reproduced on both a never-touched and a filled-then-cleared
Name), single-cause (one missing validation walk — root cause in #1984), and
linked to an OPEN issue. It does **not** block exploration.

Therefore, per `.agents/testing.md` § Merge gate → *Analysis-time entry
(2026-07-23, #557/ELITEA-1965)*, this AFS is `ready-for-automation`, **not**
`defect-found`, and the implementer writes the Name-half assertions as the
**correct expected behaviour** using `expect.soft()` + `# Known defect: #1984`.
The spec will merge RED on that one deterministic signature and flip green when
the product is fixed. This preserves coverage of the Display-Name half, which
works today.

⚠️ A soft-assert failure **is** a pytest FAILURE (`.agents/testing.md`, verified
in-venv 2026-08-22): this spec is sanctioned-RED, owes a closure-record entry,
and its case status stays `blocked-on-#1984` rather than `automated`.

## Case-identity note
"Settings → AI Configuration → click '+' → select 'LLM Model'" =
`/settings/ai-providers` → `sidebar-create-button` →
`toolkit-type-card-llm_model`. Page-identity drift filed as
EliteaAI/elitea-testing-public#1250; not re-filed.

## Preconditions
- `auth_state` fixture.
- A usable AI Credential exists (shared `ELPS`).
- **Read-mostly.** The only mutation risk is step 4's Save, which currently
  succeeds — see § Cleanup.

## Test Data

| Param | Field under test | Other required fields | Expected Save state |
|---|---|---|---|
| A | **Display Name** (`toolkit-field-label-input`) empty | Name = `gpt-4o`, credential = `ELPS` | **disabled** — ✅ live behaviour matches |
| B | **Name** (`toolkit-field-name-input`) empty | Display Name = `Autotest 2408 <suffix>`, credential = `ELPS` | **disabled** — ❌ live behaviour is **enabled**, and Save creates the model (#1984) |

## Test Steps

| # | Action | Expected | Live (2026-08-29) |
|---|---|---|---|
| 1 | `/settings/ai-providers` → `sidebar-create-button` → `toolkit-type-card-llm_model` | create form renders | ✅ form present; Save disabled on a pristine form |
| 2A | Fill Name + pick the credential; leave **Display Name** empty | — | ✅ |
| 3A | Read `credential-form-save-button` `disabled` | **True** | ✅ `True` |
| 2B | Reload a fresh form; fill **Display Name** + pick the credential; leave **Name** empty (never touched) | — | ✅ |
| 3B | Read `credential-form-save-button` `disabled` | **True** | ❌ **`False`** — #1984 |
| 4B | Attempt Save; assert the model is **not** created | LLMs card count unchanged | ❌ card created, count 13 → 14 — #1984 |

Param A must run **before** param B in a single spec, or as two tests in a class
where A is not skipped by B's failure — the working half must keep reporting.

## Expected Results
1. With a required field empty, `credential-form-save-button` is disabled.
2. With a required field empty, no LLM model configuration is created.

Both hold for **Display Name**. Both are violated for **Name**, whose
required-ness is declared by the toolkit schema
(`config_schema.properties.data.required == ["name","ai_credentials"]`, read from
`GET /api/v2/configurations/available/?section=…`) and rendered with the required
asterisk. The case text is **correct**; the product is wrong — this is a defect,
not case-text drift.

## Coverage Map

### Axis 1 — every case element
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` | fixture | covered (setup) |
| 1. Navigate → "+" → LLM Model | page/section loads | step 1 | URL + `toolkit-field-label-input` present | covered |
| 2. Leave Display Name empty, fill other required fields | no error | step 2A | field values | covered |
| 3. Save disabled AND creation impossible | holds | step 3A (+ no-create implied: Save cannot be clicked) | `save_button` `disabled` is True | covered — **passes** |
| 4. Repeat 2-3 for Name (model identifier) | holds | steps 2B/3B/4B | `save_button` `disabled`; LLMs card count | covered — **fails, #1984**, `expect.soft()` + `# Known defect: #1984` |

### Axis 2 — asserted beyond the case
| Extra observable | Why (grounded) |
|---|---|
| Save is **enabled** once every required field is filled (positive control) | without it, a spec that asserts "disabled" passes trivially against a form that is broken shut. Verified live: label + name + credential ⇒ `disabled: False` |
| Card count before/after step 4B | the case's "it is not possible to create a new model" half. Asserting only the button state would have missed that the record is actually persisted — which is the severe part of #1984 |
| `aria-invalid` / helper-text absence on the empty Name field | records that there is no *inline* validation either, so the fix can be verified as complete rather than partial |

## Cleanup (MANDATORY while #1984 is open)
Step 4B **creates a real configuration**. Delete it in a `finally`: card →
`controls-menu-button` → `delete-credentials-menuitem` → type the Display Name
into `delete-confirm-name-input` → `delete-confirm-button`. Verified live. Use a
per-run suffix on the Display Name so cleanup can never delete someone else's
model, and assert the LLMs card count returns to its starting value.

When #1984 is fixed, step 4B creates nothing and the cleanup becomes a no-op —
write it tolerant of the model being absent.

## Concrete Handles
Same inventory as
`test-specs/settings-ai-providers/l3_create-llm-model-configuration_ELITEA-2395.md`
§ Concrete Handles (all **on-main ✓**, fresh fetch 2026-08-29). Specific to this case:

| Purpose | Handle | Provenance |
|---|---|---|
| Save gate | `credential-form-save-button` (assert the `disabled` **property**, not a class) | on-main ✓ |
| Empty-field inline error | `[data-testid="toolkit-field-{}-input-helper-text"]` (`CredentialFormFieldsMixin.FIELD_HELPER_TEXT`) — asserted **absent** | on-main ✓ |
| Card count | `ai-provider-configuration-card` (`AIProvidersPage.get_configuration_card_count()`) | on-main ✓ |

**No new testid is required for this case.**

## Network Behavior
Step 4B fires the create POST (2xx) followed by the list refetch. When #1984 is
fixed, no request should fire at all.

## Known Defects Found During Exploration
- **EliteaAI/elitea-testing-public#1984** — Create LLM Model: required `Name`
  does not gate Save; empty-name model is created. Root cause in the issue
  (`validateRequiredFields` walks only the top-level `schema.required` and never
  the nested `data.required`). Cross-linked as a sibling of #1004, #1903, #633 —
  same pattern, four different surfaces.

## Blocked Steps
None — the defect is isolable to step 4 and does not prevent reaching any later step.

## Automation Hints
- Reuse `CredentialFormFieldsMixin.is_save_enabled()`.
- Get a **fresh form per param**. A `page.reload()` mid-edit raises the native
  `beforeunload` dialog (hit live); navigate through the app, or handle the dialog.
- After a direct `goto` to the create route, **wait for `toolkit-field-label-input`**
  — the schema fetch delays the form mount by seconds.
- Clearing Display Name also clears the auto-derived ID field. Do not assert a
  stale ID value after clearing.
- Console: `utils/console_errors.collect_console_errors()` + the `#1971` URL
  filter. Assert the console axis **before** teardown (the delete refetch logs a
  404 — ELITEA-2395 § Known Defects).
- `with allure.step("Step N — …")`. **Markers as shipped:** `ui`, `settings`,
  `p2`, `regression`, `new` — this folder maps l3 to `p2` (sibling ELITEA-2392 /
  ELITEA-2397 specs), amended at implementation.
- **Amended at implementation — #1984 is narrower than the root-cause note
  implies.** The `Ai Credentials` select (also in `data.required`) DOES gate
  Save: verified live in ELITEA-2395's run, Display Name + Name filled with no
  credential leaves Save `disabled`. Only `name` fails to gate. Param A's
  positive control is written accordingly.
