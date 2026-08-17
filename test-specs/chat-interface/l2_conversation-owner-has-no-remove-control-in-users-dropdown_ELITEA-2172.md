# Test Case: Chat – Team Project – Conversation Owner Cannot Be Removed from Participants List

## Metadata
- **TMS ID**: ELITEA-2172
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (per source case's `priority: high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend;
  Team project "Elitea Testing Team", `projectId=471`)
- **User set**: `${TEST_USER}` — localhost: no login needed, `VITE_DEV_TOKEN` auto-auths (dev-token user
  renders as "Test Bot"/"TB"; this is the only real logged-in account this single-account environment
  can drive, and it is always the creator/"owner" of every conversation it opens or creates)
- **Analyst**: qa-engineer (agent), batch `chat-remaining-w10`, cluster dispatch with ELITEA-2171, 2026-08-15
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright MCP against
  `http://localhost:5173`. No blockers, no defects found — the product behaves exactly as the case
  expects. All testids this case needs already exist on `origin/main` (added by the merged ELITEA-2168
  implementation) — no new testid work required.
- **surface_key**: `chat-users-participant-dropdown` (shared with ELITEA-2171 — same "Users" dropdown
  remove-control surface, different behavior asked; NOT a family AFS — the two cases differ in STEPS,
  not merely in data: ELITEA-2171 exercises the Cancel-preserves-user flow on a non-owner row,
  ELITEA-2172 exercises the absence of the control on the owner's OWN row plus its presence on others'
  — per the skill's "differ in steps → separate AFS" rule)
- **Related, NOT a target for `extend-existing` or `already-covered`**:
  `test-specs/chat-interface/l2_team-users-mention-and-remove-participants_ELITEA-2168.md` (merged,
  `automation/tests/ui/chat/test_team_users_mention_and_remove_participants.py`) exercises removing
  TWO NON-OWNER participants (Levon Dadayan, Hrach Sargsyan) but never asserts anything about the
  OWNER's own row — no hover-owner, no absence-of-delete-control check anywhere in that test. This
  case's own observable (the owner row specifically lacks a delete control) is genuinely new.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User is in a **Team project** ("Elitea Testing Team", `471`) — same explicit-switch requirement as
  ELITEA-2167/2168/2169/2171 (`ChatPage.switch_project("471")`).
- A conversation exists with participants including the owner AND at least one non-owner user (so both
  rows — owner and non-owner — can be compared in the same dropdown).

## Test Data

### reuse-existing
- `${TEST_USER}` — the dev-token owner ("Test Bot"/"TB"). See `.agents/profile.md` § Roles & sample users.
- Team project "Elitea Testing Team", id `471` — `ChatPage.switch_project("471")`.
- One existing org user to add as a non-owner participant, searched via the "Add users" modal's search
  field (same client-side substring filter ELITEA-2167/2168 documented) — confirmed live this session:
  `"sa"` → **Hrach Sargsyan** (same name ELITEA-2168's own "user_1" already uses, for continuity).

### generate-per-test (created in test setup/steps, cleaned up in its own teardown)
- **New conversation** — created via `+ Chat` (retry-guarded open, same `_open_blank_conversation()`
  pattern ELITEA-2167/2168 already establish — issue #1082's stale-conversation flake applies here too).
  Seed ONE non-owner participant (Hrach Sargsyan) via Invite Users, then send a message so the owner +
  the invited user both persist server-side as real PARTICIPANTS.

## Test Steps

**Setup** (not a case step — establishes the precondition): switch to Team project 471; open a
genuinely blank conversation (retry-guarded); open "Add users", search+select Hrach Sargsyan, click
Add; type+send a setup message; wait for the LLM reply and for the participants badge to read `"2"`
(owner + 1 invited user).

1. Open a conversation, click avatar group to open USERS dropdown.
   - **Verify**: `ChatPage.open_participants_popover(section="users")` returns a visible popper listing
     all participants — confirmed live this session: the popper showed `menuitem "Hrach Sargsyan..."` and
     `menuitem "TB Test Bot"` (both rows present).
2. Identify the conversation owner in the dropdown.
   - **Verify**: the owner row is the one whose `meta.user_name` matches `${TEST_USER}`'s display name
     ("Test Bot") — resolvable via `ConversationAPI.get_conversation(conv_id)`'s `participants` array
     (same `entity_meta.id`/`meta.user_name` resolution mechanism ELITEA-2168's test already uses for
     non-owner rows, generalized to resolve the OWNER's own id instead of a searched-for name).
   - **Substitution note (source-confirmed mechanism, not a case-text drift)**: the product does not
     carry an explicit "is conversation owner" flag on the participant object that the UI reads for this
     check. `UserMenu.jsx`'s per-row `isSelectable = selectable && user.entity_meta?.id !== currentUserId`
     compares each row's user id against `currentUserId` (`state.user.id` — the CURRENTLY LOGGED-IN
     session's own user id), and it is `isSelectable` (NOT the raw `selectable` prop) that gates the
     delete button's hover-visibility CSS (`'&:hover #DeleteButton': { visibility: selectable ?
     'visible' : 'hidden' }` — `userItemStyles`' own `selectable` param receives `isSelectable`, per-row).
     In other words, the mechanism the product actually implements is **"you cannot remove yourself"**,
     not a distinct "conversation owner" role. In THIS single-account testing environment the two concepts
     are indistinguishable and produce identical, case-text-satisfying behavior: the dev-token account
     both IS the currently-logged-in session AND created every conversation it opens, so its row is always
     both "the owner" (case's own wording) and "yourself" (the product's actual mechanism) — asserting
     against it faithfully verifies the case's own intent. Documented here per the interaction-discovery
     ladder / reverse-masking guard: this is a mechanism clarification, not a defect, and not a case-text
     drift (the live behavior matches the case's expectation exactly).
3. Hover over the owner's row.
   - **Verify**: NO trash bin ("Remove user") icon appears — confirmed live this session via Playwright
     MCP: hovering the `menuitem "TB Test Bot"` row (`ref=f9e2251`) produced NO accessible "Remove user"
     button in the post-hover accessibility snapshot (contrast: hovering the non-owner row in the SAME
     dropdown, same session, immediately produced `button "Remove user"` — see step 5). Source-confirmed
     mechanism: the delete `IconButton` (`id="DeleteButton"`) is always present in the DOM (never
     conditionally rendered/removed) but stays `visibility: hidden` even on hover when `isSelectable` is
     `false` for that row (`UserMenu.jsx`'s `userItemStyles`) — the correct automation assertion is
     `not_to_be_visible()` on the scoped `chat-participant-remove-button` locator (element present,
     never visible), not `to_have_count(0)`.
4. Verify owner row has no delete control.
   - **Verify**: same observation as step 3 — `row.locator(PARTICIPANT_REMOVE_BUTTON)` (scoped inside
     `chat-participant-row-user_{ownerId}_`) stays not-visible after a hover+300ms settle (same
     hover-reveal CSS-transition wait the existing `open_remove_user_dialog()` method already uses).
5. Verify all other (non-owner) rows show trash bin on hover.
   - **Verify**: confirmed live this session — hovering the non-owner row (Hrach Sargsyan,
     `ref=f9e2245`) produced `menuitem "Hrach Sargsyan @ Hrach Sargsyan Remove user" [ref=f9e2265]` with
     a `button "Remove user" [ref=f9e2268]` — the delete icon reveals correctly for a non-owner row in
     the exact same dropdown, same hover mechanism, immediately contrasting with step 3's owner-row
     absence. (This is the SAME mechanism ELITEA-2168's test already exercises and asserts via its own
     Step 8/9/10 — reused here as the positive control, not re-derived.)

## Expected Results
- The owner's row in the Users participants dropdown never reveals a delete/"Remove user" control, on
  hover or otherwise — confirmed live, matches the case's Pass criteria exactly.
- Every non-owner row DOES reveal a delete control on hover — confirmed live (already proven by the
  merged ELITEA-2168 test's Step 8–10 for two different non-owner rows; independently re-confirmed here
  for a third, Hrach Sargsyan, as this case's own positive control).
- No defects found — live product behavior matches the case's expected result exactly.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state`/`VITE_DEV_TOKEN` fixture | asserted |
| Precondition: conversation with participants including the owner | — | Setup | badge visible, count == "2" | asserted *(seeded per § Preconditions — not ambient)* |
| 1. Open conversation, click avatar group → USERS dropdown shows all participants | dropdown shows all | step 1 | `open_participants_popover(section="users")` visible; both rows present | asserted |
| 2. Identify conversation owner in dropdown | owner identified | step 2 | resolved via `ConversationAPI.get_conversation()` matching `${TEST_USER}` display name | asserted *(substitution note: product mechanism is "currentUserId self-check", not an explicit owner flag — see step 2's note; behaviorally equivalent in this single-account environment)* |
| 3. Hover over owner's row → no trash bin icon | no icon appears | step 3 | `chat-participant-remove-button` scoped in owner row stays `not_to_be_visible()` after hover | asserted |
| 4. Verify owner row has no delete control | no delete control | step 4 | same assertion as step 3 | asserted |
| 5. Verify non-owner rows show trash bin on hover | trash bin visible | step 5 | `chat-participant-remove-button` scoped in non-owner row becomes `to_be_visible()` after hover | asserted |
| Expected Final State / Pass-Fail: "Owner cannot be removed; only non-owner rows have delete controls" | — | steps 3–5 | as above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- The `isSelectable`/`currentUserId` mechanism note (step 2) — *added: found by reading
  `UserMenu.jsx` source after the live hover-comparison confirmed the behavior, to root-cause WHY it
  works rather than merely observing THAT it works; also documents the single-account-environment
  caveat for whoever next touches this in a multi-account context.*
- Positive-control row (step 5) — *added: the case's own step 5 asks for this, and it also serves as
  this AFS's negative-control validation (if the delete icon revealed for NEITHER row, the assertion
  mechanism itself would be broken, not proving anything about ownership) — both rows checked in the
  SAME dropdown instance, same session, ruling out a stale-popover or timing artifact.*
- Console/network side-channel checked throughout this session's live exploration — no new errors;
  only the already-known, already-filed #719 `sx`-on-svg warning and the project-471 `secrets` 403 noise
  (same pattern ELITEA-2167/2168 already document).

## Cleanup
1. Delete the conversation created by this test's setup via the existing testid-compliant id-scoped
   flow (`chat_page.open_conversation_context_menu(conversation_id)` → `click_conversation_menu_item("delete")`
   → `confirm_delete_conversation(conversation_id)`).
2. No agent/toolkit entities created — only conversation + conversation-scoped participant links,
   cascade-deleted with the conversation.
3. This session's own manual exploration (Playwright MCP, on a separate pre-existing shared conversation,
   `/chat/420`) added and then removed Hrach Sargsyan as a participant to confirm the mechanism live —
   confirmed restored to its original state (badge back to "1") before ending the session. The
   IMPLEMENTED test creates and deletes its own fresh conversation; it does not reuse `/chat/420`.

## Concrete Handles (discovered during exploration)
Locator policy on this project is **testid-only** — no role/label/text fallback ladder
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `git grep`
on both `origin/main` and `origin/automation/testids` in the sibling `EliteaUI` clone (fetched fresh
this session) — **every handle this case needs already exists on `main`**, added by the merged
ELITEA-2168 implementation; no new testid work required.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Users participants badge (opens dropdown) | `chat-participants-badge-button` | on-`main` ✓ / on-`automation/testids` ✓ | Reused as-is from ELITEA-2167/2168. |
| "Users" participants dropdown — per-user row | `chat-participant-row-user_{userId}_` (dynamic, trailing segment always empty for "user" participants) | on-`main` ✓ / on-`automation/testids` ✓ | Added by ELITEA-2168 (`EliteaAI/EliteaUI@16fb99e3`), confirmed present on `main` this session via fresh `git grep`. `ChatPage.PARTICIPANT_ROW.format(f"user_{user_id}_")` — reuse directly. |
| Row's delete/"Remove user" icon button | `chat-participant-remove-button` | on-`main` ✓ / on-`automation/testids` ✓ | Pre-existing shared handle (also used by agent-participant removal). `ChatPage.PARTICIPANT_REMOVE_BUTTON` — scope inside the row locator (`row.locator(PARTICIPANT_REMOVE_BUTTON)`), then assert `not_to_be_visible()` (owner) / `to_be_visible()` (non-owner) after a hover. |
| "Remove user?" confirmation dialog | Same `Modal.DeleteEntityModal`/`Dialog` helper | on-`main` ✓ | Not needed by THIS case (no click on the owner's icon is possible — there is none to click) — listed for completeness only; ELITEA-2171/2168 already exercise it. |

**Provenance grep (this session, fresh `git fetch origin` first):**
```
chat-participants-badge-button          main:YES  testids:YES
chat-participant-row-{unique_id}         main:YES  testids:YES
chat-participant-remove-button           main:YES  testids:YES
```

## Network Behavior
- Steps 1–5 (open dropdown, hover, verify): no network call — pure client-side rendering off the
  conversation's already-loaded `participants` array (same as ELITEA-2168's dropdown-open/hover
  mechanism).
- Setup (seed conversation + add user + send): same conversation-create/participants-persist/predict
  requests ELITEA-2167/2168 already document.

## Known Defects Found During Exploration
None. Live product behavior matches the case's expected result exactly — the owner's row never reveals
a delete control (hover or otherwise), and every non-owner row does.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Page object: extend `ChatPage` with a small new method, e.g. `is_remove_control_visible(user_id,
  timeout)` — resolves the row via `PARTICIPANT_ROW.format(f"user_{user_id}_")`, hovers it (same
  `force=True` + `page.wait_for_timeout(300)` hover-reveal-CSS-transition pattern
  `open_remove_user_dialog()` already uses), and returns whether
  `row.locator(PARTICIPANT_REMOVE_BUTTON)` is visible — WITHOUT clicking it (this case never opens the
  confirmation dialog for the owner, since there is no control to click). Reuse
  `open_remove_user_dialog()`'s existing row-hover mechanics as a reference, but do not modify or
  chain off it — this is a read-only "is it visible" check, a different shape from the
  open-then-click-then-return-dialog flow that method implements.
- Resolve the owner's `user_id` the SAME way ELITEA-2168's test resolves non-owner ids —
  `ConversationAPI.get_conversation(conv_id)`'s `participants` array, matched by `meta.user_name` ==
  `${TEST_USER}`'s known display name ("Test Bot") instead of a searched-for name. Do not assume a
  fixed numeric id — resolve it live each run, same as every other participant id in this test family.
- **Residual-hover reset between rows** (same class already documented for
  `remove_agent_participant()`/`open_remove_user_dialog()`): call `page.mouse.move(0, 0)` before
  hovering EACH row (owner, then non-owner, or vice versa) — a lingering real-mouse `:hover` on the
  previously-hovered row can otherwise prevent the next row's own hover-reveal CSS from firing reliably.
- **Assertion shape matters**: use `expect(locator).not_to_be_visible()` for the owner row (element
  IS in the DOM, permanently `visibility: hidden`) — never `to_have_count(0)`, which would pass
  vacuously for the wrong reason if the row itself failed to resolve. Use `expect(locator).to_be_visible()`
  for the non-owner row's positive control.
- Wait strategy elsewhere: reuse `wait_for_participants_badge_count()` (condition-based) for setup —
  never a fixed sleep, per `.agents/testing.md`.
