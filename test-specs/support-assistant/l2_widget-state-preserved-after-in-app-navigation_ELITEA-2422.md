# Test Case: Widget state preserved after in-app navigation

## Metadata

- **TMS ID**: ELITEA-2422
- **Source case**: `.agents/automation/support-assistant-w01/cases/ELITEA-2422.md`
  (intake snapshot of `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2422_widget-state-preserved-after-in-app-navigation.md`)
- **Priority**: l2 (case priority `medium` → `p2` marker)
- **Module**: support-assistant · **Type**: functional
- **Environment Explored**: local `http://localhost:5173` — EliteaUI on `automation/testids`,
  connected assistant repo aliased live (`VITE_ASSISTANT_LOCAL=1`), DEV backend via `VITE_DEV_TOKEN`
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token)
- **Analyst**: qa-engineer (Sage) · **Run date**: 2026-08-22
- **Batch**: `support-assistant-w01`
- **Status**: **ready-for-automation**

> ⚠️ **This AFS SUPERSEDES the 2026-08-18 `defect-found` version** of the same file
> (commit `a77917f1f`), which was blocked at Step 2 by issue **#1581** ("Send button never
> enables"). #1581 is a **non-reproducing false bug** — it was an artefact of synthetic
> `input.value = …` writes against a React controlled `<textarea>`, not product behaviour
> (surface digest quirk 4; #1581 already carries two "does not reproduce" comments and is
> now contradicted by the green ELITEA-2418 spec). **Re-verified a third time in this run:**
> real typing enabled Send immediately (`disabled: false`) and both messages sent and were
> answered. Nothing in this case is blocked.

---

## Classification

`ready-for-automation` — fresh spec, **no new testids required** (every handle already exists
on the integration branches), no page-object additions strictly required beyond one optional
convenience helper.

**Why not `already-covered` / `extend-existing`.** The closest merged spec is
`automation/tests/ui/support_assistant/test_support_assistant_smoke.py::TestSupportAssistantLauncher::test_widget_state_persists_after_close_reopen`
(lines 89-127) — it proves persistence across a **widget close/reopen toggle** while the
route never changes. ELITEA-2422's observable is a different trigger and a stronger claim:
persistence across **React-Router in-app navigation** (`/chat` → `/agents/all` → `/chat`)
**without** closing the widget, including that the widget stays *mounted and open* through
the route change. No merged spec navigates anywhere while the widget is open — verified:
`grep -rn "navigat" automation/tests/ui/support_assistant/` returns only the
`navigate_to_chat()` call each test opens with. Different trigger ⇒ different regression;
a route-level unmount would sail past the close/reopen test.

---

## Preconditions

- User authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed: `auth_state` fixture).
- Support Assistant feature enabled — `ELITEA_ASSISTANT_ENABLED` truthy. Confirmed live: the
  sidebar launcher renders and `onToggleAssistant` is wired
  (`../EliteaUI/src/[fsd]/widgets/support-assistant/ui/SupportAssistant.jsx:31-45`).
- No data seeding. The widget restores whatever conversation the test user already has —
  **never assert an absolute message count** (digest quirk 2/10).

## Test Data

| Field | Value |
|---|---|
| Base URL | `http://localhost:5173` (`settings.app_base_url`) |
| Entry page | `/chat` |
| Navigate-away page | Agents — sidebar entry `agents` → `/agents/all` |
| First message | `Navigation persistence test` (exact string from the case) |
| Follow-up message | `Follow-up after navigation` |

---

## Execution Evidence (live, 2026-08-22, `http://localhost:5173`)

### Step 1 — Open the Support Assistant widget on the Chat page

`browser_navigate http://localhost:5173/chat` → then a **real click** on
`[data-testid="sidebar-support-assistant-button"]`.

```
before click: { launcher: true, widgetOpen: false, input: false, items: 0 }
after  click: { widget: true, cls: "elitea-assistant-window",
                title: "ELITEA Support", items: 2, copyBtns: 1, inputVal: "" }
```

✅ Widget opens; header title is `ELITEA Support`. It **restored a prior conversation**
(2 items, 1 completed assistant response) — exactly the digest-quirk-2 behaviour. Baseline
must be captured, never assumed zero.

