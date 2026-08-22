---
id: ELITEA-2424
title: Assistant uses correct project context
status: ready-for-automation
priority: medium
type: functional
module: support-assistant
tms_case: ../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2424_assistant-uses-correct-project-context.md
snapshot: .agents/automation/support-assistant-w02/cases/ELITEA-2424.md
analyst: qa-engineer (Sage)
analysis_date: 2026-08-22
supersedes: "the 2026-08-18 `defect-found` analysis of this same case (commit 597793d24) — #1585 did NOT reproduce today; see § Known Defects"
known_defects: ["#1585 — OPEN but NOT reproducing as of 2026-08-22; commented, not closed (agents never close)"]
surface_key: support-assistant-widget
---

# Automation-Friendly Spec: Assistant uses correct project context

**TMS Case:** ELITEA-2424 · **Status:** `ready-for-automation` · **Priority:** medium (l2)
**Surface:** Support Assistant widget + sidebar project selector
**Environment:** `http://localhost:5173` — EliteaUI `automation/testids` + `elitea_assistant`
`automation/testids` (`VITE_ASSISTANT_LOCAL=1`), live DEV backend
**Analysis date:** 2026-08-22 (live, headless Chromium via a scripted Playwright probe)

---

## Executive Summary

The Support Assistant **does** receive and use the current project context. Verified live today
across two project switches: the widget emits a Socket.IO `support_predict` frame whose
`support_assistant_context` carries `project_id` / `project_name` taken from the sidebar's selected
project, and the assistant's reply names that project ID back.

The case is fully automatable, with one important design decision the implementer must respect:

> **Assert on `project_id`, not on the reply's project *name*.**
> Observed live: for the personal ("Private", id 399) project the assistant answered
> `Project name: project_user_659 / Project ID: 399` on one run and
> `Project name: Private / Project ID: 399` on another — the backend sometimes resolves the
> personal project to its internal name while the UI label stays "Private". The **ID was correct
> and stable in 3/3 project questions**. For team projects the name matched exactly
> (`Bugs & Features` / 406). The project *name* is asserted against the **outbound context frame**
> (deterministic, UI-produced), never against the LLM prose.

