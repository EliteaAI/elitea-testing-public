# Test Case: Chat – Team Project – Non-Owner Cannot Regenerate LLM Response in Public Conversation

## Metadata
- **TMS ID**: ELITEA-2191
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; Team project "Elitea Testing Team", `projectId=471`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login (dev-token identity renders as "Test Bot"/"TB", confirmed live as `author_id: 659`)
- **Analyst**: qa-engineer (agent)
- **Status**: **blocked** — same shared precondition gap as ELITEA-2189/ELITEA-2190 (this is a 3-case cluster on the identical root cause): the case requires viewing a public conversation as a user who did NOT author it, and only one authenticated identity exists in this environment's test data. See § Blocked Steps.

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
2. Hover over the last LLM response.
   - Not reached — depends on step 1.
3. Verify regenerate icon NOT present in response action icons.
   - Not reached — depends on steps 1–2.
4. Verify only speaker and copy icons are available for non-owner.
   - Not reached — depends on steps 1–3.

## Expected Results
- Non-owner has no Regenerate control on another user's LLM responses in a public conversation.
- Not verified — precondition unsatisfiable in current environment/test-data.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a public conversation owned by another user | Full history visible | step 1 | — | blocked *(no other-owned conversation exists in current test data — confirmed live via API)* |
| 2 Hover over the last LLM response | (hover to reveal icons) | step 2 | — | blocked *(depends on step 1)* |
| 3 Verify Regenerate NOT visible | No regenerate icon | step 3 | — | blocked *(depends on steps 1–2)* |
| 4 Verify only speaker + copy icons present | Only speaker/copy present | step 4 | — | blocked *(depends on steps 1–3)* |

### Axis 2 — Analyst additions
- None — no step was reachable to add assertions to.

## Cleanup
None performed — no test data was created (blocked before any action).

## Concrete Handles (discovered during exploration)

Per `.agents/testing.md` § Locator policy (testid-only, no fallback ladder). These
are the OWNER-side baseline handles confirmed live this session against the
account's own AI response ("Hi! How can I help?", conversation `566`, "HI
Chat") — reusable once a second identity is provisioned; NOT yet confirmed
from a non-owner's perspective (the case's claim is that the non-owner sees a
SUBSET of these — speaker + copy only, no regenerate — which cannot be
verified without the second identity).

| Element | Testid / Handle | State |
|---|---|---|
| "Read out" (speaker) icon | accessible name "Read out" — confirmed live on the owner's AI response, hover-revealed | — |
| Copy-to-clipboard (AI response) | `chat-copy-button` `LocatorDescriptor(testid="chat-copy-button")` — existing, confirmed-live real testid (ELITEA-2181), preferred over the legacy `copy_message_button`/`message-copy-button` fallback-only field | — |
| Regenerate (AI response) | `chat-regenerate-button` `LocatorDescriptor(testid="chat-regenerate-button")` — existing, confirmed-live real testid (ELITEA-2181), preferred over the legacy `regenerate_button`/`message-regenerate-button` fallback-only field | — |
| Delete (AI response) | accessible name "Delete" — confirmed live on the owner's AI response, hover-revealed; no dedicated `LocatorDescriptor` found via grep for this specific per-message delete affordance (distinct from the conversation-level `delete-confirm-*` dialog) | — |

**Note on the case's own scope**: the case's step 4 ("only speaker and copy
icons are available") does not mention Delete — live, the OWNER's response
action row shows FOUR icons (Read out / Copy / Regenerate / Delete), not the
two the case's non-owner expectation names. Whether Delete is also hidden for
a non-owner (consistent with the case's "limited options" theme across this
whole 3-case cluster) or is a case-text gap is exactly the kind of thing that
can only be confirmed once the second identity exists — flag for the
implementer to verify Delete's visibility too when this is unblocked, not
just the two icons the case text names.

## Network Behavior
- Not observed — no non-owner session was reachable.

## Known Defects Found During Exploration
None found — no product behavior under test was exercised (blocked before
any action under test).

## Blocked Steps

**All case steps are blocked on the same shared precondition documented in
ELITEA-2189's AFS** (`test-specs/chat-interface/l2_non-owner-cannot-delete-public-conversation_ELITEA-2189.md`
§ Blocked Steps) — no second real-user identity exists to act as the
"non-owner" viewing this case's public conversation. Full investigation
(credential check, live API query proving every reachable conversation in
project 471 has the SAME `author_id`, rejected-workaround list) is not
repeated here verbatim; see that file for the complete write-up. All three
cases in this cluster were investigated in the same live session and hit the
identical wall.

**Filed**: [Question #1563](https://github.com/EliteaAI/elitea-testing-public/issues/1563)
— covers this case together with ELITEA-2189/ELITEA-2190 (one shared root
cause, one issue, per the precedent set by #1314 for the analogous
RBAC-role credential gap).

## Automation Hints
- Framework: Playwright/pytest, testid-only locators (`.agents/testing.md` §
  Locator policy).
- Page object: `automation/pages/chat_page.py` already has confirmed-live
  real testids for copy/regenerate (`chat-copy-button`/`chat-regenerate-button`,
  ELITEA-2181) — reuse those, not the legacy fallback-only fields. The
  per-message Delete icon has no confirmed testid — flag alongside the
  credential gap for `add-data-testid` work when this is revisited.
- Once a second identity is provisioned (issue #1563), re-run this analysis:
  have `${TEST_USER}` create + make public a conversation with at least one
  completed AI response, switch session to the second identity, hover the
  response, and confirm the regenerate icon's absence (and check Delete's
  visibility too — see § Concrete Handles note) directly.