> Do **not** click `button.elitea-assistant-button` (the floating launcher) — a MUI Tooltip
> clone eats the pointer event (digest quirk 1). The sidebar element is the one with `onClick`.

### Step 2 — Send "Navigation persistence test" and wait for a response

Typed for real (`fill`), then read the Send button:

```
{ disabled: false, val: "Navigation persistence test" }     ← #1581 does NOT reproduce
```

Clicked `[data-testid="support-assistant-send-button"]`; polled the copy-button count
(the response-complete signal, digest quirk 9):

```
{ elapsedMs: 31046, copyBtns: 2, itemCount: 4,
  items: [ {user,  "Explain in one sentence what an AI agent is"},
           {assistant, "In ELITEA, an AI agent is a customizable…"},
           {user,  "Navigation persistence test"},
           {assistant, "Noted — I can help with ELITEA documentat…"} ] }
```

✅ Message sent, assistant replied in **31.0 s**. Item count 2 → 4, copy buttons 1 → 2.

### Step 3 — Navigate to the Agents page via the sidebar (widget left open)

Clicked `[data-testid="sidebar-menu-item-agents"]`.

```
Page URL: http://localhost:5173/agents/all   ·  Page Title: "Agents: all - Private"
Console: 0 errors
```

✅ Client-side route change (no full document load — the widget's DOM survived, see Step 4).

### Step 4 — Verify the widget is still open with the previous conversation intact

```
{ url: "http://localhost:5173/agents/all",
  widgetPresent: true, widgetVisible: true, inputPresent: true,
  itemCount: 4, copyBtns: 2,
  items: [ user "Explain in one sentence…", assistant "In ELITEA…",
           user "Navigation persistence test", assistant "Noted — I can help…" ] }
```

✅ **The widget stays OPEN — it is not even closed, let alone reset.** All 4 message items
and both copy buttons are byte-identical to Step 2. Evidence:
`test-results/screenshots/ELITEA-2422-step-04-widget-open-on-agents.png`.

**Root cause (why this is the correct expected result, not luck):** the widget is mounted
**outside** the routed subtree — `SupportAssistantWidget` renders `<EliteaAssistant>` as a
sibling of `children({onToggleAssistant})` in
`../EliteaUI/src/[fsd]/widgets/support-assistant/ui/SupportAssistant.jsx:33-44`, i.e. at the
app-shell level, so a route change never unmounts it. The case's hedge *"(or can be reopened
via the launcher)"* is therefore **weaker than the live contract** — see § Known Deviations.

### Step 5 — Navigate back to the Chat page

Clicked `[data-testid="sidebar-menu-item-chat"]` → `http://localhost:5173/chat`, 0 console errors.

### Step 6 — Verify the previous session messages are still visible

```
{ url: "http://localhost:5173/chat", widgetVisible: true,
  itemCount: 4, copyBtns: 2, inputVal: "",
  items: [ user "Explain in one sentence…", assistant "In ELITEA…",
           user "Navigation persistence test", assistant "Noted — I can help…" ] }
```

✅ Widget never needed reopening; conversation identical after the round trip. Input is empty
(no draft carried, and none was left).

### Step 7 — Send a follow-up and verify the assistant responds in the same session

Typed `Follow-up after navigation`, clicked Send, polled for `copyBtns > 2`:

```
{ elapsedMs: 31049, copyBtns: 3, itemCount: 6,
  items: [ user "Explain in one sentence what an AI agent…",
           assistant "In ELITEA, an AI agent is a customizable…",
           user "Navigation persistence test",
           assistant "Noted — I can help with ELITEA documentat…",
           user "Follow-up after navigation",
           assistant "Noted — I can help with ELITEA documentat…" ] }
```

✅ Reply in **31.0 s**, appended to the **same** thread — the pre-navigation messages are
still present *above* the follow-up pair, which is the actual proof of "same session"
(a new session would have dropped them). Item count 4 → 6, copy buttons 2 → 3.

### Side channels

