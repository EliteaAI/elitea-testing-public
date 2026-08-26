---
id: ELITEA-2425
title: Assistant receives current page context
status: ready-for-automation
priority: medium
type: functional
module: support-assistant
tms_case: ../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2425_assistant-receives-current-page-context.md
snapshot: .agents/automation/support-assistant-w02/cases/ELITEA-2425.md
analyst: qa-engineer (Sage)
analysis_date: 2026-08-22
sibling_afs: test-specs/support-assistant/l2_assistant-uses-correct-project-context_ELITEA-2424.md
surface_key: support-assistant-widget
---

# Automation-Friendly Spec: Assistant receives current page context

**TMS Case:** ELITEA-2425 · **Status:** `ready-for-automation` · **Priority:** medium (l2)
**Surface:** Support Assistant widget, driven from Agents / Pipelines / Agent-detail routes
**Environment:** `http://localhost:5173` — EliteaUI `automation/testids` + `elitea_assistant`
`automation/testids` (`VITE_ASSISTANT_LOCAL=1`), live DEV backend
**Analysis date:** 2026-08-22 (live, headless Chromium via a scripted Playwright probe)

---

## Executive Summary

Confirmed live: the widget sends the current route with **every** message, and the assistant answers
from it. Three questions, three correct answers:

| Route at send time | `support_assistant_context` sent | Reply (verbatim, trimmed) |
|---|---|---|
| `/agents/all` | `current_page: "/agents/all"` | *"You're on the /agents/all page. current_page in the runtime context is /agents/all, which is the Agents list page."* |
| `/pipelines/all` | `current_page: "/pipelines/all"` | *"You're on the /pipelines/all page. (…) which is the Pipelines list page."* |
| `/agents/all/894` | `current_page: "/agents/all/894"`, `current_entity_type: "agent"`, `current_entity_id: 894`, `current_entity_name: "Qtest_versionID"`, `selected_model: "gpt-5.6-luna"`, `meta.versionId: 1577` | *"You're viewing the agent Qtest_versionID. From the runtime context: current_entity_id: 894, entity_type: agent (…)"* |

Case step 7 asks the assistant to report the entity "**from the context payload**" — the payload is
literally observable on the outbound socket frame, so that step gets a mechanical assertion rather
than prose-matching.

The one implementation trap worth knowing up front: `current_entity_name` is resolved from the
**RTK-Query cache** (`findApplicationDetailsInCache` in
`EliteaUI/src/[fsd]/widgets/support-assistant/lib/hooks/useAssistantContext.hooks.js`), so the
detail query must have **resolved** before the message is sent, or the name field is simply absent
from the payload. Gate on the agent-detail form being populated, not on a timer.

---

## Coverage Map

### Axis 1 — every case element

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — Navigate to the Agents page (`/agents/all`) | Page loads | `goto("/agents/all")`, wait for the entity list | `entity-card-name` visible; `page.url` ends `/agents/all` | covered |
| Step 2 — Open the Support Assistant widget | Widget opens | Click `sidebar-support-assistant-button` | `support-assistant-widget` visible | covered |
| Step 3 — Send "What page am I currently on in the application?" | Completes without error | Type + send | User message item appears; a `support_predict` frame is emitted; no console errors | covered |
| Step 4 — Assistant references the Agents section or the correct current path | Reply names the page | (a) frame `current_page == "/agents/all"`; (b) reply text contains the value of `ctx["current_page"]` | Step 4 assertions | covered |
| Step 5 — Navigate to the Pipelines page and open the widget again | Page loads, widget reopens | `goto("/pipelines/all")`, re-click the launcher | `page.url` ends `/pipelines/all`; widget visible | covered |
| Step 6 — Same question now reports the Pipelines page context | Reply names the new page | Same two assertions with `/pipelines/all`, **plus** the new frame's `current_page != ` the previous one | Step 6 assertions | covered |
| Step 7 — Open a specific Agent detail page; send "What entity am I currently viewing?"; assistant reports the agent name/type **from the context payload** | Reply names the agent + type | frame `current_entity_type == "agent"`, `current_entity_id == <id from URL>`, `current_entity_name == <name in the detail form>`; reply text contains that name | Step 7 assertions | covered |

### Axis 2 — observables asserted beyond the case

