# Test Case: Chat – Team Project – Remove User from Conversation via Confirm Dialog

## Metadata
- **TMS ID**: ELITEA-2170
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; Team project "Elitea Testing Team" — observed live as `projectId=471`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login (dev-token user renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live (both preconditions + all 5 steps observed against the real app, using an isolated browser instance after a mid-session browser-lane contamination incident — see § Automation Hints note). One CLARIFICATION filed (issue #1020 — case-text drift on step 4's confirm-dialog wording + the `user_1` test-data placeholder, reverse-masking guard, not a product defect). One REQUIRED testid gap found and specced below (`chat-participant-remove-button` — and every other handle inside the USERS popper row — currently resolves to N non-unique elements when N users are listed, with zero way to scope to a specific user's row). This is implementer work per `.agents/role-overrides.md`, not a softened note, and not a blocker for this AFS's `ready-for-automation` status (the fix is a one-line mirror of an already-established pattern — see § Concrete Handles).

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- A conversation exists in a **Team project** with **at least 2 other participants** added (in addition to the conversation owner). Team-project membership is NOT ambient — the account's default/last-active project can be Private, so automation must explicitly switch via `ChatPage.switch_project("471")` (existing method, ELITEA-2095/ELITEA-2166/ELITEA-2167 precedent) to the Team project **"Elitea Testing Team"** (`471`) before proceeding. The USERS section of the PARTICIPANTS panel/badge only renders for Team projects (`showUsersSection = !isPrivateProject` in `CollapsedPerticapantsList.jsx`; `!isPrivateProject` guard in `ExpandedParticipantsList.jsx`) — it is entirely absent for the account's own Private project, matching the precedent already established by ELITEA-2095/ELITEA-2098/ELITEA-2167.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Team project "Elitea Testing Team", id `471` — `ChatPage.switch_project("471")`.
- Existing org users, invited via the "Add users" modal (ELITEA-2167 precedent — `open_add_users_modal()` / `search_and_select_add_user()`):
  - **"Hrach Sargsyan"** (search `"sa"`) — used as the user to remove (**substituted** for the case's literal Test Data value `user_1`, which does not exist as a real user in this environment — same substitution pattern already logged for ELITEA-2167's "Admin Bot"; filed as part of clarification issue #1020).
  - **"Levon Dadayan"** (search `"da"`) — second participant, kept in the conversation throughout (not removed) so the case's "at least 2 added participants" precondition and the post-removal "still ≥1 other participant remains" state are both exercised.
- Test message: `"hi all"` — sent once, to persist the invited users as real server-side participants (client-side-only until the first message, per the ELITEA-2167 Network Behavior finding — same mechanism applies here, confirmed unchanged in this session).

### generate-per-test (created in test setup, cleaned up in its own teardown)
- **New conversation** — created via the UI's own `+ Chat` flow (`sidebar-create-button` testid), matching the case's own precondition (not API-created), with "Hrach Sargsyan" + "Levon Dadayan" invited before the first message. LLM auto-titles it from the first message (observed live as **"All"**, matching the identical `"hi all"` → "All" naming already documented in ELITEA-2167's Test Data note) — not asserted by this case's Pass/Fail criteria.

## Test Steps

1. Open the conversation and click the avatar group in the PARTICIPANTS USERS section.
   - **Verify**: a dropdown (`chat-participants-popper`) opens showing a "USERS" heading, one row per participant (here: "Hrach Sargsyan", "Levon Dadayan", "Test Bot" — the owner), plus an "All users" footer item. Confirmed live via `ChatPage.open_participants_popover(section="users")` (existing method, ELITEA-2167 precedent — reused as-is, no new page-object work needed for this step). **Note on which sub-surface renders the trigger:** at the standard automation viewport (Playwright's default ~1280×720, not flagged as a "small window" by `useIsSmallWindow`) and a fresh browser context (no persisted panel-collapse state), the PARTICIPANTS panel renders its **collapsed icon-rail** form (`CollapsedPerticapantsList.jsx`) by default — the "avatar group" is the small badge icon with a participant-count superscript, wrapped in `chat-participants-badge-users`, which is exactly what `open_participants_popover()` already targets. A separate, always-rendered-at-narrow-viewport `ExpandedParticipantsList.jsx` form also exists (shows inline overlapping avatars + a hover-only trigger button with the SAME underlying `chat-participants-badge-button`/`chat-participants-popper` testids, but NOT wrapped in `chat-participants-badge-users`) — `Participants.jsx`'s `showCollapsedParticipants = collapsed && !isSmallWindow` memo is the exact source of this branching. Not expected to affect this case at the project's standard automation viewport; documented here as a risk if the viewport ever changes (see § Automation Hints).
2. Hover over the target user's ("Hrach Sargsyan") row; verify a trash-bin icon appears with a "Remove user" tooltip.
   - **Verify**: hovering the row reveals a trash-bin icon button (`chat-participant-remove-button` testid — reused from the existing agent/pipeline/toolkit/mcp participant-removal family, `ChatPage.PARTICIPANT_REMOVE_BUTTON`). Hovering the icon itself shows tooltip text **"Remove user"** — confirmed live, exact match to the case's literal text (`DeleteParticipantButton.jsx`'s `removeLabel = 'Remove ${entityType}'`, `entityType='user'` for a Users-type participant).
3. Click the trash-bin icon for the target user.
   - **Verify**: a confirmation modal (`delete-confirm-dialog` testid) appears with title **"Remove user?"** (`delete-confirm-title`) — exact match to the case's literal text.
4. Verify the modal body text.
   - **Verify** (`delete-confirm-message` testid): the live text reads **"Are you sure to remove the Hrach Sargsyan user from chat?"** — **CLARIFICATION, not a defect (reverse-masking guard):** the case's literal text says `"Are you sure to remove the user_1 user from **conversation**?"`; the live product's own, internally-consistent wording says **"from chat"**, never "conversation" (same terminology as the rest of this modal family: title "Remove user?", confirm button "Remove"). Filed as issue #1020 (bundles both this wording drift and the `user_1` placeholder substitution, per `strict-per-bug` — one root TMS-case-text-quality issue, two related findings). Automation asserts the LIVE wording verbatim, substituting the actual selected user's display name for `{name}`.
5. Click Remove.
   - **Verify**: the modal closes (`delete-confirm-dialog` hidden); "Hrach Sargsyan" is removed from the still-open `chat-participants-popper` dropdown (now lists only "Levon Dadayan" + "Test Bot" + "All users"); the "Users in this conversation" badge count decrements from **"3" to "2"**. Confirmed **persisted server-side**, not just client-state: a full page reload afterward still shows the badge at "2" and the popper still lists only the two remaining participants — "Hrach Sargsyan" does not reappear.

## Expected Results
- All 5 steps pass as specced above (with the step-4 reverse-masking correction — case text says "from conversation", live wording is "from chat"; case's `user_1` placeholder substituted with a real org user).
- The removed user disappears from both the USERS popper dropdown and the participants badge count immediately on confirm, and the removal survives a page reload (real server-side persistence, not optimistic-UI-only).
- One CLARIFICATION filed (issue #1020, case-text-quality, not a product defect). No product defects found — the flow itself is functionally correct.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: conversation with ≥2 participants in a Team project | — | Setup | `ChatPage.switch_project("471")` + invite-two-users setup (ELITEA-2167 precedent) + send first message to persist | asserted *(not ambient — explicit project switch + invite + send required)* |
| 1 Open conversation, click avatar group in PARTICIPANTS USERS section → Dropdown shows all participants + 'All users' | dropdown with all participants + All users | step 1 | `step 1`: `chat-participants-popper` visible, lists "Hrach Sargsyan"/"Levon Dadayan"/"Test Bot" + "All users" footer | asserted |
| 2 Hover user_1's row; verify trash bin icon and 'Remove user' tooltip → Trash bin visible | trash bin + tooltip | step 2 | `step 2`: `chat-participant-remove-button` visible on hover; tooltip text "Remove user" | asserted *(substitution: "user_1" → "Hrach Sargsyan", see § Test Data)* |
| 3 Click the trash bin icon for user_1 → 'Remove user?' modal appears | confirm modal, title "Remove user?" | step 3 | `step 3`: `delete-confirm-dialog` visible, `delete-confirm-title` text "Remove user?" | asserted |
| 4 Verify modal body: 'Are you sure to remove the user_1 user from conversation?' → Modal text correct | exact modal text | step 4 | `step 4`: `delete-confirm-message` text | asserted *(clarification: live text says "from chat" not "from conversation" — issue #1020, reverse-masking guard, not filed as a product defect)* |
| 5 Click Remove → Modal closes; user_1 removed from dropdown and PARTICIPANTS | modal closes, user removed from both surfaces | step 5 | `step 5`: dialog hidden; popper no longer lists the removed user; badge count "3"→"2"; persistence confirmed via reload | asserted |
| Expected Final State: "User removed via confirm dialog." | — | step 5 | as above | asserted |
| Pass/Fail: "All steps complete without errors. User removed successfully." | — | steps 1–5 | as above; no console/network errors beyond the one pre-existing, already-tracked warning (see § Known Defects) | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- `step 5` additionally asserts **server-side persistence via a full page reload**, not just the immediate client-state update — *added: the case's own Pass/Fail criteria ("User removed successfully") is ambiguous between optimistic-UI-only and real persistence; a reload-survives check is the stronger, more meaningful assertion and costs one extra `reload()` + re-open-popper round trip.*
- **Testid collision found and specced as required implementer work** (not filed as a defect — this is exactly the class of gap `.agents/role-overrides.md` § Analyst slot directs to specify, not soften): `chat-participant-remove-button` currently renders identically on **every** row inside the USERS popper (confirmed live: querying `[data-testid="chat-participant-remove-button"]` with 3 participants present returns **3 elements**, one per row, with no scoping container to disambiguate). The SAME collision applies to hovering a specific row (`UserMenu.jsx`'s row `Box` also carries no testid) — automation cannot currently target "the trash icon for THIS SPECIFIC user" via testid alone when 2+ users are listed. See § Concrete Handles for the exact, low-risk fix (a one-line mirror of an already-shipped sibling pattern).
- Confirmed, as a side observation, that the delete button also renders (unscoped) on the **current user's own row** ("Test Bot" / the conversation owner) — self-removal is not blocked at the UI-affordance level by this component. Not part of this case's steps (which only exercise removing a different participant) and not filed as a defect; flagged here in case a future case wants to test self-removal specifically, since it would hit the exact same row-scoping gap.
- Console/network side-channel checked after every step — *added: confirmed clean for the removal flow itself (steps 1–5, no new errors). One PRE-EXISTING, already-tracked console warning reproduced during this session's SETUP (inviting the two users via the "Add users" modal, not the removal flow under test) — see § Known Defects.*

## Cleanup
1. Delete the created conversation via the existing testid-compliant id-scoped flow (ELITEA-2114 precedent): `chat_page.open_conversation_context_menu(conversation_id)` → `chat_page.click_conversation_menu_item("delete")` → `chat_page.confirm_delete_conversation(conversation_id)`.
2. No agent/toolkit/user entities were created by this case — only conversation-scoped participant links, which cascade-delete with the conversation. No separate user cleanup needed (the invited org users are not modified — only their participant-link to this specific conversation is created and removed).
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `git grep` on both `origin/main` and `origin/automation/testids` in the sibling `EliteaUI` clone.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Project selector trigger | `project-selector-trigger-combobox` | on-main ✓ | Existing `ChatPage.project_selector_trigger`. Reused as-is. |
| `+ Chat` / create-conversation button | `sidebar-create-button` | on-main ✓ | Existing `ChatPage.create_conversation_button`. |
| Composer `+` menu / Invite Users flow | `plus-menu-button`, `invite-users-menuitem`, `add-users-dialog`, `add-users-search-input`, `[data-testid^="add-users-option-"]`, `add-users-confirm-button` | on-main ✓ (per ELITEA-2167 AFS, re-verified live this session) | All existing `ChatPage` methods (`open_add_users_modal()`, `search_and_select_add_user()`, `click_add_users_confirm()`) — reused as-is, zero new work for the setup phase. |
| Message input / Send | `chat-message-input` | on-main ✓ | Existing `ChatPage.message_input`; Enter submits. |
| Users participants badge (collapsed-icon-rail form) | `chat-participants-badge-users` (`ChatPage.PARTICIPANTS_BADGE.format("users")`) | on-main ✓ | Existing generic template, reused as-is (ELITEA-2167 precedent). |
| Users badge trigger button | `chat-participants-badge-button` (scoped under the badge container) | on-main ✓ | Existing `ChatPage.PARTICIPANTS_BADGE_BUTTON`; `open_participants_popover(section="users")` already drives this end-to-end. |
| Participants popper container | `chat-participants-popper` | on-main ✓ | Existing `ChatPage.participants_popper`. |
| **USERS popper — per-user row container** | **NO TESTID (collision — same testid on every row's children)** | needs-adding | `testid needed: chat-participant-row-{uniqueId}` on `UserMenu.jsx`'s row-wrapping `<Box onMouseEnter=... onMouseLeave=... sx={itemStyles.root}>` (the element carrying the row's `onMouseEnter`/`onMouseLeave` handlers). **This is a direct, one-line mirror of an ALREADY-SHIPPED sibling pattern** — `ExpandedParticipants/ParticipantItem.jsx:256` does exactly this for agent/pipeline/toolkit/mcp rows: `data-testid={\`chat-participant-row-${getChatParticipantUniqueId(participant)}\`}`. For a Users-type participant, `getChatParticipantUniqueId()` (already imported/available via `participants.helpers.js`) yields `user_{entity_meta.id}_{project_id}` (`ChatParticipantType.Users === 'user'`, confirmed in `common/constants.js:971`) — the exact same family already covered by the **EXISTING** `ChatPage.PARTICIPANT_ROW` template (`'[data-testid="chat-participant-row-{}"]'`) and consumed by the existing `remove_agent_participant()` method (`automation/pages/chat_page.py:3374`). **Zero new page-object class constants are needed** — only the JSX addition, plus a new `remove_user_participant(user_id, project_id)` action method mirroring `remove_agent_participant()`'s body verbatim (open popper → scope `PARTICIPANT_ROW.format(f"user_{user_id}_{project_id}")` → hover → click the row-scoped `PARTICIPANT_REMOVE_BUTTON` → confirm via the existing `Dialog` helper). |
| USERS popper — per-row remove (trash) button | `chat-participant-remove-button` | on-main ✓ (component-level; **collision at the instance level** — see previous row) | Existing `ChatPage.PARTICIPANT_REMOVE_BUTTON` — usable ONLY once scoped under the new per-row testid above (`row.locator(self.PARTICIPANT_REMOVE_BUTTON)`, exact same idiom `remove_agent_participant()` already uses). Tooltip text "Remove user" (dynamic per `entityType`, hardcoded string, safe to assert verbatim). |
| Confirmation dialog | `delete-confirm-dialog` / `delete-confirm-title` / `delete-confirm-message` / `delete-confirm-button` / `delete-confirm-cancel-button` | on-`automation/testids` (per ELITEA-2167 AFS — awaiting human promotion to main) | All existing, shared `DeleteEntityModal` testids — the SAME dialog family already used by conversation deletion (ELITEA-2114) and agent/pipeline/toolkit participant removal. Zero new work. |
| USERS popper — per-user avatar (optional, nice-to-have) | **NO TESTID** | needs-adding (OPTIONAL — not required to unblock this case once the row testid above lands) | `UserAvatar` (`src/components/UserAvatar.jsx`) already ACCEPTS and wires a `testId` prop straight onto `data-testid` — confirmed via source read — but `UserMenu.jsx`'s call site (`<UserAvatar name={user_name} avatar={user_avatar} size={20} />`) simply doesn't pass one (a pure prop-threading gap, same shape as the ELITEA-2082 toolkit-canvas-title finding). The row-container testid above is sufficient to scope every other assertion in this case; this is a lower-priority polish item, not required work. If added, follow `UserParticipantItem.jsx`'s own precedent (`testId="chat-participants-users-avatar"`, a shared non-unique identity testid) rather than inventing a new per-user template. |

## Network Behavior
- Steps 1–4 (opening the popper, hovering, opening the confirm dialog): **no network call** — purely client-side UI state (Popper open/close, MUI Tooltip, Dialog open).
- Step 5 (Remove click): fires the participant-removal request (not captured via network-tab this session — the CDP tool used captures network per-process-invocation, and separate short-lived tool invocations don't share a capture buffer across the whole flow; persistence was instead confirmed behaviorally via a full page reload, which is the stronger and more direct proof of a server-side effect than an intercepted request URL would have been).
- No Socket.IO/AI-response involvement in the removal flow itself (only used earlier, during setup, for the initial "hi all" message that persists the invited participants — same mechanism already documented in the ELITEA-2167 AFS, unchanged in this session).
- Pre-existing, unrelated noise (not this case's concern, not a new finding): none observed beyond the one console warning below, itself from setup, not the removal flow.

## Known Defects Found During Exploration

- **[CLARIFICATION, filed] Issue #1020** — case's step-4 confirm-dialog text says "from conversation", live product consistently says "from chat"; case's Test Data table names a placeholder user (`user_1`) that doesn't exist in this environment. Reverse-masking guard — the live product is correct and internally consistent (same wording pattern across the whole `DeleteEntityModal` family); the TMS case text is stale. Not a product defect, no code change requested. https://github.com/EliteaAI/elitea-testing-public/issues/1020
- **[re-confirmed during setup, not re-filed] Issue #719** — the "Add users" modal's search-result checkmark icon (`AutoCompleteDropDown.jsx:425`) forwards an MUI `sx` prop onto a raw `<svg>`, producing a React console warning on every user selection. Reproduced again during this case's SETUP phase (inviting "Hrach Sargsyan"/"Levon Dadayan") — same root cause already filed and tracked in the ELITEA-2167 AFS, cross-referenced here rather than re-filed (`strict-per-bug` policy). Does not affect the removal flow under test; not part of this case's Pass/Fail criteria.
- **No product defects found in the removal flow itself** (steps 1–5) — the feature works correctly end-to-end, including real server-side persistence confirmed via reload.

## Blocked Steps
None. Both preconditions and all 5 case steps were executed and observed end-to-end live.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Page object: extend `ChatPage` with `remove_user_participant(user_id: int, project_id: int, timeout=10000)`, mirroring `remove_agent_participant()` (`automation/pages/chat_page.py:3374`) verbatim in structure — the only difference is the `uniqueId` prefix (`user_` instead of `application_`) and confirming via the "Remove user?" dialog (same shared `DeleteEntityModal`, entity-type-driven title/text, no new dialog handling needed).
- **This case's `testid needed` is a prerequisite, not a nice-to-have** — without the `chat-participant-row-{uniqueId}` addition to `UserMenu.jsx`, there is NO testid-only-compliant way to click "the remove button for THIS SPECIFIC user" once 2+ users are listed (which this case's own precondition requires — "at least 2 added participants"). `add-data-testid` work is a strict precondition for implementing steps 2–5 per the project's locator policy.
- **Viewport/layout risk (documented, not expected to block at the standard config):** `Participants.jsx`'s `showCollapsedParticipants = collapsed && !isSmallWindow` memo determines whether the USERS trigger renders inside the `chat-participants-badge-users`-wrapped collapsed icon-rail (`CollapsedPerticapantsList.jsx`, what `open_participants_popover()` already targets) or the un-wrapped `ExpandedParticipantsList.jsx` avatar row (same underlying `chat-participants-badge-button`/`chat-participants-popper` testids, different DOM parent, NOT reachable via the existing `PARTICIPANTS_BADGE` locator). Confirmed live at Playwright's default viewport (~1280×720) with a fresh browser context (no persisted panel-collapse state): the collapsed icon-rail form renders, matching the existing method's expectations. If a future test ever runs at a narrower viewport or a persisted-expanded panel state, `open_participants_popover(section="users")` would need a fallback locator for the un-wrapped `chat-participants-badge-button` — out of scope for this case, flagged for awareness only.
- **Self-removal is not blocked at the affordance level** (see § Axis 2) — if a future case wants to test attempting to remove the CURRENT user from their own conversation, the same row-scoping fix (this case's testid addition) is the prerequisite; no separate investigation needed.
- Reuse `ChatPage.switch_project("471")` + the ELITEA-2167 `open_add_users_modal()`/`search_and_select_add_user()`/`click_add_users_confirm()` methods verbatim for setup — do not re-implement the invite flow.
- Assert persistence via `page.reload()` + re-open the popper + re-check the badge count/list, exactly as this session did — a stronger signal than trusting the immediate client-side UI update alone.

## Implementer Exploration Amendment (Phase 2 — corrects the uniqueId format above)

**The `user_{entity_meta.id}_{project_id}` format claimed above is WRONG —
confirmed live via a diagnostic pytest run.** A "user"-entity participant's
`entity_meta` carries **only `id`** — `entity_meta.project_id` is never
set for `entity_name === "user"` (live API response for this session's
conversation: `{'id': 43, 'entity_name': 'user', 'entity_meta': {'id': 43},
'meta': {'user_name': 'Hrach Sargsyan', ...}}` — no `project_id` key at
all). `getChatParticipantUniqueId()`'s trailing segment
(`participant.entity_meta?.project_id || ''`) therefore falls back to an
**empty string**, and the real rendered testid is
`chat-participant-row-user_{entity_meta.id}_` — a **trailing underscore
with nothing after it**, not `..._471`. Confirmed against all three live
rows in this session: `chat-participant-row-user_43_`,
`chat-participant-row-user_7_`, `chat-participant-row-user_659_`. This is
consistent with (and explains) `ParticipantDetailsContext.jsx`'s own
detail-fetch guard, which explicitly EXCLUDES `ChatParticipantType.Users`
from its `entity_meta?.project_id`-required check — Users-type
participants simply don't carry one, by design (agent/pipeline/toolkit
participants do, which is why `remove_agent_participant()`'s
`application_{id}_{project_id}` is correct as documented).

**Implementer action taken:** `ChatPage.get_user_participant_row()` /
`get_user_participant_remove_button()` build the locator as
`f"user_{user_id}_"` (no `project_id` parameter at all — it would be
silently unused/misleading for this participant type). This is a
technique-only fix (Phase 2, not a scope change) — the case's own steps
and assertions are unaffected; only the internal row-scoping locator
construction changed. `remove_user_participant(user_id, project_id)` as a
single opaque method (as hinted above) was NOT added — the implementation
instead exposes `get_user_participant_row()` /
`get_user_participant_remove_button()` as discrete steps so this case's
own Coverage Map (steps 2-4 verify intermediate hover/click/dialog state,
not just the end result) can assert against each one, matching this
suite's own established decomposition style (e.g.
`open_add_users_modal()` / `search_and_select_add_user()` /
`click_add_users_confirm()` in the ELITEA-2167 precedent) rather than one
end-to-end black box.

