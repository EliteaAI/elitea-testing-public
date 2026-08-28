# Test Case: Context management settings apply to new conversations only

## Metadata
- **TMS ID**: ELITEA-2390
- **Priority**: l1 (case priority `high`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `settings-w08`, 2026-08-28
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/settings-user-profile/_surface.md` →
  `_surface/memory-context-management.md` (settings side) +
  `test-specs/chat-interface/_surface.md` (chat side)

## Not already covered — checked

`automation/tests/ui/chat/test_context_management.py::test_context_budget_reflects_profile_max_tokens`
looks adjacent (profile Max Context Tokens → chat Context Budget) but is
**`@pytest.mark.skip`ped** with a stale reason ("Context management section
removed from UI"), belongs to a different TMS case (ELITEA-1340), and asserts
only the *new*-conversation half — it never touches Preserve Recent Messages
and never checks that a **pre-existing** conversation keeps its own values,
which is this case's actual subject. A skipped test is not coverage, so this
case is `ready-for-automation` as its own spec, not `already-covered` /
`extend-existing`. *(The stale skip is reported as a finding for the lead —
not repaired here: one PR, one purpose.)*

## Preconditions
- User is logged in (`auth_state`; localhost bypass).
- The user's Context Management defaults are per-account and shared —
  read-before-write and restore (surface digest § Test data gotcha).
- **No pre-existing conversation can be assumed.** Verified live: the current
  project's conversation list renders folders only, zero
  `chat-conversation-item-*` rows. The spec therefore *creates* its own
  "previously existing" conversation under a first settings baseline before
  changing the settings — which is also what makes the assertion falsifiable
  (we know exactly what that conversation should still show).

## Test Data
### create-per-run
| Phase | Max Context Tokens | Preserve Recent Messages | Purpose |
|---|---|---|---|
| Baseline A | `32000` | `10` | values in force when the "previously existing" conversation is created |
| Case values (B) | `32000` (case step 2) | `3` (case step 2) | values in force when the NEW conversation is created |

`10` vs `3` is the discriminator: it must differ from the case's `3`, so the
step-7 assertion ("remain unchanged") cannot pass by accident.
- Conversation seed message: a short prompt (`"Reply with the single word OK."`).
  The conversation — and its context-strategy snapshot — is created by
  **sending**, not by the model answering (confirmed live: the `/chat/<id>`
  route and a 200 `GET /elitea_core/context_analytics/.../<id>` carrying
  `max_tokens: 32000` both landed before any answer arrived). The spec
  therefore never waits on an LLM answer — that keeps the known trigger-side
  LLM flakiness out of this case entirely.

## Test Steps
1. **Baseline A.** Navigate to `${BASE_URL}/settings/memory`; ensure Context
   Management is ON; read the current Max Context Tokens / Preserve Recent
   Messages (for teardown); set them to `32000` / `10`, each blur asserted via
   `PUT /api/v2/social/author/` → 200.
2. **Create the "previously existing" conversation.** Navigate to
   `${BASE_URL}/chat`, send the seed message, capture the conversation id from
   the `/chat/<id>` URL.
3. Expand the participants panel (`chat-participants-panel-toggle-button`;
   the Context Budget renders only while the panel is expanded — see
   § Automation Hints), wait for `context-budget-panel`, open the modal via
   `context-budget-edit-button`.
   - **Verify** (records the baseline for step 7):
     `context-modal-max-tokens-input` = `32000`,
     `context-modal-preserve-recent-input` = `10`,
     `context-modal-management-toggle` checked.
   - Close the modal **without saving** (the modal is per-conversation and
     has an explicit Save button — never click it here; that would rewrite
     the very value step 7 checks).
4. **Case steps 1–2 — apply the case's settings.** Back on
   `${BASE_URL}/settings/memory`: Context Management ON, Max Context Tokens
   `32000`, Preserve Recent Messages `3`; assert the autosave PUT → 200 for
   the changed field.
5. **Case step 3 — navigate away and back to confirm the values auto-saved.**
   Leave `/settings/memory` (to `/chat`) and return; **verify** the fields
   read `32000` / `3` after the round trip.
6. **Case step 4 — create a new conversation.** `${BASE_URL}/chat`, send the
   seed message, capture the new `/chat/<id>` (must differ from step 2's id).
7. **Case step 5 — verify the new conversation carries the configured
   values.** Expand the participants panel, wait for `context-budget-panel`,
   open the modal.
   - **Verify**: `context-modal-management-toggle` is **checked** (context
     management active), `context-modal-max-tokens-input` = `32000`,
     `context-modal-preserve-recent-input` = `3`.
   - Close without saving.
8. **Case step 6 — open the previously existing conversation** (step 2's id)
   via `${BASE_URL}/chat/<id>`.
9. **Case step 7 — verify its context management settings remain unchanged.**
   Expand the panel, open the modal.
   - **Verify**: `context-modal-preserve-recent-input` = `10` — the value in
     force when THAT conversation was created — and **not** the new global
     `3`; `context-modal-max-tokens-input` = `32000` (unchanged in both
     phases by design, so it must also be unchanged here);
     `context-modal-management-toggle` still checked.
   - Close without saving.

## Expected Results
- A conversation snapshots the user's context-management defaults **at
  creation time**.
- Changing the defaults afterwards affects only conversations created after
  the change; an existing conversation keeps its own values.
- Confirmed live end-to-end this session: conversation `9859` (created under
  `32000/10`) still showed `preserve = 10` after the global default was
  changed to `3`, while conversation `9860` (created after) showed
  `preserve = 3`.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | fixture | `auth_state` | asserted (implicitly, page loads) |
| 1 Navigate to Settings → Personalization → DEFAULT CONTEXT MANAGEMENT | Section loads | AFS step 4 | step 4: `context-management-section` visible | clarification *(live route is Settings → Memory; `/settings/personalization` 404s — tracked by EliteaAI/elitea-testing-public#1238)* |
| 2 Enable context management, Max Context Tokens 32000, Preserve Recent Messages 3 | Applied without error | AFS step 4 | step 4: toggle ON; both fields typed; autosave PUT → 200 | asserted |
| 3 Navigate away and back to confirm values were auto-saved | Values persisted | AFS step 5 | step 5: fields read `32000` / `3` after leaving and returning | asserted |
| 4 Create a new conversation | Created successfully | AFS step 6 | step 6: new `/chat/<id>` in the URL, distinct from the baseline conversation | asserted |
| 5 Verify the new conversation has context management active with the configured values | Active + configured | AFS step 7 | step 7: modal toggle checked, max `32000`, preserve `3` | asserted |
| 6 Open a previously existing conversation | Opens | AFS steps 2–3 (creates it) + 8 (reopens) | step 8: `/chat/<baseline id>` loads, panel renders | asserted |
| 7 Verify its context management settings remain unchanged | Unchanged | AFS step 9 | step 9: preserve `10` (its creation-time value, ≠ the new global `3`), max `32000`, toggle checked | asserted |

### Axis 2 — Analyst additions
- Steps 1–3 (baseline A + reading the baseline conversation's modal) —
  *added: the case says "open a previously existing conversation" but the
  account has none, and "unchanged" is unfalsifiable without a recorded
  before-value. Creating the conversation under a deliberately DIFFERENT
  Preserve Recent Messages (`10`) turns step 7 into a real discriminator.*
- "close the modal without saving" — *added: the per-conversation modal has
  an explicit Save button; clicking it would write the value the case is
  observing.*
- Asserting the autosave `PUT → 200` on the settings side — *added: the wait
  signal, and it makes step 3's "confirm auto-saved" a network fact rather
  than a re-read of React state.*

## Cleanup
- Delete both conversations created by the run (`conversation_api` fixture,
  as the neighbouring chat specs do).
- Restore Max Context Tokens / Preserve Recent Messages to the values read in
  step 1, and restore the Context Management toggle if the test flipped it.

## Concrete Handles (discovered during exploration)

| Element | Testid | PROVENANCE (verified 2026-08-28, fresh `git fetch origin`) | Notes |
|---|---|---|---|
| Context Management section / toggle | `context-management-section`, `context-management-toggle` | on-main ✓ | Settings side. |
| Max Context Tokens / Preserve Recent Messages | `max-context-tokens-input`, `preserve-recent-messages-input` | on-main ✓ | Settings side. |
| Chat message input | `chat-message-input` | on-main ✓ | Creates the conversation. |
| Participants panel toggle | `chat-participants-panel-toggle-button` | on-main ✓ | Carries `data-expanded` — state via a `data-*` attribute, the compliant shape. |
| Context Budget panel | `context-budget-panel` | on-main ✓ | Renders only with the participants panel expanded. |
| Edit context settings button | `context-budget-edit-button` | on-main ✓ | Opens the per-conversation modal. |
| Modal: Context Management toggle | `context-modal-management-toggle` | **on-`automation/testids` only (awaiting human promotion to main)** | Added in the ELITEA-2216 session, `EliteaAI/EliteaUI@69b103b2`. |
| Modal: Max Context Tokens | `context-modal-max-tokens-input` | on-main ✓ | |
| Modal: Preserve Recent Messages | `context-modal-preserve-recent-input` | on-main ✓ | |

No new testid work — every handle already exists; two of them are not yet on
`main`, which is a promotability note for the closure record, not a blocker
(the dev server serves `automation/testids`).

## Network Behavior
- Settings side: `PUT /api/v2/social/author/` → 200 per blur, then a `GET`
  refetch.
- Chat side: `GET /api/v2/elitea_core/context_analytics/prompt_lib/<project>/<conversationId>`
  → 200 feeds the Context Budget panel; the panel component renders `null`
  until it resolves. Response body carries `max_tokens`, confirming
  server-side (not client-side) inheritance of the setting.

## Known Defects Found During Exploration
- None new for this case. Route drift → existing clarification
  **EliteaAI/elitea-testing-public#1238**.
- Reported as a finding (not filed): the stale `@pytest.mark.skip` on
  `test_context_management.py::test_context_budget_reflects_profile_max_tokens`
  claims "Context management section removed from UI" — false today; the
  section lives at `/settings/memory`.

## Blocked Steps
- None. Every case step was executed live and observed.

## Automation Hints
- Framework: Playwright + pytest. New spec
  `automation/tests/ui/settings/test_context_settings_new_conversations_only.py`
  (settings feature, drives `ChatPage` for the chat half).
- **The Context Budget panel is unmounted while the participants panel is
  collapsed, and it starts collapsed on every fresh conversation load** —
  `Participants.jsx` renders it under `{conversationId && ...}` inside the
  panel body, and `ContextBudgetCollapsed` (the collapsed variant) carries
  none of the `context-budget-*` testids. Always call
  `ChatPage.expand_participants_panel_via_toggle()` first; a missing panel is
  otherwise indistinguishable from a product failure. *(Cost this session:
  several probes chasing a "missing" panel that was merely collapsed — now in
  the digest.)*
- `ChatPage` already models everything needed on the chat side
  (`expand_participants_panel_via_toggle`, `context_budget_panel`,
  `edit_context_button`, `context_modal_*` fields) — reuse, do not duplicate.
- `UserProfileSettingsPage` needs the additive `set_preserve_recent_messages()`
  helper introduced by the ELITEA-2376/2379 family AFS (same batch).
- Do **not** wait for an AI answer — the conversation exists as soon as the
  message is sent (see § Test Data).
- **Two navigation realities found during implementation (both cost a red run
  before they were understood):**
  1. `ChatPage.navigate_to_chat()` + `send_message()` does **not** reliably
     create a conversation — the SPA restores the last-viewed one, so the
     message lands in an EXISTING conversation (observed: step 4 re-used the
     conversation created moments earlier). The spec clicks **+Chat**
     (`click_create_conversation()`) and then verifies BOTH an id-less `/chat`
     URL and a zero message count before sending — a suite-local
     `_open_blank_composer()`, duplicated-with-attribution from
     `_open_genuinely_blank_conversation()` in
     `tests/ui/chat/test_team_users_mention_and_remove_participants.py`.
     **The restore is DELAYED**, so the blank state must be shown to *hold*
     across a settle window, not merely to be true at one instant: the helper
     carries the ancestor's `_poll_blank_state_holds()` verbatim (poll both
     signals at 250 ms across a 1500 ms window, exit the moment either flips).
     PR #1962 review round 1 blocked an earlier revision that substituted a
     fixed `page.wait_for_timeout(1500)` + one recheck for that poll — a
     `.agents/conventions.md` § Hard don'ts violation, and a shape that samples
     the window only at its end. Pinned by
     `automation/tests/unit/test_blank_composer_settle_is_polled.py`.
  2. `ChatPage.navigate_to_chat(conversation_id=X)` **cannot switch
     conversations**: it short-circuits with "already on chat page, skipping
     navigation" whenever the current URL contains `/chat`, so asking for
     conversation A while sitting on B silently leaves you on B. Added an
     ADDITIVE `ChatPage.open_conversation(conversation_id)` (navigates
     unconditionally, then verifies the route landed) rather than changing
     `navigate_to_chat()`, which has many merged callers relying on the skip.
