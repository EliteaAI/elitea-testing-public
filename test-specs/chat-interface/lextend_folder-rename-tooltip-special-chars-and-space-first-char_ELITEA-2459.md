# Test Case: Chat – Folder rename – validation tooltip for invalid input and first character cannot be a space

## Metadata
- **TMS ID**: ELITEA-2459
- **Source case**: `.agents/automation/elitea-2459-chat-folder-rename-tooltip/cases/ELITEA-2459.md`
  (snapshot; TMS module `chat-interface`)
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case frontmatter: `priority: high` -> `p1`, same class as
  the covering test's own per-function `@pytest.mark.p1` decorator — no
  module-level priority-drift risk here: `test_chat_folder_rename_checkmark_validation.py`'s
  `pytestmark` carries no `p*` marker at module level, only `ui`/`chat`/
  `regression`; the single existing test decorates itself `@pytest.mark.p1`
  directly, so the new sibling method follows the same per-function
  pattern, not a module default).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids`, DEV backend; project "Private", `projectId=399`,
  `${ELITEA_PROJECT_ID}`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN`
  skips explicit Keycloak login
- **Analyst**: qa-engineer (agent), combined analyst+implementer slot
- **Status**: extend-existing

## Extension target

**Covering spec**: `automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py`
(class `TestChatFolderRenameCheckmarkValidation`, method
`test_folder_rename_checkmark_validation`), merged to `origin/automation/base`
via PR #1311 (`da71d4b5`), AFS
`test-specs/chat-interface/l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md`.

**Behavioural-overlap argument, confirmed LIVE this session (not assumed from
source alone)**: ELITEA-2458's covering test already exercises the identical
tooltip text, the identical `chat-folder-name-confirm-button` `data-disabled`
state attribute, and the identical `ConversationNameRegExp` enable/disable
logic for the empty, 2-char, unchanged-valid, and 3-char-changed name
scenarios. This case (ELITEA-2459) asks for exactly two ADDITIONAL invalid
inputs — (a) a name containing unsupported special characters
(`"Folder$$%%"`), and (b) a name whose first character is a space
(`" ValidRest"`, otherwise valid/long-enough) — that the covering spec never
types. Both were driven live against `http://localhost:5173` this session
(seeded folder id `146`, name `ELITEA2459RenameTest`) and behaved **exactly**
the same as the covering spec's already-asserted invalid states: same
`data-disabled="true"`, same exact tooltip copy, same network-silent no-op
click (zero new PUT requests, editor stays open, input value unchanged). No
distinct error path, no product defect, no case-text drift — a genuine
`extend-existing` fit, not a coincidence assumed from the regex alone.

**Gap this case fills**: the covering spec's parameter space is
{empty, 2-char, unchanged-valid, 3-char-changed} — all of which fail (or
pass) the regex via LENGTH or CHANGE-state, never via CHARACTER CLASS. This
case is the first to type a name that is long enough and changed, yet still
invalid because of its CONTENT — proving the regex's charset/first-character
exclusion is enforced through the same `data-disabled`/tooltip mechanism, not
just the length/change gate.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- User is on the Chats section (`${BASE_URL}/chat`).
- A folder exists that the test owns (seeded fresh, same pattern as the
  covering spec — a controlled, known starting name is required so the
  "reachable via the dot-menu Rename item" step has a deterministic target).

## Test Data

