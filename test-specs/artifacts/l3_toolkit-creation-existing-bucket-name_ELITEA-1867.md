# Test Case: Artifact Toolkit Creation When Bucket Name Already Exists

## Metadata

- **TMS ID**: ELITEA-1867
- **Priority**: l3 (medium — as authored in the source TMS case frontmatter, `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch →
  DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399; `cd ../EliteaUI && git fetch origin`
  run this session before the provenance check below).
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot · **Batch**: `artifacts-w04`
- **Status**: **blocked** — pending the human ruling on
  [#1685](https://github.com/EliteaAI/elitea-testing-public/issues/1685).

### Why blocked (read this first)

The case was executed end-to-end, live, **twice**. Its namesake expectation is **false against the
live product**, and not by a margin an assertion tweak can absorb:

> Creating an Artifact toolkit whose `Bucket` field names an **already-existing** bucket
> **SUCCEEDS**. The toolkit is created, the wizard navigates to `/toolkits/all/{id}`, and **no
> error notification is shown**. No bucket is duplicated.

That inverts steps 12-15 (error notification / form stays open / URL unchanged / toolkit absent
from the list). Steps 1-11 and 16-17 hold exactly as written.

This is **case-text drift, not a product defect** — decided by the decisive step of the
interaction-discovery ladder (read the source), see § Root Cause. Per the reverse-masking guard I
must not classify it `defect-found`; per `.agents/role-overrides.md` § declared-improvisation
protocol **limit 1** (a declaration may never change *what* is being verified), I also must not
quietly re-point the case at the opposite observable and call it `ready-for-automation`. Inverting
a case's namesake objective is a **human decision**. It is filed as
[#1685 [CLARIFICATION]](https://github.com/EliteaAI/elitea-testing-public/issues/1685).

**Everything needed to implement is already in this AFS** (§ Option A — pre-specced). The moment a
human rules "rewrite the case", this becomes a ~30-minute implementation with zero re-exploration:
all handles are confirmed live and all are already on EliteaUI `main`.

---

## Root Cause of the drift (evidence, not inference)

1. The error string the case cites — `Bucket with name new-bucket already exists` — is the
   **Artifacts "New Bucket" form's** server error. It comes from the `createBucket` RTK-Query
   mutation, `EliteaUI/src/api/artifacts.js:46` (`POST /artifacts/buckets/default/{projectId}`).
2. That mutation has **exactly one caller in the entire UI**:
   `EliteaUI/src/pages/Artifacts/CreateBucket.jsx:119`. The toolkit-creation wizard never calls it.
3. Confirmed at the network layer during this run: across the whole toolkit Save,
   **zero requests fire to `/artifacts/buckets/…`**. The bucket is materialised backend-side as a
   side effect of the toolkit's config (the same mechanism ELITEA-1866 documents for the
   *new*-bucket case), with **create-if-not-exists** semantics.

⇒ An "already exists" error is **architecturally impossible** on the toolkit path. The case reads
as a mis-transposition of **ELITEA-1809**'s expectation (`Duplicate Bucket Name Is Not Allowed` —
the *Artifacts* New Bucket form, correctly automated in
`automation/tests/ui/artifacts/test_artifacts_duplicate_bucket_name.py`) onto the Toolkits surface.

**Bonus provenance for the case's test data:** `EliteaUI/src/pages/Artifacts/CreateBucket.jsx:91`
— the New Bucket form's name field **defaults to the literal `'new-bucket'`**. The case's
"new-bucket" is simply that default, accepted as-is. (There is no bucket literally named
`new-bucket` in project 399 today — verified via `GET /artifacts/s3/?project_id=399&format=json`.)

---

## Live execution log (what actually happened)

Reproduced **twice**, deterministic, both via native Playwright locator clicks (no JS-dispatched
input), against two different pre-existing buckets:

| Run | Bucket (pre-existing) | Toolkit name | Result |
|---|---|---|---|
| 1 | `dup-bucket-1867new-bucket` — created minutes earlier via the Artifacts **New Bucket** form | `my-duplicate-toolkit-1867` | **Created.** Navigated to `/toolkits/all/2979?name=my-duplicate-toolkit-1867`. No error toast; form did not stay open. |
| 2 | `autotest-scratch-empty-191178` — long-standing bucket, unrelated to this session | `my-duplicate-toolkit-1867b` | **Created.** Navigated to `/toolkits/all/2980`. Identical outcome. |

Post-run bucket check (`GET /artifacts/s3/?project_id=399&format=json`): **exactly one** bucket
named `dup-bucket-1867new-bucket`; 976 buckets total in the project. **No duplicate was created** —
so the case's steps 16-17 hold.

**Cleanup performed:** both throwaway toolkits (2979, 2980) were deleted through the UI. The
precondition bucket `dup-bucket-1867new-bucket` remains (bucket deletion is separately broken —
see the OPEN [#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)).

**Side channels:** no application console error attributable to this flow; no `4xx`/`5xx` on the
save path (which is itself the point — nothing was rejected).

---

## Preconditions

- Authenticated as `${TEST_USER}` (localhost: `auth_state` fixture, no login step).
- Project `Private` (`${ELITEA_PROJECT_ID}` = 399) selected.
- **A bucket with a known name exists.** The case names `new-bucket`; do **not** hardcode it —
  it does not exist in the shared project, and the name is the New Bucket form's default, so it
  collides with anyone who ever accepted that default. Seed a unique bucket in the test's own
  setup (`autotest-1867-<ts>`) via the Artifacts **New Bucket** form, which is the same interface
  the case's precondition implies (not a wrong-interface substitution — the case's own observable
  lives on the *Toolkits* surface, so this is transit).
- **No toolkit by the test's chosen name exists.** Capture a baseline count rather than asserting
  an absolute 0 — the project is shared and accumulates.

## Test Data

| Field | Value |
|-------|-------|
| Existing bucket name | `autotest-1867-<ts>` (generated; the case's literal `new-bucket` is the form default — see § Root Cause) |
| New toolkit name | `autotest-my-duplicate-toolkit-<ts>` |
| Type-picker search term | `art` |
| Toolkit type key | `artifact` |

---

## Concrete Handles (discovered live this run)

**Locator policy note:** this project is **testid-only, no fallback ladder**
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`) —
`LocatorDescriptor(testid=…)` as class-level page-object fields, dynamic testids as UPPER_CASE
class-constant templates. Every handle below was exercised live this run.