- **Console:** `0 errors` reported on every navigation and every action of this run.
  Pre-existing session noise (from before this run) consisted only of
  `ws://localhost:5173/ @vite/client` and `/socket.io/?EIO=4&transport=polling`
  `ERR_CONNECTION_REFUSED` entries — Vite HMR/dev-server infrastructure, not app errors.
  A `Module "stream" has been externalized…` **warning** appears every load (digest quirk 6).
  ⇒ Filter console assertions to `type == "error"` and exclude `@vite/client` / `/socket.io/`
  connection-refused noise.
- **Network:** sending is a **Socket.IO frame, not a POST** (digest quirk 8) — do not try to
  prove "message sent" with a POST assertion. This spec does not need traffic assertions at
  all: the rendered message items and copy buttons are the observables.

---

## Handles Reference

**All handles are testid-primary and ALREADY EXIST — no `add-data-testid` work in this case.**

| # | Element | Handle (testid) | Provenance (verified 2026-08-22, `git fetch origin` + on-disk) |
|---|---|---|---|
| 1 | Sidebar Support Assistant launcher | `sidebar-support-assistant-button` | `on-automation/testids only` — EliteaAI/EliteaUI@37176b46; **not on `main`** (awaiting human cherry-pick) |
| 2 | Widget window | `support-assistant-widget` | `on-automation/testids only` — EliteaAI/elitea_assistant@b8a287b |
| 3 | Widget header title (`ELITEA Support`) | `support-assistant-widget-title` | `on-automation/testids only` — EliteaAI/elitea_assistant@b8a287b |
| 4 | Message input textarea | `support-assistant-message-input` | `on-automation/testids only` — EliteaAI/elitea_assistant@b8a287b |
| 5 | Send button | `support-assistant-send-button` | `on-automation/testids only` — EliteaAI/elitea_assistant@b8a287b |
| 6 | Message item (repeated) | `support-assistant-message-item` (+ `data-role="user"\|"assistant"`) | `on-automation/testids only` — EliteaAI/elitea_assistant@b8a287b / @216da01 |
| 7 | Message bubble | `support-assistant-message-bubble` | `on-automation/testids only` — EliteaAI/elitea_assistant@216da01 |
| 8 | Copy-to-clipboard button (response-complete signal) | `support-assistant-message-copy-button` | `on-automation/testids only` — EliteaAI/elitea_assistant@216da01 |
| 9 | Sidebar menu entry — Agents | `sidebar-menu-item-agents` (via `BasePage.SIDEBAR_MENU_ITEM` template) | `on-automation/testids only` — composed at runtime, `SidebarBody.jsx:272` `testId={\`sidebar-menu-item-${i.value}\`}`; **not on `main`** |
| 10 | Sidebar menu entry — Chats | `sidebar-menu-item-chat` (same template) | `on-automation/testids only` — same source line |

**Provenance verified 2026-08-22** with a fresh `git fetch origin` in **both** repos, using the
`.agents/workflow.md` two-stage grep (`-i` + `[:=]`, so the prop-passed `testId=` forms are
caught). Result: **every handle above is `main:no · testids:YES`** — this case is
**green on localhost, red on any deployed env** until a human cherry-picks. Enumerated live,
the sidebar `value`s are: `chat`, `agents`, `pipelines`, `skills`, `toolkits`, `mcps`,
`credentials`, `applications`, `artifacts`.

Rows 1-8 are already bound as class-level `LocatorDescriptor` fields on
`automation/pages/support_assistant_page.py` (`sidebar_launcher`, `widget`,
`widget_header_title`, `message_input_field`, `send_message_button`, `message_items`,
`message_bubbles`, `message_copy_buttons`) plus the class constants
`ASSISTANT_MESSAGE_ITEM` / `USER_MESSAGE_ITEM` / `MESSAGE_BUBBLE` / `MESSAGE_COPY_BUTTON`.

Rows 9-10 are already reachable through `BasePage.sidebar_menu_item(value)`
(`automation/pages/base_page.py:143-190`, dynamic-testid template
`SIDEBAR_MENU_ITEM = '[data-testid="sidebar-menu-item-{}"]'`) — the sanctioned dynamic shape.
**Do not build a new inline `get_by_test_id(f"…")`.**

### Page-object work needed

Existing helpers cover everything: `open_widget_via_sidebar()`, `get_message_item_count()`,
`get_copy_button_count()`, `set_message_text()`, `send_message_via_testid()`,
`last_assistant_item()`, `last_user_item()`, `bubble_in()`.

