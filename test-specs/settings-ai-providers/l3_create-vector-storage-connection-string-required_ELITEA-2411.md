# Test Case: Create Vector Storage — Connection String is required

## Metadata
- **TMS ID**: ELITEA-2411
- **Linked Story**: none
- **Priority**: l3 (frontmatter `priority: medium`; folder mapping)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` @ `a64d3308`, DEV backend), project `UI Testing` (id 400)
- **User set**: `${TEST_USER}` (`auth_state` fixture)
- **Analyst**: qa-engineer (analyst slot), 2026-08-29, batch `settings-w10`
- **Status**: **blocked** — awaiting a human decision on #1988 § 1
- **Clarification / decision ticket**: EliteaAI/elitea-testing-public#1988 (§ 1)
- **Surface digest**: `test-specs/settings-ai-providers/_surface.md`

## Why this is `blocked` and not `ready-for-automation`

The case has exactly **one** observable — *"the Save button is disabled OR an inline
validation error appears for Connection String"*, and its corollary *"no vector storage
configuration is created"*. Executed live, **neither holds, and the product is
internally consistent in not holding them**:

- `GET /api/v2/configurations/available/?section=vectorstorage` returns, for `pgvector`:
  ```json
  "data": { "title": "PgVectorConfiguration", "type": "object",
            "properties": { "connection_string": {
              "default": null, "format": "password", "title": "Connection String",
              "type": "string", "writeOnly": true } } }
  ```
  There is **no `required` array inside `data` at all**. The top-level
  `config_schema.required` is `["elitea_title", "label", "type", "data"]`.
  `connection_string` is declared **optional with a `null` default**.
- The UI is faithful to that schema: the field renders **without a required asterisk**
  (contrast the sibling `Display Name * *` and `ID * *` labels in the same DOM).
- With Display Name filled and Connection String empty:
  `credential-form-save-button.disabled == false`,
  `toolkit-field-connection_string-input-field` `aria-invalid == "false"`, and no
  `toolkit-field-connection_string-input-helper-text` node renders.
- Clicking Save **creates the configuration** — it appeared as a card
  (`Autotest PGVector 2411` / `OK • Local`), and the configurations API returned it
  with `"data": {}`.

So this is **not** a product defect in the #1984 mould (there, the schema *did* declare
the field required and the UI *did* render the asterisk — the form simply failed to
enforce its own contract). Here nothing in the product ever claims Connection String is
required. Per the **reverse-masking guard** the correct classification is
*case-text drift → clarification*, not `defect-found`.

But the guard's usual remedy — *"assert the live contract"* — is **not available**
here, because the live contract is the **negation of the case's subject**. Writing a
spec that asserts *"a PgVector configuration can be created with no connection
string"* would swap what the case verifies. That is expressly outside what a declared
improvisation may authorise (`.agents/role-overrides.md` § declared-improvisation
protocol, limit 1: a declaration *"never covers a change to what is being verified …
dropping or weakening a case's observable, or swapping the subject of the case. Those
are human decisions — route them"*).

Hence: **`blocked`**, routed to a human via #1988 § 1.

## The decision needed (from #1988 § 1)

**Should `connection_string` be required for a PgVector configuration?**

- **(a) The case is wrong** → rewrite ELITEA-2411 or retire it. The natural rewrite is
  to re-target it at **Display Name**, which *does* gate Save on this form (verified
  live: `disabled: true` on a pristine form, enabled the moment a Display Name is
  typed) — the exact working shape ELITEA-2410 param A already has for the embedding
  form. That case would be `ready-for-automation` immediately.
- **(b) The product is wrong** → `connection_string` belongs in `data.required` and the
  form should gate Save on it. Then this case stands **as written**, a bug ticket is
  filed, and this AFS becomes `ready-for-automation (sanctioned-RED)` with
  `expect.soft()` + `# Known defect: #N`, in the same shape as ELITEA-2410/#1984.

Either way the live evidence below is already captured, so re-analysis is not needed —
only the ruling.

## Preconditions (for whichever resolution is chosen)
- `auth_state` fixture.
- ⚠️ **Under resolution (b) this case CREATES a real configuration** (Save currently
  succeeds), and on a project whose Vector Storage section is empty that configuration
  is **permanently undeletable** — see ELITEA-2399 § Known constraints
  (`isLastInSection`, `CredentialsControls.jsx:51,63`). Any spec written from this AFS
  must first guard that the section already holds ≥1 configuration, and must delete its
  artifact in a `finally`. This is the sharpest reason not to automate the case before
  the ruling: a red run leaves permanent residue.

## Live execution record (2026-08-29)

| # | Case action | Case expectation | Observed |
|---|---|---|---|
| 1 | `/settings/ai-providers` → "+" → `toolkit-type-card-pgvector` | page/section loads | ✅ `/settings/create-ai-provider/pgvector?viewMode=owner&from=ai-providers`; Save `disabled: true` on the pristine form. **NB the case's "→ select 'Vector Storage' → PGVector" is a single click** — there is no "Vector Storage" card (#1988 § 2) |
| 2 | Fill Display Name (`Autotest PGVector 2411`), leave Connection String empty | field accepts input | ✅ label held; `toolkit-field-elitea_title-input` auto-derived `autotest_pgvector_2411`, `disabled` |
| 3 | Save disabled **or** inline validation error on Connection String | holds | ❌ `credential-form-save-button.disabled == false`; `aria-invalid == "false"`; no helper-text node; no required asterisk on the label |
| 4 | No vector storage configuration is created | holds | ❌ Save succeeded, the app navigated back to `/settings/ai-providers`, the **Vector Storage section appeared** (0 → 1 items) with the card `Autotest PGVector 2411` / `OK • Local`; persisted with `"data": {}` |

