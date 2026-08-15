# Test Case: Chat – Folder Rename – Check Icon Inactive for Less Than 3 Characters

## Metadata
- **TMS ID**: ELITEA-2125
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case frontmatter: `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", `projectId=399`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-15, wave-06
- **Status**: extend-existing
- **Extension target**: `automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py`,
  method `test_folder_rename_checkmark_validation` (its own AFS:
  `test-specs/chat-interface/l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md`)

**Nearly a full subset of the covering test, ONE genuine gap.** ELITEA-2125's
steps 1–3 (open editor, type 2 chars, verify `data-disabled="true"` + tooltip)
map 1:1 onto the covering test's Steps 1, 4, 5. The one case element the
covering test never independently asserts is step 4: **"Attempt to click the
checkmark → click has no effect"** specifically while the name is 2
characters. The covering test's own no-op-click check (its Steps 3 and 6)
only exercises that click at the EMPTY-name state and the
valid-but-unchanged-name state — never at the "invalid because too short"
state. Same underlying mechanism (`onClick={isFolderSaveEnabled ? handler :
null}`), but a genuinely distinct state combination not yet independently
observed on the live system, so per the Coverage Map discipline this is a
real gap, not an assumed one — filling it is a small, additive insertion into
the SAME existing test, not a new test method (the click is designed to be a
no-op, so it doesn't disrupt the test's subsequent steps 5–9).

**Live-verified this session** (fresh live drive, `browser_run_code_unsafe`
against `localhost:5173`, project 399): seeded a fresh folder
("W06GapCheck5", id 242), opened its rename editor via the dot-menu →
"Rename" (case says "Edit" — same already-documented drift as the sibling
ELITEA-2121/2130/2122/2127/2123/2124/2126 cases, not re-filed here), typed
exactly `"AB"`, confirmed `data-disabled="true"`, then clicked
`chat-folder-name-confirm-button` and observed all three no-op signals hold:
editor stayed open (`folder_name_input.isVisible() === true`), input value
unchanged (`"AB"`), the folder's own `chat-folder-item-{id}` accordion row
did NOT re-render (count `0`, same "edit mode never exited" proof the
covering test already uses), and zero new `PUT
.../folder/prompt_lib/399/242` requests fired. Confirms the gap this AFS
fills is real behavior, not a guess.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least one folder exists that the test owns — this AFS extends the
  covering test's OWN existing seeded-folder flow; no separate seed needed.

## Test Data
Reuses the covering test's own seeded folder (`ORIGINAL_FOLDER_NAME =
"AutomationRenameTest"`) and its existing `TWO_CHAR_NAME = "AB"` constant —
no new test data introduced.

## Test Steps (delta only — see § Gap assertions for the exact insertion point)

1. (Already covered by the covering test's Step 1 — open rename editor.)
2. (Already covered by the covering test's Step 4 — type `"AB"`, verify
   input + `data-disabled="true"`.)
3. (Already covered by the covering test's Step 5 — hover, verify tooltip text.)
4. **NEW** — Click `chat-folder-name-confirm-button` while the name is
   `"AB"`.
   - **Verify**: the editor stays open (`chat-folder-name-input` still
     visible), the input value is still `"AB"` (the no-op click must not
     mutate the editor's own local state either), the folder's
     `chat-folder-item-{folder_id}` row does NOT re-render (proves edit mode
     was never unexpectedly exited), and zero new `PUT
     .../folder/prompt_lib/{project_id}/{folder_id}` requests fire.

## Expected Results
- The checkmark (confirm) icon is inactive for a 2-character name AND
  clicking it while inactive has no effect — no `onClick` handler fires, no
  network call, no rename, the editor stays open exactly as it does for the
  covering test's OTHER two already-asserted inactive states (empty,
  valid-but-unchanged).

## Gap assertions

**Insertion point:** inside `test_folder_rename_checkmark_validation`, a NEW
`with allure.step("Step 4a — ELITEA-2125: click the checkmark while the name
is 2 characters; verify no effect")` block placed AFTER the existing "Step 5
— Hover the checkmark…" block (i.e. after the tooltip text has been read, so
the click doesn't disturb the tooltip-visible precondition Step 5 needs) and
BEFORE the existing "Step 6 — Restore the original…" block. This is a pure
insertion — none of the existing `with allure.step(...)` blocks or their
bodies change.

```python
with allure.step(
    "Step 4a — ELITEA-2125: click the checkmark while the name is "
    "2 characters (\"AB\"); verify it has no effect"
):
    puts_before = len(put_requests)
    chat.folder_name_confirm_button.click()
    page.wait_for_timeout(300)
    assert chat.folder_name_input.is_visible(), (
        "Editor should stay open after clicking the inactive "
        "(2-character) checkmark"
    )
    assert chat.folder_name_input.input_value() == TWO_CHAR_NAME, (
        "Input should remain unchanged by the no-op click"
    )
    assert chat.get_folder_item(folder_id).count() == 0, (
        f"Folder {folder_id} should NOT re-render as an accordion row"
    )
    assert len(put_requests) == puts_before, (
        "No PUT to the folder endpoint should fire on an "
        f"inactive-checkmark click, saw: {put_requests[puts_before:]}"
    )
```

Reuses the exact `put_requests` list and `_on_request` listener the covering
test already registers at the top of the method — no new fixture/listener
needed.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| 1 Hover folder, click 3-dot, click Edit → folder name editable | Target state reached | covering test Step 1 | pre-fill/focus assertions | already-covered |
| 2 Clear + type 2 chars ("AB") → checkmark inactive | 2 characters in field | covering test Step 4 | `input_value() == "AB"` + `is_folder_name_confirm_enabled()` is `False` | already-covered |
| 3 Verify checkmark disabled + tooltip shown | Checkmark inactive; tooltip visible | covering test Step 5 | exact tooltip text assertion | already-covered |
| 4 Attempt to click the checkmark → click has no effect | No-op | **new Step 4a (this AFS)** | editor-open + input-unchanged + folder-row-absent + no-PUT assertions | asserted (new) |
| Expected Final State: "Checkmark stays inactive for input shorter than 3 characters" | — | covering test Step 4 + new Step 4a | covered by the rows above | already-covered |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked`
/ `out-of-scope`. All rows resolved; one genuinely new assertion added, the
rest already-covered by the merged spec.

### Axis 2 — Analyst additions
- The no-op click check reuses the covering test's own THREE-independent-
  signal pattern (editor-open, input-unchanged, no-PUT, plus the
  folder-row-absence signal) rather than a single check — *added: consistent
  with the covering test's own Axis-2 rationale (a single signal could pass
  even if some other unintended side effect fired).*
- (nothing else added beyond filling this one gap.)

## Cleanup
No new cleanup needed — the inserted step runs inside the covering test's
existing seeded-folder lifecycle, cleaned up by that test's existing
`finally` block.

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `chat-folder-name-input`,
`chat-folder-name-confirm-button` (`data-disabled` state attribute),
`chat-folder-item-{id}` — all confirmed present and functioning on live
localhost this session (fresh live drive, folder id 242, see § Metadata's
live-verification note). No new handles needed.

## Network Behavior
- Zero new `PUT /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_id}`
  requests fire on the 2-char-state no-op click — live-confirmed this session
  via `browser_network_requests`-equivalent request tracking (a
  `page.on('request', ...)` collector), same idiom the covering test already
  uses for its own no-op-click checks.

## Known Defects Found During Exploration
None. The gap this AFS fills is a coverage gap (an unasserted state
combination), not a product defect — the mechanism behaves identically to
the two adjacent states the covering test already asserts.

## Blocked Steps
None. The new assertion is executable via existing page-object infrastructure
(`chat.folder_name_confirm_button`, `chat.folder_name_input`,
`chat.get_folder_item()`), no new handles or methods needed.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Additive-only edit to `test_chat_folder_rename_checkmark_validation.py`'s
  `test_folder_rename_checkmark_validation` method — insert the new
  `allure.step` block per § Gap assertions; every existing line stays
  byte-identical. Verify via
  `git diff automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py | grep -E '^-[^-]'` → empty.
- Coverage-tag mechanics: append a second `@allure.issue(...)` decorator (this
  case's own onetest-ai case-file URL) onto the SAME `test_folder_rename_checkmark_validation`
  method (it already carries ELITEA-2458's `@allure.issue`) — Playwright/
  pytest supports stacking `@allure.issue` decorators the same way the file's
  other extended methods don't need to (this one's extension is inline, not a
  new method, so the tag lives on the existing method's decorator stack).