Optional (nice, not required) additions on `SupportAssistantPage`:

```python
def get_message_texts(self) -> list[str]:
    """Ordered inner texts of every rendered message item (identity fingerprint)."""

def user_message_item_with_text(self, text: str):
    """The user message item whose bubble carries *text* — for a same-session proof."""
    # composed from the existing USER_MESSAGE_ITEM / MESSAGE_BUBBLE constants
```

Both must be composed from the **existing UPPER_CASE class constants** — no new raw handles.

---

## Implementation Notes

### Waiting

- **Reply wait: the copy-button count**, never a sleep and never a message-count delta —
  a message item appears before its content settles, the copy button appears only when
  `role === 'assistant' && content && !isStreaming && !isAnimating`
  (`../elitea_assistant/src/components/chat/MessageItem.tsx:70-73`).
  `expect(page.message_copy_buttons).to_have_count(baseline + 1, timeout=AI_RESPONSE_TIMEOUT)`
  is the whole wait (digest quirk 17).
- **`AI_RESPONSE_TIMEOUT = 180_000`.** This run measured 31.0 s and 31.0 s; the digest's
  recorded band is 33-135 s. 120 s is tight on this surface — use 180 s.
- **Navigation wait:** after clicking a sidebar entry, wait on the URL
  (`page.wait_for_url("**/agents/all")` / `"**/chat"`) — a client-side route change, so
  `wait_for_load_state("networkidle")` is both unnecessary and flaky here.
- **No `page.wait_for_timeout` anywhere.** The widget's DOM is never torn down across the
  route change, so there is nothing to re-settle: assert directly.

### The two assertions that actually carry this case

1. **Widget survives navigation without being reopened.** Immediately after
   `wait_for_url("**/agents/all")`, `expect(support_page.widget).to_be_visible()` — with
   **no launcher click in between**. This is the strong form; do not weaken it to
   "reopen then check" (§ Known Deviations).
2. **Same session, not a fresh one.** After the follow-up reply lands, assert the
   pre-navigation user message is *still present*, **and** the item count equals
   `baseline + 4` (2 pairs). A reset session would render only the follow-up pair (plus a
   greeting) and this fails — which is precisely the regression the case exists to catch.
   Counting alone is not enough; assert on the *text* too.

   **Amended at implementation (2026-08-22, shipped form):** the text assertion is a
   **delta, not an absolute** — `to_have_count(1)` would flake from the second run onward.
   This spec leaves its messages behind by design (§ Cleanup) and the widget restores the
   previous session, so a prior run's copy of `Navigation persistence test` is already in
   the conversation the test opens with. The shipped form takes a third baseline right
   after the widget opens —
   `baseline_first_message = support_page.user_message_item_with_text(FIRST_MESSAGE).count()`
   — and asserts `to_have_count(baseline_first_message + 1)` at Steps 4, 6 and 7. Same
   claim, same strength, deterministic across the 3× merge gate. This is the
   "baselines, not absolutes" rule below applied to the text assertion as well as the counts.
   The helper `user_message_item_with_text()` was added to `SupportAssistantPage`
   (additive, composed from the existing `USER_MESSAGE_ITEM` constant — no new handle).

### Baselines, not absolutes

Capture `baseline_items = get_message_item_count()` and
`baseline_copies = get_copy_button_count()` right after the widget opens, and assert **deltas**
(`baseline_items + 2` after the first exchange, `+ 4` after the follow-up). The widget restores
a pre-existing conversation whose size varies by test-user history (2 items in this run, 16 in
the ELITEA-2418 run) — absolute counts will flake.

### Cleanup