Artifact cleanup: the created configuration could not be deleted while it was the only
one in the section; a valid second configuration was created so it could be removed,
and project 400 was left holding exactly one deliberate seed
(`Autotest PGVector Seed`) — see #1988 § 4.

## Coverage Map

### Axis 1 — every case element
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | covered (setup) |
| 1. Navigate → "+" → Vector Storage → PGVector | page/section loads | live step 1 | URL == `/settings/create-ai-provider/pgvector?…` | **executed** — plus case-text drift #1988 § 2 |
| 2. Fill Display Name, leave Connection String empty | field accepts input | live step 2 | field values | **executed**, passes |
| 3. Save disabled OR inline validation error for Connection String | holds | live step 3 | `save_button` `disabled`; `aria-invalid`; helper-text absence | **blocked** — the product declares the field optional; asserting either polarity is a human decision (#1988 § 1) |
| 4. No vector storage configuration is created | holds | live step 4 | Vector Storage card count | **blocked** — same ruling; and see § Preconditions on the residue risk |

### Axis 2 — asserted beyond the case
Not applicable while blocked. When the ruling lands, carry these forward:

| Extra observable | Why (grounded) |
|---|---|
| Save **is** disabled on the pristine form and enables on Display Name alone | the positive control that separates "this field gates Save" from "the form is broken shut"; needed under either resolution |
| The schema response's `data.required` (absent today) | the product's own declaration of the contract — the assertion that makes resolution (b)'s fix verifiable, and the one that would have caught this drift automatically |
| Vector Storage card count before/after the Save attempt | the "not created" half; button state alone cannot see persistence (the #1984 lesson) |

## Blocked Steps

- **Steps 3 and 4** cannot be automated as written. What is missing is **not access,
  data, or environment** — it is a **ruling on whether `connection_string` is
  required**. Tracked as EliteaAI/elitea-testing-public#1988 § 1.
- **Unblocks when:** a human answers #1988 § 1. Under (a) the TMS case is rewritten
  (likely re-targeted at Display Name) and re-analysed — cheaply, since every handle
  below is already confirmed. Under (b) a product bug is filed and this AFS is
  promoted to `ready-for-automation (sanctioned-RED)` without further live work.
- **Owner:** human (product/QA decision).

## Concrete Handles (all confirmed live; **testid-only**)

Kept so the eventual spec needs no re-exploration.

| Purpose | Handle | Provenance (fresh `git fetch origin`, 2026-08-29) |
|---|---|---|
| "+" create button | `sidebar-create-button` | on-main ✓ |
| PgVector type card | `toolkit-type-card-pgvector` | on-main ✓ |
| Display Name / ID inputs | `toolkit-field-label-input` / `toolkit-field-elitea_title-input` | on-main ✓ |
| Connection String — native input | `toolkit-field-connection_string-input-field` | on-main ✓ (`SecretField.jsx:77`) — the outer `toolkit-field-connection_string-input` is a DIV wrapper, do not type into it |
| Connection String — inline error (asserted **absent** today) | `toolkit-field-connection_string-input-helper-text` | on-main ✓ (`SecretField.jsx:88`) |
| Save gate | `credential-form-save-button` — assert the `disabled` **property** | on-main ✓ |
| Vector Storage section root | `ai-providers-section-vector-storage` | on-main ✓ — absent entirely when the section is empty |
| Card / card name | `ai-provider-configuration-card` / `-card-name` | on-main ✓ |
| Delete flow (residue cleanup) | `controls-menu-button` → `delete-credentials-menuitem` → `delete-confirm-name-input` → `delete-confirm-button` | on-main ✓ — **the menu item is `aria-disabled="true"` while the configuration is the only one in the section** |

**No new testid is required for this case.**

## Network Behavior
- `GET /api/v2/configurations/available/?section=vectorstorage` — the schema oracle
  quoted above. This is the request the eventual spec should read to prove the
  required-set, rather than inferring it from the asterisk.
- The Save attempt fires the create POST (2xx today) followed by the combined
  configurations refetch. Under resolution (b), **no request should fire at all**.

## Known Defects Found During Exploration
- **#1987** — Vector Storage cards never render the `Default` badge (ELITEA-2401's
  subject). Unrelated to this case's steps.
- Nothing here was filed as a bug: per the reverse-masking guard, a product that
  matches its own declared schema is not defective. #1988 carries the decision.

## Automation Hints (for after the ruling)
- Do **not** `goto` the create route and `fill()` immediately — the schema-driven form
  remounts and silently wipes an early value (hit live this session).
- Register `page.on("dialog", lambda d: d.accept())` — a dirty form arms `beforeunload`.
- Guard the "≥1 existing vector storage" precondition **before** any Save attempt, or a
  failing run leaves an unremovable configuration behind.
- `with allure.step("Step N — …")`. **Markers (when written):** `ui`, `settings`, `p2`,
  `regression`, `new`.
