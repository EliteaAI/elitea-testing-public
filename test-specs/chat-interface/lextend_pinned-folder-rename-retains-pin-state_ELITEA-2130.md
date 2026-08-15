# Test Case: Chat – Pinned Folder Can Be Renamed

## Metadata
- **TMS ID**: ELITEA-2130
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", observed live as `projectId=399`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer)
- **Status**: extend-existing
- **Extension target**: `automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py` (its own AFS: `test-specs/chat-interface/l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md`); analysed in the SAME session as `test-specs/chat-interface/lextend_folder-rename-via-context-menu-edit-option_ELITEA-2121.md`, which shares this file's regression-fix dependency.

**Depends on the SAME `#1533` regression fix as ELITEA-2121** (see that AFS's intro for
the full history) — the folder dot-menu's Rename item had lost its testid `key`,
blocking every folder-rename-via-context-menu flow, this one included. Fixed this
session (`EliteaAI/EliteaUI@be489cee`, `automation/testids`) before this case was
attempted.

**This case has a genuine NEW gap ELITEA-2121/ELITEA-2458 don't cover: pin-state
persistence across a rename.** Neither existing folder-rename test ever pins a folder.
Two NEW pieces of product surface needed adding this session, both source-confirmed
absent before this pass:
1. The folder dot-menu's "Pin on top"/"Unpin" item had **never** carried a testid
   (unlike Rename, this isn't a regression — first testid ever, mirroring the same
   `DotMenu`/`BasicMenuItem` `key` → `{key}-menuitem` mechanism). Added
   `key: 'chat-folder-menu-pin'` this session.
2. The folder row (`chat-folder-item-{id}`) had a `data-expanded` state attribute but
   **no `data-pinned` one** — the ONLY signal of pin state in the DOM was a raw,
   testid-less `<PinIcon>` conditionally rendered in the collapsed header
   (`FolderAccordion.jsx`), which the project's own policy (state via `data-*`
   attribute, never a bare conditional-render icon with no stable handle) doesn't
   sanction as a locator target. Added `data-pinned={isPinned}` alongside the existing
   `data-expanded={expanded}` on the SAME already-testid'd `StyledAccordion` element —
   zero new DOM node, mirrors `ConversationItem.jsx`'s existing `data-pinned` sibling
   convention (`is_conversation_pinned()` already reads the analogous attribute on
   conversations).

Both landed in the SAME commit as the Rename-regression fix,
`EliteaAI/EliteaUI@be489cee` (`automation/testids` only, human-cherry-pick promotion to
`main` pending, standard project policy). Live-reverified end-to-end this session (see
§ Blocked Steps) — no defects.

**Live gotcha, confirmed and already handled by the existing page-object
methods without any change needed:** a PINNED folder's outer draggable wrapper
(`DraggableFolderItem`, `isDragDisabled={isPinned}` per `Folders.jsx`) renders as a
genuinely HTML-`disabled` ancestor around the folder's own title button — a bare
`Locator.click()` on the scoped dot-menu button times out with "element is not
enabled" for a pinned folder specifically (confirmed live via Playwright MCP: the
element's own `.disabled` DOM property is `false`, `pointer-events: auto`, but
Playwright's actionability check still refuses a plain click, walking up to the
disabled ancestor). **`open_folder_rename_editor()`'s and `delete_folder_via_menu()`'s
EXISTING `menu_button.click(force=True)`** (already in `chat_page.py`, not added this
session) already bypasses this — confirmed live this session with a real pytest-style
force-click succeeding where a plain click via MCP tooling (which has no `force` option)
did not. No page-object change needed for this; documented here so nobody "fixes" it a
second time.

**Case-text drift, filed together with ELITEA-2121's clarification (`#1534`)**: case
step 2 says "verify context menu: Delete, Edit, Export, Unpin" for a pinned folder. Live
item set (matching ELITEA-2121's finding, with "Unpin" instead of "Pin on top" since
this folder IS pinned): **New chat, Rename, Unpin, Delete**. Same "Edit"→"Rename" /
no-"Export" / unlisted-"New chat" drift as ELITEA-2121 — not re-filed separately, `#1534`
covers both cases (title names both TMS IDs).

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- User is on the Chats section (`${BASE_URL}/chat`).
- At least one PINNED folder exists — this case seeds its own folder AND pins it via
  the UI dot-menu (§ Test Data), rather than assuming a pre-existing pinned folder in
  the shared, already-polluted DEV project (see ELITEA-2121 AFS's precedent note on
  pollution) — this also makes the "pin" step of the flow itself part of what's proven
  live, not an assumed precondition.

## Test Data

### generate-per-test (created by the test's own setup, cleaned up in its own teardown)
- One folder, created via the existing create-folder flow, seed name
  `"ELITEA2130PinnedSource"` (live-verified value used this session, folder id `213` at
  exploration time — ephemeral).