**Provenance verified this run** — `cd ../EliteaUI && git fetch origin` first, then the two-stage
`git grep` (bare substring → `-iE '(data-testid|testid[[:space:]]*[:=])'`) against **both**
`origin/main` and `origin/automation/testids`:

| Element | testid | Status | Provenance | Notes |
|---|---|---|---|---|
| Sidebar → Toolkits | `sidebar-menu-item-toolkits` | existing | **on-main ✓** | `SidebarBody.jsx` |
| Sidebar → Artifacts | `sidebar-menu-item-artifacts` | existing | **on-main ✓** | same component |
| "+ Toolkit" create button | `sidebar-create-button` | existing (shared) | **on-main ✓** | generic create button on list pages (per ELITEA-1868 AFS) |
| Type-picker search input | `toolkit-wizard-type-search-input` | existing | **on-main ✓** | filters live on `onChange` — no Enter, no debounce |
| Category group tab | `[data-testid="category-filter-tab"]` (12 rendered) | existing | **on-main ✓** | shared value reused per chip |
| Toolkit type card (dynamic) | `[data-testid="toolkit-type-card-{key}"]` | existing | **on-main ✓** | `CategoryItemCard.jsx`; **never text-match this card** — a text locator resolves to a non-interactive wrapper and silently no-ops (ELITEA-1868 finding, re-confirmed) |
| Toolkit Name input | `toolkit-form-name-input` | existing | **on-main ✓** | `NameDescriptionInput.jsx`, generic across all toolkit types |
| Bucket field (dynamic) | `[data-testid="toolkit-field-{k}-input"]` → `toolkit-field-bucket-input` | existing | **on-main ✓** (`ToolBaseProperty.jsx:281,316` — templated, so grep the template, not the resolved value) | schema-driven; `k` = `bucket` |
| Save button | `toolkit-form-save-button` | existing | **on-main ✓** | `CreateToolkitToolTabBar.jsx`, shared toolkit/MCP/application |
| Cancel button | `toolkit-form-cancel-button` | existing | **on-main ✓** | added by ELITEA-1868 |
| Toast (generic, success **and** error) | `toast-message` | existing | **on-main ✓** | ~3s auto-dismiss — wait for `visible`, never assert continued presence |
| Toolkit kebab menu | `controls-menu-button` | existing | **on-main ✓** | teardown path; `Delete` is a `role=menuitem` with no testid — **testid needed** if a test ever asserts it (this case's teardown may use `ToolkitAPI.delete_toolkit`) |
| Delete-confirm button | `delete-confirm-button` | existing | **on-main ✓** | **disabled until the toolkit's exact name is typed** into the dialog's `input[name="name"]` — that input carries **no testid** (`testid needed: toolkit-delete-confirm-name-input`) if teardown goes through the UI |
| Artifacts "Create bucket" | `artifacts-create-bucket-button` | existing | **on-main ✓** | precondition seeding |
| Bucket name input | `artifacts-bucket-name-input` | existing | **on-main ✓** | **prefilled with `new-bucket`** — see § Automation Hints |
| Bucket save button | `artifacts-bucket-save-button` | existing | **on-main ✓** | |
| Search-buckets icon button | `artifacts-search-buckets-button` | existing | **on-main ✓** | reused from ELITEA-1809 |
| Bucket search input | `artifacts-bucket-search-input` | existing | **on-main ✓** | 300 ms debounce, client-side |
| Bucket row (dynamic) | `[data-testid="artifacts-bucket-row-{name}"]` | existing | **on-main ✓** | already `BUCKET_ROW` in `artifacts_page.py` |
| Toolkit list card (generic) | `entity-card` | existing (shared) | **on-main ✓** | count proof for "toolkit not in list" |

**No new testids are required** for the case as executed. The two `testid needed:` rows above apply
only if the implementer drives **teardown through the UI** instead of the API.

---

## Network Behavior

| Trigger | Request | Observed |
|---|---|---|
| Save (toolkit form) | `POST /api/v2/elitea_core/toolkits/prompt_lib/399` | **200** — toolkit created even though the bucket exists |
| Save (toolkit form) | any `/artifacts/buckets/…` | **never fires** — this is the load-bearing observation (§ Root Cause) |
| Post-save | `GET /api/v2/elitea_core/toolkit_validator/prompt_lib/399/{id}` | 200 — detail page load |
| Bucket listing | `GET /artifacts/s3/?project_id=399&format=json` | 200, 976 buckets — the independent ground truth for the "exactly one" assertion |
| Bucket create (precondition only) | `POST /api/v2/artifacts/buckets/default/399` | 200 |

---

## Coverage Map

### Axis 1 — every element of the source case

| # | Case element | Expected (as authored) | Live result | Disposition |
|---|---|---|---|---|
| pre | Bucket `new-bucket` already exists | precondition | No such bucket in project 399; the name is the New Bucket form's **default** (`CreateBucket.jsx:91`) | **clarification** → #1685; spec seeds a unique bucket instead |
| 1 | Artifacts shows the bucket | listed | ✅ holds (seeded bucket listed) | covered by Option A step 1 |
| 2 | Navigate to Toolkits | page loads | ✅ holds | Option A step 2 |
| 3 | Click "+ Toolkit" | wizard opens | ✅ holds (`/toolkits/create`) | Option A step 3 |
| 4 | "Choose the toolkit type" heading | correct | ✅ holds — assert via URL + the type-picker's own controls (heading carries no testid; the URL already satisfies the observable, per ELITEA-1868's ruling) | Option A step 4 |
| 5 | Type `art` → **only** Artifact shown | only Artifact | ⚠️ **two** cards match: `toolkit-type-card-artifact` (STORAGE) **and** `toolkit-type-card-mcp_Elitea Artifacts` (PLATFORM — a backend-supplied MCP type) | assert **scoped**, never a total count — the merged ELITEA-1868 test already codifies this (`test_toolkit_creation_cancel_no_toolkit_no_bucket.py:223`) |
| 6 | Only Artifact under **STORAGE** | filter works | ✅ holds exactly — verified: STORAGE group contains only the `Artifact` card | Option A step 5 |
| 7 | Click the Artifact card | form opens | ✅ holds | Option A step 6 |
| 8 | "New Artifact Toolkit" form visible | visible | ✅ holds (`/toolkits/create/artifact`, Name + Bucket + TOOLS render) | Option A step 6 |
| 9 | Toolkit Name = `my-duplicate-toolkit` | field shows it | ✅ holds | Option A step 7 |
| 10 | Bucket = existing name | field shows it | ✅ holds | Option A step 7 |
| 11 | Click Save | save attempted | ✅ holds (Save is enabled once dirty) | Option A step 8 |
| 12 | **Error notification "…already exists"** | error shown | ❌ **no error** — POST 200, toolkit created | **blocked / inverts** → #1685 |
| 13 | **Form remains open, toolkit NOT saved** | form visible | ❌ navigates to `/toolkits/all/{id}`; toolkit **is** saved | **blocked / inverts** → #1685 |
| 14 | **URL unchanged** | still on create page | ❌ URL becomes `/toolkits/all/{id}?name=…` | **blocked / inverts** → #1685 |
| 15 | **No `my-duplicate-toolkit` in the list** | absent | ❌ present | **blocked / inverts** → #1685 |
| 16 | Search the bucket name in Artifacts | search performed | ✅ holds | Option A step 10 |
| 17 | **Exactly one** matching bucket (no duplicate) | one entry | ✅ **holds** — 1 match, verified in the UI **and** via `GET /artifacts/s3/` | Option A step 11 — this is the part of the case worth keeping |
| final | No toolkit, no duplicate bucket | — | half true: no duplicate bucket ✅, toolkit created ❌ | → #1685 |