None. The case is read-mostly plus two chat messages appended to the shared support
conversation — consistent with the existing merged support-assistant specs, which also leave
their messages behind. No teardown; do **not** call `start_new_chat()` at the end (it would
change the state the next spec's baseline sees, and baselines already handle drift).

### Suggested location & shape

New file `automation/tests/ui/support_assistant/test_support_assistant_navigation_persistence.py`,
one class `TestSupportAssistantNavigationPersistence`, one test
`test_widget_state_preserved_after_in_app_navigation`. Steps wrapped in
`with allure.step("Step N — …")`, one block per case step (7 blocks).

### Markers

`p2`, `ui`, `support_assistant`, `regression`. **Not `smoke`** — two live AI replies put the
runtime around 70-90 s.

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition — user logged in | Session active | `page` fixture / `auth_state` (dev token on localhost) | implicit; `/chat` renders the sidebar | covered |
| 1 Open the Support Assistant widget on the Chat page | Page/section loads successfully | Navigate `/chat`, click `sidebar_launcher` | `expect(widget).to_be_visible()`, `expect(widget_header_title).to_have_text("ELITEA Support")` | covered |
| 2 Send "Navigation persistence test", wait for a response | Completes without error, expected UI state | `set_message_text(...)` → `expect(send_message_button).to_be_enabled()` → click | `expect(message_copy_buttons).to_have_count(baseline_copies+1, timeout=180_000)`; `expect(message_items).to_have_count(baseline_items+2)`; last user bubble text == the sent string | covered |
| 3 Navigate to Agents via the sidebar (do not close the widget) | Page/section loads successfully | click `sidebar_menu_item("agents")` | `page.wait_for_url("**/agents/all")` | covered |
| 4 Widget still open (or reopenable) with the conversation intact | Condition holds | no launcher click | `expect(widget).to_be_visible()`; `expect(message_input_field).to_be_visible()`; `expect(message_items).to_have_count(baseline_items+2)`; `expect(message_copy_buttons).to_have_count(baseline_copies+1)`; `expect(user_message_item_with_text("Navigation persistence test")).to_have_count(baseline_first_message+1)` | covered — **strengthened**, see Axis 2 / Known Deviations |
| 5 Navigate back to the Chat page | Page/section loads successfully | click `sidebar_menu_item("chat")` | `page.wait_for_url("**/chat")` | covered |
| 6 Open the widget if it closed — previous session messages still visible | Page/section loads successfully | no reopen needed (assert it never closed) | `expect(widget).to_be_visible()`; item/copy counts unchanged; pre-nav user message text present | covered |
| 7 Send a follow-up; assistant responds in the same session | Completes without error, expected UI state | `send_message_via_testid("Follow-up after navigation")` | `expect(message_copy_buttons).to_have_count(baseline_copies+2, timeout=180_000)`; `expect(message_items).to_have_count(baseline_items+4)`; last user bubble text; input cleared; **and** the Step-2 user message is still rendered at `baseline_first_message+1` (same-session proof) | covered |
| Expected final state — follow-up answered in the same session | — | Step 7 assertions | same as above | covered |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why (grounded) |
|---|---|
| Widget stays visible **without** any reopen click at Steps 4 and 6 | The product mounts the widget at app-shell level (`SupportAssistant.jsx:33-44`), so it *cannot* unmount on a route change — asserting the strong form is what makes a future regression to a routed mount fail. The case's "or can be reopened" hedge would silently pass such a regression. |
| Pre-navigation **message text** still rendered after the follow-up | Counts alone can be satisfied by a reset session that happens to have the same number of items. The text is what proves "same session". |
| Message-input value is empty after each send | The product clears the input on a successful send (digest quirk 3 — a *rejected* input is not cleared), so a non-empty input after send is a real failure signal, free to assert. |
| No console **errors** across both navigations and both sends | Silent errors are exactly what a route change can introduce. Filter to `type == "error"` and exclude `@vite/client` / `/socket.io/` `ERR_CONNECTION_REFUSED` dev-server noise. |

---

## Fidelity Declaration

**No substitutions of any kind.** Every asserted observable — widget visibility, message
items, message text, copy buttons, input value, URL, console — is produced by the live
product and read directly from the DOM. Both AI replies are real live responses over the
assistant's own socket (31.0 s and 31.0 s), never fabricated. Authentication uses the
framework's dev-token fast path (`auth_state`), which is transit only and not the subject of
this case. Typing uses real input events (`fill` / `type`), **never** `page.evaluate` value
assignment — see § Known Defects for why that distinction is load-bearing here.

## Known Deviations (case text vs live product)

| Case text | Live product | Disposition |
|---|---|---|
| Step 4: "Verify the widget is still open **(or can be reopened via the launcher)**" | The widget is **never closed** by in-app navigation — it stays open and fully rendered on `/agents/all`. | **Case text is weaker than reality.** Automate the strong form (still open, no reopen). Not a defect — a case-text imprecision. Worth a TMS **clarification**, low value: the strong assertion supersedes it and the hedge is harmless as written. Recorded here rather than filed, per the light-touch rule; raise it if the TMS owner does a case-text pass. |
| Step 6: "Open the widget **if it closed during navigation**" | Conditional never fires — it does not close. | Same as above; the implementer must **not** write a conditional reopen (a conditional branch that never executes is untested code and would mask a regression). Assert it is open. |

## Known Defects

**None blocking.** Issue **#1581** (referenced by the superseded 2026-08-18 version of this
AFS as blocking) is a **false bug** and does not affect this case: re-verified non-reproducing
in this run (Send enabled immediately on real typing, both messages sent and answered). It
carries two prior "does not reproduce" comments and is contradicted by the green ELITEA-2418
spec, yet is still **OPEN** — a human close is pending (agents never close issues). **No
`expect.soft()`, no `# Known defect:` comment belongs in this spec — it is hard-green.**

