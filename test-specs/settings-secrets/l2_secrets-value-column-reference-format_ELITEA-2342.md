# Test Case: Value column shows {{secret.name}} reference format when secret is masked

## Metadata
- **TMS ID**: ELITEA-2342
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2342.md` (intake snapshot)
- **Priority**: l2 (case frontmatter `priority: high`) → **pytest marker `@pytest.mark.p1`**
- **Environment Explored**: local (`http://localhost:5173`, project `Private` / 399, 121 secrets)
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (Axel), combined slot, batch `settings-w05`, 2026-08-27
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Filed**: none — the product matches the case text on every step.

## Preconditions
- Project `Private` (399), ≥ 1 secret — 121 live.
- **Every row is masked on load**: the list GET returns `secret_name` (the template
  string), never the plaintext, and `SecretValueCell.jsx` renders it as-is until the
  row-level eye toggle fetches the real value (a separate case, ELITEA-2343). So the
  case's "when secret is masked" condition is the page's default state — no setup needed.
- **Read-only case.**

## Test Data
### reuse-existing
- The live secret set, read-only. The expected value for each row is **computed from the
  name the product itself rendered** (`"{{secret." + name + "}}"`), never hardcoded.

## The product's actual masking contract (source + live confirmed)

- The list response carries `secret_name` per item; `SecretsContent.jsx:47-56` maps it to
  each row's `secretValue`.
- `SecretValueCell.jsx` renders that string verbatim as the cell's clickable label
  (clicking copies the real value via the lazy `showSecret` query — **not** exercised by
  this case).
- The reveal endpoint's own response shape confirms the server is the producer of the
  template: `{"name": "<name>", "secret_name": "{{secret.<name>}}", …}` (digest,
  ELITEA-2343).

### Live observations (2026-08-27, project 399, page 1)

| `secret-name-cell` | `secret-value-cell` |
|---|---|
| `auth_token` | `{{secret.auth_token}}` |
| `default_image_generation_model_name` | `{{secret.default_image_generation_model_name}}` |
| `default_llm_model_project_id` | `{{secret.default_llm_model_project_id}}` |
| `pgvector_project_connstr` | `{{secret.pgvector_project_connstr}}` |

(10 of 10 rows matched; the case's own `auth_token` example is one of them.)

## Test Steps

1. Navigate to `${BASE_URL}/settings/secrets`.
   - **Verify**: `secret_row` count ≥ 1 (populated path reached — a zero-row table would
     make steps 2-3 vacuously true).

2. **Verify every rendered row's Value column shows the reference format
   `{{secret.<name>}}`** — for each row, read the name cell and the value cell and assert
   `value == "{{secret." + name + "}}"`. Assert the **count equality** too
   (`len(values) == len(names) == row_count`), so a row rendering no value cell at all
   cannot pass.

3. **Verify the format exactly matches that row's own secret name** — this is step 2's
   equality, stated per-row and **exactly** (`==`, not "contains" and not a regex on the
   braces): the case's failure mode of interest is a value cell showing *some other* row's
   name, or a truncated/ellipsised name, both of which a format-only check would miss.

4. **(Axis 2)** Repeat the same per-row correspondence on a **second page** of data
   (click the next-page arrow) — the case says "each secret row", and a page-1-only check
   would miss a mapping bug that only shows up once the list is re-sliced.

5. **(Axis 2)** **Verify no plaintext leaks into the masked cell**: no rendered value cell
   equals its row's name alone, and every rendered value cell starts with `{{secret.` and
   ends with `}}`. This is the security-relevant half of "when the secret is masked" — a
   regression that rendered the real value would still satisfy a name-correspondence check
   only if the plaintext happened to equal the template, which it never does.

6. **(Axis 2)** No unexpected console errors (`#1203` isolated as a soft failure).

## Handles Reference

| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Row | `secret-row` | on-`automation/testids` | existing field |
| Name cell | `secret-name-cell` | on-`automation/testids` | existing field / `get_row_name_cell()` |
| Value cell | `secret-value-cell` | on-`automation/testids` | existing field / `get_row_value_cell()` |
| Next-page arrow (Axis-2 second page) | `secrets-pagination-next-button` | **ADDED this session** — EliteaAI/EliteaUI@249c0186 on `automation/testids` | see ELITEA-2332's AFS |

Zero new testids are needed **for the case's own steps** — the row/name/value handles all
pre-date this batch.

## Assertion shape
The expected value is **derived from the product's own rendered name**, so the assertion
is fully deterministic while every asserted value still comes from the system (fidelity
policy: the oracle is the product, not a payload the test wrote). No substitution of any
kind: no `page.route`, no `evaluate`-injected state, no fabricated response.

## Implementer notes
- Page-object additions: `get_row_names()` / `get_row_values()` list readers (already
  needed by the sibling ELITEA-2330/2334 specs — reuse, don't duplicate).
- The value cell is a button (clicking copies the plaintext) — **never click it** in this
  case; reading its text is the whole observable.
- No network wait: the masked template arrives with the initial list GET that
  `SecretsPage.navigate()` already awaits.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate to Settings → Secrets | populated page loads | Step 1 | `secret_row` count ≥ 1 after the list GET | asserted |
| Step 2: each row's Value column shows `{{secret.<name>}}` | every row does | Step 2 | per-row `value == "{{secret." + name + "}}"` + count equality | asserted |
| Step 3: the format exactly matches the secret's name (e.g. `auth_token` → `{{secret.auth_token}}`) | exact, per row | Step 3 | the same equality stated exactly, per row (the live set includes `auth_token` itself) | asserted |
| Expected Final State: format exactly matches the name | as step 3 | Step 3 | same | asserted |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| the correspondence holds on a **second page** too | the case says "each secret row"; page 1 is a sample, and re-slicing is where a row/value mapping bug would surface |
| no value cell renders the plaintext (prefix `{{secret.` + suffix `}}`, never the bare name) | "when the secret is masked" is the case's stated condition; without this the case would still pass if masking broke into a plaintext leak that happened to be well-formed |
| value-cell count == name-cell count == row count | a row that rendered no value cell at all would otherwise pass silently |
| no console errors (`#1203` isolated) | project standard |

## Known Defects / Clarifications
- **#1203 (OPEN)** — React "Maximum update depth exceeded" on mount; isolated soft failure.

> **Implementation outcome (2026-08-27):** `#1203` **did** fire in the automated run —
> 32-41 occurrences per test across all five specs of this wave — even though the live
> Playwright-MCP walk of the identical flow produced **zero**. Every functional assertion
> passed; the spec is therefore **sanctioned-RED on this one signature** and flips green
> when the product fix ships. Counts commented on `#1203`; the live-vs-automated split is
> recorded in the surface digest.

## Blocked Steps
None.
