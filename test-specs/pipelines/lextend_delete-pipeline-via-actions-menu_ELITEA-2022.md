# Test Case: Delete Pipeline — via three-dot Actions menu, verify auto-redirect + removal

## Metadata
- **TMS ID**: ELITEA-2022
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `pipelines-remaining-w2`
- **Status**: extend-existing
- **Amended**: 2026-09-10 (analyst re-run, board card #2139) — see
  § AMENDMENT 2026-09-10 immediately below. The 2026-08 implementation-time
  amendment that made Step 6 a sanctioned-RED soft assertion is **withdrawn**:
  it was caused by an unfaithful precondition in the test, not by the case.
- **Environment re-verified**: `https://dev.elitea.ai` (`APP_PREFIX=/app`),
  project `Private` id 399, EliteaUI `main` @ `0678b8b8`.

## AMENDMENT 2026-09-10 — the RED was manufactured by the test's own precondition

**What changed:** nothing in the product, and nothing in the case. What changed
is the analysis. The 2026-08 implementation-time amendment concluded that case
Step 6 (auto-redirect to the Pipelines dashboard after delete) is a product
defect (`EliteaAI/elitea-testing-public#1332`) and specced it as a sanctioned-RED
soft assertion. That conclusion was reached against a precondition the case never
describes — `pipeline_api.create_pipeline()` followed by
`detail_page.navigate(pid)`, i.e. a `page.goto()` deep link with no prior in-app
history entry. Because the product's redirect is `navigate(-1)` (go back one
history entry), **that precondition is the direct and sole cause of the failure.**
It is a wrong-interface precondition per `.agents/testing.md` § Fidelity policy —
a substitution that was assumed to be transit-only ("test isolation, not testing
creation") but is in fact **observable-changing**: it manufactures the exact
condition the case's own Step 6 observable cannot survive.

**Live re-verification on `https://dev.elitea.ai`, 2026-09-10** (three arrival
paths, same delete action, same three-dot menu, same type-to-confirm dialog):

| Path | How the detail page was reached | `history.length` | Redirect to `/app/pipelines/all`? | Runs |
|---|---|---|---|---|
| **C — case-literal** | Dashboard → sidebar `+` → fill Name+Description → **Save** → app lands on the detail page → delete right there (case Steps 1→2→3, no navigation step in between) | 4 | ✅ **YES**, immediate | 1/1 |
| **A — in-app arrival** | Dashboard → click the pipeline card → detail page → delete | 3–6 | ✅ **YES**, 0.0 s / 7.1 s / 6.6 s after the delete settled | **3/3** |
| **B — deep link** (the current test's precondition) | `page.goto('/app/pipelines/all/{id}?viewMode=owner')` in a page with empty history → delete | 2–3 | ❌ **NO** — stranded on the deleted pipeline's stale detail route for the full 15 s observation | **3/3** |

All nine observations: `DELETE` succeeded, **0 console errors**, and in every
in-app run the pipeline was independently confirmed absent from the dashboard
list. Evidence: [Path C](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-2022-2139-pathC-case-literal-redirected-to-dashboard.png)
· [Path A](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-2022-2139-pathA-in-app-card-click-redirected-to-dashboard.png)
· [Path B — stranded](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-2022-2139-pathB-deep-link-stranded-on-deleted-detail.png).

**Consequence for this AFS:** case Step 6 is a **hard assertion**, not a
sanctioned RED. The case's arrival at the detail page is in-app, so the redirect
is producible by the system and must be asserted as such.

**Consequence for `#1332`:** it stays **OPEN and valid**. The deep-link dead-end
is a genuine user-facing bug (bookmarks, shared links, restored tabs) and it
reproduces 3/3 on DEV. It simply is not what ELITEA-2022 tests. Deep-link
coverage is a **separate decision for the lead** — see § Deep-link coverage
(#1332) below. Do not treat this amendment as evidence that `#1332` is fixed.

## Extension target

**Covering spec**: `automation/tests/ui/pipelines/test_pipeline_management.py`,
class `TestDeletePipeline`, method `test_delete_pipeline_via_ui_menu`
(lines 389–419), merged to `origin/automation/base` (originating commit
`9327052c`, allure-step wrapping added by `7c2d2e5b`; latest touch on this
file is `e7897955`, ELITEA-2020).

**Behavioural overlap (what's already proven).** `test_delete_pipeline_via_ui_menu`
already covers, end-to-end, live-reconfirmed this session:
- Create pipeline via API (`pipeline_api.create_pipeline`) — precondition-equivalent
  to case Steps 1–2 (see note below on why UI-creation isn't re-tested here).
- Navigate to the pipeline detail page.
- Open the three-dot Actions menu (`PipelineDetailPage.open_actions_menu()`,
  reused as-is by `delete_pipeline_via_menu()`) — case Step 3.
- Click "Delete pipeline" (PIPELINE-group item) — case Step 4 (menu opens with
  the correct item).
- Type-to-confirm dialog: fills the pipeline name, clicks "Delete" — case
  Step 5 (deletion submitted).
- Verifies the pipeline is absent from the dashboard list — case Step 7.

**The gap (why this isn't `already-covered`).** Case Step 6 requires verifying
that the app **automatically redirects** to the Pipelines dashboard
(`/pipelines/all`) as a *result of* the delete action. The existing test's
Step 4 (`test_pipeline_management.py:409-414`) does **not** assert this — it
explicitly does `list_page = PipelinesListPage(page); list_page.navigate()`,
i.e. it manually navigates to the dashboard itself rather than asserting the
app already landed there on its own. This masks a real regression class: if a
future change broke the auto-redirect (e.g. left the user on a 404'd detail
page for the now-deleted pipeline, or on some other route), this test would
still pass because it drives its own navigation afterward. Confirmed live this
session (see Test Steps below) that the auto-redirect DOES currently work
correctly — this is a genuine automation gap, not a defect, and the fix is a
missing assertion, not new interaction code.

**Why case Steps 1–2 (UI-driven creation) are not re-tested here.** The case's
Preconditions section already states "A pipeline named 'ToDelete_Pipeline'
exists and is saved" — Steps 1–2 restate that precondition as UI actions.
Pipeline creation via the UI create form is already thoroughly covered by
`ELITEA-2020` (`test-specs/pipelines/lextend_create-pipeline-minimal-sidebar_ELITEA-2020.md`)
and `ELITEA-2021` (`l2_create-pipeline-full-details-persist-after-reload_ELITEA-2021.md`).
Re-driving UI creation here would duplicate that coverage without adding a new
assertion; the covering spec's API-based creation is a faster, equally valid
way to reach the delete flow's precondition (test isolation, not testing
creation). Confirmed live this session anyway (see Test Steps step 1) purely
to validate the case's own precondition text is accurate — no drift found.

## Preconditions
- User is logged in (`auth_state` on localhost; Keycloak on deployed envs).
- A pipeline exists and is saved — the case states this as a **precondition**
  ("A pipeline named 'ToDelete_Pipeline' exists and is saved"), so seeding it via
  `pipeline_api.create_pipeline()` remains a legitimate, declared **transit**
  substitution: it is not the case's observable and it does not touch the arrival
  path. Keep it.
- **The user is on the Pipelines dashboard and opens the pipeline from there.**
  This is not optional colour — it is load-bearing for case Step 6. The case has
  **no navigation step between Step 2 (Save) and Step 3 (open the three-dot
  menu)**, so the user it describes arrives at the detail page *through the app*
  (either by saving a freshly created pipeline, or by opening it from the
  dashboard). Reaching it by `page.goto()` is a **different scenario** the case
  does not describe, and it is the one and only reason Step 6 fails
  (`navigate(-1)` has nowhere to go). See § AMENDMENT 2026-09-10.

## Test Data
- Reuses the covering spec's own pattern: a pipeline named
  `autotest_delete_ui_pipe` (or equivalent per-test name) created via
  `pipeline_api.create_pipeline(name=..., description=...)` in test setup.
  No new test data needed — this AFS adds an assertion to the existing flow,
  it does not need its own fixture.

## Test Steps

(Steps below map onto the *existing* test's flow — the implementer inserts
the new assertion at the marked point; steps 1–5 already pass unmodified.)

1. Create a pipeline via API (existing covering-spec behavior; live-verified
   equivalent via UI create form this session: name `ToDelete_Pipeline_2022`,
   description filled, Save clicked → pipeline id `8222` created, redirected
   to `/pipelines/all/8222?...`). **Verify**: pipeline exists (case Steps 1–2,
   already satisfied by either creation path).
2. **[AMENDED 2026-09-10 — this is the change that removes the RED]** Reach the
   pipeline detail page **through the app**: open the Pipelines dashboard
   (`PipelinesListPage.navigate()`), then click the pipeline's card
   (`PipelinesListPage.open_pipeline_by_name(name)`), then
   `PipelineDetailPage.wait_for_detail_page_load()`. **Do NOT use
   `detail_page.navigate(pid)`** — that is a `page.goto()` deep link, which is
   the unfaithful precondition this amendment removes. Verified live 3/3 on DEV
   with an API-seeded pipeline + this exact arrival.
3. Open the three-dot Actions menu, next to the VERSION controls
   (`PipelineDetailPage.open_actions_menu()`, testid `agent-actions-menu-button`
   — confirmed live: `page.getByTestId('agent-actions-menu-button')` resolves
   and opens `[role="menu"]`). **Verify**: menu opens showing two groups —
   VERSION (Set as a default / Export / Share / Fork / **Delete**, disabled
   while the open version is `base`) and PIPELINE (Share / Pin to top /
   **Delete pipeline**) (case Step 3).
4. Click "Delete pipeline" (PIPELINE-group item; testid resolves to
   `delete-agent-menuitem` — confirmed live via
   `page.getByTestId('delete-agent-menuitem').click()`; the generic
   `delete-agent` key is shared between Agent and Pipeline entity types in
   `ApplicationControls.jsx`, only the visible **label** switches to
   "Delete pipeline" for `isFromPipeline`). **Verify**: "Delete confirmation"
   dialog opens with the type-to-confirm pattern: message
   `Are you sure to delete the {name}? Enter the name to complete the action.`,
   a "Name" textbox, and a "Delete" button disabled until the name is typed
   correctly (case Step 4).
5. Type the exact pipeline name into the confirm textbox
   (`page.getByTestId('delete-confirm-name-input').locator('#name')`, existing
   `Dialog.type_to_confirm()` helper), then click "Delete"
   (`page.getByTestId('delete-confirm-button')`, existing
   `Dialog.click_button()` helper). **Verify**: `DELETE
   /api/v2/elitea_core/application/prompt_lib/{project}/{pipeline_id}` fires
   and returns `204 No Content` (confirmed live via network capture) (case
   Step 5).
6. **[GAP — new assertion; HARD, per § AMENDMENT 2026-09-10]** Immediately
   after the delete confirms (no manual navigation), assert
   `page.url` resolves to the Pipelines dashboard route (`/pipelines/all` on
   localhost — `APP_PREFIX` is empty there; `/app/pipelines/all` on deployed
   envs per `settings.app_base_url`) **without calling
   `PipelinesListPage.navigate()` first**. Confirmed live this session: the
   URL bar transitioned automatically from
   `http://localhost:5173/pipelines/all/8222?...` to
   `http://localhost:5173/pipelines/all` the instant the delete API call
   settled — no manual navigation involved, no console errors during the
   transition (`browser_console_messages(level="error")` → 0 errors) (case
   Step 6).
7. Verify the deleted pipeline no longer appears in the dashboard list
   (via `PipelinesListPage.wait_for_pipeline_absent()` — see the Edit-3 amendment
   below; the covering spec's old `pipeline_exists_in_list()` call is gone) (case
   Step 7). Confirmed live: `ToDelete_Pipeline_2022` absent from the grid
   after a 1.5s settle, no manual reload needed.

## Expected Results
- Steps 1–5, 7: unchanged from the existing covering spec — all still pass.
- Step 6 (the gap): the app auto-redirects to the Pipelines dashboard as a
  direct consequence of the delete action, with no manual navigation and no
  console errors. This is the assertion the covering spec is currently
  missing.

**~~AMENDED (implementation time, 2026-08): sanctioned RED via #1332.~~
WITHDRAWN 2026-09-10** — see § AMENDMENT 2026-09-10. The redirect DOES fire
under the case's own arrival path (3/3 on DEV, in-app card click; 1/1
case-literal create→save→delete). It failed only under the *test's* `page.goto()`
deep-link precondition, which the case never describes. Step 6 is a **hard
assertion** and the spec is expected **GREEN**. Step 7 (pipeline absence) is
unchanged and also green.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create pipeline "ToDelete_Pipeline" | Pipeline is created | step 1 | covering spec's existing API-creation setup | asserted (existing) |
| 2 Save it | Pipeline is saved successfully | step 1 | covering spec's existing setup | asserted (existing) |
| 3 Open the three-dot menu (next to version controls) | Three-dot menu opens | step 3 | covering spec's existing `open_actions_menu()` call | asserted (existing) |
| 4 Click "Delete" option from the menu | Delete confirmation dialog opens | step 4 | covering spec's existing `Dialog.wait_for()` | asserted (existing) |
| 5 Confirm deletion in the confirmation dialog | Deletion is submitted | step 5 | covering spec's existing `Dialog.type_to_confirm()` + `Dialog.click_button()` | asserted (existing) |
| 6 Verify redirect to Pipelines dashboard (URL: /app/pipelines/all) | Browser navigates to the Pipelines dashboard | step 6 | **NEW** — `page.wait_for_url(...)` on the dashboard route post-delete, **before any manual navigation**, reached via the case-faithful in-app arrival (AFS step 2) | **gap — needs new HARD assertion** (was mis-specced as sanctioned-RED 2026-08; corrected 2026-09-10) |
| 7 Verify "ToDelete_Pipeline" no longer appears in the pipeline list | The deleted pipeline is not visible in the dashboard list | step 7 | `PipelinesListPage.wait_for_pipeline_absent()` — waiting, list-scoped absence check | asserted |

**Axis 2 — Analyst additions**

- Console-error check across the whole delete flow — *added: zero-cost given
  the live session was already open; silent errors are the worst bugs per
  skill discipline. Confirmed 0 errors.*
- Network-level confirmation of the `DELETE .../application/prompt_lib/{project}/{id}`
  → `204` response — *added: gives the implementer a concrete assertion point
  beyond DOM state if they want one (e.g. via `pipeline_api` or a captured
  response), though the DOM-level redirect + absence checks are sufficient on
  their own for this AFS's Coverage Map.*

## Cleanup
- Covering spec's existing `finally: pipeline_api.delete_pipeline(pid)` block
  is a no-op safety net here (the pipeline is already deleted by the test
  itself) — keep as-is, matches existing pattern.
- This analyst session's own probe pipeline (`ToDelete_Pipeline_2022`, id
  `8222`) was created AND deleted live during this analysis — confirmed
  absent from the dashboard afterward. No residue left behind.

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only** — see
`.agents/role-overrides.md` / `.agents/testing.md` § Locator policy. All
handles below already exist and are already wired in `PipelineDetailPage`
(`automation/pages/pipeline_detail_page.py`) via the existing
`delete_pipeline_via_menu()` method — **no new testid work needed** for this
extension; only a new assertion line in the test.

| Element | Testid | LocatorDescriptor / access path | Provenance |
|---|---|---|---|
| Three-dot Actions menu button | `agent-actions-menu-button` | Not yet a `LocatorDescriptor` field — `open_actions_menu()` uses a bounding-box JS hack (`pipeline_detail_page.py:1744-1770`, pre-existing tech debt per ELITEA-2003's AFS note, unchanged by this extension) | on-main ✓ — confirmed live this session via direct `page.getByTestId('agent-actions-menu-button').click()` resolution |
| "Delete pipeline" menu item (PIPELINE group) | `delete-agent-menuitem` | Not yet a `LocatorDescriptor` field — `delete_pipeline_via_menu()` currently uses `get_by_role("menuitem", name="Delete pipeline")` text-matching (pre-existing tech debt, unchanged by this extension) | on-main ✓ — confirmed live this session via `page.getByTestId('delete-agent-menuitem').click()`. **Gotcha for the next reader**: the testid key is `delete-agent`, NOT `delete-pipeline` — `ApplicationControls.jsx`'s `deleteApplicationMenuItem` is a single shared menu-item object reused for both Agent and Pipeline entities; only the **label** text switches (`Delete ${isFromPipeline ? 'pipeline' : 'agent'}`), the testid does not. Do not go looking for a `delete-pipeline-menuitem` testid — it doesn't exist. |
| Delete confirmation dialog — name input | `delete-confirm-name-input` (container) → `#name` (inner input) | `Dialog.type_to_confirm()` (`components/mui.py`, existing) | on-main ✓ — confirmed live: `page.getByTestId('delete-confirm-name-input').locator('#name').fill(...)` resolved and worked |
| Delete confirmation dialog — Delete button | `delete-confirm-button` | `Dialog.click_button(dialog, "Delete")` (existing) | on-main ✓ — confirmed live: `page.getByTestId('delete-confirm-button').click()` resolved |
| Pipelines dashboard header (redirect-target proxy) | `pipelines-page-header` | `PipelinesListPage.page_header` (existing) | on-main ✓ (pre-existing, per ELITEA-2023's AFS) |

## Network Behavior
- `DELETE /api/v2/elitea_core/application/prompt_lib/{project}/{pipeline_id}`
  → `204 No Content` — confirmed live this session (request #1944 in this
  session's capture, pipeline id `8222`, project `399`).
- No error responses observed on the delete or the subsequent dashboard
  reload (`GET .../applications/prompt_lib/399?agents_type=pipeline...` →
  `200`).

## Known Defects Found During Exploration

**None that affect this case.** (Superseded section — the 2026-08
implementation-time entry claiming case Step 6 was blocked by
`EliteaAI/elitea-testing-public#1332` is withdrawn; see § AMENDMENT 2026-09-10.
The redirect works under the case's own arrival path.)

### Deep-link coverage (#1332) — a SEPARATE decision, deliberately not silently dropped

`EliteaAI/elitea-testing-public#1332` is a **real, open, reproducible product
bug** and nothing here weakens it. Re-confirmed on `https://dev.elitea.ai`
2026-09-10, **3/3 deterministic**: opening a pipeline's detail page by direct URL
(empty history) and deleting it leaves the user stranded on the deleted
pipeline's stale detail route indefinitely — DELETE `204`, toast shown and
dismissed, 0 console errors, no redirect within 15 s
([screenshot](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-2022-2139-pathB-deep-link-stranded-on-deleted-detail.png)).
Real users hit it via bookmarks, shared links and browser-restored tabs.

**But it is not what ELITEA-2022 tests.** Removing the deep-link precondition
from this spec therefore removes the only automated observation of `#1332`.
Stating that explicitly so the loss is a decision, not an accident:

| Option | Shape | Cost |
|---|---|---|
| **(i) Accept the gap** (default unless the lead says otherwise) | ELITEA-2022 goes green on the case-faithful path; `#1332` stays OPEN, tracked manually. | Zero. No automated guard against a `#1332` regression/fix. |
| **(ii) Add a dedicated deep-link spec** | A NEW, separate test (its own AFS/case) asserting the deep-link redirect, carried as sanctioned RED with `# Known defect: #1332` + `soft_failures`, per `.agents/testing.md` § Merge gate. | One permanently-red spec in the gate until `#1332` ships a fix; needs a closed-set entry in the closure record. |

**The implementer must NOT build option (ii) off this AFS.** It is coverage
beyond the case (Axis 2) and a merge-gate commitment — the lead decides, and if
chosen it gets its own card and AFS.

## Blocked Steps
None. **(Stale sentence removed 2026-09-10, board #2139: this section still
described Step 6 as a soft-tagged sanctioned RED, which § AMENDMENT 2026-09-10
withdrew. Step 6 is a HARD assertion and the spec is expected green.)**

## Automation Hints

- Framework: Playwright + pytest (confirmed, matches covering spec).
- **Spec to edit:** `automation/tests/ui/pipelines_2/test_pipeline_management.py`
  → `TestDeletePipeline::test_delete_pipeline_via_ui_menu` (note: the file moved
  to `tests/ui/pipelines_2/` since the 2026-08 pass; the `tests/ui/pipelines/`
  path in § Extension target above is stale).
- **The whole change is three edits. Nothing else moves.**

**Edit 1 — Step 2: reach the detail page IN-APP (this is the fix).**
```python
with allure.step("Step 2 — Open the pipeline from the Pipelines dashboard"):
    list_page = PipelinesListPage(page)
    list_page.navigate()
    list_page.open_pipeline_by_name(PIPELINE_NAME)   # in-app arrival — the case's own path
    detail_page = PipelineDetailPage(page)
    detail_page.wait_for_detail_page_load()
```
Replaces `detail_page = PipelineDetailPage(page); detail_page.navigate(pid)`.
`detail_page.navigate(pid)` is a `page.goto()` deep link — the unfaithful
precondition. Verified live 3/3 on DEV with an API-seeded pipeline + this exact
arrival. Bonus: it also sidesteps the DEV `page.goto` hang class
(`#2124`/`#2137`), which this analyst hit twice while probing the deep-link path.

**Edit 2 — Step 4: the redirect assertion becomes HARD.** Delete
`soft_failures`, the `try/except PlaywrightTimeoutError`, the trailing
`pytest.fail(...)` block, and the `# Known defect: #1332` framing.
```python
with allure.step("Step 4 — Verify the app auto-redirects to the Pipelines dashboard"):
    page.wait_for_url(
        lambda url: urlparse(url).path.rstrip("/").endswith("/pipelines/all"),
        timeout=REDIRECT_TIMEOUT,
    )
```
⚠️ **`timeout=8000` is NOT enough — raise it.** Measured on DEV across three
in-app runs the redirect landed at **0.0 s / 7.1 s / 6.6 s** *after*
`delete_pipeline_via_menu()` had already returned. The redirect is coupled to the
success toast's close (`onCloseToast` → `navigate(-1)`;
`TOAST_DURATION_DEFAULTS.success = 3000` ms in `src/common/constants.js`, but
env-configurable and empirically slower on DEV). Use **≥ 20 000 ms**. Letting a
7-second reality run against an 8-second budget is a flake generator.

**Edit 3 — Step 5: drop the conditional fallback navigation.** The redirect is
now asserted, so the test is provably on the dashboard when it gets here.
Remove the `if not urlparse(page.url)...: list_page.navigate()` guard — it exists
only to work around the manufactured `#1332` condition. Keeping it would let a
future genuine redirect regression pass silently, which is the exact masking this
extension was written to remove.

**AMENDED at implementation time (2026-09-10, board #2139) — the absence check
must WAIT and must not be page-wide.** This AFS originally specced Step 5 as
`assert not list_page.pipeline_exists_in_list(PIPELINE_NAME, timeout=3000)`.
Run live on `https://dev.elitea.ai` that shape fails for two reasons, both
caused by removing the manual `list_page.navigate()` this same edit removes:

1. **It samples instead of waits.** `pipeline_exists_in_list()` returns True
   the moment it sees the name and only waits for it to APPEAR. The redirect is
   a history-back, so the dashboard repaints its CACHED list — still holding the
   deleted card — and drops it only when the refetch lands. The old code hid
   this because its `list_page.navigate()` did a full `goto` + networkidle,
   which absorbed the refetch. Measured failure: Step 5 failed in **0.03 s**.
2. **It is page-wide, and the delete success toast carries the name.** The toast
   reads *"The `<name>` pipeline has been successfully deleted."* and is still on
   screen at this point, so a page-wide `text="…"` match can never distinguish
   "gone from the list" from "named in the toast". Evidenced by the failure
   screenshot (`automation/screenshots/test_delete_pipeline_via_ui_menu_FAIL_20260910_070532.png`)
   — grid mid-refetch showing loading skeletons, toast showing the name.

That screenshot also shows the third hazard: while the grid renders skeletons it
has **no `entity-card-name` nodes at all**, so a bare `to_have_count(0)` on the
card handle passes VACUOUSLY — the same trap the ELITEA-2024 repair (board
#2118) documents for the positive direction.

Shipped shape — a new, additive page-object method
`PipelinesListPage.wait_for_pipeline_absent(name, timeout)`:

```python
card = self.entity_card_name.filter(has_text=name)
expect(card).to_have_count(0, timeout=timeout)                      # wait the card OUT
expect(self.entity_card_name.first.or_(self.empty_state_title)).to_be_visible(
    timeout=timeout)                                                # grid actually RENDERED
expect(card).to_have_count(0, timeout=timeout)                      # re-assert on it
```

Testid-only throughout (`entity-card-name`, `empty-state-title` — both existing
`LocatorDescriptor` fields, both on EliteaUI `main`), scoped to the LIST, which
is exactly the case's Step 7 observable ("no longer appears in the pipeline
list"). Measured green: Step 5 = 1.01-1.33 s.

**Docstring.** Rewrite the `Known product defect (step 4, sanctioned RED)`
paragraph out entirely. Replace with a one-line declaration of the surviving
transit substitution, per `.agents/role-overrides.md` § Implementer slot:
*"Precondition seeded via `pipeline_api.create_pipeline()` (transit only — the
case lists the pipeline's existence as a precondition); the detail page is then
reached in-app from the dashboard, because the case's Step 6 redirect observable
depends on the arrival path (`navigate(-1)`) — see
`test-specs/pipelines/lextend_delete-pipeline-via-actions-menu_ELITEA-2022.md`
§ AMENDMENT 2026-09-10."*

**Cleanup unchanged.** Keep the `finally: pipeline_api.delete_pipeline(pid)`
no-op safety net.

**Also needs updating (orchestrator/implementer, not silently):**
- `PipelineDetailPage.delete_pipeline_via_menu()`'s docstring
  (`pages/pipeline_detail_page.py:2658-2671`) tells the next reader that the
  redirect is `#1332`-affected "which is exactly how this method's callers reach
  it". After this change that is no longer true of *this* caller. Amend the
  docstring to say the redirect fires on in-app arrival and no-ops on deep-link
  arrival (`#1332`), and that callers choose their arrival path deliberately.
- The TMS case's `sanctioned_red: "#1332"` frontmatter key
  (`ELITEA-2022_delete-pipeline.md`) should be **removed** on back-write — the
  case is no longer sanctioned RED. Orchestrator's job, not the implementer's.

**Expected outcome:** GREEN, deterministically. Gate it as a normal 3x-green
spec, not as a sanctioned-RED exception.

- `settings.app_base_url` / `APP_PREFIX` handling: on localhost `APP_PREFIX`
  is empty, so the URL ends `/pipelines/all`; on a deployed env it is
  `/app/pipelines/all`. Keep the suffix-match assertion (`.endswith(...)`)
  rather than an exact string, consistent with the rest of the suite.