- Pinned via the dot-menu's "Pin on top" item (NEW testid, see intro) — live-confirmed:
  `PATCH /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_id}` → `200 OK`
  (note: **`PATCH`, not `PUT`** — a different HTTP method than the rename endpoint,
  confirmed this session, worth recording since every other folder-mutation endpoint
  documented so far in this suite is `PUT`/`POST`/`DELETE`).
- New name from the case's own § Test Data table: `"Pinned Renamed Folder"`.

## Test Steps

1. Seed a folder (§ Test Data), pin it via the dot-menu "Pin on top" item, then identify
   it as pinned.
   - **Verify**: `chat-folder-item-{folder_id}` carries `data-pinned="true"` (NEW
     attribute, see intro) after the pin action's `PATCH → 200` resolves.
2. Hover the pinned folder, click its 3-dot icon, verify the context menu (real item
   set — see intro + `#1534`, NOT the case's literal "Delete, Edit, Export, Unpin"
   list).
   - **Verify**: the popover is visible; the "Rename" item
     (`chat-folder-menu-rename-menuitem`) is present; the Pin/Unpin item
     (`chat-folder-menu-pin-menuitem`) is present AND its text reads `"Unpin"` (proving
     the menu's own label correctly reflects the already-pinned state, not just that
     the item exists).
3. Click "Rename"; clear the name and type `"Pinned Renamed Folder"`.
   - **Verify**: the inline editor opens pre-filled with `"ELITEA2130PinnedSource"`,
     then shows `"Pinned Renamed Folder"` after typing.
4. Click the checkmark icon.
   - **Verify**: `PUT /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_id}`
     resolves `200 OK`; the editor closes; the folder's displayed name now reads
     `"Pinned Renamed Folder"`.
5. Verify the folder retains its pinned state (pin icon still visible) after the
   rename.
   - **Verify**: `chat-folder-item-{folder_id}` STILL carries `data-pinned="true"`
     immediately after step 4's rename resolves — proving the rename mutation didn't
     reset or drop the folder's `meta.is_pinned` server-side state. (State via
     `data-*` attribute, not a bare icon-presence check — `.agents/testing.md` §
     Locator policy; the icon's own conditional render is driven by the exact same
     `isPinned` value this attribute exposes, so the attribute is strictly stronger
     evidence, not a substitute observable.)
6. Verify no error message is shown.
   - **Verify**: no unexpected console errors fired across the whole flow (0 observed
     this session — same `secrets` 403 filter as every sibling folder test).

## Expected Results
- Pinning a folder via the dot-menu persists server-side (`PATCH … → 200`) and is
  reflected in the DOM (`data-pinned="true"`); the dot-menu's Pin item correctly
  relabels to "Unpin" once pinned.
- The pinned folder can be renamed through the identical Rename flow ELITEA-2121/
  ELITEA-2458 already prove — same editor, same checkmark mechanism, same `PUT … →
  200`.
- The rename does NOT unpin the folder — `data-pinned="true"` (and, transitively, the
  pin icon it drives) survives the rename unchanged.
- No new console errors beyond the pre-existing, environment-wide `secrets` 403 noise.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: pinned folder exists | Pinned folder found | AFS step 1 | step 1: seed + pin, `data-pinned="true"` | asserted |
| 1 Identify pinned folder (pin icon visible) | Pinned folder found | AFS step 1 | step 1: `data-pinned="true"` | asserted |
| 2 Hover, click 3-dot, verify menu: Delete/Edit/Export/Unpin | Context menu visible | AFS step 2 | step 2: popover visible + real item set + "Unpin" label text — case's literal list is drifted, `#1534` | asserted *(case-text drift, clarification filed, real behavior asserted)* |
| 3 Click Edit, clear, type 'Pinned Renamed Folder' | New name in input | AFS step 3 (as "Rename" — drift) | step 3: editor pre-filled, then shows new name | asserted |
| 4 Click checkmark | Pinned folder renamed; new name displayed | AFS step 4 | step 4: `PUT → 200`, displayed name | asserted |
| 5 Verify folder retains pinned state (pin icon still visible) | Pin icon still visible | AFS step 5 | step 5: `data-pinned="true"` post-rename | asserted |
| 6 Verify no error message | Rename successful | AFS step 6 | step 6: console-error check | asserted |
| Expected Final State: "Pinned folder renamed and retains its pinned state" | — | steps 4+5 | covered by the rows above | asserted |
| Pass/Fail: "Folder loses pinned state or rename fails" (fail condition) | — | step 5 | `data-pinned` check is exactly the inverse of this fail condition | asserted |

Disposition key as ELITEA-2121's AFS. All rows `asserted`. No reverse-masking: the
case-text/product menu-label mismatch is handled identically to ELITEA-2121 (assert the
live-confirmed reality, file the drift separately).

### Axis 2 — Analyst additions

- Step 1 asserts the PIN action's own network result (`PATCH → 200`) and DOM reflection
  (`data-pinned="true"`) BEFORE proceeding to rename — *added: the case's precondition
  ("at least one pinned folder exists") is silently assumed reachable; proving how it
  got pinned, live, through the real UI mechanism, is stronger than asserting only the
  END state, and catches a pin-specific regression independently of the rename this
  case is really about.*
