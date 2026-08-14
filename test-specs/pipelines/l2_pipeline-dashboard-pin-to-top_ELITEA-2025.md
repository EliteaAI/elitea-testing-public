# Test Case: Pipeline Dashboard — Pin to Top

## Metadata
- **TMS ID**: ELITEA-2025
- **Linked Story**: none
- **Priority**: l2 (medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `pipelines-remaining-w2`
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` on localhost).
- Two disposable pipelines exist, created via `pipeline_api.create_pipeline()`
  for isolation (same pattern as ELITEA-1974's credential-pin test and
  ELITEA-2049's pipeline three-dot-menu test) — no nodes/config needed, the
  pin/unpin flow doesn't depend on pipeline content.
- Pipelines dashboard is in **card view** (confirmed live default —
  `test-specs/pipelines/lextend_pipeline-dashboard-view-toggle-default-and-layout_ELITEA-2024.md`
  — asserted explicitly via `is_card_view_active()` rather than assumed).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- **Pipeline A** and **Pipeline B**, `pipeline_api.create_pipeline(name=..., description=...)`.
  Pipeline B is created a few seconds AFTER Pipeline A so it sorts ABOVE A
  under the dashboard's default `created_at`-desc order — this is what gives
  Steps 2/6 a real "position" to move to/from (mirrors ELITEA-1974's Test
  Data rationale exactly). Both cleaned up via `pipeline_api.delete_pipeline(pid)`
  in a `finally` block.

## Test Steps

(Live-executed and confirmed this session against the Pipelines dashboard,
`/pipelines/all`, project `Private`/399 — using pre-existing pipelines
`probe-pipeline` id `6934` as the pin target and the surrounding cards as the
baseline order, since no disposable pipelines were created for this
analyst-session probe; the AFS below specs the isolated-data shape per the
project's standard pattern.)

1. **Setup** — create Pipeline A, then Pipeline B (via `pipeline_api`).
2. Navigate to the Pipelines dashboard (`PipelinesListPage.navigate()`),
   confirm card view is active. **Verify**: baseline order has B above A
   (`get_card_names()`, `index(B) < index(A)`); Pipeline A's pin button reads
   `"Pin to top"` (case Steps 1–2 — an unpinned pipeline card is identified).
3. Click Pipeline A's "Pin to top" icon button (`pin_toggle_button(pipeline_a_id)`).
   **Verify**: the underlying `POST
   /api/v2/social/pin/prompt_lib/{project}/application/{id}` returns `201`
   — confirmed live; the card grid re-sorts **immediately, client-side, no
   reload needed** — confirmed live (`probe-pipeline` moved from index 6 to
   index 0 in the very next DOM read, no navigation between click and read);
   Pipeline A's pin button flips to `"Unpin from top"` (case Steps 3–4).
4. Click Pipeline A's pin button again (unpin). **Verify**: the underlying
   `DELETE /api/v2/social/pin/prompt_lib/{project}/application/{id}` returns
   `204` — confirmed live; the pin button's label flips back to `"Pin to
   top"` **immediately** — confirmed live (case Step 5).
5. **Re-navigate** to the Pipelines dashboard (`PipelinesListPage.navigate()`).
   **Verify**: the order reverts to B above A — confirmed live (case Step 6).
   **Gotcha — asymmetric reorder timing, confirmed live this session:**
   pinning re-sorts the grid instantly in place (no reload); **unpinning does
   NOT** — the just-unpinned card stays at the top of the grid until a fresh
   navigate/re-fetch happens, even though its own button label flips back
   immediately. This is the SAME shape ELITEA-1974's merged credential test
   already codifies (its Step 7b explicitly re-navigates before asserting
   the reverted order — `test_credential_pin_unpin.py:141`) — **reuse that
   pattern exactly**, do not assert order immediately after the unpin click.
6. **Side-channel check** — zero console errors across the whole flow —
   confirmed live (`browser_console_messages` → 0 errors, both mid-flow and
   after the final re-navigate).

## Expected Results
- Clicking "Pin to top" on an unpinned pipeline card moves it above every
  card that outranks it under the default sort, instantly, no reload needed.
- Clicking the same button again ("Unpin from top") reverts the pin state
  (label flips immediately); the grid's visual order reverts only after a
  fresh navigate/re-fetch (confirmed asymmetric behavior, matches the
  established credential/skill pin pattern already merged on `automation/base`).
- Zero console errors across the whole pin → unpin → re-navigate flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Pipelines dashboard in card view | Dashboard loads with pipelines in card view | step 2 | `is_card_view_active()` + `get_card_names()` non-empty | asserted |
| 2 Find a pipeline card that is NOT pinned | An unpinned pipeline card is identified | step 2 | `get_pin_toggle_label(pipeline_a_id) == "Pin to top"` | asserted |
| 3 Click "Pin to top" on that card | Pipeline is pinned to the top of the list | step 3 | `click_pin_toggle()` → `201`, `get_pin_toggle_label() == "Unpin from top"` | asserted |
| 4 Verify the pinned pipeline moves to the top | The pipeline card now appears first | step 3 | `get_card_names()` — `index(A) < index(B)`, checked immediately (no reload) | asserted |
| 5 Click "Pin to top" again (unpin) | Pipeline is unpinned | step 4 | `click_pin_toggle()` → `204`, `get_pin_toggle_label() == "Pin to top"` | asserted |
| 6 Verify pipeline returns to its original position (or is no longer at top) | The pipeline is no longer at the top of the list | step 5 | `get_card_names()` **after re-navigate** — `index(B) < index(A)` restored | asserted — **navigate-then-check, not immediate-check; see step 5 Gotcha** |
| Expected Final State: Pin to Top moves pipeline to top when pinned, removes it from top when unpinned | — | steps 3–5 | steps 3–5 | asserted |
| Pass/Fail: all steps complete without errors; pipeline moves to top when pinned, returns when unpinned | — | all steps | all steps + console-error check | asserted |

### Axis 2 — Analyst additions

- **Immediate-vs-deferred reorder timing (pin vs. unpin)** — *added: the case
  text treats "pin" and "unpin" as symmetric operations, but the live
  product isn't — pin re-sorts instantly, unpin needs a fresh fetch to
  visually revert. Without documenting this, an implementer could naively
  assert order right after the unpin click (matching the pin step's shape)
  and get a false failure on correct product behavior. Confirmed live this
  session; the credential AFS/test already handles this correctly via
  re-navigate, so this is now the second surface confirming the same
  platform-wide `usePin` hook shape, not a pipeline-specific quirk.*
- **Console-error check across the whole pin → unpin → re-navigate flow** —
  *added: zero-cost given the live session was already open; silent errors
  are the worst bugs per skill discipline. Confirmed 0 errors.*
- **Network-level pin/unpin confirmation** (`201`/`204` on
  `/social/pin/prompt_lib/{project}/application/{id}`) — *added: a stronger,
  non-flaky proof of the state change than the label/order alone; the same
  request-capture shape ELITEA-1974's test already uses (`expect_response`
  matching the URL suffix), confirmed live for the `application/{id}`
  path segment (pipelines share the `application` API surface with agents —
  see `automation/api/client.py`'s `PipelineAPI` docstring).*

## Cleanup
- `pipeline_api.delete_pipeline(pipeline_a_id)` and
  `pipeline_api.delete_pipeline(pipeline_b_id)` in a `finally` block.
- This analyst session's own probe used a pre-existing pipeline
  (`probe-pipeline`, id `6934`) rather than creating fresh ones, and left it
  fully unpinned at the end (verified via the final re-navigate + DOM read)
  — no residue created, nothing to clean up from this session.

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only** — see
`.agents/role-overrides.md` / `.agents/testing.md` § Locator policy.

| Element | Testid | LocatorDescriptor field | Provenance |
|---|---|---|---|
| Pipeline card name | `entity-card-name` | `entity_card_name` (existing field, `pipelines_list_page.py`) | on-main ✓ — confirmed live |
| List-row "Pin to top"/"Unpin from top" icon button | `pipelineall-pin-toggle-button-{id}` (dynamic, per pipeline id) | **NEW dynamic constant needed**: `PIN_TOGGLE_BUTTON = '[data-testid="pipelineall-pin-toggle-button-{}"]'` on `PipelinesListPage`, + `pin_toggle_button(pipeline_id)` / `get_pin_toggle_label(pipeline_id)` / `click_pin_toggle(pipeline_id)` methods — **mirror `CredentialsListPage`'s identical trio exactly** (`automation/pages/credentials_list_page.py:196-217`), only the URL-suffix path segment changes: `.../application/{id}` (pipelines) vs `.../configuration/{id}` (credentials) | **on `automation/testids` only, NOT yet on `main`** (fresh `git fetch origin` this session: `git grep -- "pin-toggle-button" origin/main -- src/` → 0 hits; `origin/automation/testids` → hit at `src/[fsd]/widgets/pin-toggler/ui/PinButton.jsx:98`). Originating commit: `EliteaAI/EliteaUI@b54bc281` ("[EL-1974] add data-testid for credential pin/unpin controls") — the testid is a SHARED `PinButton.jsx` component wired generically; pipelines inherit it via that same component with **zero pipeline-specific EliteaUI change needed**. |

**Naming-leak observation (NOT a blocker, NOT filed — see Known Defects for
why):** the testid's `pipelineall` prefix comes from `PinButton.jsx`'s local
`getPinTestIdSlug(entityType)` helper (`src/[fsd]/widgets/pin-toggler/ui/PinButton.jsx:19-27`),
which special-cases `credential`/`skill`/`toolkit`/`mcp`/`application` but has
**no `isPipelineCard` branch** — so it falls through to
`String(entityType).toLowerCase()`, and the Pipelines dashboard passes
`cardContentType={ContentType.PipelineAll}` (`Pipelines.jsx:196`), which is
the literal string `'PipelineAll'` → `'pipelineall'`. The testid is fully
stable and unique for this test's scope (the `/pipelines/all` dashboard,
`ContentType.PipelineAll`, confirmed unchanging across 3 live pin/unpin
cycles this session) — just cosmetically inconsistent with the project's
`{section}-{element}-{type}` naming convention (`pipeline-pin-toggle-button-{id}`
would be the clean form). Not this case's scope to fix (`.agents/role-overrides.md`
§ locator scope discipline — touch only what the test needs); flagged here
so a future analyst hitting a DIFFERENT pipeline card view (Top/Latest/
Trending/Draft — none of which map through `isPipelineCard` either) knows
the SAME pipeline could carry a DIFFERENT pin-button testid per view
(`pipelinetop-...`, `pipelinelatest-...`, etc.) — untested by this case,
worth a source-level `isPipelineCard` fix in `getPinTestIdSlug` if a future
case needs pin behavior on one of those other views.

