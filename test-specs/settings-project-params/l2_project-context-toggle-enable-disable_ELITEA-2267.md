# Test Case: Project Context toggle enables and disables context injection

## Metadata
- **TMS ID**: ELITEA-2267
- **Source case**: `.agents/automation/settings-w03/cases/ELITEA-2267.md`
- **Linked Story**: none
- **Priority**: l2 (high, per case frontmatter). **pytest marker: `@pytest.mark.p1`**
  — project convention: TMS `high` → AFS `l2_` prefix → pytest `p1` (NOT `p2`).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399), 2026-08-26
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Clarifications filed**: #1792 (layout drift), #1793 (toggle reachability)
- **Blocking suite defect (pre-existing, not this case)**: #1794 — see § Known Defects.

## Classification note — declared improvisation (reverse-masking guard)

The case says **"Click Save"** after each toggle flip (steps 4 and 7). Executed live,
**the saved view has no Save button**: `ProjectContextSavedView.handleToggle` fires
`updateProjectContext` (`PUT`) immediately on change. Confirmed live — flipping the
toggle produced
`PUT /api/v2/elitea_core/project_context/prompt_lib/399/project-context => [200] OK`
with no further interaction, and the new state survived both an in-app navigation
round-trip and a full page reload.

Per the reverse-masking guard the product is correct and the case text is stale. The
case's **observable is unchanged** — *the toggle's state persists across a reload* —
only the case's assumed mechanism (an explicit Save click) does not exist. This AFS
asserts the live contract: flip → wait for the `PUT` to resolve → reload → assert the
persisted state. No step and no assertion is dropped. Clarification #1792 filed.

## Preconditions
- User is logged in (localhost dev-token auth).
- Non-Public project required (`PUBLIC_PROJECT_ID` guard hides the tab).
  `${ELITEA_PROJECT_ID}` = 399 ("Private").
