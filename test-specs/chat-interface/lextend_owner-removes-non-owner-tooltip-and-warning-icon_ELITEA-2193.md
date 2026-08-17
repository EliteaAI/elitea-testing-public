# Test Case: Chat – Team Project – Owner Can Remove Non-Owner Participant via Confirm Dialog

## Metadata
- **TMS ID**: ELITEA-2193
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (per source case's `priority: high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend;
  Team project "Elitea Testing Team", `projectId=471`)
- **User set**: `${TEST_USER}` — localhost: no login needed, `VITE_DEV_TOKEN` auto-auths (dev-token user
  renders as "Test Bot"/"TB", always the owner of every conversation it opens)
- **Analyst**: qa-engineer (agent), batch `chat-remaining-w11`, cluster dispatch with ELITEA-2192/2194, 2026-08-15
- **Status**: **extend-existing**
- **surface_key**: `chat-users-participant-dropdown` (shared with ELITEA-2171/2172/2192/2194 — same
  "Users" dropdown remove-control surface)

## Preconditions
- User is logged in to the Elitea platform.
- Logged in as conversation owner in a Team project with multiple participants.

## Extension target — Rule-6 partial overlap

**Covering spec:** `automation/tests/ui/chat/test_team_users_mention_and_remove_participants.py`, class
`TestTeamUsersMentionAndRemoveParticipants`, method
`test_team_users_mention_and_remove_participants` (TMS ELITEA-2168, AFS
`test-specs/chat-interface/l2_team-users-mention-and-remove-participants_ELITEA-2168.md`), **Steps 8-9**
(source lines 530-559). Merged to `origin/automation/base` (confirmed present this session via a fresh
`git fetch origin`; `git log` shows commits `6ef5ef7b`/`fda5de19`/`37dbd948` touching this file, all
already on `origin/automation/base`).

**Behavioural-overlap argument.** Most of ELITEA-2193's own steps already have a direct assertion in
the covering test's Step 8/9:

| ELITEA-2193 step | Covering test, Step 8/9 |
|---|---|
| 1. Open a conversation where current user is owner | Setup — the dev-token user is always the owner of every conversation it creates |
| 2. Click avatar group → USERS dropdown shows all participants | Step 8 opens the dropdown via `open_remove_user_dialog()` (internally calls `open_participants_popover`) |
| 4. Click trash bin → 'Remove user?' modal with orange warning icon appears | Step 8 clicks the delete icon and gets the dialog back — modal APPEARS, but the covering test never asserts the ICON |
| 5. Verify modal body: 'Are you sure to remove the user from chat?' | Step 8 — `assert dialog_text == f"Remove user?Are you sure to remove the {USER_2_NAME} user from chat?CancelRemove"` — the exact body text ELITEA-2193's own step 5 asks for |
| 6. Click Remove → Modal closes; user removed from dropdown and PARTICIPANTS | Step 9 — `Dialog.click_button(dialog, "Remove")`, `wait_for_hidden`, badge count "6"→"5", popper text no longer contains the removed name |

**Gap: two assertions ELITEA-2193's own steps ask for that the covering test does not make**, both
live-confirmed this session (Playwright MCP, `/chat/566` "HI Chat", owner "Test Bot" + non-owner
"Hrach Sargsyan"):

1. **Step 3's tooltip** — "Hover over a non-owner; verify trash bin with 'Remove user' tooltip". The
   covering test's `open_remove_user_dialog()` hovers and clicks in one motion; it never separately
   asserts the tooltip/accessible-name text on the delete icon before clicking. Live-confirmed this
   session: hovering the non-owner row (Hrach Sargsyan) produces an accessible
   `button "Remove user"` — the `DeleteParticipantButton.jsx` MUI `Tooltip`'s `title` prop is literally
   `` `Remove ${entityType}` ``, and `entityType` resolves to `'user'` for a Users-section participant,
   so the tooltip text is exactly "Remove user" as the case expects.
2. **Step 4's "orange warning icon"** — the covering test's dialog-text assertion (`dialog.text_content()`)
   checks the TEXT ONLY; it never inspects the modal's icon. Live-confirmed this session via
   `browser_evaluate`: the dialog's `delete-confirm-title` node (existing testid,
   `ChatPage.delete_confirm_title`) contains an `<svg>` whose computed `fill` is `rgb(233, 121, 18)` —
   a genuine orange — matching `Modal.DeleteEntityModal`'s `titleIcon={ModalConstants.MODAL_ICON_TYPE.warning}`
   prop (`DeleteParticipantButton.jsx`).

Both gaps are additive assertions on the SAME dialog-open flow the covering test already drives —
not a new interaction, not a near-rewrite. Classified `extend-existing`, not `ready-for-automation`.