### Axis 2 — observables asserted beyond the case

| Observable | Why |
|---|---|
| No `/artifacts/buckets/…` request fires during Save | The strongest, non-DOM proof that the toolkit path does not go through the bucket-create API — the whole basis of the drift verdict. Cheap: one network-log filter. |
| Bucket count read from `GET /artifacts/s3/` in addition to the DOM | Independent ground truth for "exactly one" — the bucket panel is virtualized and slow (§ Automation Hints), so a DOM-only count is a weaker oracle. |
| Toolkit-list baseline captured before the flow | The project is shared and accumulating; an absolute `0` is a false assertion waiting to happen. |

---

## Blocked Steps

| Step | What could not be produced | What is needed to unblock |
|---|---|---|
| 12 | The error notification `Bucket with name <name> already exists` — the toolkit-creation path never calls the endpoint that emits it, so no input produces it | **Human ruling on [#1685](https://github.com/EliteaAI/elitea-testing-public/issues/1685)**: rewrite the case to the live contract (Option A), or accept uniqueness as a product requirement (Option B → product discussion, not a test fix) |
| 13, 14, 15 | Form-stays-open / URL-unchanged / toolkit-absent — all downstream of step 12 | same |

No workaround was engineered. Producing the case's observable would require fabricating a response
(`route.fulfill`) for the very thing the case came to observe — a **terminal substitution**,
forbidden by `.agents/testing.md` § Fidelity policy, and the case text asks for no simulation.

---

## Option A — pre-specced, implement as-is IF #1685 rules "rewrite the case"

**Proposed title:** *Creating an Artifact toolkit with an existing bucket name succeeds and reuses
the bucket (no duplicate bucket created).*

Suggested spec: `automation/tests/ui/toolkits/test_toolkit_creation_existing_bucket_name.py`
(sibling of the merged `test_toolkit_creation_cancel_no_toolkit_no_bucket.py`; reuses
`ToolkitCreationPage`, `ToolkitsListPage`, `ArtifactsPage` unchanged — **no page-object changes
required**, except the two teardown handles noted above if teardown goes via the UI).

| # | Action | Expected (live-verified) |
|---|---|---|
| 0 | Setup: seed bucket `autotest-1867-<ts>` via Artifacts → New Bucket; capture a toolkit-list baseline for the chosen toolkit name; start a network log | bucket created (POST 200) |
| 1 | Artifacts: search the seeded name | exactly one `artifacts-bucket-row-<name>` |
| 2 | Sidebar → Toolkits | `/toolkits/all` loads, `entity-card`s render |
| 3 | Click `sidebar-create-button` | URL `**/toolkits/create` |
| 4 | Type `art` into `toolkit-wizard-type-search-input` | `toolkit-type-card-artifact` visible; `toolkit-type-card-github` count 0 (**scoped**, never a total count) |
| 5 | Assert the STORAGE group holds only the Artifact card | Artifact under STORAGE |
| 6 | Click `toolkit-type-card-artifact` (by testid) | `/toolkits/create/artifact`; `toolkit-form-name-input` visible |
| 7 | Fill Name + `toolkit-field-bucket-input` = the seeded bucket name (MUI: `click()` + `press_sequentially()`) | both values echo back; Save enabled |
| 8 | Click `toolkit-form-save-button` | **succeeds** — `POST …/toolkits/prompt_lib/399` → 200; URL becomes `**/toolkits/all/{id}` |
| 9 | Assert **no** `/artifacts/buckets/` request fired across the whole flow | 0 matches in the network log |
| 10 | Toolkits list: search the toolkit name | exactly 1 card (baseline + 1) |
| 11 | Artifacts: search the bucket name | **exactly one** row — and `GET /artifacts/s3/` shows exactly one bucket of that name (no duplicate) |
| 12 | Teardown: delete the toolkit (prefer `ToolkitAPI.delete_toolkit(id)`; `save_creation()` already returns the id) | toolkit gone |

Markers: `ui`, `regression`, `toolkits`, `p2`.

---

## Automation Hints (live-confirmed this run — read these, they cost me turns)

1. **The wizard form is NOT deep-linkable.** Navigating straight to `/toolkits/create/artifact`
   renders the **type-picker**, not the form. You must click `toolkit-type-card-artifact`. Use
   `ToolkitCreationPage.select_toolkit_type("art", "artifact")`, which already does this and waits
   on the Name field.
2. **`ToolkitCreationPage.save_creation()` fits this case unchanged** — it clicks Save, waits for
   `**/toolkits/all/*`, and returns the new toolkit id (which teardown needs). Under Option A that
   navigation is the *expected* outcome, so no new method is needed.
3. **The Artifacts "New Bucket" name field is PREFILLED with `new-bucket`**
   (`CreateBucket.jsx:91`). A bare `click()` + `press_sequentially()` puts the caret at position 0
   and **prepends**, producing mangled names — this run created `dup-bucket-1867new-bucket` exactly
   that way, and the project already contains an older `new-bucketautotest-buck1-800755` from the
   same mistake. **Clear the field first.** (`ArtifactsPage`'s own bucket-creation helper is the
   safe path — reuse it, don't hand-roll.)
4. **The bucket panel is very slow in project 399 (976 buckets).** A poll of
   `[data-testid^="artifacts-bucket-row-"]` returned 0 for **>13 s** after navigation before the
   list rendered, with the footer still reading `Buckets: 0`. Never assert "no buckets" off a short
   wait, and always **search** rather than scan. Budget ≥20 s for the first bucket-list render.
5. **`toolkit-field-bucket-input` is a TEMPLATE** (`toolkit-field-{k}-input`). Grepping the
   resolved value against EliteaUI returns nothing — grep the template. It is on `main`.
6. **UI teardown of a toolkit is a 3-step gate:** kebab (`controls-menu-button`) → `Delete`
   (`role=menuitem`, no testid) → dialog, where `delete-confirm-button` stays **disabled** until
   the toolkit's exact name is typed into the dialog's `input[name="name"]` (no testid). Prefer the
   API teardown.
7. **`art` matches two type cards** — `artifact` (STORAGE) and `mcp_Elitea Artifacts` (PLATFORM,
   backend-supplied). Assert scoped presence/absence, never a total count. The merged ELITEA-1868
   test already documents this at
   `automation/tests/ui/toolkits/test_toolkit_creation_cancel_no_toolkit_no_bucket.py:223`.

---

## Overlap check (why this is not `already-covered` / `extend-existing`)

| Candidate (merged to `origin/automation/base`) | Same observable? |
|---|---|
| `automation/tests/ui/artifacts/test_artifacts_duplicate_bucket_name.py` (ELITEA-1809) | **No.** Same error *string*, different surface: the Artifacts **New Bucket** form, where the 400 genuinely fires. Its subject is the bucket-create API; this case's subject is the toolkit-create wizard, which never calls it. |
| `automation/tests/ui/toolkits/test_toolkit_creation_create_bucket_verify_list_files.py` (ELITEA-1866) | **No.** Bucket does **not** exist (created as a side effect). This case's whole premise is the opposite precondition. |
| `automation/tests/ui/toolkits/test_toolkit_creation_cancel_no_toolkit_no_bucket.py` (ELITEA-1868) | **No.** Cancel path; never saves. Shares handles and page object only. |

Reused wholesale: `ToolkitCreationPage`, `ToolkitsListPage`, `ArtifactsPage`, and ELITEA-1868's
type-card / MUI-typing findings.

## Related

- [#1685](https://github.com/EliteaAI/elitea-testing-public/issues/1685) — `[CLARIFICATION]` filed by this pass (**blocker**)
- [#636](https://github.com/EliteaAI/elitea-testing-public/issues/636) — OPEN: bucket cleanup fails silently (why the precondition bucket was left behind)
- ELITEA-1866 AFS `test-specs/artifacts/l2_create-bucket-via-toolkit-verify-list-files_ELITEA-1866.md`
- ELITEA-1868 AFS `test-specs/artifacts/l3_cancel-artifact-toolkit-creation-no-toolkit-no-bucket_ELITEA-1868.md`