### generate-per-test (created by the test's own setup, deleted in its own cleanup)
- One folder, created via the existing `click_create_folder_button()` +
  `set_folder_name(<name>)` + `folder_name_confirm_button.click()` flow
  (ELITEA-2132/ELITEA-2458's create path), name `ELITEA2459RenameTest`
  (live-verified value, distinct from the covering spec's own
  `AutomationRenameTest` seed so the two tests' folders are trivially
  distinguishable in the shared DEV project's folder list if run
  back-to-back).

### literal (typed during the test, never submitted/persisted)
- `"Folder$$%%"` — 10 characters, valid length, but contains unsupported
  special characters (`$`, `%`) outside `ConversationNameRegExp`'s allowed
  charset (`a-z A-Z 0-9 _ [ ] ( ) . -` and space, per the digest's source
  derivation).
- `" ValidRest"` — 10 characters, valid length, all characters (after the
  first) are within the allowed charset, but the FIRST character is a
  space — excluded by the regex's first-character class
  (`[a-zA-Z0-9_[\].()]`, which does NOT include a space, unlike the
  remainder-character class `[a-zA-Z0-9_[\].() -]` which does).

## Test Steps

1. Navigate to `${BASE_URL}/chat`, seed the folder (§ Test Data), open its
   rename editor via the dot-menu Rename item (mirrors the covering spec's
   own Step 1 — `chat.open_folder_rename_editor(folder_id)`).
   - **Verify**: the inline editor opens — `chat-folder-name-input` is
     visible and pre-filled with the seeded name.
2. Clear the input and type `"Folder$$%%"`.
   - **Verify**: the input shows `"Folder$$%%"` verbatim (the field accepts
     the characters — no client-side input-blocking on keystroke, confirmed
     live).
   - **Verify (state)**: `chat-folder-name-confirm-button` carries
     `data-disabled="true"`.
   - **Verify (tooltip)**: hovering the confirm button shows the EXACT same
     validation tooltip text as ELITEA-2458's own Step 5 (live-confirmed
     identical, not re-derived): `"The folder name should be 3 to 64
     characters long. It can include letters (a-z, A-Z), numbers (0-9),
     underscores (_), brackets ([]), parentheses (()), dots (.), hyphen(-),
     and spaces. Please note that the first character should not be a
     space."`
   - **Verify (no-op)**: click `chat-folder-name-confirm-button`; the editor
     stays open, `chat-folder-name-input` still shows `"Folder$$%%"`
     unchanged, and no `PUT .../folder/prompt_lib/{project_id}/{folder_id}`
     request fires.
3. Clear the input and type `" ValidRest"` (space first character).
   - **Verify**: the input shows `" ValidRest"` verbatim — the leading space
     is accepted by the field (not trimmed/blocked on keystroke, confirmed
     live).
   - **Verify (state)**: `chat-folder-name-confirm-button` carries
     `data-disabled="true"` — the SAME inactive state as step 2, despite
     every character after the first being individually valid and the
     total length being well within 3-64.
   - **Verify (tooltip)**: hovering shows the identical exact tooltip text
     as step 2 / ELITEA-2458's Step 5 — confirmed live, byte-identical.
   - **Verify (no-op)**: click `chat-folder-name-confirm-button`; same
     no-effect checks as step 2 (editor stays open, input unchanged, no PUT
     fires).