## Blocked Steps

None. All 7 steps executed end-to-end against the live system.

## Gotchas (carried into the surface digest)

1. The Support Assistant widget is mounted at **app-shell level**, outside the routed subtree
   (`../EliteaUI/src/[fsd]/widgets/support-assistant/ui/SupportAssistant.jsx:33-44`) — SPA
   navigation neither unmounts nor closes it, and the conversation is not re-fetched.
2. Sidebar navigation entries are testid-addressable via the existing
   `BasePage.SIDEBAR_MENU_ITEM` template: `chat`, `agents`, `pipelines`, `skills`, `toolkits`,
   `mcps`, `credentials`, `applications`, `artifacts` (full list enumerated live).
   `sidebar-menu-item-chat` → `/chat`, `sidebar-menu-item-agents` → `/agents/all`.
3. Reply latency sample 2026-08-22: **31.0 s** twice for short prompts — the fast end of the
   digest's 33-135 s band, but still far above 120 s-is-generous thinking. Keep 180 s.


---

## Implementation record (2026-08-22, test-automation-engineer)

- **Shipped spec:** `automation/tests/ui/support_assistant/test_support_assistant_navigation_persistence.py`
  → `TestSupportAssistantNavigationPersistence::test_widget_state_preserved_after_in_app_navigation`
  (8 `allure.step` blocks — the case's 7 steps plus the console side-channel check).
- **Result:** GREEN 1/1 first run, **77.8 s**, 0 reruns, headless against `http://localhost:5173`.
  Both live replies landed inside the 180 s budget; the AFS's 70-90 s runtime estimate held.
- **Page-object change:** one additive helper, `SupportAssistantPage.user_message_item_with_text()`,
  composed from the existing `USER_MESSAGE_ITEM` class constant. The AFS's other optional
  suggestion (`get_message_texts()`) was **not** added — nothing in the shipped assertions
  needs it, and Rule 7 (reuse before create) says don't ship an unused helper.
- **No new testids.** Every handle already existed on the integration branches, exactly as the
  Handles Reference states; the provenance rows were not re-derived and remain the analyst's
  verified data (`main:no · testids:YES` for all 10 rows ⇒ localhost-green, deployed-red until
  a human cherry-picks).
- **Mechanical self-checks on `git diff tests/batch-support-assistant-w01...HEAD -- automation/`:**
  fidelity grep (`.mock_|page.route(|route.fulfill(|monkeypatch|.evaluate(`) → **0 hits**;
  locator grep → **1 hit**, `self.page.locator(self.USER_MESSAGE_ITEM).filter(has_text=text)`,
  compliant via the UPPER_CASE `[data-testid=` class constant (one-hop); removals grep
  (`^-[^-]`) → **0** — purely additive.
- **Console filter as shipped:** `msg.type == "error"` **and** not
  (`ERR_CONNECTION_REFUSED` and (`@vite/client` or `/socket.io/`)) — the digest-quirk-21
  dev-server noise only; every other console error still fails the test.