## Network Behavior
- Pin: `POST /api/v2/social/pin/prompt_lib/{project}/application/{pipeline_id}`
  → `201 Created` — confirmed live.
- Unpin: `DELETE /api/v2/social/pin/prompt_lib/{project}/application/{pipeline_id}`
  → `204 No Content` — confirmed live.
- No other network calls are triggered by the pin/unpin click itself beyond
  the dashboard's own list re-fetch on re-navigate (`GET
  /api/v2/elitea_core/applications/prompt_lib/{project}?...agents_type=pipeline...`).

## Known Defects Found During Exploration
None. The case automates cleanly against the live product; the testid-naming
observation above is a cosmetic inconsistency in a shared component (not a
functional defect, no collision risk within this case's own scope), so per
`.agents/profile.md` § Bug filing it doesn't meet the bar for a filed ticket
— documented here instead for the next analyst/implementer who touches a
different pipeline card view.

## Blocked Steps
None. All 6 case steps automate cleanly against the live product using an
already-live, already-on-`automation/testids` testid — no `add-data-testid`
work needed for this case.

## Automation Hints
- Framework: Playwright + pytest (confirmed, matches every other pipeline spec).
- Reuse `pipeline_api.create_pipeline()` / `pipeline_api.delete_pipeline()` for
  test data (same pattern as ELITEA-1974/ELITEA-2049's pipeline/credential tests).
- **Mirror `CredentialsListPage`'s pin trio exactly** (`automation/pages/credentials_list_page.py:196-217`)
  onto `PipelinesListPage`:
  ```python
  PIN_TOGGLE_BUTTON = '[data-testid="pipelineall-pin-toggle-button-{}"]'

  def pin_toggle_button(self, pipeline_id) -> Locator:
      return self.page.locator(self.PIN_TOGGLE_BUTTON.format(pipeline_id))

  def get_pin_toggle_label(self, pipeline_id) -> str:
      return self.pin_toggle_button(pipeline_id).get_attribute("aria-label") or ""

  def click_pin_toggle(self, pipeline_id) -> Response:
      pattern = "/social/pin/prompt_lib/"
      with self.page.expect_response(
          lambda r: pattern in r.url and r.url.rstrip("/").endswith(f"/application/{pipeline_id}")
      ) as response_info:
          self.pin_toggle_button(pipeline_id).click()
      return response_info.value
  ```
- Reuse the existing `get_card_names()` method for order assertions (already
  on `PipelinesListPage`, functionally identical to `CredentialsListPage.get_display_name_order()`).
- **Do not assert order immediately after the unpin click** — re-navigate
  first (`PipelinesListPage.navigate()`), exactly as
  `test_credential_pin_unpin.py`'s Step 7b does, or the assertion will
  flakily fail against genuinely-correct product behavior (see step 5 Gotcha).
- No clipboard/permission grants needed (unlike ELITEA-2049) — this flow is
  pure client-state + one social-pin REST call, nothing async beyond the
  normal network-response wait.