## Test Steps (source case, reproduced for traceability; only the gap steps need new code)
1. Open a conversation where current user is owner — Conversation open. **already-covered** (Setup).
2. Click avatar group to open USERS dropdown — Dropdown shows all participants. **already-covered**
   (covering test Step 8).
3. Hover over a non-owner; verify trash bin with 'Remove user' tooltip — Trash bin visible. **GAP** —
   add an accessible-name/tooltip-text assertion on the delete button after hover, before clicking.
4. Click trash bin — 'Remove user?' modal with orange warning icon appears. **GAP (icon half only)** —
   add an icon-presence + orange-fill assertion on `delete_confirm_title`'s `<svg>`; the modal-appears
   half is already covered.
5. Verify modal body: 'Are you sure to remove the user from chat?' — Modal text correct.
   **already-covered** (covering test Step 8's `dialog_text` assertion).
6. Click Remove — Modal closes; user removed from dropdown and PARTICIPANTS. **already-covered**
   (covering test Step 9).

## Expected Results
- Steps 1, 2, 5, 6 already proven by the covering test's Steps 8-9, re-confirmed live this session
  (badge count transition, exact dialog body text, popper listing update).
- Step 3's tooltip text and step 4's warning-icon color are genuinely NEW assertions, both live-confirmed
  this session and both additive on the covering test's existing dialog-open call site — no defect found,
  the live product matches the case's own expectation on both counts.

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: owner logged in, Team project, multiple participants | — | covering test's Setup | badge count "6" (owner + 5 seeded) | already-covered |
| 1. Open conversation as owner | conversation open | Setup | dev-token user is always the owner | already-covered |
| 2. Click avatar group → USERS dropdown shows all | shows all | covering test Step 8 | `open_remove_user_dialog()` → popover opens | already-covered |
| 3. Hover non-owner; trash bin with 'Remove user' tooltip | tooltip visible | **GAP** — new assertion needed | accessible-name/tooltip-text check on `chat-participant-remove-button` after `hover_participant_user_row()` | **extend — gap assertion** |
| 4. Click trash bin → 'Remove user?' modal with orange warning icon | modal + icon | modal: covering test Step 8; icon: **GAP** | modal: `dialog_text` assertion; icon: new `<svg fill>` check on `delete_confirm_title` | **partially already-covered / extend — icon gap** |
| 5. Verify modal body text | text correct | covering test Step 8 | `assert dialog_text == "Remove user?Are you sure to remove the {name} user from chat?CancelRemove"` | already-covered |
| 6. Click Remove → modal closes, user removed | removed | covering test Step 9 | badge "6"→"5"; popper text no longer contains name | already-covered |
| Expected Final State / Pass-Fail: "Owner can remove non-owner via confirm dialog" | — | Steps 8-9 + 2 new gap assertions | as above | already-covered + extend |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- Tooltip-text mechanism (`DeleteParticipantButton.jsx`'s `removeLabel = 'Remove ' + (entityType ||
  'participant')`, `entityType` resolved to `'user'`) — *added: source-confirmed after the live hover
  produced the accessible name, to root-cause WHY the text is exactly "Remove user" for this entity
  type (not assumed from the case's own wording alone).*
- Warning-icon color mechanism (`Modal.DeleteEntityModal`'s `titleIcon={ModalConstants.MODAL_ICON_TYPE
  .warning}`, rendered fill `rgb(233, 121, 18)`) — *added: same treatment, confirmed via
  `browser_evaluate` computed-style read on the live dialog rather than assumed from the "orange"
  case-text wording.*
- Console/network side-channel checked throughout this session's live exploration — no new errors.

## Cleanup
Cancelled the one confirm dialog opened during this session's live investigation (Cancel, not Remove —
Hrach Sargsyan was NOT actually removed by this AFS's own exploration; see ELITEA-2194's AFS, which
reused this exact same dialog-open+Cancel action as its own live re-confirmation). Conversation
`/chat/566` left in its pre-existing state (badge "2", both participants present) — no new
conversation created, no participant actually removed by this session's exploration.

## Concrete Handles (discovered during exploration)
Locator policy on this project is **testid-only** — no role/label/text fallback ladder
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `git grep`
on both `origin/main` and `origin/automation/testids` in the sibling `EliteaUI` clone (fetched fresh
this session) — **every handle this case needs already exists on `main`**, no new testid work required.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Users participants badge (opens dropdown) | `chat-participants-badge-button` | on-`main` ✓ / on-`automation/testids` ✓ | Reused as-is from ELITEA-2168/2172. |
| "Users" participants dropdown — per-user row | `chat-participant-row-user_{userId}_` (dynamic) | on-`main` ✓ / on-`automation/testids` ✓ | `ChatPage.PARTICIPANT_ROW.format(f"user_{user_id}_")`. |
| Row's delete/"Remove user" icon button | `chat-participant-remove-button` | on-`main` ✓ / on-`automation/testids` ✓ | Scoped inside the row; `ChatPage.hover_participant_user_row(user_id)` returns this Locator post-hover, ready for an accessible-name assertion — reuse directly, do not click through it for the tooltip check (only for the confirm-and-continue flow, i.e. `open_remove_user_dialog()`). |
| "Remove user?" confirmation dialog | `delete-confirm-dialog` | on-`main` ✓ | `ChatPage.delete_confirm_dialog` — existing field. |
| Dialog title (contains the warning icon) | `delete-confirm-title` | on-`main` ✓ | `ChatPage.delete_confirm_title` — existing field, currently unused for icon inspection anywhere in the suite; this case is its first icon-check caller. Confirmed live this session: `dialog.locator('[data-testid="delete-confirm-title"] svg')` resolves to exactly one `<svg>`, computed `fill: rgb(233, 121, 18)`. |
| Warning icon itself (inside the title) | `delete-confirm-title-icon` | on-`automation/testids` ✓ (not yet on `main` — human cherry-pick pending) | **Implementer amendment (fix round 1):** the round-0 build used a #579-shape-1 raw `svg` tag selector scoped off `delete_confirm_title`, reasoning the icon was MUI-internal chrome. Reviewer-caught misclassification: the icon (`ModalConstants.MODAL_ICONS[typeIcon]`, e.g. `WarningIcon`) is first-party app JSX (`@/assets/attention-icon.svg?react`) rendered by `BaseModal.jsx`'s `renderIconType()` — the SAME title `Box` that already threads `titleTestId`/`closeButtonTestId`/`confirmButtonTestId`/`cancelButtonTestId`. A real testid was genuinely placeable and has been added: `BaseModal` gained a `titleIconTestId` prop (same channel as the sibling four), wired `data-testid="delete-confirm-title-icon"` from `DeleteEntityModal` (EliteaAI/EliteaUI@7b359d32 on `automation/testids`). `ChatPage.delete_confirm_title_icon` is now a real `LocatorDescriptor(testid="delete-confirm-title-icon")`; `get_delete_confirm_title_icon()` resolves it directly — no raw handle. Same observable (`fill: rgb(233, 121, 18)`), different (correct) handle. |

**Provenance grep (this session, fresh `git fetch origin` first):**
```
chat-participants-badge-button          main:YES  testids:YES
chat-participant-row-{unique_id}         main:YES  testids:YES
chat-participant-remove-button           main:YES  testids:YES
delete-confirm-dialog                    main:YES
delete-confirm-title                     main:YES
```

## Network Behavior
- Steps 2-5 (open dropdown, hover, click, modal): no network call — pure client-side rendering, same as
  ELITEA-2168's dropdown-open/hover mechanism.
- Step 6 (Remove confirm): the participant-deletion `DELETE`/mutation request the covering test's Step
  9 already waits on via `wait_for_network()` — no new network behavior needed for the two gap
  assertions (both are pre-Remove, purely visual/DOM checks).

## Known Defects Found During Exploration
None. Live product behavior matches the case's expected result on both new gap assertions (tooltip
text "Remove user", orange warning icon in the confirm dialog).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Implement as a NEW test method or an addition to `test_team_users_mention_and_remove_participants.py`
  (implementer's call, per the covering test's own extend-existing precedent set by ELITEA-2136/2138's
  section of this feature's digest) — either way, do not modify the covering test's existing Step 8/9
  assertions, only ADD the two gap checks around the existing `open_remove_user_dialog()` call:
  1. **Before** calling `open_remove_user_dialog()` (which hovers AND clicks in one motion), call the
     read-only `hover_participant_user_row(user_id)` (ELITEA-2172's own new method) first and assert
     `expect(button).to_have_accessible_name("Remove user")` (or equivalent tooltip-text check) — then
     proceed to `open_remove_user_dialog()` for the click+modal step (this re-opens the popover fresh
     internally, so no state is shared/reused unsafely between the two calls).
  2. **After** the dialog is returned by `open_remove_user_dialog()`, before clicking Remove, assert an
     `<svg>` exists inside `chat.delete_confirm_title` and its computed `fill` equals the orange
     `rgb(233, 121, 18)` (or use a `to_have_css("fill", ...)` style Playwright assertion if the project
     has a helper for this pattern — check `components/mui/` first, this may be a novel assertion shape
     for this suite).
- Reuse the covering test's own Setup (Team project 471, seeded owner + non-owner conversation) and its
  `USER_2_NAME`/`participant_id_by_name` resolution — do not re-derive.
- Wait strategy elsewhere: reuse `wait_for_participants_badge_count()`/`Dialog.wait_for_hidden()`
  (condition-based) — never a fixed sleep, per `.agents/testing.md`.