| Observable | Why (grounded) | Asserted where |
|---|---|---|
| `current_page` equals `urlparse(page.url).path` (prefix-stripped) at each send | The case says "the correct current page path"; comparing against the live URL is the only independent ground truth (asserting a hardcoded string would still pass if the hook froze at mount) | Steps 4, 6, 7 |
| The context **changes** between two sends in the *same* conversation | The regression this case exists to catch is a stale/frozen context, which a single-page check cannot see | Step 6 |
| `current_entity_name` equals the name shown in `agent-name-input` | Ties the payload to what the user actually sees, rather than to the URL's `?name=` query param (which the app also carries and which could drift) | Step 7 |
| No console messages of type `error` | Standard side-channel check | Step 8 |

---

## Handles Reference

**Locator policy: testid-only.** Provenance verified 2026-08-22 (`git fetch origin` in both UI repos).

| Element | Handle | Repo / source | Provenance |
|---|---|---|---|
| Sidebar Support Assistant launcher | `sidebar-support-assistant-button` | EliteaUI `src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx` | on `automation/testids` (EliteaAI/EliteaUI@37176b46) — awaiting human cherry-pick |
| Widget window | `support-assistant-widget` | elitea_assistant | on `automation/testids` (EliteaAI/elitea_assistant@b8a287b) |
| Message input | `support-assistant-message-input` | elitea_assistant `src/components/chat/MessageInput.tsx` | on `automation/testids` (EliteaAI/elitea_assistant@b8a287b) |
| Send button | `support-assistant-send-button` | elitea_assistant `src/components/chat/MessageInput.tsx` | on `automation/testids` (EliteaAI/elitea_assistant@b8a287b) |
| Message item (`data-role="user"\|"assistant"`) | `support-assistant-message-item` | elitea_assistant `src/components/chat/MessageItem.tsx` | on `automation/testids` (EliteaAI/elitea_assistant@b8a287b) |
| Copy button on a completed reply — **the reply-ready signal** | `support-assistant-message-copy-button` | elitea_assistant `src/components/shared/CopyButton.tsx` | on `automation/testids` (EliteaAI/elitea_assistant@216da01) |
| Agent card name in the list (repeated) | `entity-card-name` | EliteaUI | **pre-existing** |
| Agent name on the detail page (the entity-name ground truth) | `agent-name-input` | EliteaUI | **pre-existing** |
| "New chat" button | `support-assistant-new-chat-button` | elitea_assistant `src/components/chat/ChatHeader.tsx` | **ADDED during ELITEA-2424 implementation** — EliteaAI/elitea_assistant@583b5dd on its `automation/testids` (canon #705) |

### Provenance verification (fresh `git fetch origin` in both repos, 2026-08-22)

```
$ cd ../EliteaUI && git fetch origin && for t in ...; do ...; done
sidebar-support-assistant-button     main:no   testids:YES
project-selector-trigger             main:YES  testids:YES
select-option-                       main:YES  testids:YES
project-general-section              main:YES  testids:YES
entity-card-name                     main:YES  testids:YES
agent-name-input                     main:YES  testids:YES

$ cd ../elitea_assistant && git fetch origin && for t in ...; do ...; done
support-assistant-widget                   main:no   testids:YES
support-assistant-message-input            main:no   testids:YES
support-assistant-send-button              main:no   testids:YES
support-assistant-message-item             main:no   testids:YES
support-assistant-message-copy-button      main:no   testids:YES
support-assistant-new-chat-button          main:no   testids:YES     <- ADDED during implementation
                                                                        (EliteaAI/elitea_assistant@583b5dd, 2026-08-22)
```

Consequence for the closure record: the widget testids are on `automation/testids` in **both**
repos but on neither `main`, so these tests are green on localhost and **not deployable-env
promotable** until a human cherry-picks (and, for the assistant, until EliteaUI bumps the
`@eliteaai/elitea-assistant` git-dependency — `.agents/workflow.md` § Connected repos).

### Existing page-object surface to reuse

`automation/pages/support_assistant_page.py` — testid-bound fields `sidebar_launcher`, `widget`,
`message_input_field`, `send_message_button`, `message_items`, `message_copy_buttons`, and the class
constants `ASSISTANT_MESSAGE_ITEM` / `USER_MESSAGE_ITEM`. Add the frame-capture helper here (shared
with ELITEA-2424) rather than in the specs.

### The frame capture (not a substitution — see § Fidelity Declaration)

```python
frames: list[str] = []
page.on("websocket", lambda ws: ws.on("framesent", lambda f: frames.append(f)))  # BEFORE first goto
```

Verified frame, agent-detail page:

```
42["support_predict",{"conversation_uuid":"…","content":"What entity am I currently viewing?",
 "support_assistant_context":{"project_id":406,"project_name":"Bugs & Features",
  "current_page":"/agents/all/894",
  "meta":{"tab":"all","versionId":1577,"browser":"…"},
  "current_entity_type":"agent","current_entity_id":894,
  "current_entity_name":"Qtest_versionID","selected_model":"gpt-5.6-luna"}}]
```

Event name is **`support_predict`** (not `predict` — the surface digest's older note is corrected
here). Parse `re.match(r'^\d+(\[.*\])$', frame)` → `json.loads` → `[event, payload]`.

**Payload contract, read from source** (`useAssistantContext.hooks.js`): `project_id`,
`project_name`, `current_page` (= `useLocation().pathname`) and `meta.browser` are always present;
entity fields are added per `pageType` — `ApplicationDetails` → `agent`, `PipelineDetails` →
`pipeline`, `ToolkitDetails`/`MCPDetails`/`AppDetails`/`CredentialDetails`/`Chat` each add their own
shape. `filterDefined` **drops undefined keys entirely**, so assert with
`ctx.get("current_entity_name")` rather than assuming the key exists on list pages.

---

## Fidelity Declaration

**No substitutions.** The context payload is built by EliteaUI and emitted by the assistant's own
socket; the test only **listens** (`page.on("websocket")` — passive, no `route`/`fulfill`, nothing
rewritten or delayed). The replies are live LLM output over the real backend (40.7 s / 41.2 s /
76.5 s observed today).

The nondeterministic producer is handled by the sanctioned pattern
(`.agents/testing.md` § How to test a NONDETERMINISTIC producer): the captured frame is the
**oracle**, and the reply is asserted against values read *out of that frame / the live DOM* —
never against authored strings:

```python
assert ctx["current_page"] in reply_text                    # value came from the product
assert ctx["current_entity_name"] == agent_name_from_form   # payload vs what the user sees
assert ctx["current_entity_name"] in reply_text
```

Typing uses `fill()` — real input events. A `page.evaluate` value assignment does **not** update the
React controlled textarea (surface digest quirk 4; it produced the false bug #1581).

---

## Preconditions

- Local UI on `http://localhost:5173` (EliteaUI `automation/testids`, `VITE_ASSISTANT_LOCAL=1`).
- `auth_state` (localhost: no login, `VITE_DEV_TOKEN`).
- The active project contains **at least one agent** (the test opens the first card). Verified live
  in project 406 *Bugs & Features* (first card `Qtest_versionID`, id 894). No agent is created or
  modified — read-only.

## Test Data

| Field | Value | Note |
|---|---|---|
| Page question | `"What page am I currently on in the application?"` | verbatim from the case |
| Entity question | `"What entity am I currently viewing?"` | verbatim from the case |
| Routes | `/agents/all`, `/pipelines/all`, `/agents/all/{id}` | the third is discovered at runtime by clicking the first `entity-card-name` |
| Reply timeout | `240_000` ms | observed today 40.7-76.5 s for these questions (digest range 31-135 s) |

**Conversation hygiene:** a *New chat* at the start keeps the transcript to this test's exchanges.
Note the deliberate live counter-observation: questions 2 and 3 were asked in the **same**
conversation that already held the `/agents/all` answer, and both still returned the **current**
page/entity — the context is re-sent per message, so a fresh chat is hygiene, not a requirement.
Never assert an absolute message count: the widget restores the previous conversation on open
(digest quirk 2).

---

## Step-by-step spec

> `allure.step("Step N — …")` around each block.

**Step 0 — arm the frame listener** before the first `goto` (see § Handles).

**Step 1 — Agents page.** `goto("/agents/all")`; wait for `entity-card-name` to be visible.
*Assert:* `page.url` path ends `/agents/all`.

**Step 2 — open the widget, fresh chat.** Click `sidebar-support-assistant-button`; wait for
`support-assistant-widget`. Click the New-chat button (once
`support-assistant-new-chat-button` exists).

**Step 3 — ask the page question.** Baseline `copy_count = message_copy_buttons.count()`;
`fill()` + click send.

**Step 4 — wait, then assert the Agents context.**
`expect(message_copy_buttons).to_have_count(copy_count + 1, timeout=240_000)` — the **only**
correct ready-signal. (The assistant message item mounts instantly with a `Starting up…`
placeholder, so an item-count wait returns before the answer exists — this cost one wasted probe
run today.)
Parse the last `support_predict` frame:
- `ctx["current_page"] == "/agents/all"` (and equals the live URL path)
- `ctx["current_page"] in last_assistant_message_text`

**Step 5 — Pipelines page.** `goto("/pipelines/all")`, wait for the list, re-open the widget
(a full page load closes it — the launcher click reopens and the conversation is restored).
*Assert:* `page.url` path ends `/pipelines/all`; widget visible.

**Step 6 — ask again, assert the context moved.** Repeat Step 3-4 with the same question.
*Assert:* `ctx["current_page"] == "/pipelines/all"`, it is **different** from the Step-4 value, and
the reply text contains it.

**Step 7 — Agent detail page + entity question.**
`goto("/agents/all")`, click the first `entity-card-name`, and capture
`agent_name = agent_name_input.input_value()` and `agent_id = int(path.rsplit("/", 1)[-1])` from the
URL.

> **Amended 2026-08-22 (implementer, Phase 2 — shipped truth).** The detail URL carries query
> params (`/agents/all/9433?viewMode=owner&name=Echo%20Agent`), so the id must be parsed from
> `urlparse(url).path`, not from the raw URL string. Shipped as
> `AgentsListPage.open_first_agent()` (additive), which clicks the shared `entity-card-name` testid
> and returns the parsed id — the legacy `select_agent(name)` resolves cards by a raw `text=`
> locator and is left byte-identical for its callers. **Wait for `agent-name-input` to hold a non-empty value before opening the widget** — that is
the observable proxy for "the `applicationDetails` query resolved", which is what populates
`current_entity_name` (see § Executive Summary).
Re-open the widget, ask the entity question, wait on the copy-button delta, then assert on the last
frame:
- `ctx["current_entity_type"] == "agent"`
- `ctx["current_entity_id"] == agent_id`
- `ctx["current_entity_name"] == agent_name`
- `ctx["current_page"] == f"/agents/all/{agent_id}"`
- `agent_name in last_assistant_message_text`

**Step 8 — side channel.** No console messages of type `error` for the whole test (the Vite
`Module "stream" has been externalized` message is a **warning**, already excluded by a
`type == "error"` filter — digest quirk 6).

---

## Cleanup

None — read-only. Two/three Support Assistant conversations are left behind (harmless; all counts
are deltas). The test leaves the browser on an agent detail page.

---

## Known Defects

None found. #1585 (filed from the sibling case ELITEA-2424 on 2026-08-18, "assistant echoes the
question, 403 on `project_info`") **did not reproduce** — every question in this run was answered
from the context payload. See the ELITEA-2424 AFS § Known Defects for the full non-repro evidence.

---

## Classification Rationale

**`ready-for-automation`.** All seven case steps executed live end-to-end; every observable has a
stable handle; the case's own wording ("from the context payload") points at an assertion target
that is directly and honestly observable.

**Not `already-covered` / `extend-existing`:** grepped the merged suite by behaviour —
`grep -rn "support_assistant_context\|current_page\|current_entity" automation/tests/ automation/pages/`
returns nothing. The seven merged support-assistant specs assert widget *mechanics* (open/close,
send/receive, history restore, copy, attachments, navigation persistence); none inspects the
outbound context payload or the reply's content. `test_support_assistant_navigation_persistence.py`
(ELITEA-2422) is the closest neighbour — it navigates between pages with the widget open — but it
asserts the widget *stays mounted*, never what context it sends.

**Not merged into a family AFS with ELITEA-2424:** the two differ in **steps** (route navigation +
entity detail vs sidebar project switching) and in the payload fields they assert, so per the
analyst contract's family test they stay separate specs. They share the frame-capture helper and the
reply-wait helper, which belong in `SupportAssistantPage`.

---

## Evidence

Under `test-results/screenshots/` (2026-08-22):

- `ELITEA-2425-step-03-agents.png` — reply on `/agents/all`
- `ELITEA-2425-step-06-pipelines.png` — reply on `/pipelines/all`
- `ELITEA-2425-step-07-agent-detail.png` — the agent detail page under test
- `ELITEA-2425-step-07-entity.png` — reply naming the agent

Captured frames (verbatim, live) — see the § Executive Summary table.

---

## Blocked Steps

None.

---

## Out of Scope

- Entity contexts other than `agent` (`pipeline`, `toolkit`, `mcp`, `app`, `credential`,
  `conversation` — all built by the same hook, none named by this case).
- `selected_model` / `selected_provider` (present on the payload; belongs to a chat-context case).
- The LLM's prose quality beyond "does it carry the payload's values through".