- **A Project Context with non-empty content must exist** — the toggle only renders in
  the saved view (`hasContent` true). Seed it in setup, delete it in teardown.
  This is *not* stated by the case, and it is load-bearing: on an empty project the
  page shows the empty state, which has no toggle at all (#1793).

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399`.

### generate-per-test
- Short seed content, e.g. `"ELITEA-2267 toggle seed."`. Value is irrelevant; only
  non-emptiness matters.

### API used for setup/teardown only
- `PUT .../project-context` `{content, enabled}` → 200 (seed). The seed sends
  **content only** in spirit: `enabled` is echoed back from a preceding `GET`, never
  chosen by the test (§ Fidelity Declaration).
- `DELETE .../project-context` → 200, or **404 when unset** (teardown must tolerate).
  Reuse/extend `clean_project_context` (`automation/fixtures/data_fixtures.py:2521`).

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| Precondition seeding of a non-empty Project Context's **`content`** via `PUT` rather than typing + saving in the UI | **Transit** | The case's observable is the *toggle's persisted state*, read off the live UI after a real reload, and produced by the product's own `PUT`/`GET` round-trip. The seed only establishes "a context exists". |
| The **`enabled` flag** carried by that same `PUT` | **Not substituted at all** (amended in review round 1) | Case step 2's observable IS the flag — "Verify the toggle is **ON by default**". The seed therefore passes **no `enabled` argument**: `project_context_seed` defaults it to `None`, meaning "`GET` the resource and echo the product's own value back", mirroring `serverData?.enabled ?? true` (`ProjectContextSavedView.jsx:27`). The fixture seeds onto a freshly-deleted resource, so the echoed value is the **server's own default**. Every later flip (steps 3 and 7) is a real click on the real switch, waited on the product's own `PUT`. |

No terminal substitution. No fabricated responses, no injected state.

**Review-round-1 amendment.** The first implementation seeded `enabled=True` and
then asserted "ON by default" — a tautology reading case step 2's observable off
a test-authored value. Pinned against regression by
`automation/tests/unit/test_project_context_seed_enabled_flag_not_authored.py`.

## Test Steps

1. **Setup** — `DELETE` (tolerate 404), then `PUT` `{content: "<seed>"}` — **content
   only**. The `enabled` flag is case step 2's own observable ("ON by default"), so
   it is never authored: the fixture `GET`s the (just-deleted) resource and echoes
   the product's own value, i.e. the server default. See § Fidelity Declaration.
2. Navigate to `${BASE_URL}/settings/project-context`.
   - **Verify**: the toggle card `project-context-toggle-card` (*added during implementation — EliteaAI/EliteaUI@b05bbc9a*) is
     visible — confirms the saved view rendered and the precondition held.
3. **Toggle is ON by default** (case step 2).
   - **Verify**: `project-context-enable-toggle` (*added during implementation — EliteaAI/EliteaUI@b05bbc9a*) is **checked**.
   - **Verify**: `project-context-disabled-banner` (*added during implementation — EliteaAI/EliteaUI@b05bbc9a*) count is **0**.
   - **Verify**: the saved-view `project-context-edit-button` (*added during implementation — EliteaAI/EliteaUI@b05bbc9a*) is
     **enabled**.
4. **Turn the toggle OFF** (case step 3). Click the toggle and wait on the real network
   response — `page.expect_response` on
   `**/elitea_core/project_context/prompt_lib/*/project-context` with `PUT`.
   - **Verify**: the response status is **200**.
   - **Verify**: the toggle is **unchecked**.
   - **Verify**: `project-context-disabled-banner` is visible and reads exactly
     `Project Context is turned off. The project background is not applied to AI responses or workflows.`
     (confirmed live, byte-identical).
   - **Verify**: `project-context-edit-button` and
     `ai-edit-project-context-open-button` are both **disabled** — confirmed live,
     `disabled={!enabled}` in `ProjectContextSavedView.jsx`.
   - **Case step 4 ("Click Save")** has no live counterpart — the `PUT` above *is* the
     save. Declared above; no assertion lost.
5. **Navigate away and back** (case step 5). Click
   `settings-nav-item-project-general`, then `settings-nav-item-project-context`.
   - **Verify**: the toggle card is visible again.
6. **Toggle remains OFF** (case step 6).
   - **Verify**: the toggle is **unchecked**; the disabled banner is visible.
   - Then perform a **full page reload** (`page.goto` on the same URL) and re-assert
     both — a hard reload defeats any RTK-Query cache and proves server persistence,
     which an in-app route change alone does not. Confirmed live: both survive.
7. **Toggle back ON** (case step 7). Click the toggle, again waiting on the real `PUT`.
   - **Verify**: response status **200**.
8. **Toggle is saved as ON** (case step 8). Full page reload.
   - **Verify**: `project-context-enable-toggle` is **checked**.
   - **Verify**: `project-context-disabled-banner` count is **0**.
   - **Verify**: `project-context-edit-button` is **enabled** again.
9. **Side channel** — no console errors across the whole run, via
   `automation/utils/console_errors.py`'s `collect_console_errors(page)`.
10. **Teardown** — `DELETE` (tolerate 404).

## Concrete Handles

| Element | Handle (testid) | Provenance | Verified |
|---|---|---|---|
| Settings content pane | `settings-content` | on `automation/testids` only | live 2026-08-26 |
| Settings nav → Project Context | `settings-nav-item-project-context` (dynamic, `SettingsDrawer.jsx:102`) | on `automation/testids` only | live 2026-08-26 |
| Settings nav → General | `settings-nav-item-project-general` (same dynamic pattern) | on `automation/testids` only | live 2026-08-26 |
| "Edit with AI" button | `ai-edit-project-context-open-button` | **on-main ✓** | live 2026-08-26 |
| Toggle card container | `project-context-toggle-card` | on `automation/testids` (**added during ELITEA-2266/2267/2276 implementation** — EliteaAI/EliteaUI@b05bbc9a; awaiting human promotion to main) (`EnableToggleCard.jsx` root) | — |
| Enable toggle (switch input) | `project-context-enable-toggle` | on `automation/testids` (**added during ELITEA-2266/2267/2276 implementation** — EliteaAI/EliteaUI@b05bbc9a; awaiting human promotion to main) — caller-supplied prop from `EnableToggleCard.jsx` into shared `Switch.BaseSwitch`; never hardcode inside `shared/ui` | — |
| "turned off" banner | `project-context-disabled-banner` | on `automation/testids` (**added during ELITEA-2266/2267/2276 implementation** — EliteaAI/EliteaUI@b05bbc9a; awaiting human promotion to main) — caller-supplied prop into shared `Banner.BannerMessage` | — |
| Saved-view Edit button | `project-context-edit-button` | on `automation/testids` (**added during ELITEA-2266/2267/2276 implementation** — EliteaAI/EliteaUI@b05bbc9a; awaiting human promotion to main) (`ProjectContextSavedView.jsx`) | — |

**State is asserted via the element's own checked/disabled state, never via a
state-switched testid** (`.agents/testing.md` § Locator policy, PR #581 ruling). The
disabled banner is a genuinely conditional *element*, not a state-flipped testid value,
and both of its branches are referenced on the executed path (visible in step 4,
`count(0)` in steps 3 and 8) — compliant with canon ruling #511.

**Endpoint observed** (for the `expect_response` wait, not asserted as a substitute for
the UI): `PUT /api/v2/elitea_core/project_context/prompt_lib/{project_id}/project-context`,
body `{content, enabled}` → 200.

**Provenance verified with a fresh fetch** — same command block and output as
`l3_project-context-page-layout_ELITEA-2266.md` § Concrete Handles (run once for both).

## Coverage Map

### Axis 1 — every case element

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| 1 | Navigate to Settings → Project Context | page loads | Step 2 | toggle card visible | covered |
| 2 | Toggle is ON by default | checked | Step 3 | `project-context-enable-toggle` checked + banner count 0 + Edit enabled | covered — and the **default** is the product's own: the setup seeds `content` only and never authors `enabled` (§ Fidelity Declaration) |
| 3 | Click the toggle to turn it OFF | responds, state shown | Step 4 | unchecked + banner text + Edit/Edit-with-AI disabled | covered |
| 4 | Click Save | saved | Step 4 | the auto-fired `PUT` → 200 | covered, mechanism differs — **clarification #1792** (no Save button exists) |
| 5 | Navigate away and back | page loads | Step 5 | nav General → Project Context, card visible | covered |
| 6 | Toggle remains OFF after save and reload | unchecked | Step 6 | unchecked after in-app return **and** after a full reload | covered |
| 7 | Toggle back ON — click Save | ON, saved | Step 7 | click + `PUT` → 200 | covered, mechanism differs (#1792) |
| 8 | Toggle is saved as ON | checked | Step 8 | checked after full reload + banner count 0 + Edit enabled | covered |
| P | Precondition: user logged in | — | Setup | `auth_state` | covered |
| P2 | (implicit) a Project Context exists | — | Setup | seeded via `PUT` | covered — **not stated by the case**; without it there is no toggle at all (#1793) |

### Axis 2 — observables asserted beyond the case

| Observable | Why |
|---|---|
| `PUT` status is 200 on each flip | The case's "Click Save" step needs *some* success evidence; the real response is the honest one, and it is what makes the later reload assertion a persistence check rather than a re-read of local state. |
| Disabled banner text, exact | The banner is the only user-visible statement of what OFF *means* ("not applied to AI responses or workflows") — the case title claims the toggle "disables context injection", and this is the closest observable the UI offers for that claim. |
| Edit / Edit-with-AI become disabled when OFF | A second, independent consequence of the OFF state, so the test fails if the flag stops propagating even when the switch still animates. Also the mechanism behind #1793. |
| Full page reload in addition to in-app navigation | The case says "reload"; an in-app route change alone can be satisfied by an RTK-Query cache. The hard reload is what proves the server persisted it. |

## Known Defects

- **#1793** — once content is empty the toggle disappears entirely (empty state has no
  toggle), and a newly created context silently inherits the previous `enabled` flag.
  Does **not** affect this case (which keeps content non-empty throughout), but it is
  why the precondition is load-bearing.
- **#1794 (suite, pre-existing)** — `ProjectContextPage.click_create()` still waits for
  the retired `?view=create` URL and times out. **RESOLVED during implementation**
  (2026-08-26): the page object and the merged ELITEA-2272 spec both now pin
  `/settings/project-context/edit`.
- **#1792** — case-text layout drift.

## Blocked Steps
None — every step was executed live and observed.