4. Verify no unexpected console errors fired across steps 1-3 (side-channel
   discipline, same idiom as the covering spec's own final step).

## Expected Results
- A name containing unsupported special characters (outside
  `ConversationNameRegExp`'s allowed charset) is treated as INVALID by the
  exact same mechanism as an empty/2-char name: `data-disabled="true"`, the
  same validation tooltip, and a no-op checkmark click.
- A name whose first character is a space is likewise treated as INVALID by
  the identical mechanism — even when every subsequent character and the
  total length are otherwise conforming — because the regex's
  first-character class specifically excludes space.
- Both new invalid states show the SAME tooltip copy as the length/emptiness
  invalid states (the tooltip text is not scenario-specific — it is the one
  static `FolderNameWarningMessage` constant, shown whenever
  `isFolderNameValid` is `false`, regardless of WHICH regex clause failed).
- Neither invalid input ever fires a network request or otherwise mutates
  the folder.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| 1 Navigate to Chats, hover folder, click 3-dot icon, click Edit | Target page/section loads | AFS step 1 | step 1: editor opens, pre-filled | asserted |
| 2 Clear name, type unsupported special characters (e.g. "Folder$$%%") | Action completes, expected UI state | AFS step 2 | step 2: input shows the typed value | asserted |
| 3 Verify tooltip appears with the exact validation message | Condition holds | AFS step 2 | step 2: hover -> exact tooltip text | asserted |
| 4 Verify checkmark icon is disabled and clicking it has no effect | Condition holds | AFS step 2 | step 2: `data-disabled="true"` + click no-op (no PUT, editor stays open, value unchanged) | asserted *(decomposed: state + behavior)* |
| 5 Clear the name and press Space as the first character | Action completes, expected UI state | AFS step 3 | step 3: input shows `" ValidRest"` (space + valid remainder, so the SPECIFIC "space-led" claim is isolated from the already-covered "unsupported charset" claim) | asserted |
| 6 Verify space is not accepted as first character and checkmark remains inactive | Condition holds | AFS step 3 | step 3: `data-disabled="true"` + tooltip + click no-op | asserted *(decomposed: state + tooltip + behavior)* |
| Expected Final State (prose): "space is not accepted as first character, checkmark stays inactive" | — | step 3 | covered by the row above | asserted |
| Pass/Fail: "All steps complete without errors" | — | all steps | console-check after every interaction (Axis 2) | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked`
/ `out-of-scope`. All rows `asserted` — both case scenarios were executable
and confirmed live this session, no blockers, no reverse-masking (the case's
claims match `FolderItem.jsx`'s actual `ConversationNameRegExp` logic
exactly, confirmed both via source read — inherited unchanged from
ELITEA-2458's AFS — and via fresh live execution of THESE TWO specific
inputs, not just the ones ELITEA-2458 already tried).

### Axis 2 — Analyst additions

- Step 2 chose `"Folder$$%%"` — the case's own literal example — rather than
  inventing a new string, so the AFS traces 1:1 to the case text.
- Step 3 chose `" ValidRest"` (space + otherwise-fully-valid remainder)
  specifically to ISOLATE the first-character-space claim from the
  unsupported-charset claim already covered in step 2 — *added: a weaker
  test could type e.g. `" Bad$Name"` (space AND special chars together),
  which would pass for the wrong reason (ambiguous whether the space or the
  `$` caused the invalid state); using an otherwise-clean remainder proves
  the space alone is sufficient to invalidate.*
- Both steps assert the click-has-no-effect claim via the same
  THREE-independent-signal pattern the covering spec established (editor
  stays open, input value unchanged, no PUT fires) — *added, matching
  precedent: consistency with the covering spec's own Axis-2 reasoning
  (a single signal could pass even if some other unintended side effect
  fired).*
- Both steps assert the exact tooltip text (not a substring) — *added:
  confirms the SAME static warning constant renders regardless of which
  regex clause failed (charset vs. first-character vs, per the covering
  spec, length/emptiness) — a bug that showed a DIFFERENT message per
  failure reason would regress silently without this.*
- Console side-channel checked after the full flow — *added: standard
  discipline; confirmed clean this session (no errors beyond the
  pre-existing, unrelated Vite `stream` externalization warning already
  documented in the covering spec and the surface digest).*
- (nothing else added beyond the case — no defects found, no case-text
  drift.)

## Cleanup
1. Delete the seeded folder via the UI Delete flow (three-dot menu ->
   "Delete" menu item -> `delete-confirm-button`) — same pattern as the
   covering spec's own cleanup. **Same caution applies**:
   `ChatPage.delete_folder_via_menu()` / `FOLDER_MENU_DELETE_ITEM` currently
   target a DEAD testid (`chat-folder-menu-delete-menuitem`, regression
   tracked in EliteaAI/elitea-testing-public#1309 — **reconfirmed dead this
   session**, live `document.querySelector` returned null for that testid
   even though the visible "Delete" menuitem and its confirmation dialog
   both still work by text/role). Wrap in `try`/`except` per the covering
   spec's existing pattern so a cleanup failure never fails the test itself.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data
   Lifecycle.

## Concrete Handles (discovered during exploration)

**No new handles needed — every testid, page-object method, and constant
this case's two scenarios require already exists**, added by ELITEA-2458
and confirmed live again this session:

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Folder dot-menu button (3-dot) | `[data-testid="conversation-menu-menu-button"]`, scoped inside `chat-folder-item-{folder_id}` | on-`main` ✓ | Reused verbatim via `open_folder_rename_editor()`. |
| Folder dot-menu "Rename" item | `[data-testid="chat-folder-menu-rename-menuitem"]` | on-`automation/testids` ✓ (added ELITEA-2458) | Reused verbatim via `open_folder_rename_editor()`. |
| Folder-name inline input | `[data-testid="chat-folder-name-input"]` | on-`automation/testids` ✓ | `chat.folder_name_input` / `chat.set_folder_name()`. |
| Folder-name confirm (checkmark) button | `[data-testid="chat-folder-name-confirm-button"]` | on-`automation/testids` ✓ | `chat.folder_name_confirm_button`, `chat.is_folder_name_confirm_enabled()` (reads `data-disabled`, added ELITEA-2458). |
| Folder-name confirm tooltip content | `[data-testid="chat-folder-name-confirm-tooltip-content"]` | on-`automation/testids` ✓ (added ELITEA-2458) | `chat.get_folder_name_confirm_tooltip_text()` — live-reconfirmed this session returns the exact same string for both new invalid inputs. |
| Delete confirmation dialog / button (cleanup only) | `[data-testid="delete-confirm-dialog"]` / `[data-testid="delete-confirm-button"]` | on-`automation/testids` ✓ | Already-covered, not new. |

All handles verified live this session via direct DOM query
(`document.querySelector('[data-testid="..."]')`) against the actual
running app, not re-derived from the covering AFS's claims alone.

## Network Behavior
- No network call fires on a click while the checkmark is inactive for
  EITHER new scenario — confirmed live via `browser_network_requests`
  filtered to `folder/prompt_lib` immediately after each no-op click: zero
  new PUT/POST entries in both cases.
- `POST /api/v2/elitea_core/folder/prompt_lib/{project_id}` -> `201` fires
  only once, during the test's own seed step (same as the covering spec's
  Step 1) — confirmed live this session, folder id `146`.

## Known Defects Found During Exploration
None. Both new invalid-input scenarios matched `FolderItem.jsx`'s actual
`ConversationNameRegExp` logic exactly — no case-text drift, no
reverse-masking needed, no distinct behavior from the covering spec's
already-asserted invalid states beyond the different literal input strings.

## Blocked Steps
None. Both scenarios were executable and confirmed live.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`).
- Page object: `automation/pages/chat_page.py` — no changes needed, every
  method/constant this case's steps require already exists
  (`open_folder_rename_editor()`, `set_folder_name()`,
  `is_folder_name_confirm_enabled()`, `get_folder_name_confirm_tooltip_text()`,
  `get_folder_item()`, `delete_folder_via_menu()`).
- See § Gap assertions below for the exact additive test method to append to
  the covering spec.

## Gap assertions (implementer: append to the covering spec)

Add a **new, independent `test()` method** to
`automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py`'s
`TestChatFolderRenameCheckmarkValidation` class — purely additive, the
existing `test_folder_rename_checkmark_validation` body stays byte-identical.
Decorate the new method with its own `@pytest.mark.p1` (matching the
existing test's own per-function decorator — the module's `pytestmark` list
carries no `p*` marker, so there is no drift risk to guard against here,
unlike the ELITEA-2337/personal-tokens precedent).

```python
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2459_chat-folder-rename-validation-tooltip-for-invalid-input-and.md",
    "onetest-ai Test Case link",
)
@pytest.mark.p1
def test_folder_rename_checkmark_special_chars_and_leading_space_invalid(self, page):
    """ELITEA-2459 — two additional invalid-name scenarios beyond the ones
    test_folder_rename_checkmark_validation (ELITEA-2458) already covers:
    (a) a name containing unsupported special characters, and (b) a name
    whose FIRST character is a space (otherwise valid/long-enough). Both
    are asserted, via the SAME data-disabled/tooltip/no-op mechanism, to be
    just as inactive as the empty/2-char/unchanged states ELITEA-2458
    already exercises — proving ConversationNameRegExp's charset and
    first-character exclusions, not just its length/change gate.
    """
    chat = ChatPage(page)
    folder_id = None
    seed_name = "ELITEA2459RenameTest"

    console_messages = []

    def _on_console(msg):
        if msg.type == "error" and not _is_known_secrets_403(msg):
            console_messages.append(msg)

    page.on("console", _on_console)

    put_requests = []

    def _on_request(request):
        if request.method == "PUT" and "/folder/prompt_lib/" in request.url:
            put_requests.append(request.url)

    page.on("request", _on_request)

    try:
        with allure.step(
            "Step 1 — Seed a folder, open its rename editor via the dot-menu"
        ):
            chat.navigate_to_chat()
            chat.wait_for_page_load()

            chat.click_create_folder_button(timeout=UI_ELEMENT_TIMEOUT)
            with page.expect_response(
                lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "POST",
                timeout=NAVIGATION_TIMEOUT,
            ) as create_response_info:
                chat.set_folder_name(seed_name)
                chat.folder_name_confirm_button.click()
            create_response = create_response_info.value
            assert create_response.status == 201, (
                f"Seed folder POST should resolve 201, got {create_response.status}"
            )
            folder_id = create_response.json().get("id")
            assert folder_id is not None, "Seed folder response should include a real 'id'"
            chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
            chat.get_folder_item(folder_id).wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

            chat.open_folder_rename_editor(folder_id, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            'Step 2 — Type unsupported special characters ("Folder$$%%"); '
            "verify invalid state, exact tooltip, and no-op click"
        ):
            chat.set_folder_name("Folder$$%%")
            assert chat.folder_name_input.input_value() == "Folder$$%%", (
                "Input should show 'Folder$$%%' verbatim"
            )
            assert not chat.is_folder_name_confirm_enabled(), (
                'chat-folder-name-confirm-button should carry '
                'data-disabled="true" for a name with unsupported '
                "special characters"
            )
            tooltip_text = chat.get_folder_name_confirm_tooltip_text(timeout=UI_ELEMENT_TIMEOUT)
            assert tooltip_text == VALIDATION_TOOLTIP_TEXT, (
                f"Validation tooltip text mismatch — got: {tooltip_text!r}"
            )

            puts_before = len(put_requests)
            chat.folder_name_confirm_button.click()
            page.wait_for_timeout(300)
            assert chat.folder_name_input.is_visible(), (
                "Editor should stay open after clicking the inactive checkmark"
            )
            assert chat.folder_name_input.input_value() == "Folder$$%%", (
                "Input should remain unchanged by the no-op click"
            )
            assert len(put_requests) == puts_before, (
                "No PUT to the folder endpoint should fire on an "
                f"inactive-checkmark click, saw: {put_requests[puts_before:]}"
            )

        with allure.step(
            'Step 3 — Type a leading space (" ValidRest"); verify invalid '
            "state, exact tooltip, and no-op click, despite an otherwise "
            "fully valid remainder"
        ):
            chat.set_folder_name(" ValidRest")
            assert chat.folder_name_input.input_value() == " ValidRest", (
                "Input should show ' ValidRest' verbatim — the leading "
                "space is accepted by the field itself"
            )
            assert not chat.is_folder_name_confirm_enabled(), (
                'chat-folder-name-confirm-button should carry '
                'data-disabled="true" for a name starting with a space, '
                "even though every subsequent character is individually "
                "valid and the length is within range"
            )
            tooltip_text = chat.get_folder_name_confirm_tooltip_text(timeout=UI_ELEMENT_TIMEOUT)
            assert tooltip_text == VALIDATION_TOOLTIP_TEXT, (
                f"Validation tooltip text mismatch — got: {tooltip_text!r}"
            )

            puts_before = len(put_requests)
            chat.folder_name_confirm_button.click()
            page.wait_for_timeout(300)
            assert chat.folder_name_input.is_visible(), (
                "Editor should stay open after clicking the inactive checkmark"
            )
            assert chat.folder_name_input.input_value() == " ValidRest", (
                "Input should remain unchanged by the no-op click"
            )
            assert len(put_requests) == puts_before, (
                "No PUT to the folder endpoint should fire on an "
                f"inactive-checkmark click, saw: {put_requests[puts_before:]}"
            )

        with allure.step(
            "Side-channel check — no unexpected console errors across the "
            "full flow"
        ):
            assert not console_messages, (
                "Unexpected console errors during folder rename validation: "
                f"{[m.text for m in console_messages]!r}"
            )

    finally:
        # Same caution as test_folder_rename_checkmark_validation's own
        # cleanup: delete_folder_via_menu() targets a DEAD testid
        # (regression #1309, NOT this case's scope) — wrapped so a cleanup
        # failure never fails the test itself.
        if folder_id:
            try:
                chat.delete_folder_via_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                logger.info("Cleaned up folder %s", folder_id)
            except Exception as exc:
                logger.warning("Failed to delete folder %s: %s", folder_id, exc)
```

No new page-object methods, no new `LocatorDescriptor` fields, no new
module-level constants beyond what the covering spec already defines
(`UI_ELEMENT_TIMEOUT`, `NAVIGATION_TIMEOUT`, `VALIDATION_TOOLTIP_TEXT`,
`_is_known_secrets_403`, `ChatPage`, `allure`, `pytest`, `logger` are all
already imported/defined in the covering spec file — no new imports needed).
