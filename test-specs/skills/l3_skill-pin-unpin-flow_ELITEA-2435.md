# Test Case: Skill — Pin/Unpin Flow

## Metadata
- **TMS ID**: ELITEA-2435
- **Linked Story**: none
- **Priority**: l3 (case frontmatter: `medium`, case body header also says
  `medium` — no drift, unlike the sibling ELITEA-1974 case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual`. Per `.agents/test-automation.yaml` § `intake`,
  `status: draft` is the **intake-eligible** value for this project, not an
  exclusion — proceeded to full execution.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips
  login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Skills section is accessible (`/skills/all`).
- **At least one skill exists** in the project. Unlike the credential/
  configuration list (ELITEA-1974's AFS, which redirects to a create form on
  zero credentials), the live `/skills/all` list at zero skills was NOT
  independently re-verified this run (this project's Skills list already had
  10 pre-existing skills, none pinned) — if the implementer's fixture seeds
  an otherwise-empty project, verify the empty-state behavior separately
  before relying on it.
- **This AFS seeds two skills, not one** — a single pinned skill trivially
  satisfies "moved to top" when it is already the newest/topmost item
  (confirmed live: pinning the pre-existing newest skill,
  `elitea-1793-ghost-skill`, produced no observable reordering since it was
  already position 1). A second, unpinned skill created *after* it gives an
  unambiguous before/after position to assert against — same reasoning
  already used in ELITEA-1974's AFS for credentials.

## Test Data

### generate-per-test (created in test setup via `SkillAPI.create_skill()`,
cleaned up in its own teardown)
- Skill A: `SkillAPI.create_skill(name="autotest-pin-skill-a-<ts>",
  description="...", instructions="...")` — this is the skill that gets
  pinned/unpinned.
- Skill B: `SkillAPI.create_skill(name="autotest-pin-skill-b-<ts>", ...)` —
  created **second** (a few seconds after Skill A) so it sorts **above**
  Skill A under the list's default `sort_by=created_at&sort_order=desc` —
  this is what gives the position-based steps a real "position" to move
  to/from. Skill name must match the create-form's client-validated regex
  `/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/` (documented in `test-specs/skills/
  _surface.md`) — lowercase/digits/hyphens only.
- `SkillAPI.create_skill()`/`SkillAPI.delete_skill()` already exist
  (`automation/api/client.py:1427,1460`) — reuse directly, no new API helper
  needed.
- No shared/reused fixture applies — pin state is a per-record mutation;
  reusing a shared skill across parallel/retried runs risks state bleed
  between tests asserting on list order (same reasoning as ELITEA-1974).

## Test Steps

1. Navigate to the Skills list (`${BASE_URL}/skills/all`), with Skill A and
   Skill B already seeded via API (test setup, not a numbered case action —
   see Preconditions/Test Data).
   - **Verify**: page loads, both skills appear as cards (default/only list
     view — unlike Credentials, this run observed no Table/Card view toggle
     on the Skills page), in order **B above A** — this is the *before*
     baseline the later position-assertion diffs against. Confirmed live
     this run using two pre-existing skills as stand-ins for the pattern:
     `GET /api/v2/elitea_core/skills/prompt_lib/399?sort_by=created_at&
     sort_order=desc&...` returns `is_pinned: false` for every row when
     nothing is pinned, and every card in the accessibility snapshot shows a
     **"Pin to top"** icon button (confirmed live, `IconButton` with
     `aria-label="Pin to top"`, visible unconditionally at rest — same
     hover-opacity styling in source as credentials, did not suppress the
     icon from the accessibility snapshot).

2. Open an existing unpinned Skill (Skill A — click the skill card's
   name/title, same click-through entry point as other skill cases in this
   suite).
   - **Verify**: page loads at
     `${BASE_URL}/skills/all/{skillA_id}?viewMode=owner&name=autotest-pin-skill-a-...`
     (confirmed live pattern via `elitea-1793-ghost-skill` →
     `/skills/all/1203?viewMode=owner&name=elitea-1793-ghost-skill`), the
     skill detail form loads.

3. Open the overflow (three-dot) menu
   (`page.get_by_test_id("skill-controls-menu-button")` — **confirmed live,
   existing testid**, already wired into `SkillDetailPage.controls_menu_button`).
   - **Verify**: dropdown menu opens (confirmed live via snapshot) showing
     two sections — **VERSION** (Set as a default / Export / Share / Fork /
     Publish / Delete) and **SKILL** (Share / pin-toggle item / Delete
     skill).

4. Verify the menu shows a "Pin" label/button.
   - **Verify**: confirmed live — the exact live label is **"Pin to top"**
     (not a bare "Pin"), `menuitem "Pin to top"` present in the a11y tree.
     Source: `usePinMenu.hooks.jsx` — `label: isPinned ? 'Unpin from top' :
     'Pin to top'` — identical mechanism/wording to the Credentials case
     (ELITEA-1974), shared via `SkillControls.jsx`'s `usePinMenu` call. The
     case's generic "Pin" wording is satisfied by this live text; not
     case-text drift worth a clarification (same non-issue class as
     ELITEA-1974's identical observation).

5. Click "Pin"
   (`page.get_by_role("menuitem", { name: "Pin to top" })` — **no
   `data-testid` on this menu item in the live DOM, see Concrete Handles for
   the gap and fix**).
   - **Verify**: `POST /api/v2/social/pin/prompt_lib/{project_id}/skill/{id}`
     fires and returns **201 Created** (confirmed live via
     `browser_network_requests`, using Skill-A-equivalent
     `elitea-1793-ghost-skill`/id `1203`: `POST http://localhost:5173/
     api/v2/social/pin/prompt_lib/399/skill/1203 => [201] Created`; also
     independently confirmed against a second skill, `changelog-editor`/id
     `682`: `POST .../social/pin/prompt_lib/399/skill/682 => [201] Created`).
     Zero console errors/warnings across this interaction (confirmed via
     `browser_console_messages`).

6. Re-open the overflow menu.
   - **Verify**: menu opens (same handle as step 3).

7. Verify the menu now shows "Unpin from top" (not "Pin to top").
   - **Verify**: confirmed live — `menuitem "Unpin from top"` present,
     matching `usePinMenu.hooks.jsx`'s flipped label.

8. Navigate back to the Skills list page (`${BASE_URL}/skills/all`).
   - **Verify**: page loads.

9. Verify the pinned Skill is visually marked as pinned (pin icon, top of
   list).
   - **Verify** (two-part, both confirmed live using the reordering-capable
     pair — pinning `changelog-editor`, the list's **last** item before
     pinning, id `682`):
     (a) the pinned skill's card **moves to the very top of the list**
     (re-snapshot confirmed: `changelog-editor` now precedes every other
     card, including the item that was previously first by
     `created_at desc`);
     (b) its list-row icon button's accessible name flips to **"Unpin from
     top"** (confirmed live) and carries **`data-testid=
     "skill-pin-toggle-button-{id}"`** — **confirmed live, PRE-EXISTING
     testid** (`page.get_by_test_id("skill-pin-toggle-button-682")` resolved
     correctly via the Playwright MCP tool's own accessible-name-based click
     during this run; the shared `PinButton.jsx` component already wires
     `data-testid={`${getPinTestIdSlug(entityType)}-pin-toggle-button-${entityId}`}`
     with `getPinTestIdSlug` mapping Skill cards → `'skill'` — no testid gap
     on the list-view icon button, unlike the detail-page menu item below).

10. Re-open the same Skill (click the pinned card's name again).
    - **Verify**: detail page loads.

11. Open the overflow menu and click "Unpin".
    - **Verify**: `DELETE /api/v2/social/pin/prompt_lib/{project_id}/
      skill/{id}` fires and returns **204 No Content** (confirmed live:
      `DELETE http://localhost:5173/api/v2/social/pin/prompt_lib/399/
      skill/1203 => [204] No Content`, and independently for id `682`).
      Zero console errors/warnings.

12. Re-open the overflow menu.
    - **Verify**: menu opens.

13. Verify the menu now shows "Pin" (i.e. "Pin to top") again.
    - **Verify**: confirmed live — `menuitem "Pin to top"` present again
      immediately after the unpin click, before navigating away (proving
      the unpin took effect client-side immediately).

14. Navigate back to the Skills list page.
    - **Verify**: page loads.

15. Verify the Skill is no longer marked as pinned.
    - **Verify**: confirmed live — re-navigating to `/skills/all` shows the
      list back in its **original order** (the previously-pinned skill
      returns to its normal chronological position, no longer first unless
      it was already the newest item), and its list-row icon button reads
      **"Pin to top"** again (confirmed live). Full round-trip re-verified
      twice this run: once with `elitea-1793-ghost-skill` (id 1203, already
      the newest item — position unchanged but menu-label round-trip
      confirmed) and once with `changelog-editor` (id 682, the list's oldest
      item — full top→bottom reordering round-trip confirmed, list reverted
      to `elitea-1793-ghost-skill, ..., changelog-editor` exactly matching
      the pre-test baseline).

**Side-channel check (all steps):** zero console errors or warnings across
the full pin → navigate → menu-open → unpin → re-verify flow, confirmed via
`browser_console_messages` (`all: true`) for the entire session (Total
messages: 7, Errors: 0, Warnings: 0).

## Expected Results
Matches the case's Pass criteria exactly, live-verified end-to-end: pinning
moves the skill to the top of the list (step 9), the detail page's
three-dot menu reflects pinned state via "Unpin from top" (steps 6–7),
unpinning fires the expected `DELETE` and reverts both the menu label and
the list position (steps 11–15). No functional defect found in the
pin/unpin mechanism itself.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture (localhost dev token) | asserted |
| Precondition: Skills section accessible with ≥1 skill | — | AFS Preconditions + Test Data | two skills seeded via `SkillAPI` | asserted |
| 1 Navigate to Skills list, note pinned skills | list page loads | step 1 | step 1: both cards visible, B-above-A baseline order, all `is_pinned: false` | asserted |
| 2 Open an existing unpinned Skill | detail page loads | step 2 | step 2: URL pattern + form loads | asserted |
| 3 Open the overflow menu | menu opens | step 3 | step 3: `skill-controls-menu-button` opens menu, both VERSION/SKILL sections visible | asserted |
| 4 Verify menu shows "Pin" label | Pin option displays | step 4 | step 4: exact live text "Pin to top" | asserted |
| 5 Click "Pin" | skill gets pinned | step 5 | step 5: `POST .../social/pin/.../skill/{id}` 201 | asserted |
| 6 Re-open the overflow menu | menu opens | step 6 | step 6: same handle as step 3 | asserted |
| 7 Verify menu now shows "Unpin" | Unpin option displays | step 7 | step 7: exact live text "Unpin from top" | asserted |
| 8 Navigate back to Skills list | list page loads | step 8 | step 8: page loads | asserted |
| 9 Verify pinned Skill visually marked as pinned | pin icon / top of list | step 9 | step 9a (position — moved to top, using the reordering-capable pair) + step 9b (icon flips + testid) | asserted *(decomposed — position and icon-state are both distinct observables the case's single expected result implies)* |
| 10 Re-open the same Skill | detail page loads | step 10 | step 10: page loads | asserted |
| 11 Open overflow menu, click "Unpin" | skill gets unpinned | step 11 | step 11: `DELETE .../social/pin/.../skill/{id}` 204 | asserted |
| 12 Re-open the overflow menu | menu opens | step 12 | step 12: same handle as step 3 | asserted |
| 13 Verify menu shows "Pin" again | Pin option displays again | step 13 | step 13: exact live text "Pin to top" | asserted |
| 14 Navigate back to Skills list | list page loads | step 14 | step 14: page loads | asserted |
| 15 Verify Skill no longer marked as pinned | not pinned | step 15 | step 15: list reverts to original order, icon reads "Pin to top" | asserted |
| Expected Final State: verify the skill is no longer marked as pinned | — | steps 11–15 | full unpin round trip | asserted |

### Axis 2 — Analyst additions

- step 1 documents the underlying `GET .../skills/prompt_lib/{project}/...`
  list response's `is_pinned` field — *added: gives the implementer a
  data-level assertion (not just visual) for "currently pinned" state.*
- step 5/11 document the underlying `POST`/`DELETE .../social/pin/.../
  skill/{id}` network calls and their status codes — *added: the case only
  asks to verify visual state, but the network call is the mechanism an
  implementer will want to wait on (`page.wait_for_response`) rather than a
  fixed sleep, same reasoning as ELITEA-1974.*
- step 9 documents the list-view icon button's pre-existing
  `skill-pin-toggle-button-{id}` testid — *added: saves the implementer an
  `add-data-testid` round-trip for this element, unlike the detail-page menu
  item (see Concrete Handles gap).*
- "zero console errors/warnings across the full flow" — *added: side-channel
  check per this skill's standard discipline; not itself a case requirement.*
- Ran the flow twice with two different skills (one already at list-top, one
  at list-bottom) — *added: the case's own single skill doesn't force a
  position CHANGE if that skill happens to already be topmost; using a
  bottom-ranked skill proves actual reordering, not just label round-trip.
  This AFS specs the two-skill seeded pattern so the implementer's automated
  test always exercises real reordering, regardless of pre-existing data.*

## Cleanup
1. Delete both skills created in Test Data via `SkillAPI.delete_skill(skill_id)`
   in test teardown (regardless of pass/fail).
2. No other product state is created by this case — pin/unpin state lives on
   the skill record itself (`is_pinned` field) and is removed along with it;
   no separate "pin" record needs independent cleanup (same
   `DELETE .../social/pin/.../skill/{id}` pattern observed for credentials —
   pinning is scoped to `skill/{id}`, not a standalone entity).
3. **This run used two pre-existing production-like skills
   (`elitea-1793-ghost-skill` id 1203, `changelog-editor` id 682) instead of
   API-seeded ones**, since no API-seeding helper call was made during
   exploration itself (exploration reused existing data to move faster, per
   this skill's fast-reach guidance). Both were pinned then unpinned and
   **fully reverted to their original unpinned state** before this run
   ended — reconfirmed via a final `/skills/all` re-navigation showing the
   original 10-skill order restored exactly. No stray pinned state was left
   behind. The implementer's actual automated test should use the seeded
   Skill A/B pattern above (own data, own cleanup) rather than mutating
   pre-existing skills.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Skills list → "Pin to top" / "Unpin from top" icon button (`PinButton.jsx`, used in `DataTableRow.jsx`'s card rendering, shared across entity types) | **confirmed live, PRE-EXISTING testid** — `data-testid="skill-pin-toggle-button-{id}"`, scoped per-row by skill id (`getPinTestIdSlug()` in `PinButton.jsx` maps `isSkillCard → 'skill'`). `page.get_by_test_id(f"skill-pin-toggle-button-{skill_id}")` — no page-object method exists yet, add one (e.g. `SkillsListPage.pin_toggle_button(skill_id)`) mirroring `CredentialsListPage.pin_toggle_button()`. | none needed — testid already present, no fallback required |
| Skill detail page → three-dot menu button (`ControlsDropdown` via `SkillControls.jsx`'s `anchorButtonProps={{'data-testid': 'skill-controls-menu-button'}}`) | `page.get_by_test_id("skill-controls-menu-button")` — **confirmed live, existing testid**, already wired as `SkillDetailPage.controls_menu_button` | `page.get_by_role("button")` inside the tab-bar controls group |
| Skill detail page → pin-toggle menu item ("Pin to top" / "Unpin from top", `usePinMenu.hooks.jsx` → rendered via `DotMenu`'s `BasicMenuItem`) | **TESTID NEEDED — confirmed live gap.** `SkillControls.jsx`'s `menuItems` array spreads `pinMenuItem` directly (`pinMenuItem,` at line ~199) with **no `key` field**, unlike its sibling `delete-skill` item which sets `slotProps.MenuItem['data-testid']` explicitly. `DotMenu.jsx` derives `testId: item.key` for each menu entry, so with no `key` the rendered `<MenuItem>` gets `data-testid={undefined}`. **Fix (one-line, same shape as `EliteaAI/EliteaUI#569`'s credential fix):** in `SkillControls.jsx`, change `pinMenuItem,` to `{ key: 'pin-toggle-skill', ...pinMenuItem },` inside the `menuItems` array — this flows through `DotMenu.jsx`'s `${testId}-menuitem` convention to produce `data-testid="pin-toggle-skill-menuitem"`. Route through `add-data-testid` before implementing; naming follows the credential precedent (`pin-toggle-credential-menuitem` → `pin-toggle-skill-menuitem`). This is the SAME sibling gap ELITEA-1974's AFS flagged as "likely applies to SkillControls.jsx ... not fixed for those other pages in this run" — now confirmed live and scoped for this case. | `page.get_by_role("menuitem", { name: "Unpin from top" })` / `page.get_by_role("menuitem", { name: "Pin to top" })` — unambiguous in this run since only one menu is open at a time and only one item carries that exact accessible name. **Per this project's testid-only locator policy, do not ship using this fallback — land the testid fix first.** |
| Skill card name (list view) | `page.get_by_test_id("entity-card-name")` — **existing testid**, already in `SkillsListPage.skill_card_name` (shared `Card.jsx` component, collection locator) | n/a |
| Skill card outer container (list view) | `page.get_by_test_id("entity-card")` — **existing testid**, already in `SkillsListPage.skill_card` | n/a |

**Summary for the implementer / `add-data-testid`:** one testid gap found
during analysis — the pin-toggle menu item on the Skill detail page's
three-dot menu has zero `data-testid`, purely because `SkillControls.jsx`'s
`pinMenuItem` spread never sets a `key` (unlike its sibling delete item).
One-line fix at the `SkillControls.jsx` call site (add `key:
'pin-toggle-skill'`), same shape as the fix already landed for Credentials
on `EliteaAI/EliteaUI#569`. The list-view pin/unpin icon button needs
**no fix** — it already carries `skill-pin-toggle-button-{id}` via the
shared `PinButton.jsx` component (this appears to have landed generically
across all entity types when #569 fixed the credential-specific gap,
confirmed live for Skills in this run).

## Network Behavior
- `POST /api/v2/social/pin/prompt_lib/{project_id}/skill/{id}` — fires on
  pin, returns `201 Created`. No response body inspected beyond status code.
- `DELETE /api/v2/social/pin/prompt_lib/{project_id}/skill/{id}` — fires on
  unpin, returns `204 No Content`.
- `GET /api/v2/elitea_core/skills/prompt_lib/{project_id}?sort_by=
  created_at&sort_order=desc&query=&tags=&limit=20&offset=0` — list load,
  each row carries an `is_pinned` boolean field — usable for a data-level
  assertion alongside the visual one.
- `GET /api/v2/elitea_core/skill/prompt_lib/{project_id}/{id}` (implied
  detail load, not independently re-verified this run — same pattern as
  other skill detail pages already documented in `test-specs/skills/
  _surface.md`).
- The skills' own `POST .../skills/prompt_lib/{project_id}` (create, Test
  Data setup) and `DELETE .../skill/prompt_lib/{project_id}/{id}` (cleanup)
  — both via `SkillAPI`, not asserted as part of the pin/unpin case itself.