- Step 2's Pin/Unpin item TEXT assertion (`"Unpin"`, not just presence) — *added: a
  presence-only check could pass even if the label failed to update after pinning
  (a plausible regression class distinct from the item losing its testid entirely);
  reading the label proves the menu's OWN state-derivation, not just DOM existence.*
- Step 5 uses the `data-pinned` attribute rather than the bare `<PinIcon>`'s DOM
  presence — *added: per `.agents/testing.md` § Locator policy, state belongs on a
  `data-*` attribute of an already-testid'd element, not a testid-less conditional icon;
  the attribute is driven by the exact same `isPinned` boolean the icon's conditional
  render uses, so it's not a weaker proxy, just a stable handle for the same fact.*
- Console-error check after the full flow — *added: standard side-channel discipline.*

## Cleanup
1. Delete the seeded folder via `ChatPage.delete_folder_via_api()` directly (same
   reasoning as ELITEA-2121's AFS — the UI Delete path's testid remains dead, `#1309`,
   out of this case's own scope).
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

| Element | Testid / attribute | Provenance | Notes |
|---|---|---|---|
| Folder dot-menu "Pin on top"/"Unpin" item | `[data-testid="chat-folder-menu-pin-menuitem"]` | **NEW this session**, `EliteaAI/EliteaUI@be489cee` (`automation/testids` only). | Label toggles "Pin on top" ↔ "Unpin" per `folder.meta?.is_pinned` — read via `.text_content()` on this testid's locator. |
| Folder pinned state | `data-pinned="true"/"false"` on `chat-folder-item-{folder_id}` (SAME element as `data-expanded`) | **NEW this session**, `EliteaAI/EliteaUI@be489cee` (`automation/testids` only). | Mirrors `ConversationItem.jsx`'s existing `data-pinned` convention (already consumed by `is_conversation_pinned()`); testid identity unchanged, purely a new sibling attribute. |
| Folder dot-menu "Rename" item | `[data-testid="chat-folder-menu-rename-menuitem"]` | **RESTORED this session** (regression, `#1533`) | Same handle as ELITEA-2121's AFS. |
| Folder-name inline input / confirm button | `chat-folder-name-input` / `chat-folder-name-confirm-button` | on-`automation/testids` ✓, on-`main` ✗ | Pre-existing, reused verbatim. |

## Network Behavior
- `PATCH /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_id}` → `200 OK` on
  the Pin-menu-item click (step 1). Live-observed: folder id `213`,
  `PATCH .../folder/prompt_lib/399/213 => [200] OK`. **Different HTTP method than
  rename** (`PUT`) — see intro.
- `PUT /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_id}` → `200 OK` on the
  rename confirm (step 4). Live-observed: `PUT .../folder/prompt_lib/399/213 => [200] OK`,
  and the folder's `data-pinned` attribute read `"true"` both immediately before AND
  immediately after this request resolved — the rename's own payload/response never
  touches `meta.is_pinned`.

## Known Defects Found During Exploration
Same `#1533` regression as ELITEA-2121 (shared dependency, fixed before either case was
attempted) and the same `#1534` case-text clarification (menu item labels). No NEW
defects specific to this case — pin-then-rename behaves exactly as expected, live,
end-to-end.

## Blocked Steps
None, after the `#1533` fix. All 6 case steps executed live end-to-end this session
(folder id `213`: created → pinned, `PATCH → 200`, `data-pinned="true"` → renamed via
dot-menu Rename, `PUT → 200`, displayed name `"Pinned Renamed Folder"` →
`data-pinned="true"` reconfirmed post-rename). 0 console errors across the whole
exploration session (both this case and ELITEA-2121's, same browser session).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: extend `automation/pages/chat_page.py`. Reuse everything ELITEA-2121's
  AFS lists, plus:
  - `FOLDER_MENU_PIN_ITEM` constant (added for/shared with ELITEA-2121's AFS — define
    once).
  - `is_folder_pinned(folder_id, timeout) -> bool` — reads `data-pinned` off
    `get_folder_item(folder_id)`, mirrors the existing `is_conversation_pinned()`
    exactly (same attribute-read idiom, different scoping locator).
  - `pin_folder_via_menu(folder_id, timeout)` — `open_folder_context_menu(folder_id)`
    (shared helper, see ELITEA-2121's AFS) + click `FOLDER_MENU_PIN_ITEM`. The menu
    auto-closes on any item click (`DotMenu.jsx`'s `withClose` wrapper) — no explicit
    close needed.
- **Force-click discipline**: any dot-menu-button click on a PINNED folder must go
  through a method using `.click(force=True)` (already true of `open_folder_rename_editor()`
  — no change needed there) — a plain click times out on the disabled draggable-wrapper
  ancestor. If a NEW method opens the menu for a pinned folder (e.g. to Unpin again),
  it must use the SAME force-click pattern.
- Wait strategy: `page.expect_response()` for the seed-folder `POST`, the pin `PATCH`,
  and the rename `PUT` — three separate awaited responses across the flow, same idiom
  as the sibling rename tests.