The case's distinguishing requirement — "NOT the internal Support Assistant deployment project" —
is directly observable: the same socket carries `chat_enter_room` with the **support deployment**
project (`project_id: 536`, not a project in this user's selector list) while
`support_assistant_context.project_id` carries the **user's** project (399 / 406). Asserting the
two differ is a real, system-produced check of exactly what the case asks.

**Note for the previous analysis:** this case was returned `defect-found` on 2026-08-18, blocked by
**#1585** ("403 Forbidden on project_info, assistant echoes the question"). Today the echo behaviour
**did not reproduce at all** — 3/3 project questions answered correctly, and a dedicated
response-listener probe recorded **zero 4xx/5xx responses** across page load, widget open and a full
question/answer round trip. See § Known Defects.

---

## Coverage Map

### Axis 1 — every case element

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — Navigate to a project other than the Support Assistant's own deployment project | Target page loads | Switch the sidebar project selector to project **A** (`select-option-<A>`), land on `/settings/project-general` | Trigger text shows A's name; the support deployment project (536) is not in the selector list at all | covered |
| Step 2 — Note the current project name shown in Settings | Action completes | Read the sidebar trigger text + `project-general-section` | `project-selector-trigger-combobox` text contains A's name | covered |
| Step 3 — Open the Support Assistant widget | Widget opens | Click `sidebar-support-assistant-button` | `support-assistant-widget` visible | covered |
| Step 4 — Send "What project am I currently working in? What is the project name and project ID?" | Action completes, no error | Type into `support-assistant-message-input`, click `support-assistant-send-button` | A new user message item appears; a `support_predict` frame is emitted; no console errors | covered |
| Step 5 — Assistant responds with the project name and ID matching the project being browsed, **NOT** the internal Support Assistant deployment project | Reply reflects project A | (a) captured frame `support_assistant_context.project_id == A` and `.project_name == trigger text`; (b) reply text contains `str(A)`; (c) frame's context project_id **≠** the `chat_enter_room` project_id (the support deployment project) | Steps 4-5 assertions | covered |
| Step 6 — Navigate to a different project and repeat steps 3-5; assistant reflects the new project context | Reply reflects project B | Switch to `select-option-<B>`, re-open widget, re-ask; same three assertions with B; plus `B != A` | Steps 6-8 assertions | covered |

### Axis 2 — observables asserted beyond the case

| Observable | Why (grounded) | Asserted where |
|---|---|---|
| `support_assistant_context.project_id` on the outbound `support_predict` frame equals the project the test selected | The deterministic, system-produced form of the case's whole claim; the LLM prose is the downstream consumer of exactly this value | Steps 5, 8 |
| `support_assistant_context.project_id` ≠ `chat_enter_room.project_id` | The case's explicit "NOT the internal deployment project" clause, made mechanical (observed: 399/406 vs 536) | Steps 5, 8 |
| `support_assistant_context.current_page` equals the current route | Rides along on the same frame at zero cost and pins the frame to the moment of sending (ELITEA-2425 owns the page-context case; here it is only a frame-integrity check) | Steps 5, 8 |
| No console **errors** during the flow | Standard side-channel check; this is the surface where #1585 was originally reported from a console 403 | Step 9 |

---

## Handles Reference

**Locator policy: testid-only.** Provenance verified 2026-08-22 with `git fetch origin` in both
`../EliteaUI` and `../elitea_assistant`.

| Element | Handle | Repo / source | Provenance |
|---|---|---|---|
| Sidebar Support Assistant launcher | `sidebar-support-assistant-button` | EliteaUI `src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx` | on `automation/testids` (EliteaAI/EliteaUI@37176b46) — awaiting human cherry-pick to main |
| Widget window | `support-assistant-widget` | elitea_assistant | on its `automation/testids` (EliteaAI/elitea_assistant@b8a287b) |
| Message input | `support-assistant-message-input` | elitea_assistant `src/components/chat/MessageInput.tsx` | on `automation/testids` (EliteaAI/elitea_assistant@b8a287b) |
| Send button | `support-assistant-send-button` | elitea_assistant `src/components/chat/MessageInput.tsx` | on `automation/testids` (EliteaAI/elitea_assistant@b8a287b) |
| Message item (repeated, `data-role="user"\|"assistant"`) | `support-assistant-message-item` | elitea_assistant `src/components/chat/MessageItem.tsx` | on `automation/testids` (EliteaAI/elitea_assistant@b8a287b) |
| Copy button on a **completed** assistant reply — **the reply-ready signal** | `support-assistant-message-copy-button` | elitea_assistant `src/components/shared/CopyButton.tsx` | on `automation/testids` (EliteaAI/elitea_assistant@216da01) |
| Sidebar project selector trigger | `project-selector-trigger-combobox` | EliteaUI `src/[fsd]/widgets/sidebar-root/ui/SidebarProjectSelect.jsx:94` (`ProjectSelect` appends `-combobox`) | **pre-existing**, already used by `AdminUsersPage` / `AnalyticsPage` — verify on main at closure |
| Project option in the dropdown (dynamic) | `[data-testid="select-option-{project_id}"]` | EliteaUI `src/[fsd]/shared/ui/select/SingleSelectMenuItem.jsx:117` | **pre-existing** |
| Settings ▸ General project section | `project-general-section` | EliteaUI `src/[fsd]/features/settings/ui/project-general/ProjectGeneralContent.jsx:30` | **pre-existing** |
| "New chat" button (optional, see § Test Data) | **testid needed: `support-assistant-new-chat-button`** | elitea_assistant `src/components/chat/ChatHeader.tsx:83` (currently only `aria-label="New chat"`) | **needs-adding** — connected first-party repo, canon #705: add it in `elitea_assistant` on ITS `automation/testids`, never a raw handle |

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
support-assistant-new-chat-button          main:no   testids:no      <- needs adding
```

Consequence for the closure record: the widget testids are on `automation/testids` in **both**
repos but on neither `main`, so these tests are green on localhost and **not deployable-env
promotable** until a human cherry-picks (and, for the assistant, until EliteaUI bumps the
`@eliteaai/elitea-assistant` git-dependency — `.agents/workflow.md` § Connected repos).

### Existing page-object surface to reuse

`automation/pages/support_assistant_page.py` already has testid-bound
`LocatorDescriptor` fields: `sidebar_launcher`, `widget`, `message_input_field`,
`send_message_button`, `message_items`, `message_copy_buttons`, plus the class constants
`ASSISTANT_MESSAGE_ITEM` / `USER_MESSAGE_ITEM` / `MESSAGE_COPY_BUTTON`. The project-selector
pattern is already implemented twice — `AnalyticsPage.switch_project()`
(`automation/pages/analytics_page.py:689`, with `SELECT_OPTION = '[data-testid="select-option-{}"]'`
at line 402) and `AdminUsersPage.switch_project()`. **Reuse that shape**; don't invent a third.

### The frame capture (not a substitution — see § Fidelity Declaration)

```python
# register BEFORE the first navigation — page.on("websocket") only fires for
# sockets opened after it is attached (surface digest quirk 8)
frames: list[str] = []
page.on("websocket", lambda ws: ws.on("framesent", lambda f: frames.append(f)))
```

Socket.IO frame shape, verified live:

```
42["support_predict",{"conversation_uuid":"…","content":"What project am I…",
   "support_assistant_context":{"project_id":406,"project_name":"Bugs & Features",
   "current_page":"/settings/project-general","meta":{"browser":"…"}}}]
42["chat_enter_room",{"project_id":536,"conversation_id":"…"}]
```

The event name is **`support_predict`**, NOT `predict` (the surface digest's older note said
`predict`; the assistant build serving localhost today emits `support_predict` — filtering on
`predict` as a substring still matches both). Parse with
`re.match(r'^\d+(\[.*\])$', frame)` → `json.loads` → `[event, payload]`.

**Where the payload comes from** (read the source, don't guess):
`EliteaUI/src/[fsd]/widgets/support-assistant/lib/hooks/useAssistantContext.hooks.js` builds it from
`useSelectedProjectId()` / `useSelectedProjectName()` / `useLocation()`, and
`ui/SupportAssistant.jsx:43` passes it as the `supportAssistantContext` prop into
`<EliteaAssistant>`; the assistant emits it at
`elitea_assistant/src/lib/hooks/chat.hook.ts:527`.

---

## Fidelity Declaration

**No substitutions.** Every asserted value is produced by the system:

| Observable | Producer |
|---|---|
| `support_assistant_context` payload | EliteaUI's `useAssistantContext` hook → the assistant's own socket emit. The test only **listens** to the frame the product sent. |
| Assistant reply text | The live LLM over the real backend (33-77 s round trips observed today). |
| Project name shown in the sidebar / Settings | The live UI. |

`page.on("websocket")` is **passive observation**, not `page.route`/`route.fulfill` — nothing is
intercepted, delayed, rewritten or fabricated. It is the same class of evidence as reading a
response body.

**Nondeterministic producer handled by the sanctioned pattern**
(`.agents/testing.md` § How to test a NONDETERMINISTIC producer): the captured context frame is the
**oracle**, and the LLM reply is asserted *against values taken from that frame* — never against a
hand-written payload:

```python
assert str(ctx["project_id"]) in reply_text      # the number came from the frame, not from us
```

---

## Preconditions

- Local UI up on `http://localhost:5173` (EliteaUI `automation/testids`, `VITE_ASSISTANT_LOCAL=1`
  so `../elitea_assistant` is served live) — `start-ui-localhost` skill.
