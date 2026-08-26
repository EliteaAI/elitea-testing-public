# Test Case: MCP Dashboard — Pin/Unpin MCP

## Metadata
- **TMS ID**: ELITEA-1945
- **Linked Story**: none
- **Priority**: l2 (case frontmatter + body both say `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project 399)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths the dev server)
- **Analyst**: qa-engineer (agent), session 2026-08-24, cluster dispatch with ELITEA-1958 (batch `mcp-w03`)
- **Status**: ready-for-automation
- **Filed this session**: clarification **#1740** (case step 7 omits the list re-fetch the "returns to its original position" assertion needs)
- **Sibling case**: ELITEA-1958 (mixed types / count identity) — **blocked**, unrelated flow, its own AFS

## Preconditions

- User authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- `/mcps/all` renders in **Card view** (the default; the pin toggle lives on the
  card — see § Concrete Handles for the table-view note).
- **At least two MCPs exist and NONE of them is pinned.** Live at analysis time:
  19 MCPs in project 399, all Remote, all reading `aria-label="Pin to top"`
  (0 pinned) — verified before and after the run, the project was left clean.
- **The MCP under test must NOT already be at index 0.** Default sort is
  newest-first (id-descending), so a freshly created MCP is *already* first and
  pinning it proves nothing (`_surface.md`, ELITEA-1946 lesson). Seed **two**
  MCPs, A then B, and pin **A** (B is newer ⇒ B sorts above A).
- A **stray pin left by an aborted run breaks the "moved to top" assertion** —
  the test must assert its own precondition (no MCP reads `Unpin from top`
  before it pins) rather than assume it, exactly as
  `test_mcp_three_dot_menu_actions.py` already does.

## Test Data

### seed-two-mcps (created + deleted by the test)
| Field | Value |
|---|---|
| MCP A name | `autotest_mcp_pin_a_<unix-ts>` (prefix 20 chars + 10 digits = 30 ≤ MAX_NAME_LENGTH 32) |
| MCP B name | `autotest_mcp_pin_b_<unix-ts>` |
| URL (both) | `https://mcp.example.com/sse` (never loaded — the case never clicks Load Tools) |

Seed through the **UI create flow**, reusing `_create_mcp()` from
`automation/tests/ui/toolkits/test_mcp_three_dot_menu_actions.py:80-95`
(`navigate_to_create → select_remote_mcp_type → fill_name → fill_url →
save_and_wait_for_created`). `ToolkitAPI.create_toolkit()`'s Remote-MCP
`settings` shape is still unverified on this surface (that file's own note), so
the proven UI path is used.

**Fidelity note (transit, declared):** seeding via the UI create flow is
*transit only* — it merely produces two MCPs to pin. Every observable this case
asserts (list order, `aria-label` flip, pin/unpin HTTP status) is produced by
the live product. No substitution of any kind is specced.

Cleanup: `toolkit_api.delete_toolkit(id)` for both, in a `finally` (the merged
pattern). **Unpin before delete is not required** — the pin record dies with the
toolkit — but the test unpins as part of the case anyway, so the project is left
pin-free either way.

## Test Steps

1. **Setup (not a case step)** — create MCP **A**, then MCP **B**, via the UI
   create flow. Register the console-error listener **after** this setup: the
   `/mcps/create` type picker emits a React dev-mode "unique key prop" error on
   every mount, already tracked as [#656](https://github.com/EliteaAI/elitea-testing-public/issues/656)
   (`_surface.md`).
2. Navigate to `${BASE_URL}/mcps/all` (Card view; `APP_PREFIX` empty on localhost).
   - **Verify** (case step 1): the MCP list renders in Card view — capture
     `baseline_names = [entity-card-name…]`.
   - **Verify** (precondition guard): `index(A) > 0` and `index(B) < index(A)`
     — B, being newer, sorts above A.
   - **Verify** (precondition guard): **no** rendered pin toggle has
     `aria-label == "Unpin from top"` (nothing is pinned).
3. Hover MCP A's card pin toggle
   `[data-testid="mcp-pin-toggle-button-{id_a}"]`.
   - **Verify** (case step 2): the toggle is visible **and revealed** —
     `to_have_css("opacity", "1")` — and carries
     `aria-label == "Pin to top"`.
   - **CLARIFICATION (not a defect):** unhovered the button renders at
     `opacity: 0` (hover-reveal on the card). Playwright's own visibility
     definition ignores `opacity`, so a bare `to_be_visible()` passes even when
     the control is invisible to a human — the opacity assertion is what makes
     case step 2 ("Pin to top button is **visible** on the card") honest.
     Clicking without hovering does work (`pointer-events: auto`), but the case
     asserts visibility, so hover first.
4. Click MCP A's pin toggle (case step 3).
   - **Verify**: `POST /api/v2/social/pin/prompt_lib/{project_id}/toolkit/{id_a}`
     returns **201 Created** (await the response in the same chain as the click).
5. Verify the pin re-sorted the list (case step 4).
   - **Verify**: `index(A) == 0` — A is first.
   - **Verify**: `index(A) < index(B)` — A now sorts above the *newer* B, which
     is the part that proves the pin did the re-sorting and not the default sort.
   - Re-sorting is **immediate and client-side** — no reload, no extra fetch
     (observed live: index 18 → 0 in the same tick as the 201).
6. Verify the control's label flipped (case step 5).
   - **Verify**: A's pin toggle now reads `aria-label == "Unpin from top"`.
   - **Verify**: B's pin toggle still reads `aria-label == "Pin to top"`
     (the flip is scoped to the pinned entity, not global).
   - The MUI **tooltip** text flips identically (`Pin to top` → `Unpin from
     top`, confirmed live on hover both before and after), but the tooltip node
     carries no testid — `aria-label` on the testid-anchored button is the
     testid-only equivalent read and is what the case's "tooltip/label" reduces
     to. Do **not** add a testid for the tooltip (#511 — nothing else needs it).
7. Click A's pin toggle again to unpin (case step 6).
   - **Verify**: `DELETE /api/v2/social/pin/prompt_lib/{project_id}/toolkit/{id_a}`
     returns **204 No Content**.
   - **Verify**: A's toggle reads `aria-label == "Pin to top"` again.
8. Re-navigate to `${BASE_URL}/mcps/all` (list re-fetch), then verify the
   original position is restored (case step 7).
   - **Verify**: `index(A)` equals its baseline index from step 2, and
     `index(A) > 0` — A is no longer at the top.
   - **Verify**: the rendered order is **byte-identical to `baseline_names`**
     captured in step 2.
   - **Verify**: no rendered pin toggle reads `Unpin from top` (nothing left
     pinned).
   - **CLARIFICATION [#1740](https://github.com/EliteaAI/elitea-testing-public/issues/1740)
     — the re-navigation is MANDATORY and is not in the case text.** Live,
     unpinning does **not** re-sort in place: right after the DELETE the card is
     still at index 0 while its label already reads `Pin to top`. The order is
     recomputed only from the next list fetch. Asserting "no longer at the top"
     immediately after the unpin click would fail against a correctly-behaving
     product. Asymmetric with pinning, and consistent with the merged
     credential/pipeline pin tests.
   - **Do NOT assert the intermediate "still at index 0 after unpin" state** —
     it is real today but it is an optimistic-update detail, not the case's
     observable; locking it in would turn a future improvement red.
9. **Verify no console errors** across steps 2-8 (listener registered after
   setup, per step 1) — verified live: 0 errors on `/mcps/all` throughout the
   whole pin/unpin flow.

## Expected Results

- The card's pin control is revealed on hover and reads "Pin to top" while the MCP is unpinned.
- Clicking it pins the MCP (`POST … → 201`), moves the card to index 0 above a *newer* MCP, and flips the control to "Unpin from top" (label and tooltip).
- Clicking again unpins (`DELETE … → 204`) and flips the control back to "Pin to top".
- After the next list fetch the MCP is back in its original position and the whole list order matches the pre-pin baseline exactly.
- No console errors during the flow.

## Coverage Map

**Axis 1 — Case coverage.**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | § Preconditions | `auth_state` (localhost auto-auth) | covered |
| Precondition: MCP list in Card view | — | step 2 | card-view list rendered (`entity-card` collection) | covered |
| Precondition: at least one card with a "Pin to top" button | — | steps 1-2 | two MCPs seeded; all toggles read `Pin to top` | covered |
| 1 Navigate to MCP list page in Card view | list loads in Card view | step 2 | baseline order captured, cards rendered | asserted |
| 2 Identify a card and locate "Pin to top" button | button visible on the card | step 3 | `opacity == 1` on hover + `aria-label == "Pin to top"` | asserted *(hover required — CLARIFICATION in step 3)* |
| 3 Click "Pin to top" on a specific MCP | MCP moves to top | steps 4-5 | `POST → 201`, `index(A) == 0` | asserted |
| 4 Verify MCP moves to top position | selected MCP appears first | step 5 | `index(A) == 0` **and** `index(A) < index(B)` | asserted |
| 5 Verify tooltip/label changes to "Unpin from top" | label shows "Unpin from top" | step 6 | A's `aria-label == "Unpin from top"`, B's unchanged | asserted *(via `aria-label`; the tooltip node has no testid)* |
| 6 Click "Unpin from top" | MCP is unpinned | step 7 | `DELETE → 204` + label back to `Pin to top` | asserted |
| 7 Verify MCP returns to its original position | MCP no longer at the top | step 8 | after re-navigate: `index(A) == baseline index`, full order == baseline | asserted *(re-fetch required — clarification #1740)* |
| Expected Final State: unpinned, not at the top | — | step 8 | same + zero `Unpin from top` toggles | asserted |

**Axis 2 — Analyst additions.**

- Seed **two** MCPs and pin the older one — *added: the default sort is
  newest-first, so pinning the newest MCP leaves it at index 0 and the case's
  central assertion ("moves to top") passes vacuously. Asserting `index(A) <
  index(B)` after the pin is what proves the pin re-sorted anything.*
- Assert the precondition "nothing is pinned" before pinning — *added: a stray
  pin from an aborted run would sit at index 0 and make "A is first" fail for a
  reason unrelated to the case. Same guard the merged three-dot-menu test uses.*
- Assert the HTTP 201/204 of the pin/unpin calls — *added: the label flip alone
  is an optimistic client update; without the status codes a silently-failing
  backend write would still show a flipped label. The DELETE's 204 is the only
  evidence the unpin persisted, since the list does not re-sort.*
- Assert `opacity == 1` after hover rather than bare `to_be_visible()` —
  *added: Playwright treats an `opacity: 0` element as visible, so the case's
  "button is visible on the card" would be asserted by something that is
  invisible to a user.*
- Assert B's toggle still reads "Pin to top" after pinning A — *added: proves
  the label flip is per-entity state, not a global re-render artefact.*
- Assert the **whole** restored order equals the baseline, not just A's index —
  *added: catches a re-sort that puts A back while disturbing everything else.*
- Console-error check — *added: standard side-channel check; verified clean
  live (0 errors) on `/mcps/all`, so the assertion is honest. Scope the listener
  to post-setup because the create flow carries the known #656 warning.*

## Concrete Handles (discovered/confirmed during exploration)

| Element | Handle | Provenance (verified 2026-08-24, `cd ../EliteaUI && git fetch origin` first) | Notes |
|---|---|---|---|
| Card pin toggle (dynamic) | `[data-testid="mcp-pin-toggle-button-{id}"]` | **on-main ✓** (`origin/main:src/[fsd]/widgets/pin-toggler/ui/PinButton.jsx:98`) | Already `McpListPage.PIN_TOGGLE_BUTTON` (UPPER_CASE class template) + `get_pin_toggle_label(mcp_id)`. Rendered only when `entityId` is truthy. State is in `aria-label` (`Pin to top` / `Unpin from top`) — testid stable, state in an attribute, exactly the shape `.agents/testing.md` § Locator policy asks for. |
| MCP card name | `entity-card-name` | **on-main ✓** | `McpListPage.mcp_card_name` / `get_card_names()` — the order/index source. |
| MCP card | `entity-card` | **on-main ✓** | `McpListPage.mcp_card`. |
| Card type badge | `entity-card-tag-chip` | **on-main ✓** | `McpListPage.entity_card_tag_chip` — not needed by this case. |
| Pin tooltip | *(none — MUI `role="tooltip"`)* | n/a | **Do not add.** Text duplicates the button's `aria-label`; a testid here would be an untested-element testid (#511). |

**No new testids are required for this case** — every handle already exists on
`EliteaAI/EliteaUI` `main`, so the resulting test is deployed-env promotable
with no cherry-pick pending.

## Network Behavior

- Pin: `POST /api/v2/social/pin/prompt_lib/{project_id}/toolkit/{toolkit_id}` → **201 Created**.
- Unpin: `DELETE` the same path → **204 No Content**.
- Both are observed live; the list itself is **not** re-fetched by either call —
  the pin's re-sort is a client-side optimistic update, and the unpin's is
  simply absent (§ step 8 clarification).
- The list query is the usual
  `GET /api/v2/elitea_core/tools/prompt_lib/{project}?query=&sort_by=created_at&sort_order=desc&mcp=true&limit=20&offset=0`.

## Automation Hints

- **Reuse `McpListPage.get_pin_toggle_label(mcp_id)`** (`mcp_list_page.py:426`)
  — it already reads the `aria-label` off `PIN_TOGGLE_BUTTON`. What is missing
  is a **click** method: add `click_pin_toggle(mcp_id)` returning the awaited
  pin/unpin `Response` (mirror `McpFormPage.click_pin_toggle_menu_item()`, which
  already does the `expect_response` dance for the detail menu), plus a hover
  step. Keep both as `McpListPage` methods; the locator stays the existing
  class-level `PIN_TOGGLE_BUTTON` template — no inline `get_by_test_id(f"…")`.
- **Card index** comes from `get_card_names()` (already exists) —
  `names.index(name)`. Names are truncated at 32 chars on create, so compare
  against the name the seed helper actually used.
- **Await the pin response in the click's own chain.** The 201 arrives fast, but
  the re-sort is what the next assertion reads — awaiting the response is the
  condition wait; never a sleep.
- The list is paginated at `limit=20`; project 399 held 19 MCPs at analysis
  time and the test adds 2 ⇒ **21, past the first page.** Seeded MCPs are the
  newest, so both land on page 1 and A's pinned position is unaffected — but
  the *baseline order* comparison in step 8 must read the same page it read in
  step 2 (it does: both are a plain `/mcps/all` load). Do not add paging.
- Existing merged reference for the whole pin shape:
  `automation/tests/ui/toolkits/test_mcp_three_dot_menu_actions.py:219-268`
  (pins via the **detail three-dot menu** — different entry point, same API and
  same asymmetry). This case is the **list-card** entry point and adds the
  unpin-and-restore half that test never asserts.
- Test file: new `automation/tests/ui/toolkits/test_mcp_pin_unpin.py`, markers
  `p2`, `ui`, `toolkits`, `mcp`, `regression`.
- Steps wrapped in `with allure.step("Step N — …")` per `.agents/testing.md`.

## Known Defects Found

- **None.** The flow works end-to-end; the only surprise is the unpin
  re-sort asymmetry, filed as **clarification
  [#1740](https://github.com/EliteaAI/elitea-testing-public/issues/1740)**
  (case text, not product).
- Pre-existing, unrelated, not re-verified here: #656 (React key warning on
  `/mcps/create`, affects the seed step's console scope), #521 (view-toggle
  testids carry an `agent-` prefix), #1737 (Local type filter — different case).

## Cleanup

- Unpin is part of the case; the test additionally deletes both seeded MCPs via
  `toolkit_api.delete_toolkit(id)` in a `finally`.
- **Leave the project pin-free** — the merged three-dot-menu test asserts "no
  MCP is pinned" as its own precondition, so a leaked pin breaks a neighbour.
  Verified clean after this analysis session (0 pinned, 19 MCPs, no filters).
