# Test Case: Chat – Team Project – Non-Owner Cannot Edit Messages in Public Conversation

## Metadata
- **TMS ID**: ELITEA-2190
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; Team project "Elitea Testing Team", `projectId=471`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login (dev-token identity renders as "Test Bot"/"TB", confirmed live as `author_id: 659`)
- **Analyst**: qa-engineer (agent)
- **Status**: **blocked** — same shared precondition gap as ELITEA-2189/ELITEA-2191 (this is a 3-case cluster on the identical root cause): the case requires viewing a public conversation as a user who did NOT author it, and only one authenticated identity exists in this environment's test data. See § Blocked Steps.

## Preconditions
- User is logged in to the Elitea platform.
- **UNSATISFIABLE with current test data**: a second, distinct user identity that is a member of the same Team project and can view a public conversation owned by a different user. See § Blocked Steps.

## Test Data

| Field | Value |
|-------|-------|
| (none required by the case) | — |

## Test Steps

1. Open a public conversation owned by another user.
   - **Verify**: full history visible. **BLOCKED** — no conversation owned by any identity other than the current one is reachable (confirmed live via API; see § Blocked Steps).
2. Hover over any user message in the conversation.
   - Not reached — depends on step 1.
3. Verify non-owner cannot trigger edit mode on any message.
   - Not reached — depends on steps 1–2.

## Expected Results
- Non-owner cannot edit messages in a public conversation they don't own.
- Not verified — precondition unsatisfiable in current environment/test-data.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a public conversation owned by another user | Full history visible | step 1 | — | blocked *(no other-owned conversation exists in current test data — confirmed live via API)* |
| 2 Hover over any user message | No pencil (edit) icon appears | step 2 | — | blocked *(depends on step 1)* |
| 3 Verify edit mode not accessible | Edit mode not accessible | step 3 | — | blocked *(depends on steps 1–2)* |

### Axis 2 — Analyst additions
- None — no step was reachable to add assertions to.

## Cleanup
None performed — no test data was created (blocked before any action).

## Concrete Handles (discovered during exploration)

Per `.agents/testing.md` § Locator policy (testid-only, no fallback ladder). These
are the OWNER-side baseline handles confirmed live this session on the
account's own message ("hi", conversation `566`, "HI Chat") — reusable once a
second identity is provisioned; NOT yet confirmed from a non-owner's
perspective.

| Element | Testid / Handle | State |
|---|---|---|
| User message row (owner's own) | accessible name "Edit the message and regenerate answer" on a hover-revealed button — **confirmed live, no `data-testid` found via grep** for this specific pencil/edit-message icon (distinct from `click_table_edit_icon`/`click_diagram_edit_icon`, which target AI-generated table/diagram edit affordances, not user-message editing) | — |
| Copy button (user message) | `copy_message_button` `LocatorDescriptor(testid="message-copy-button")` — **existing but flagged in-file as a testid that "does not exist in source (pre-existing tech debt)", kept only via a forbidden `fallback=`** (`chat_page.py:519-523`) — do not reuse as-is; needs a real testid before use in new code, per `.agents/role-overrides.md` § Implementer slot ("`locator_descriptor.py`'s `locator=`/`fallback=` params are LEGACY … never valid in new code") | — |

**Gap for the implementer, once unblocked**: the user-message pencil/edit
icon has no confirmed `data-testid` in the page object or (per the comment at
`chat_page.py:531-537`) in EliteaUI source itself. `add-data-testid` work is
needed on this element regardless of the credential gap — flag both together
when this case is revisited (do not spend a second `add-data-testid` pass
without also having the second identity, since the edit-icon-ABSENT assertion
for a non-owner needs the identity to observe against).

## Network Behavior
- Not observed — no non-owner session was reachable.

## Known Defects Found During Exploration
None found — no product behavior under test was exercised (blocked before
any action under test). Note (not a defect, a pre-existing page-object
tech-debt flag surfaced while documenting handles above): `copy_message_button`
and `regenerate_button` (`chat_page.py:519-529`) point at testids that do not
exist in EliteaUI source and are kept alive only via `fallback=` role/aria-label
lookups — forbidden in new code per current locator policy. Not filed as a new
issue (pre-existing, already commented in-file as known tech debt by a prior
pass); flagged here only because this AFS's § Concrete Handles touches the
same element family.

## Blocked Steps

**All case steps are blocked on the same shared precondition documented in
ELITEA-2189's AFS** (`test-specs/chat-interface/l2_non-owner-cannot-delete-public-conversation_ELITEA-2189.md`
§ Blocked Steps) — no second real-user identity exists to act as the
"non-owner" viewing this case's public conversation. Full investigation
(credential check, live API query proving every reachable conversation in
project 471 has the SAME `author_id`, rejected-workaround list) is not
repeated here verbatim; see that file for the complete write-up. Both cases
were investigated in the same live session and hit the identical wall.

**Filed**: [Question #1563](https://github.com/EliteaAI/elitea-testing-public/issues/1563)
— covers this case together with ELITEA-2189/ELITEA-2191 (one shared root
cause, one issue, per the precedent set by #1314 for the analogous
RBAC-role credential gap).

## Automation Hints
- Framework: Playwright/pytest, testid-only locators (`.agents/testing.md` §
  Locator policy).
- Page object: `automation/pages/chat_page.py` — the user-message edit-icon
  handle needs `add-data-testid` work (see § Concrete Handles gap) in
  addition to the credential provisioning; do both before re-running this
  analysis.
- Once a second identity is provisioned (issue #1563), re-run this analysis:
  have `${TEST_USER}` create + make public a conversation with at least one
  user message, switch session to the second identity, hover the message,
  and confirm the edit-icon's absence (or disabled state) directly.