- `auth_state` (localhost: no login, `VITE_DEV_TOKEN`).
- The acting user belongs to **at least two** projects. Verified live today, this user has 5:
  `399 Private` (personal), `406 Bugs & Features`, `25 Elitea Development`,
  `471 Elitea Testing Team`, `400 UI Testing`.

## Test Data

| Field | Value | Note |
|---|---|---|
| Project A | `settings.users_team_project_id` (default `"400"` — *UI Testing*) | config-driven; a **team** project, so its name is stable in both UI and backend |
| Project B | `settings.elitea_team_project_id` (`471` — *Elitea Testing Team*) | second config-driven team project; must differ from A |
| Question | `"What project am I currently working in? What is the project name and project ID?"` | verbatim from the case |
| Reply timeout | `240_000` ms | observed today: 77.0 s, 77.0 s for this question (digest range 31-135 s) |

**Why config projects, not the observed 399/406 pair:** the IDs above are already the suite's
configured team projects. The *mechanism* is project-agnostic (the context comes straight from the
Redux selected-project selectors), and it was verified live on 399 → 406. Should a configured
project be unavailable at implementation time, deriving A and B at runtime from the open dropdown's
`select-option-*` testids is an equally valid, env-agnostic fallback (that is what this analysis
did).

**Avoid the personal ("Private") project as A or B** — see § Executive Summary: the assistant
sometimes resolves it to its internal name (`project_user_659`). Using team projects keeps the
optional name assertion honest.

