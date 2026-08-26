# Test Case: Chat – Team Project – Cancel Remove Participant Dialog Keeps User in List

## Metadata
- **TMS ID**: ELITEA-2194
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (per source case's `priority: medium`; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend;
  Team project "Elitea Testing Team", `projectId=471`)
- **User set**: `${TEST_USER}` — localhost: no login needed, `VITE_DEV_TOKEN` auto-auths (dev-token user
  renders as "Test Bot"/"TB", always the owner)
- **Analyst**: qa-engineer (agent), batch `chat-remaining-w11`, cluster dispatch with ELITEA-2192/2193, 2026-08-15
- **Status**: **already-covered**
- **surface_key**: `chat-users-participant-dropdown` (shared with ELITEA-2171/2172/2192/2193 — same
  "Users" dropdown remove-control surface)

## Preconditions
- User is logged in to the Elitea platform.
- Logged in as conversation owner with multiple participants.

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/chat/test_team_users_mention_and_remove_participants.py`, class
`TestTeamUsersMentionAndRemoveParticipants`, method
`test_team_users_mention_and_remove_participants` (TMS ELITEA-2168, AFS
`test-specs/chat-interface/l2_team-users-mention-and-remove-participants_ELITEA-2168.md`), **Step 10**
(source lines 560-576). Merged to `origin/automation/base` (confirmed present this session via a fresh
`git fetch origin`).

**This is the SAME covering test/step ELITEA-2171 ("Chat – Team Project – Cancel Remove User Dialog
Keeps User in Participants List") already used for its own `already-covered` dedup** —
`test-specs/chat-interface/lcovered_cancel-remove-user-dialog-keeps-user-in-participants_ELITEA-2171.md`.
ELITEA-2194 is a near-duplicate TMS case of ELITEA-2171 (same wording, same 3-step flow, different TMS
ID — the same near-duplicate pattern this digest already documents recurring across this project's TMS
case set, e.g. ELITEA-2460/ELITEA-2148, ELITEA-2461/ELITEA-2149+2151, ELITEA-2123/2127/ELITEA-2459).

**Behavioural-equivalence argument.** ELITEA-2194's 3 steps are, verbatim, ELITEA-2168's own Step 10:

| ELITEA-2194 step | ELITEA-2168's covering test, Step 10 (lines 560-576) |
|---|---|
| 1. Open USERS dropdown, hover over a non-owner participant, click trash bin → 'Remove user?' modal appears | `chat.open_remove_user_dialog(participant_id_by_name[USER_1_NAME], ...)` — opens the Users popover, hovers user_1's row (Hrach Sargsyan), clicks its delete icon, returns the confirmation dialog. |
| 2. Click Cancel → Modal closes without removing user | `Dialog.click_button(dialog, "Cancel")` + `Dialog.wait_for_hidden(page, ...)` — clicks Cancel, asserts the dialog closes. |
| 3. Verify participant still listed in dropdown and PARTICIPANTS section → user still present | `assert badge_count == "5"` (unchanged PARTICIPANTS count) + `assert USER_1_NAME in popper_text` (still listed in the USERS dropdown popover) — both the PARTICIPANTS badge and the USERS dropdown listing ELITEA-2194 Step 3 asks for. |

Every element of ELITEA-2194's 3 steps has a direct, one-to-one assertion in the covering test's Step
10 — identical to the analysis ELITEA-2171's own AFS already performed for the same underlying flow.

**Live-reconfirmed this session — direct manual repro of the EXACT 3-step flow, via Playwright MCP**
(localhost:5173, Team project 471, conversation `/chat/566` "HI Chat" — owner "Test Bot" + non-owner
"Hrach Sargsyan"):

1. **Step 1** — opened the Users participants dropdown (badge click → popover), hovered the non-owner
   participant row (Hrach Sargsyan), clicked its delete icon — the "Remove user?" dialog appeared with
   the exact text `"Remove user?" / "Are you sure to remove the Hrach Sargsyan user from chat?" /
   Cancel / Remove` (confirmed via accessibility snapshot), plus (this session's own additional
   confirmation, shared with ELITEA-2193's AFS) an orange warning icon (`fill: rgb(233, 121, 18)`) in
   the dialog title.
2. **Step 2** — clicked **Cancel** (`delete-confirm-cancel-button`) — the dialog closed (no dialog node
   left in the next accessibility snapshot).
3. **Step 3** — confirmed the PARTICIPANTS badge stayed unchanged (`"2"` before and after Cancel) AND
   the USERS dropdown popover still listed "Hrach Sargsyan" — both the badge-count and dropdown-listing
   halves of ELITEA-2194's own Step 3 ask.

This is a direct, live, positive confirmation of ELITEA-2194's exact 3 steps against today's product —
not an inference from the covering test's source alone, and independent of (though consistent with)
ELITEA-2171's own earlier live repro on a different conversation.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Open USERS dropdown and hover over a non-owner participant, click trash bin — 'Remove user?' modal
   appears.
2. Click Cancel — Modal closes without removing user.
3. Verify participant still listed in dropdown and PARTICIPANTS section — User still present.

## Expected Results
- Clicking Cancel in the "Remove user?" dialog closes it without removing the participant — both the
  PARTICIPANTS badge count and the USERS dropdown popover listing stay unchanged — proven by
  `test_team_users_mention_and_remove_participants`'s Step 10, and independently re-confirmed live this
  session via manual dialog-mechanism repro (second independent confirmation of this exact mechanism,
  after ELITEA-2171's own earlier session).

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state`/`VITE_DEV_TOKEN` (localhost) | framework fixture | already-covered |
| Precondition: owner with multiple participants | — | covering test's Setup (seeds owner + 2 users) | `wait_for_participants_badge_count("3", ...)` | already-covered |
| 1. Open USERS dropdown, hover non-owner, click trash bin → 'Remove user?' modal | modal appears | covering test Step 10, `open_remove_user_dialog()` | `Dialog.wait_for()` resolves; dialog text confirmed live this session | already-covered |
| 2. Click Cancel → modal closes, not removed | modal closes | covering test Step 10 | `Dialog.click_button(dialog, "Cancel")` + `Dialog.wait_for_hidden()` | already-covered |
| 3. Verify participant still in USERS dropdown and PARTICIPANTS | still present | covering test Step 10 | `badge_count == "5"` (unchanged) + name in popper_text | already-covered |
| Expected Final State: "User preserved after cancelling removal dialog" | — | covering test Step 10 | as above | already-covered |
| Pass/Fail: "Cancel keeps user in participants" | — | covering test Step 10 | as above | already-covered |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
None beyond what the covering spec (ELITEA-2168's AFS) and ELITEA-2171's own AFS already document —
their Axis 2 covers the residual-hover gotcha this exact interaction needs
(`page.mouse.move(0, 0)` reset before the next row's hover-reveal). This session's manual live repro
used a fresh popover open (no prior row interaction), so the residual-hover gotcha did not need to be
exercised to re-confirm the dialog mechanism a second time.

## Cleanup
No new conversation created by this AFS's own exploration — reused the existing `/chat/566` "HI Chat"
conversation (shared with ELITEA-2192/2193's own investigation in this same session). The one dialog
opened during Step 1's manual repro was Cancelled (not Removed) — Hrach Sargsyan was never actually
removed. Conversation left in its pre-existing state (badge "2", both participants present) before
ending the session.

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `chat-participants-badge-button`,
`chat-participant-row-user_{userId}_` (dynamic), `chat-participant-remove-button` (scoped inside the
row), the shared `Modal.DeleteEntityModal`/`Dialog` confirmation component (`Cancel`/`Remove` buttons,
`delete-confirm-dialog`/`delete-confirm-title`). All confirmed present and functioning on live
localhost this session — provenance re-verified fresh (`git fetch origin` this session):

| Testid | main | automation/testids |
|---|---|---|
| `chat-participants-badge-button` | ✅ | ✅ |
| `chat-participant-row-{unique_id}` (dynamic) | ✅ | ✅ |
| `chat-participant-remove-button` | ✅ | ✅ |
| `delete-confirm-dialog` | ✅ | — |
| `delete-confirm-title` | ✅ | — |

No new handles needed for this traceability pass.

## Known Defects Found During Exploration
None novel this session. Same mechanism ELITEA-2171 already documents, re-confirmed a second time on
a different conversation/participant pair.

## Blocked Steps
None. The manual live repro plus the covering test's existing, reviewed Step 10 source together
confirm every element of ELITEA-2194's 3 steps against today's live product.

## TMS linkage
Link ELITEA-2194 to ELITEA-2168 in the TMS (both ways) so the audit trail resolves: ELITEA-2194's
`already-covered` disposition points at the automated test; ELITEA-2168's case gains an "also satisfies
ELITEA-2194" back-reference (in addition to the existing "also satisfies ELITEA-2171" reference — same
covering test now satisfies both near-duplicate cases). Same pattern already established between
ELITEA-2169/ELITEA-2167 and ELITEA-2171/ELITEA-2168.