## Known Defects / Observations Found During Exploration

No functional product defect was found. All 15 case steps live-verified
end-to-end with the expected pass criteria met exactly, including full
round-trip reversion back to the original list order, run twice against two
different skills (one already list-topmost, one list-bottommost) to prove
both the label round-trip and actual position reordering.

One non-blocking observation, informational only:

1. **[Informational — not filed] Pinning a skill that is already the
   newest/topmost item (sorted by `created_at desc`) produces no visible
   position change**, only the icon/menu-label flip. This is expected
   behavior (nothing to reorder above), not a defect — flagged here only so
   an implementer writing this case's automated test seeds a **second,
   older skill** (as this AFS's Test Data section specifies) rather than
   asserting "moved to top" against a single skill that happened to already
   be there, which would pass trivially and never actually prove the
   reordering.

## Blocked Steps
None. All 15 case steps were executed end-to-end live against the real DEV
backend, including the full pin → verify-detail-menu → verify-list-position
→ unpin → verify-reverted round trip, run against two different skills.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/skills/test_skill_pin_unpin.py` (new file — grep of
  `automation/tests/ui/skills/` found no existing test exercising pin/unpin
  for skills; `test_skill_management.py` and the other existing files in
  that directory don't touch the pin/unpin widget).
- `SkillAPI.create_skill()` / `SkillAPI.delete_skill()`
  (`automation/api/client.py:1427,1460`) already exist — reuse directly for
  setup/teardown, same pattern as the credential case (ELITEA-1974) and
  other skill API-seeded tests in this suite.
- **Route the confirmed testid gap (detail-page pin-toggle menu item)
  through `add-data-testid` BEFORE implementing** — per this project's
  strict testid-only locator policy (`.agents/testing.md` § Locator policy,
  `.agents/role-overrides.md`), do not ship using the `get_by_role`
  fallback used during this exploration. The list-view icon button needs no
  such round-trip (testid already present).
- New page-object locators needed on `SkillDetailPage`
  (`automation/pages/skill_detail_page.py`, extending the existing
  `controls_menu_button`): a `pin_toggle_menuitem` `LocatorDescriptor`
  (testid `pin-toggle-skill-menuitem`, once landed) + helper methods
  mirroring `CredentialDetailPage.open_controls_menu()` /
  `get_pin_toggle_menu_label()` / `click_pin_toggle_menu_item()`
  (`automation/pages/credential_detail_page.py:174-197`) — same pattern,
  different entity. On `SkillsListPage`
  (`automation/pages/skills_list_page.py`): a dynamic-testid template
  constant (e.g. `SKILL_PIN_TOGGLE_BUTTON = '[data-testid="skill-pin-toggle-button-{}"]'`)
  + a `pin_toggle_button(skill_id)` helper, per the dynamic-testid pattern
  in `.agents/testing.md` § Locator policy.
- Wait strategy: wait on the `POST`/`DELETE .../social/pin/.../skill/{id}`
  network response (`page.wait_for_response` matching the URL pattern)
  rather than a fixed sleep before asserting the reordering or menu-label
  flip — both observed to complete synchronously with the response in this
  run (no separate loading-state UI was observed for the pin toggle
  itself).
- Assertion for "moved to the top" / "returned to normal position": assert
  on the **relative DOM order** of Skill A vs Skill B's card name text
  nodes within the list container (or their bounding-box `y` positions),
  not on absolute page position — mirrors ELITEA-1974's approach for
  credentials.