**Conversation hygiene:** each question should be asked in a **fresh** session (click *New chat*
after opening the widget) so a stale answer about the previous project cannot be mistaken for the
current one. The widget restores the previous conversation on open — never assert an absolute
message count. (Live counter-observation, worth knowing: asking on `/pipelines/all` **without** a
new chat, in a conversation that already contained an `/agents/all` answer, still produced the
correct *current* answer — the context is re-sent per message. A fresh chat is belt-and-braces, not
a workaround.)

---

## Step-by-step spec

> `allure.step("Step N — …")` around each block (mandatory, `.agents/testing.md` § Step reporting).

**Step 0 — arm the frame listener.** Register `page.on("websocket")` **before** the first
`goto`. Keep the raw frame list; parse lazily.

**Step 1 — switch to project A.** Navigate to `/settings` (lands on `/settings/project-general`),
click `project-selector-trigger-combobox`, click `[data-testid="select-option-{A}"]`, wait for the
network to settle.
*Assert:* the trigger text contains project A's name; `project-general-section` is visible.
Capture `project_a_name = trigger.inner_text()`.

**Step 2 — open the widget and start a fresh chat.** Click `sidebar-support-assistant-button`;
`support-assistant-widget` becomes visible. Click the New-chat button
(`support-assistant-new-chat-button` once added).
*Assert:* the widget is visible.

**Step 3 — ask the project question.** Baseline
`copy_count = message_copy_buttons.count()`. `fill()` the question into
`support-assistant-message-input` (**real typing only** — a `page.evaluate` value assignment does
not update the React state, digest quirk 4) and click `support-assistant-send-button`.

**Step 4 — wait for the completed reply.**
`expect(message_copy_buttons).to_have_count(copy_count + 1, timeout=240_000)`.
This is the correct ready-signal: the assistant message item mounts **immediately** with a
`Starting up…` placeholder, so waiting on the item count returns before the answer exists (this
cost one wasted probe run today). The copy button renders only on a *completed* assistant response.

