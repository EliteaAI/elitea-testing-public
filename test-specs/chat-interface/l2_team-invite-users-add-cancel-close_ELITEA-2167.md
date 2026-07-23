# Test Case: Chat – Team Project – Create New Conversation and Add Users via Invite Users with Add Confirmation

## Metadata
- **TMS ID**: ELITEA-2167
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; Team project "Elitea Testing Team" — observed live as `projectId=471`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login (dev-token user renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live (both preconditions + all 10 steps observed against the real app). One CONFIRMED, novel product defect found and filed (issue #719, MINOR — see § Known Defects). One additional CONFIRMED occurrence of an already-open shared-component defect (issue #694, commented rather than re-filed — same root cause, `strict-per-bug` policy). One CLARIFICATION (case-text drift on step 1's "PARTICIPANTS panel visible with empty USERS section" — reverse-masking guard, not filed as a new ticket since it's the same already-documented ELITEA-2095/ELITEA-2166 pattern). New page-object surface is required for the "Add users" modal itself (search/select/chips/Add/Cancel/Close) — the existing `open_add_teammate_dialog()` only detects that the dialog opened, it does not drive the picker; everything else this case touches (project switch, `+` menu, participants badge/popper, message send, conversation delete) already has testid-compliant page-object methods.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User is in a **Team project**. This is NOT ambient at test start — the account's default/last-active project can be Private, so automation must explicitly switch via `ChatPage.switch_project("471")` (existing method, ELITEA-2095/ELITEA-2166 precedent) to the Team project **"Elitea Testing Team"** (`471`) before proceeding. At least two other org users must exist to search for — confirmed live: this environment has real named users including the case's own literal example "Hrach Sargsyan"; the case's other example, "Admin Bot", does **not** exist in this environment (see § Test Data substitution note).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Team project "Elitea Testing Team", id `471` — `ChatPage.switch_project("471")`.
- Existing org users, searched via the "Add users" modal's search field:
  - **"Hrach Sargsyan"** — case's literal example, confirmed to exist live (search `"sa"` returns it). Used verbatim for user #1.
  - **"Levon Dadayan"** — **substituted** for the case's literal example "Admin Bot", which does **not** exist in this environment (search `"ad"` returned "Aliaksandr Valadzko", "Levon Dadayan", "Vladyslav Variushkin" — all substring matches on "ad", no "Admin Bot" among them). Used for user #2 (the case's `sa`/`ad` partial-search pattern is preserved; only the resulting name differs from the case's literal text).
  - **"Mariam Hakobyan"** — third user (step 7, dismissed via Cancel — never persisted).
  - **"Tatiana Bontsevich"** — fourth user (step 8, dismissed via X close — never persisted).
- Test message: `"hi all"` (case's literal Test Data value).

### generate-per-test (created in test setup/steps, cleaned up in its own teardown)
- **New conversation** — created via the UI's own `+ Chat` flow (`ChatPage.click_create_conversation()`/the `sidebar-create-button` testid), matching the case's own step 1 action (not API-created). The conversation only gets a real id once step 9's send actually creates it server-side (observed live: id `259`). The LLM auto-titles it from the first message — observed live as **"All"** (from `"hi all"`), not asserted by this case's Pass/Fail criteria and not itself a defect (LLM-generated short-title behavior, same non-deterministic-naming pattern already precedented for `"hi"` → "HI Chat" elsewhere in this environment) — do not assert an exact title string in automation, only that the row exists under "Today" with the correct participant count/icon (case step 10).

## Test Steps

1. Switch to the Team project (`ChatPage.switch_project("471")`), then click **+ Chat** (`sidebar-create-button` testid).
   - **Verify**: a new, blank conversation opens (greeting text visible, e.g. "Hello, Test! What can I do for you today?"; no message history; message input focused). **Reverse-masking guard (case-text drift, not a defect):** the case's literal step-1 wording says "PARTICIPANTS panel visible with empty USERS section" — live, for a brand-new, zero-participant, unsaved conversation, **no participants element renders at all** (no badge, no panel) — matching the already-documented ELITEA-2095/ELITEA-2166 pattern that participant widgets only appear once the conversation has real content/participants. Assert "no participants badge/panel present" as the passing observation for this step, not "empty USERS section visible".
2. Click the composer's `+` menu (`plus-menu-button` testid) and verify **Invite Users** is present in the dropdown.
   - **Verify**: the menu shows exactly 6 items (Attach Files, Modules, Agents, Pipelines, Toolkits, MCPs, Invite Users — Invite Users present because this IS a Team project, the inverse of ELITEA-2166's Private-project absence case). `invite-users-menuitem` testid resolves and is visible/enabled.
3. Click **Invite Users** (`invite-users-menuitem` testid).
   - **Verify**: the "Add users" modal opens (heading "Add users"), containing a "Search users..." combobox, a **Cancel** button, an **Add** button (disabled — no users selected yet), and an X **Close** button in the header. `role="dialog"` visible.
4. Search `"sa"` in the search field and select the first matching result, **"Hrach Sargsyan"**.
   - **Verify**: a chip labeled "Hrach Sargsyan" appears inside the search field; the modal stays open; the **Add** button becomes enabled; the matching option in the still-open dropdown shows a checkmark (`state.selected`).
5. Search `"ad"` and select the second user, **"Levon Dadayan"** (case's "Admin Bot" example does not exist in this environment — see § Test Data).
   - **Verify**: two chips ("Hrach Sargsyan", "Levon Dadayan") shown in the search field; modal stays open; **Add** remains enabled.
6. Close the still-open results dropdown (native `Escape` — required, see § Automation Hints MUI-overlay note), then click **Add**.
   - **Verify**: the modal closes. `ChatPage`'s "Users in this conversation" participants badge (`chat-participants-badge-users` testid) now reads **"2"**. Opening the popover (`open_participants_popover(section="users")`) shows a "USERS" heading listing exactly "Hrach Sargsyan" and "Levon Dadayan" (plus an "All users" menuitem). No participants network call fires yet at this point — the invited users are queued in client-side state (`AddNewUserModal.jsx`'s `localUsers`) pending the conversation's actual creation; see § Network Behavior.
7. Click `+` → Invite Users again, search and select a **third** user ("Mariam Hakobyan"), then click **Cancel**.
   - **Verify**: modal closes; the badge still reads "2"; the popover still lists only "Hrach Sargsyan" and "Levon Dadayan" — "Mariam Hakobyan" was **not** added. Reopening the "Add users" modal at this point also confirms `excludedUserIds` correctly excludes the two already-added participants from future searches (positive confirming behavior, observed live: a `"sa"` search after step 6 no longer returns "Hrach Sargsyan").
8. Click `+` → Invite Users again, search and select a **fourth** user ("Tatiana Bontsevich"), then click the **X** (Close) button in the dialog header.
   - **Verify**: modal closes; the badge still reads "2"; the popover still lists only the original two users — "Tatiana Bontsevich" was **not** added. Same MUI-overlay caveat as step 6 applies (dropdown must be dismissed via `Escape` before the X is clickable, or the click will hang retrying against the intercepting `MuiAutocomplete-popper`).
9. Type `"hi all"` in the message input (`chat-message-input` testid) and click Send (`chat-send-button` testid).
   - **Verify**: the user message "hi all" appears immediately; the conversation is created server-side (`POST .../conversations/prompt_lib/471` → `201`), the two queued users are persisted as participants (`POST .../participants/prompt_lib/471/{id}` → `200`, fires only now, not at step 6 — see § Network Behavior), and the LLM responds within the documented ~2–30s WebSocket delay (observed live: "Thought for 3 secs", body "Hi! How can I help?", no new console/network errors). The "Users in this conversation" badge updates from "2" to **"3"**; opening the popover shows the USERS list now includes the conversation owner ("Test Bot" / `${TEST_USER}`) alongside the two invited users — confirmed live via `chat-participants-badge-users` → popover.
10. Verify the conversation appears under the sidebar's **"Today"** date-group with a multi-person icon.
    - **Verify**: `ChatPage.is_conversation_in_group(conversation_id, group="today")` returns `True` for the newly-created conversation's id. The row's icon container (class `css-nguu07` in this build, no testid — see Concrete Handles) renders a people/group SVG icon — confirmed by direct comparison: the same conversation item rendered this icon once 2+ users were participants, while a single-owner conversation ("HI Chat", no other participants) renders an **empty** icon container (no SVG at all) — proving the icon is a genuine multi-participant indicator, not decorative chrome present on every row.

## Expected Results
- All 10 steps pass as specced above (with the step-1 reverse-masking correction — case-text says "empty USERS section", live behavior is "no participants element at all" for a brand-new conversation).
- Add persists both selected users; Cancel and X close both discard the pending selection without persisting; the owner appears in PARTICIPANTS USERS only after the first message actually creates the conversation server-side; the created conversation shows in Today with a multi-person icon.
- One MINOR product defect confirmed and filed (issue #719); one already-open shared-component defect (issue #694) reproduces here too and was cross-referenced, not re-filed.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: user is in a Team project | — | Setup | `ChatPage.switch_project("471")` + `get_selected_project_text()` | asserted *(not ambient — explicit switch required, see § Preconditions)* |
| 1 Navigate to Chats in Team project and click + Chat → new conversation opens; PARTICIPANTS panel visible with empty USERS section | new conversation opens, empty/no participants | step 1 | `step 1`: blank-conversation greeting visible; no participants badge/panel present | asserted *(clarification: case text says "empty USERS section visible", live is "no participants element at all" for a brand-new conversation — reverse-masking guard, matches ELITEA-2095/ELITEA-2166 precedent, not filed as a new ticket)* |
| 2 Click + icon and verify 'Invite Users' is in the menu → Invite Users option present | Invite Users present | step 2 | `step 2`: `invite-users-menuitem` visible/enabled among 6 menu items | asserted |
| 3 Click Invite Users → 'Add users' modal opens with search field and Cancel/Add buttons | modal opens | step 3 | `step 3`: dialog visible, search combobox + Cancel + Add (disabled) present | asserted |
| 4 Search 'sa' and select first user (e.g. Hrach Sargsyan) → User chip appears; modal stays open | chip appears, modal open | step 4 | `step 4`: chip text + modal still open + Add enabled | asserted |
| 5 Search 'ad' and select second user (e.g. Admin Bot) → Two user chips shown; modal stays open | two chips, modal open | step 5 | `step 5`: two chips + modal still open | asserted *(substitution: "Admin Bot" does not exist live; "Levon Dadayan" used instead — see § Test Data)* |
| 6 Click Add button → Modal closes; both users in PARTICIPANTS USERS section | modal closes, both users added | step 6 | `step 6`: badge reads "2"; popover lists both names | asserted |
| 7 Click + icon, Invite Users, select a third user, click Cancel → Modal closes; third user not added | not added | step 7 | `step 7`: badge stays "2"; popover unchanged | asserted |
| 8 Click + icon, Invite Users, select a fourth user, click X (close) → Modal closes; fourth user not added | not added | step 8 | `step 8`: badge stays "2"; popover unchanged | asserted |
| 9 Type 'hi all' and click Send → Message sent; LLM responds; owner avatar added to PARTICIPANTS USERS | message sent, LLM responds, owner added | step 9 | `step 9`: user message visible; LLM reply visible; badge "2"→"3"; popover shows owner + both invited users | asserted |
| 10 Verify conversation appears in Today with multi-person icon → Conversation listed with users icon | listed with icon | step 10 | `step 10`: `is_conversation_in_group(id, "today")` True; icon container non-empty, confirmed against an empty-icon single-owner conversation as a negative control | asserted |
| Expected Final State: "Conversation created with users added; Cancel and X dismiss without adding; first message shows owner in PARTICIPANTS." | — | steps 6–9 | as above | asserted |
| Pass/Fail: "Users added via Add; Cancel/X don't add users; owner appears after first message." | — | steps 6–9 | as above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- `step 4`/`step 5` assert the search dropdown's checkmark icon renders without a console warning — *added: found it does NOT (React "Invalid value for prop `sx` on `<svg>` tag"), traced to `AutoCompleteDropDown.jsx:425`'s `<CheckedIcon sx={...} />` on a raw (non-`SvgIcon`) imported SVG component. Filed as issue #719 (MINOR) — see § Known Defects. Not part of the case's own Pass/Fail criteria, but "silent errors are the worst bugs" — a console regression on every selection is worth guarding.*
- `step 3` asserts the "Add users" dialog's `aria-labelledby`/title-id wiring — *added: confirmed the SAME broken pattern as already-filed issue #694 (`aria-labelledby="alert-dialog-title"` pointing at a title element that actually carries `id="variables-dialog-title"`) reproduces here too, since `AddNewUserModal.jsx` renders via the same shared `Modal.BaseModal`. Cross-referenced on #694 rather than re-filed (`strict-per-bug` policy — same root cause).*
- `step 6` asserts the underlying network sequence (`POST .../conversations/`, `PATCH .../entity_settings/`, `PUT .../conversation/`, `POST .../participants/`, `POST .../select_conversation/`) does NOT fire at Add-click time — *added: confirms the invited users are held in client-side state until the conversation is actually created (step 9), which is a meaningful behavioral fact for the implementer (asserting "participants persisted" too early, right after step 6, would be asserting against a call that hasn't happened yet).*
- `step 7` additionally confirms `excludedUserIds` correctly drops already-added participants from subsequent searches (a "sa" search after step 6 no longer surfaces "Hrach Sargsyan") — *added: positive confirming behavior worth guarding as a regression signal, not explicitly requested by the case text but directly relevant to "Add users" correctness.*
- `step 10` asserts the multi-person icon against a **negative control** (an existing single-owner conversation, "HI Chat", with an empty icon container) rather than just observing presence on the new conversation alone — *added: rules out "this icon renders unconditionally on every row" as a false-positive pass.*
- Console/network side-channel checked after every step — *added: standard side-channel discipline; confirmed clean except the pre-existing, unrelated `secrets` 403 noise (project-471, matches other AFS files in this suite) and the new `sx`-on-svg warning (step 4/5, filed as #719).*

## Cleanup
1. Delete the created conversation via the existing testid-compliant id-scoped flow (ELITEA-2114 precedent): `chat_page.open_conversation_context_menu(conversation_id)` → `chat_page.click_conversation_menu_item("delete")` → `chat_page.confirm_delete_conversation(conversation_id)` (asserts the `DELETE .../conversation/prompt_lib/471/{id}` response, not just a client-side list splice).
2. No agent/toolkit/user entities were created by this case — only conversation + conversation-scoped participant links, which cascade-delete with the conversation. No separate user/participant cleanup needed.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `git grep` on both `origin/main` and `origin/automation/testids` in the sibling `EliteaUI` clone (the dev server always serves `automation/testids`, so "testids-only" items are usable NOW for automation even before a human promotes them to `main`).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Project selector trigger | `project-selector-trigger-combobox` | existing `ChatPage.project_selector_trigger` | Reused as-is (ELITEA-2095). |
| Project dropdown option (dynamic) | `[data-testid="select-option-{}"]` (`ChatPage.SELECT_OPTION`) | existing | Reused as-is. |
| `+ Chat` / create-conversation button | `sidebar-create-button` | on-main ✓ | Existing `ChatPage.create_conversation_button`. **Caveat found live:** there is a SEPARATE, unlabeled sidebar-collapse toggle button rendered adjacent to the conversation-list header that looks identical in an untargeted click — always target by testid, never by visual position/index, or the wrong control (list-collapse, not create) gets clicked (self-corrected during this session's exploration). |
| Composer `+` (plus) menu button | `plus-menu-button` | on-main ✓ | Existing `ChatPage.plus_menu_button`. |
| `+` menu → "Invite Users" menuitem | `invite-users-menuitem` | on-`automation/testids` only (awaiting human promotion to main) | Existing `ChatPage.invite_users_menuitem` (added during ELITEA-2166 work) — reused as-is; present in a Team project, absent in Private (inverse of ELITEA-2166's case). |
| "Add users" modal — dialog container | **NO TESTID** | needs-adding | `testid needed: add-users-dialog` (or reuse `BaseModal`'s existing `dataTestId` prop if `AddNewUserModal.jsx` threads one through — currently it does not). Confirmed via `role="dialog"` only. |
| "Add users" modal — X (Close) button | **NO TESTID** | needs-adding | `testid needed: add-users-close-button`. Only resolvable via `aria-label="Close"` today (not testid-only compliant) — `BaseModal.jsx` already has a `closeButtonTestId` prop slot (used elsewhere in the codebase per `.claude/rules/mui-patterns.md`'s note on testid props), but `AddNewUserModal.jsx` doesn't pass one. |
| "Add users" modal — search combobox | **NO TESTID** | needs-adding | `testid needed: add-users-search-input`. Underlying component is `Autocomplete.UserSearchSelect` → `AutoCompleteDropDown.jsx`; currently only resolvable via `getByRole('combobox', { name: 'Search users...' })`. |
| "Add users" modal — search results option row (dynamic) | **NO TESTID** | needs-adding | `testid needed: add-users-option-{userId}` (dynamic). `AutoCompleteDropDown.jsx`'s `renderOption` already SUPPORTS a `getOptionTestId` prop (`data-testid={getOptionTestId ? getOptionTestId(option) : undefined}`) — `UserSearchSelect.jsx` simply doesn't pass one. Low-risk, mechanical addition (the plumbing already exists, mirrors the ELITEA-2166 accordion-section precedent). Currently only resolvable via `getByRole('option', { name })`. |
| "Add users" modal — selected-user chip (dynamic) | **NO TESTID** | needs-adding | `testid needed: add-users-chip-{userId}` (dynamic). Currently the chip only carries a positional `data-item-index` (not a stable per-user handle — reordering/removal would shift the index). Resolvable today only via `getByRole('button', { name })` (chip text). |
| "Add users" modal — Cancel button | **NO TESTID** | needs-adding | `testid needed: add-users-cancel-button`. Currently only `getByRole('button', { name: 'Cancel' })`. |
| "Add users" modal — Add button | **NO TESTID** | needs-adding | `testid needed: add-users-confirm-button`. Currently only `getByRole('button', { name: 'Add' })`; also serves as the enabled/disabled state to assert (chip count > 0). |
| Participants badge (Users section) | `chat-participants-badge-users` (`ChatPage.PARTICIPANTS_BADGE.format("users")`) | on-main ✓ | Existing generic template — this case is the first to exercise `section="users"` end-to-end against a Team project's Invite-Users flow live; `is_participants_badge_visible()`/`open_participants_popover()` docstrings are stale ("this case only ever exercises 'agents'") and should be broadened, not re-implemented. |
| Participants badge trigger button | `chat-participants-badge-button` | on-main ✓ | Existing `ChatPage.PARTICIPANTS_BADGE_BUTTON`, scoped under the badge container. |
| Participants popper container | `chat-participants-popper` | on-main ✓ | Existing `ChatPage.participants_popper`. No distinct per-row testid for a user's name inside the popper — assert via text match within the popper (same established pattern as agent participants). |
| Message input | `chat-message-input` | on-main ✓ | Existing `ChatPage.message_input`. |
| Send button | `chat-send-button` | on-main ✓ | Existing `ChatPage.send_button`. |
| Conversation date-group header (dynamic) | `chat-conversation-group-header-{}` (`ChatPage.CONVERSATION_GROUP_HEADER`) | on-`automation/testids` only (awaiting human promotion to main) | Existing; `.format("today")` used for step 10. |
| Conversation list item (dynamic) | `chat-conversation-item-{}` (`ChatPage.CONVERSATION_ITEM`) | on-`automation/testids` only (awaiting human promotion to main) | Existing; `is_conversation_in_group()` already implements exactly step 10's "conversation X is under Today" check. |
| Conversation multi-person icon (step 10) | **NO TESTID** | needs-adding | `testid needed: conversation-multi-user-icon` on the icon's wrapping `<div class="css-nguu07">` (component/file not yet located precisely — grep `ComponentsLib`/`conversation-list` for the SVG path fragment `M7.3184 10.553C8.00024...` to find the exact render site). Confirmed live via a negative control: this container is present-but-empty for a single-owner conversation and non-empty (contains the SVG) once 2+ users are participants — currently only assertable via `hasSvg` on the untagged wrapper, not testid-only compliant. |
| Conversation context-menu button (dynamic, scoped) | `conversation-menu-menu-button` (`ChatPage.CONVERSATION_MENU_BUTTON`, scoped within `CONVERSATION_ITEM`) | on-`automation/testids` (templated — not literal-grep-matchable, confirmed live via direct interaction) | Existing `open_conversation_context_menu()`. |
| Conversation context-menu "Delete" item | `chat-conversation-menu-delete-menuitem` (`ChatPage.CONVERSATION_MENU_ITEM.format("delete")`) | on-`automation/testids` | Existing `click_conversation_menu_item("delete")`. |
| Delete-confirmation dialog "Delete" button | `delete-confirm-button` | on-`automation/testids` only (awaiting human promotion to main) | Existing `ChatPage.delete_confirm_button`; used by `confirm_delete_conversation()`. **Known defect (issue #694, cross-referenced this session):** this dialog is also a `Modal.BaseModal` instance and carries the same broken `aria-labelledby` wiring — does not block automation (testid-only handles are unaffected) but affects assistive-tech/a11y. |

## Network Behavior
- Steps 1–5 (opening the modal, searching, selecting into local chips): **no network call** — `AddNewUserModal.jsx` holds selections in local React state (`localUsers`) only.
- Step 6 (Add click): the modal simply closes and the badge updates client-side to "2" — still **no participants-persistence network call** at this point (queued, not yet sent to the server, since the conversation itself doesn't exist server-side yet for a brand-new unsaved chat).
- Step 9 (first Send, which both creates the conversation AND flushes the queued participants), observed in this exact order:
  1. `POST /api/v2/elitea_core/conversations/prompt_lib/471` → `201 Created` (creates the conversation, id `259` observed)
  2. `PATCH /api/v2/elitea_core/entity_settings/prompt_lib/471/259` → `200 OK`
  3. `PUT /api/v2/elitea_core/conversation/prompt_lib/471/259` → `200 OK`
  4. `POST /api/v2/elitea_core/participants/prompt_lib/471/259` → `200 OK` — **this is what persists the two invited users as real participants**, only now, not at step 6.
  5. `POST /api/v2/elitea_core/select_conversation/prompt_lib/471/259` → `200 OK`
  6. `GET /api/v2/elitea_core/context_analytics/prompt_lib/471/259` → `200 OK` (×2)
- No Socket.IO degradation was observed in this session's LLM response (unlike the known defect in ELITEA-2166/#708) — the "hi all" message got a clean, timely reply.
- Pre-existing, unrelated noise (not this case's concern): `GET /api/v2/secrets/secrets/default/471` → `403 Forbidden` (fires on project load, matches other AFS files in this suite); after this session's cleanup delete, the app auto-navigated to a pre-existing, unrelated conversation ("Call Agent1 task...") which itself fired one `400 Bad Request` on `.../version_validator/prompt_lib/471/147/152` — out of scope for this case (pre-existing conversation, unrelated agent-versioning check, not touched by the Invite Users flow), noted here only for the next analyst's awareness, not investigated further.

## Known Defects Found During Exploration

- **[MINOR] Issue #719** (novel, filed this session) — The "Add users" picker's selected-row checkmark icon (`AutoCompleteDropDown.jsx:425`, `<CheckedIcon sx={styles.checkIconSx} />`) forwards an MUI `sx` prop straight onto a raw imported `<svg>` element (`CheckedIcon` is `@/assets/checked-icon.svg?react`, not an MUI `SvgIcon`), producing a React console warning ("Invalid value for prop `sx` on `<svg>` tag") on every user selection and silently dropping the intended theme-driven size/fill override. Functionally harmless (chip still renders, Add still enables) but a genuine, reproducible code defect with a shared-component blast radius (`AutoCompleteDropDown` is used by other pickers too). Filed: https://github.com/EliteaAI/elitea-testing-public/issues/719. Not automated as a hard-fail assertion (no functional break to assert against) — flag for the implementer as an optional console-cleanliness guard (`assert no NEW console errors beyond the two pre-known ones`), not a blocking check.
- **[re-confirmed, not re-filed] Issue #694** — The "Add users" modal (`AddNewUserModal.jsx`) renders via the same shared `Modal.BaseModal` component already found broken in issue #694 (`aria-labelledby="alert-dialog-title"` pointing at a nonexistent id, while the actual title carries the stale `id="variables-dialog-title"`). Confirmed live this session and cross-referenced on #694 rather than filing a duplicate (`strict-per-bug` policy — same root cause, now confirmed to affect at least two distinct modals). Does not block testid-only automation (this AFS's handles don't rely on `aria-labelledby`), but is an a11y regression worth the UI team's attention when they pick up #694.
- **[CLARIFICATION, not filed as a new ticket] Case-text drift, step 1** — the case's literal wording, "PARTICIPANTS panel visible with empty USERS section", does not match live behavior: a brand-new, zero-participant, unsaved conversation renders **no participants element at all** (matches the already-documented ELITEA-2095/ELITEA-2166 pattern). Treated as reverse-masking (the case text is stale, not the product) — see § Test Steps step 1 and § Coverage Map.

## Blocked Steps
None. Both preconditions and all 10 case steps were executed and observed end-to-end live; the one novel defect found (#719) is cosmetic/console-only and does not block completing or automating the rest of the flow.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Page object: extend `ChatPage` with a new nested "Add users" modal surface (new `LocatorDescriptor` fields per the `needs-adding` table above, once those testids land) — do NOT duplicate `open_add_teammate_dialog()`'s existing dialog-detection logic; add search/select/chip/Add/Cancel/Close methods alongside it, following the same class-field-only locator discipline as the rest of `chat_page.py`.
- **MUI overlay-interception gotcha (confirmed live, matches `.claude/rules/mui-patterns.md`):** after selecting a user, the `MuiAutocomplete-popper` results dropdown stays open and WILL intercept clicks on the Cancel/Add/Close buttons underneath it (`TimeoutError: ... subtree intercepts pointer events`). Always dismiss the dropdown with `page.keyboard.press("Escape")` (closes the popper without closing the dialog) before clicking Cancel/Add/Close — do not reach for `force=True` here, since the popper genuinely covers the buttons and a forced click could land on the wrong element depending on z-order.
- `excludedUserIds` (client-side) means a fresh "Add users" search after users are already participants will not show them again — don't assert their absence as evidence of a bug; it's the intended dedup behavior (see § Axis 2).
- Wait strategy for step 9: use the existing `wait_for_ai_response()` / `wait_for_generation_complete()` (condition-based), never a fixed sleep, per `.agents/testing.md` — confirmed no Socket.IO degradation in this session so no known-defect soft-assert is needed here (contrast with ELITEA-2166's #708).
- The participants-badge count assertions (`"2"` after step 6, `"3"` after step 9) are the most direct, stable signal for "who got added" — prefer them over parsing avatar text where possible; use `get_participants_user_avatar_text()`/popover text-match only to confirm WHICH users, not merely the count.
