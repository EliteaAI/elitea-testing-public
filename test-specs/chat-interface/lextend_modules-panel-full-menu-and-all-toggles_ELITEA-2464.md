# Test Case: Chat – Modules Panel Accessible From + Icon, Full Popup Menu, All Toggles Functional

## Metadata
- **TMS ID**: ELITEA-2464
- **Linked Story**: [EliteaAI/elitea-testing-public#972](https://github.com/EliteaAI/elitea-testing-public/issues/972) (originating tracking issue)
- **Priority**: lextend (case frontmatter says `priority: high`, which maps to `l2` — filename prefix
  replaced per spec-format.md's rule that `extend-existing` outcomes use `lextend_`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`,
  DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN` — no explicit login
  performed)
- **Analyst**: qa-engineer (analyst slot), combined analyst+implementer dispatch, batch
  `elitea-2464-chat-modules-panel`
- **Status**: **extend-existing** — case executed live end-to-end (all 11 steps + precondition observed
  against the running product), zero product defects, one live product **change** discovered
  (see § Overlap check). Core flow (open conversation → + icon → Modules → toggle → close) is
  materially covered by the already-merged ELITEA-2162 spec; this AFS's Gap assertions section is
  everything ELITEA-2464 demands that the covering spec does not yet assert.

## Overlap check vs existing automation

**Covering spec**: `automation/tests/ui/chat/test_chat_search_and_modules_panel.py::
TestChatSearchAndModulesPanel::test_search_filters_and_modules_panel_toggles` (merged to
`automation/base`, commit `36db543c`, covers ELITEA-2162). Its own AFS:
`test-specs/chat-interface/l2_chat-search-and-modules-panel_ELITEA-2162.md` — read in full before
this run, along with the merged spec and `automation/pages/chat_page.py`'s Modules-panel methods
(`open_internal_tools_menu()`, `verify_module_toggle_order()`, `click_module_toggle()`,
`is_module_toggle_checked()`, `close_modules_panel()`, `get_module_toggle_switches()` — all
pre-existing, all testid-based).

**What the covering spec already proves** (ELITEA-2464 steps it fully satisfies as-is):
- Step 1 (open an existing conversation) — covering spec's steps 1–5 create + open a conversation.
- Step 2 (click + icon) / Step 4 ("click" Modules, live mechanism is **hover** — covering AFS's own
  Coverage Map already dispositions this as "mechanism is hover, not click — noted in step, not a
  case defect"; ELITEA-2464's case text has the identical click-vs-hover imprecision, so no new
  clarification is filed for it here — same disposition applies) — covering spec's step 6
  (`open_internal_tools_menu()`).
- Step 5 (panel opens, toggleable features visible) — covering spec's step 6
  (`verify_module_toggle_order()`), **once `MODULE_TOGGLE_ORDER` is corrected to 8 entries** (see
  finding below — this AFS's implementer amendment, not a covering-spec defect at merge time).
- Step 9 (toast "Modules configuration Updated" after a toggle change) — covering spec's steps 7–8
  assert toast text for 2 of the (now 8) modules; same clarification already filed by the covering
  AFS (issue #1115 — actual text is lowercase "updated") applies identically here, not re-filed.

**What ELITEA-2464 demands that the covering spec does NOT yet assert** (this AFS's Gap
assertions, § below):
1. Step 3 — the popup menu's full option list (Attach Files, Modules, Agents, Pipelines, Toolkits,
   MCPs) is never asserted by the covering spec; it opens the menu and goes straight to hovering
   Modules.
2. Steps 7–8 — "click the toggle for each module one by one" / "verify the state changes correctly
   for each toggle": the covering spec samples only 2 of the (now 8) modules
   (`image_generation`, `data_analysis`). The case demands full per-module coverage.
3. Step 6 — "verify each toggle displays its current on/off state" as an explicit pre-toggle read,
   distinct from the covering spec's `verify_module_toggle_order()` (which asserts visibility +
   accessible name, not checked-state).
4. Step 10 — "verify no error messages are shown" is never explicitly asserted (only the positive
   success-toast text is checked).
5. Step 11 — "close the Modules panel and verify the main conversation view is restored": the
   covering spec's step 9 asserts the toggle-switch count drops to 0, but never asserts the
   conversation view itself (composer) is visible/interactable again.

**Live product finding (discovered this run, not a defect):** the Modules panel now renders
**8** toggles, not 7 — a new **"Ask User"** toggle (`data-testid="modules-toggle-ask_user"`,
tool key `ask_user`) appears between "Python Sandbox" and "Swarm Mode". Both ELITEA-2464's case
text and ELITEA-2162's already-merged spec predate this (ELITEA-2162 analysed 2026-08-03; this
run 2026-08-07). Filed as clarification:
[EliteaAI/elitea-testing-public#1293](https://github.com/EliteaAI/elitea-testing-public/issues/1293).
**Implementer amendment**: `ChatPage.MODULE_TOGGLE_ORDER` is extended (additive — 7 existing
entries unchanged, 1 new entry inserted in its live DOM position) so the covering spec's own
count assertion (`len(MODULE_TOGGLE_ORDER)`, not a hardcoded literal) stays correct against
current product state instead of drifting to a false red. This is a shared-constant fix that
benefits the already-merged spec, not a scope change to it.

## Preconditions
- User is authenticated (`auth_state` fixture — localhost skips real login).
- A conversation exists and is open in the main chat panel (reuses the covering spec's own
  `conversation_api`-created conversation — no separate precondition setup needed since this AFS
  extends the SAME test method).

## Test Data
No additional test data beyond what the covering spec's `conv_name`/`conv_id` already provides.

## Test Steps (delta over the covering spec — inserted at the corresponding point in the SAME
`test_search_filters_and_modules_panel_toggles` method)

1. **New — after opening the plus menu, before hovering Modules**: verify the full popup menu is
   visible with exactly 6 top-level items in DOM order — Attach Files
   (`chat-attach-menuitem-button`), Modules (`internal-tools-menuitem`), Agents
   (`agents-menuitem`), Pipelines (`pipelines-menuitem`), Toolkits (`toolkits-menuitem`), MCPs
   (`mcps-menuitem`) — all pre-existing testid-based `LocatorDescriptor` fields on `ChatPage`.
   The 6 items are asserted individually by visibility; the pre-existing
   `get_open_plus_menu_item_count()` helper additionally corroborates 5 of them
   (it is scoped to the shared `-menuitem` testid SUFFIX, which
   `chat-attach-menuitem-button` does not match — a distinct naming convention
   for that one control, live-confirmed returns 5 not 6 during implementation).
2. **Extends existing Step 6** (`verify_module_toggle_order()`): once `MODULE_TOGGLE_ORDER` is
   corrected (8 entries), this pre-existing method call already asserts all 8 switches visible,
   correctly named, in DOM order — no new page-object method needed, only the data fix above.
   - **New**: read `is_module_toggle_checked(tool_key)` for all 8 tool keys BEFORE any toggling —
     satisfies the case's step 6 "verify each toggle displays its current on/off state" as an
     explicit read distinct from `verify_module_toggle_order()`'s visibility/name check.
3. **New — extends existing Steps 7/8**: for the 6 modules the covering spec does NOT already
   exercise (`internal_mcp`, `planner`, `pyodide`, `ask_user`, `swarm`, `lazy_tools_mode`), toggle
   each on then off (mirroring the exact pattern already used for `image_generation`/
   `data_analysis`): assert the checked state flips each click
   (`is_module_toggle_checked(tool_key)` before/after), assert `toast_message` becomes visible with
   text `"Modules configuration updated"` (lowercase — same clarification as issue #1115), AND
   **assert the toast alert's severity is `success`** via the pre-existing
   `get_toast_alert("success")` / `TOAST_ALERT_SEVERITY` mechanism (testid `toast-alert` +
   `data-severity` state filter — NOT on the `toast-message` testid itself, which is a plain text
   `Box` child with no severity attribute of its own; corrected during implementation from an
   earlier draft of this AFS that conflated the two) — satisfies case step 10 "no error messages
   shown" as a positive, stable-attribute check per `.agents/testing.md`'s
   testid+`data-*`-state-filter pattern; `ToastProvider.jsx` sets `severity: 'error'` only via
   `toastError`, so asserting `success` on `toast-alert` is a genuine negative check on the error
   path, not a tautology.
4. **Extends existing Step 9** (close panel via outside click): after
   `get_module_toggle_switches()` count reaches 0, **new** — assert `chat.message_input`
   (`chat-message-input`, pre-existing testid) is visible AND enabled, satisfying the case's step
   11 "verify the main conversation view is restored" as a concrete, interactable-composer check
   rather than only "the panel's own elements are gone."

## Expected Results
- The + icon's popup menu shows exactly 6 items (Attach Files, Modules, Agents, Pipelines,
  Toolkits, MCPs) before any submenu is opened.
- The Modules panel shows all 8 currently-live toggles (not 7 — see Overlap check finding), each
  with a readable current on/off state.
- Every one of the 8 toggles flips state and shows the `"Modules configuration updated"` toast
  and the toast alert's `data-severity="success"` when clicked (via `toast-alert`, not `toast-message`) — no error-severity toast at any point.
- Closing the panel (outside click) restores the plain conversation view: 0 toggle switches
  remain AND the message composer is visible and enabled again.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | covering spec `auth_state` | fixture | asserted (reused) |
| 1 Navigate to Chats, open existing conversation | Target page loads | covering spec steps 1–5 | covering spec | asserted (reused, not re-implemented) |
| 2 Click + icon | Control responds | covering spec step 6 (`open_internal_tools_menu` click phase) | covering spec | asserted (reused) |
| 3 Verify popup menu: Attach Files, Modules, Agents, Pipelines, Toolkits, MCPs | Condition holds | new step 1 | new step 1: 6 items visible in order | asserted |
| 4 Click Modules | Control responds | covering spec step 6 (hover phase) | covering spec | asserted *(mechanism is hover, not click — same disposition as covering AFS, not re-flagged)* |
| 5 Verify Modules panel opens with 7 toggles | Condition holds | covering spec step 6 (`verify_module_toggle_order`) | covering spec, using corrected `MODULE_TOGGLE_ORDER` | clarification — live count is 8, not 7 (new "Ask User" toggle). Filed: EliteaAI/elitea-testing-public#1293. AFS asserts live count (8). |
| 6 Verify each toggle displays current on/off state | Condition holds | new step 2 | new step 2: `is_module_toggle_checked` × 8 pre-toggle | asserted |
| 7 Click toggle for each module one by one, on and off | Control responds | covering spec steps 7–8 (2 of 8) + new step 3 (remaining 6) | both | asserted |
| 8 Verify state changes correctly for each toggle | Condition holds | covering spec steps 7–8 + new step 3 | both | asserted |
| 9 Verify "Modules configuration Updated" after each toggle | Condition holds | covering spec steps 7–8 + new step 3 | both | asserted *(clarification — actual text lowercase "updated", same as issue #1115, not re-filed)* |
| 10 Verify no error messages shown | Condition holds | new step 3 | new step 3: `toast-alert` `data-severity="success"` per toggle (via `get_toast_alert("success")`) | asserted |
| 11 Close panel, verify main conversation view restored | Action completes, expected UI state | covering spec step 9 (switch count 0) + new step 4 (`message_input` visible/enabled) | both | asserted |
| Expected Final State: main view restored | — | covering spec step 9 + new step 4 | — | asserted (composite) |

**Axis 2 — Analyst additions**

- New step 3 asserts the `toast-alert` element's `data-severity` attribute (not just `toast-message`'s text) — *added:
  this is the only way to make case step 10 ("no error messages") a real, falsifiable assertion
  rather than an implicit absence-of-failure; a genuinely broken toggle that silently fired an
  error toast with reused wording would otherwise slip through.*
- (No other additions beyond the case.)

## Cleanup
None beyond the covering spec's existing `finally` block (deletes the shared conversation). The
6 newly-toggled modules are flipped on then off within the same steps (mirrors the covering
spec's existing image_generation/data_analysis pattern), so no additional state leaks forward.

## Concrete Handles (discovered during exploration)

All testid-only, all pre-existing `LocatorDescriptor` fields or class constants on `ChatPage` —
no new testids required for this case.

**Provenance correction (implementer fix round 1, 2026-08-07):** the table below originally
marked all 10 rows `on-main ✓` without a fresh grep. A reviewer fresh-session pass and this
fix round's own re-verification (`cd ../EliteaUI && git fetch origin`, then
`git grep -in -- "<testid>" origin/main -- src/` vs `origin/automation/testids -- src/`, both
case-insensitively matching `data-testid`/`testId`) found only **3 of 10** genuinely on `main`;
the other **7** exist only on `automation/testids` (awaiting human cherry-pick). This matches
the reviewer's independent finding
(`.agents/memory/qa-engineer/afs_claims_need_full_sweep_and_grep.md`, 10th occurrence). The
whole `modules-toggle-{}` dynamic-testid mechanism (`PlusChatButton.jsx` `slotProps: { input:
{ 'data-testid': \`modules-toggle-${tool.name}\` } }`) does not exist on `main` at all — not
just the new `ask_user` entry — so every toggle testid this test (and the already-merged
ELITEA-2162 spec before it) depends on is testids-only right now.

| Element | Testid | Provenance | Notes |
|---|---|---|---|
| Attach Files menuitem | `chat-attach-menuitem-button` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.attach_files_button` |
| Modules menuitem | `internal-tools-menuitem` | on-main ✓ | `ChatPage.internal_tools_menuitem` — `PlusChatButton.jsx` `data-testid={key === SUBMENU_KEYS.INTERNAL_TOOLS ? 'internal-tools-menuitem' : undefined}` |
| Agents menuitem | `agents-menuitem` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.agents_menuitem` |
| Pipelines menuitem | `pipelines-menuitem` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.pipelines_menuitem` |
| Toolkits menuitem | `toolkits-menuitem` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.toolkits_menuitem` |
| MCPs menuitem | `mcps-menuitem` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.mcps_menuitem` |
| Module toggle switch, "Ask User" (new, ×1) | `modules-toggle-ask_user` | on-`automation/testids` only (awaiting human promotion to main) — the entire `modules-toggle-{}` template mechanism is testids-only, not just this entry | Uses existing `MODULES_TOGGLE_SWITCH` template constant; only `MODULE_TOGGLE_ORDER` tuple needs the new `("ask_user", "Ask User")` entry, inserted between `pyodide` and `swarm` per live DOM order |
| Success/error toast text | `toast-message` | on-main ✓ | `ChatPage.toast_message` — text content only, no severity attribute |
| Toast severity root | `toast-alert` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.toast_alert` / `get_toast_alert(severity)` / `TOAST_ALERT_SEVERITY` (pre-existing) — `data-severity` (`success`/`error`) confirmed live via `ToastProvider.jsx`/`Toast.jsx`, state via `data-*` on a stable testid, per locator policy |
| Message composer input | `chat-message-input` | on-main ✓ | `ChatPage.message_input` |

## Network Behavior
Same as the covering spec (PUT on `useConversationEditMutation` per toggle; toast fires only
after the PUT resolves without error) — no new network behavior to document; applies identically
to all 8 toggles (confirmed via the shared `onInternalToolsConfigChange` code path, same claim
the covering AFS already made for its sampled 2).

## Known Defects Found During Exploration
None. One live product **change** (not a defect) — see § Overlap check finding, filed as
clarification EliteaAI/elitea-testing-public#1293.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest. **Artefact is an edit to the covering spec**
  (`test_chat_search_and_modules_panel.py`), not a new file — insert the new steps at the
  corresponding points inside the existing `test_search_filters_and_modules_panel_toggles` method
  (same pattern as the ELITEA-2090 extension in `test_conversation_management.py`: numbered
  sub-steps like "Step 6a (ELITEA-2464 extension)", plus a second `@allure.issue(...)` decorator
  referencing ELITEA-2464's TMS case link, alongside the existing ELITEA-2162 one).
- Page-object change: `ChatPage.MODULE_TOGGLE_ORDER` gains one entry, additive, in live DOM
  position. Verify with `git diff` on `chat_page.py` showing only an insertion, no removed line
  matching `^-[^-]` for the 7 pre-existing entries.
- **Priority marker**: `@pytest.mark.p1` (case priority "high" → `l2`/`p1`, same convention as the
  covering test and per `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`).
  Existing `@pytest.mark.chat`/`@pytest.mark.regression` already apply to the whole method.
- Run the FULL extended test method (all original + new steps) to prove the additive-only
  contract: original assertions (search/open/2-sampled-toggles) must still pass unchanged.