**Step 5 — assert project A context.** Parse the **last** `support_predict` frame:
- `ctx["project_id"] == int(A)`
- `ctx["project_name"] == project_a_name`
- `ctx["project_id"] != enter_room_project_id` (the support deployment project; parse the last
  `chat_enter_room` frame — observed `536`, which is not in this user's selector list)
- `str(A) in last_assistant_message_text` — the LLM reply names the same ID it was given.

**Step 6 — switch to project B.** Repeat Step 1 with B. *Assert:* trigger text contains B's name
and `B != A`.

**Step 7 — re-open the widget, fresh chat, ask again.** Repeat Steps 2-4.

**Step 8 — assert project B context.** Repeat Step 5's four assertions with B, and additionally
assert the newly captured `ctx["project_id"] != int(A)` — i.e. the context actually *changed*,
which is the whole point of case step 6.

**Step 9 — side channel.** No console messages of type `error` for the whole test (filter out the
Vite `Module "stream" has been externalized` **warning**, digest quirk 6 — it is a warning, not an
error, so a `type == "error"` filter already excludes it).

---

## Cleanup

None required. The test leaves two Support Assistant conversations behind (harmless — the widget
restores whatever exists, and every count assertion is a delta). It leaves the sidebar on project B;
if a later test in the same session assumes the default project, switch back to A or let each test
set its own project as this one does.

---

## Known Defects

- **#1585** — *"Support Assistant cannot access project context — 403 Forbidden on project_info API,
  echoes questions instead of answering"* (OPEN, filed 2026-08-18 from this very case).
  **Did NOT reproduce on 2026-08-22.** Evidence gathered today:
  - 3/3 project questions answered correctly with the right project ID (399, 406, 399), across two
    projects and two separate browser sessions.
  - A dedicated `page.on("response")` probe recording every `status >= 400` saw **zero** failing
    responses across page load, widget open, and a complete question → answer round trip.
  - Two console `403` errors *were* seen in the longer multi-page probe (which also visited
    `/settings/project-general` and switched projects), but they did not block any answer and did
    not recur in the assistant-only probe. Their URLs were not captured — the console API does not
    expose them.

  **Action taken:** a non-repro comment was added to #1585 with today's evidence. The issue was
  **not closed** (agents never close — `.agents/profile.md`). This AFS therefore classifies
  `ready-for-automation`, not `defect-found`: nothing blocks the case today. If the implementer's
  run hits the echo behaviour again, that is a resurrection of #1585 and the case goes `blocked`.

---

## Classification Rationale

**`ready-for-automation`.** Every case step executed live end-to-end today; every observable the
case asks for has a stable, system-produced handle; the only element that could have blocked it
(#1585) does not reproduce. No substitution is needed anywhere: the nondeterministic LLM is handled
by asserting the reply against the captured context frame rather than against authored values.

**Not `extend-existing`:** the merged support-assistant specs
(`test_support_assistant_smoke.py`, `…_navigation_persistence.py`, `…_history_after_refresh.py`,
`…_copy_response.py`, `…_attachment_send.py`, `…_drag_drop_attachment.py`,
`…_empty_message.py`) all assert widget mechanics — open/close, send/receive, history, copy,
attachments. **None reads `support_assistant_context`, none touches the project selector, and none
asserts anything about the reply's *content*.** Grepped by behaviour:
`grep -rn "support_assistant_context\|project_id\|switch_project" automation/tests/ui/support_assistant/` → no hits.

**Not a family AFS with ELITEA-2425:** the two cases differ in **steps**, not only in data —
2424 switches the sidebar project selector and asserts `project_id` / `project_name`; 2425 changes
routes and opens an entity detail page, asserting `current_page` / `current_entity_*`. Per the
analyst contract's family test ("merge only what differs in data"), they get separate specs. They
do share the whole widget/frame-capture apparatus, which belongs in the page object.

---

## Evidence

All under `test-results/screenshots/` (this analysis run, 2026-08-22):

- `ELITEA-2424-step-01-project-options.png` — the 5-project selector dropdown open
- `ELITEA-2424-step-02-settings.png` — Settings ▸ General for project A
- `ELITEA-2424-step-04-project-a.png` — reply for project 399 (`Project ID: 399`)
- `ELITEA-2424-step-06-switched.png` — sidebar after switching to 406
- `ELITEA-2424-step-06-project-b.png` — reply for project 406 (`project_id: 406`)

Captured frames (verbatim, live):

```
{"project_id": 399, "project_name": "Private",         "current_page": "/settings/project-general", …}
{"project_id": 406, "project_name": "Bugs & Features", "current_page": "/settings/project-general", …}
```

Replies (verbatim, live):

```
You're currently working in:  Project name: project_user_659  Project ID: 399
  (…) The UI context label Private is just the display/project space label (…)
You're currently in:          project_name: Bugs & Features   project_id: 406
You're working in project Private.  Project name: Private  Project ID: 399     (second session)
```

---

## Blocked Steps

None.

---

## Out of Scope

- The *quality* of the LLM's prose (only "does it carry the ID through" is asserted).
- The Support Assistant's own deployment project configuration (`support_project_id`) beyond the
  inequality assertion.
- Non-project fields of the context payload (`current_entity_*`, `selected_model`) — ELITEA-2425.
