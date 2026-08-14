---
status: ready-for-automation
afs-version: "2025-02"
type: ui
surface: agent-hub
case-id: ELITEA-2360
fixtures: [auth_state, test_user]
---

# ELITEA-2360: Agent Hub — start conversation creates new chat and redirects to Chat page

**Priority:** L2 · **Type:** functional · **Surface:** Agent Hub / Chat

**Objective:** Verify that clicking "Start Chat" in an Agent Hub detail modal creates a new conversation and redirects to the Chat page, displaying the welcome message.

**Coverage:** Steps 1–6 from TMS case; assertion is on the chat welcome message presence and visibility.

---

## Coverage Map — per TMS case

| Axis 1: TMS step | Observable | Method/page object | Assertion | Notes |
|---|---|---|---|---|
| Precondition: User logged in | Auth state loaded | `conftest.auth_state` fixture | Implicit (fixture) | On localhost, `VITE_DEV_TOKEN` skips Keycloak; test user context inherited |
| Step 1: Navigate to Agent Hub | Page loads, Agents tab visible | `navigate_to_agent_hub()` | URL matches `/elitea-catalog` | No navigation barriers; agents tab is default when catalog loads |
| Step 2: Click agent card, open modal | Detail modal for agent appears | `click_agent_card(agent_name)` | Modal visible + agent name shown in modal header | Using "User Story Creator" as representative agent (per surface digest) — no special state required |
| Step 3: Click "Start Chat" button | Modal responds; navigation begins | `click_start_chat_button()` → resolves post-navigation | Implicit in Step 5 (redirect succeeds) | No intermediate state assertion; the button click is transient |
| Step 4: Verify new chat created | New conversation exists (backend consequence) | Implicit in Step 6 (message rendered means conversation exists) | URL contains conversation ID + chat greeting rendered | Conversation creation is a backend side-effect of sending the first message; this step verifies indirectly |
| Step 5: Verify redirect to Chat interface | Navigation from `/elitea-catalog` → `/chat` successful | `verify_redirected_to_chat_page()` | URL matches `/chat` (possibly with conversation ID query params) | Confirmed live: immediate redirect to `/chat` without intermediate pages |
| Step 6: Verify welcome message displayed | Chat welcome greeting visible + readable | `expect(page.locator(...)).to_be_visible()` + text match | `"Hello, {username}! What can I do for you today?"` textually present and visible | Confirmed live: "Hello, Test! What can I do for you today?" rendered in `chat-new-conversation-greeting` testid |

---

## Handles Reference

| Surface Element | Testid / Selector | Provenance | Notes |
|---|---|---|---|
| Agent Hub page / main view | `/elitea-catalog` (URL) | Live verified ELITEA-2360 | Entry point; no testid required (URL is the handle) |
| Agent card (list item, "User Story Creator" example) | `data-testid="catalog-agent-card-172"` | Live verified ELITEA-2360 | Feature-specific agent ID (172); card carries testid natively |
| Agent detail modal (root container) | `data-testid="catalog-agent-modal"` | Surface digest (ELITEA-2368) | Modal opens on card click; contains agent details + action buttons |
| "Start Chat" button | `data-testid="catalog-agent-modal-start-chat-button"` | Live verified ELITEA-2360 | Button in modal footer; triggers navigation + conversation creation |
| Chat page URL | `/chat` → `/chat/{conversation_id}?name=…` | Surface digest (ELITEA-2368) | Redirect target; name query param populated after first message |
| Welcome message greeting | `data-testid="chat-new-conversation-greeting"` | Surface digest (ELITEA-2368) | "Hello, {user}! What can I do for you today?" — confirmed as stable handle |

---

## Test Data

| Field | Value | Notes |
|---|---|---|
| Agent name | "User Story Creator" | Pre-existing in catalog; no special state required |
| Expected welcome text | "Hello, {username}! What can I do for you today?" | `{username}` interpolated per logged-in user; test verifies substring match |
| Login state | `auth_state` fixture (Keycloak on deployed, `VITE_DEV_TOKEN` on localhost) | Inherited from `conftest.auth_state`; test is agnostic to auth mechanism |

---

## Preconditions

- User is authenticated (implicit via `auth_state` fixture).
- Agent Hub catalog is accessible at `/elitea-catalog`.
- At least one agent (e.g., "User Story Creator") is available in the catalog.
- Chat page is reachable at `/chat`.

---

## Known Defects

- **#1043** — `AgentModal.jsx`'s "Start Chat" button (`onClick={onStartConversation()}`,
  line 277) reads `agentDetails.version_details.*` from a `useState(null)` populated
  by an async `getPublicApplicationDetail` fetch. Clicking while `agentDetails` is
  still `null` throws an uncaught TypeError inside the click handler — BEFORE the
  `dispatch(...)`/`navigate(...)` calls execute — so the click registers, no
  exception surfaces to Playwright, and the modal simply stays open with no
  navigation. Confirmed to be the root cause of the "Start Chat doesn't navigate"
  failure that blocked this case's prior implementation attempts (as well as
  ELITEA-2361/2362): those attempts clicked Start Chat immediately after
  `open_agent_by_name()` returned, with no extra wait for the async state to
  commit. `modal_show_instructions_link` (the ready-signal `open_agent_by_name()`
  waits on) is NOT sufficient — it renders unconditionally regardless of fetch
  status. No DOM signal distinguishes "agentDetails committed" from "still null".
  Already tracked (case previously named as an affected sibling per the surface
  digest / other AFS in this feature area). The declared workaround (test
  synchronization for an unobservable async gap, not defect masking) has now been
  moved into `AgentHubPage.click_start_chat()` itself so every caller gets it —
  see the method's docstring for the full analysis and the live-tested 200ms/300ms
  threshold.

---

## Amendments

- **2026-08-10 (implementation analysis):** Case flow confirmed live; handles verified against surface digest and live page. All testids match explorer findings.
- **2026-08-11 (implementer root-cause debug, ELITEA-2360 dispatch):** Root-caused
  the "Start Chat doesn't navigate" failure that blocked this case (and
  ELITEA-2361/2362) to known defect #1043 — see § Known Defects above. Confirmed
  via a scripted repro matching this suite's own `conftest.py` fixtures: **0/3**
  navigations succeed clicking Start Chat within ~200ms of the modal opening
  (deterministic silent no-op — screenshot evidence: modal remains fully open,
  `page.wait_for_url(r"/chat")` times out at 15000ms every time), **3/3** succeed
  with a 1s wait first. Fixed by moving the wait into
  `AgentHubPage.click_start_chat()` so it is no longer implementer-recall-dependent
  (all three prior broken attempts omitted the wait at the call site). Re-ran the
  three existing merged callers of `click_start_chat()` after the change
  (ELITEA-2368, ELITEA-2369, ELITEA-2075) to confirm no regression per the
  additive-only shared-file protocol.
