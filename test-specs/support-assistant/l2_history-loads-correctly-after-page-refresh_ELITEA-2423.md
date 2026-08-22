# Test Case: History loads correctly after page refresh

## Metadata

- **TMS ID**: ELITEA-2423
- **Source case**: `.agents/automation/support-assistant-w01/cases/ELITEA-2423.md` (intake snapshot of
  `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2423_history-loads-correctly-after-page-refresh.md`)
- **Priority**: l2 (case priority `medium`)
- **Module**: support-assistant · **Type**: functional
- **Environment explored**: `http://localhost:5173/chat` — EliteaUI on `automation/testids`,
  `../elitea_assistant` aliased live (`VITE_ASSISTANT_LOCAL=1`), DEV backend
- **User set**: `${TEST_USER}` (localhost auto-auth via `VITE_DEV_TOKEN`; `auth_state` on deployed envs)
- **Analyst**: qa-engineer (Sage), batch `support-assistant-w01`
- **Analysed**: 2026-08-22 (live, full 6 steps executed end-to-end)
- **Status**: `ready-for-automation`
- **Filed**: #1649 — case-text clarification (`question`), Steps 4 & 5

> **This file REPLACES a stale `defect-found` AFS** (2026-08-18, commit `995f775cb`) that stopped at
> Step 1 citing blocking defect **#1581** ("send button never enables"). **#1581 is a false bug** — it
> reproduces only with synthetic `input.value = …` on a React controlled textarea (digest quirk 4/21).
> With real typing the send button enabled immediately in this run (`send-disabled after fill: False`,
> twice) and both messages were sent and answered. All six steps of ELITEA-2423 pass against the live
> product.

---

## Classification

`ready-for-automation` — fresh spec.

**Not `already-covered` / `extend-existing`.** The nearest merged neighbour is
`automation/tests/ui/support_assistant/test_support_assistant_smoke.py::TestSupportAssistantHistory::test_history_restore_and_continue`
(line 318, covering ELITEA-1800). It opens the history panel and selects a session — but it **never
reloads the page**, and it never observes the `GET /api/v2/support_assistant/conversations/` status.
This case's whole subject is *survival of a browser refresh* plus the HTTP-200-not-500 contract on the
list endpoint. Neither observable exists in any merged spec:

```
grep -rn "reload\|refresh" automation/tests/ui/support_assistant/   → 0 hits (only prose in comments)
grep -rn "support_assistant/conversations" automation/tests/         → 0 hits
```

So the overlap is *transit* (open widget, send, open history), not the observable. Fresh spec.

---

## Preconditions

- User authenticated on `http://localhost:5173` (localhost dev token; no login step).
- **At least one Support Assistant conversation already exists for the user.** The history button is
  `disabled` when `history.length === 0` (`ChatHeader.tsx:100`), so a genuinely empty account cannot
  open the panel at all. Every run of this suite leaves conversations behind, so this holds in practice
  — but the spec must not *assume* it silently: Step 1 sends a message, which guarantees ≥1 conversation
  exists from that point on.
- The Support Assistant launcher is present in the sidebar.

---

## Test Data

| Field | Value |
|---|---|
| Message 1 | `f"ELITEA-2423 refresh probe A {uuid4().hex[:8]}"` — run-unique |
| Message 2 | `f"ELITEA-2423 refresh probe B {uuid4().hex[:8]}"` — run-unique |

Run-unique suffixes are **required**, not cosmetic: this suite deliberately leaves its messages behind
(no teardown), so a fixed string accumulates across runs and any `to_have_count(1)` on it goes green on
run 1 and red on run N (digest quirk 24). A `uuid4` suffix makes `count == 1` exact and deterministic
without needing a baseline for the *text* assertion. Count assertions on items/copy-buttons still use
baselines.

---

## How this surface actually works (read this before writing the test)

Two source facts decide the whole spec — both read in `../elitea_assistant/src` and confirmed live:

1. **`GET /api/v2/support_assistant/conversations/` fires on PAGE LOAD, not on the History click.**
   `src/lib/hooks/initAssistant.hook.ts:44` calls `api.getConversations()` inside the mount `useEffect`;
   the History button (`ChatHeader.tsx:97 toggleHistory`) only flips local `showHistory` state over the
   already-fetched array. **Live proof:** the network capture taken across the History click is `[]`
   (`S4 net during history open: []`).
   ⇒ The case's Step 4 wording ("Open the History panel — verify the GET … returns 200") must be
   automated as: **capture the list request that the RELOAD triggers**, then assert the panel renders
   from it. Registering the listener on the click would capture nothing and the assertion would pass
   vacuously — a silent false green.

2. **A history item is `disabled` exactly when it is the currently-open conversation**
   (`ChatHeader.tsx:113` — `disabled={conversation.uuid === currentConversationId}`). After a refresh the
   widget auto-restores `items[0]`, so **index 0 is always disabled** at that moment. Live:
   `disabled0-2: [True, False, False]`, and after selecting index 1 the flags shift to
   `[False, True, False]`.
   ⇒ The case's Step 5 ("the previous session is listed **and can be opened**") is satisfied by an
   **enabled** item, not by index 0. Clicking index 0 is a no-op on a disabled button.

---

## Execution Evidence (live, 2026-08-22, `http://localhost:5173`)

Driven by a scripted Playwright probe (real `fill` + real `click`, no `evaluate`), full run reproduced
twice. Screenshots: `automation/test-results/screenshots/ELITEA-2423-step-04-history-panel-after-refresh.png`,
`…/ELITEA-2423-step-06-history-after-second-refresh.png`.

### Step 1 — Open the widget, send a message, wait for the response

| Observation | Value |
|---|---|
| Page-load network | `GET support_assistant/config/` **200**, `GET support_assistant/conversations/` **200** |
| Launcher | `[data-testid="sidebar-support-assistant-button"]` — count 1, plain click works |
| Widget | `[data-testid="support-assistant-widget"]` visible |
| Restored conversation | **12** message items (previous session auto-restored) |
| Send button after `fill(MSG1)` | `disabled: False` — **#1581 does not reproduce** |
| Reply | arrived in **32.3 s**; items 12 → **14**, copy buttons 5 → **6** |
| History panel before refresh | **20** items, name[0] `"Explain one sentence AI agent"`, `disabled[0] = True` |

### Step 2 — Refresh the browser page (F5)

`page.reload()`. Network captured across the reload:

```
GET support_assistant/config/         200
GET support_assistant/conversations/  200
GET support_assistant/config/         200
GET support_assistant/config/         200
GET support_assistant/conversations/  200
```

**`GET .../conversations/` statuses: `[200, 200]`.** No 500, no 4xx — `NON-200 SA CALLS: []` for the
entire session. The list endpoint is requested **twice** per load (React StrictMode double-invokes the
mount effect in dev). Assert *every* captured occurrence is 200, and assert `>= 1` occurred — not "the
first one", which would silently tolerate a second-call 500.

### Step 3 — After reload, open the Support Assistant widget

| Observation | Value |
|---|---|
| Widget auto-open after reload? | **No** — `[data-testid="support-assistant-widget"]` count **0**. An explicit launcher click is required. |
| Items after reopening | **14** — identical to the 14 before the refresh |
| MSG1 present | **1** |
| Copy buttons (assistant replies) | **6** — the reply survived the refresh too |

### Step 4 — Open the History panel; the list request returned 200

| Observation | Value |
|---|---|
| History button `disabled` | **False** (it is `True` while the list is still loading / when empty — this is the "history loaded" signal) |
| Dropdown | `.elitea-assistant-history-dropdown` visible: **True** |
| Items | **20**; names[0..2] `["Explain one sentence AI agent", "Explain one sentence AI agent", "Test message for state persistence"]` |
| `disabled[0..2]` | `[True, False, False]` — index 0 is the restored current conversation |
| Network during the click | **`[]`** — zero requests (see § How this surface actually works, fact 1) |

### Step 5 — The previous session is listed and can be opened

| Observation | Value |
|---|---|
| First enabled index | **1** |
| Click → network | `GET support_assistant/conversation/ce3dd70e-0b7a-402a-b900-db5232979f1b` → **200** |
| Message list | **14 → 4** items (conversation swapped) |
| Dropdown after select | closed |
| Re-opened panel `disabled[0..2]` | `[False, True, False]` — the disabled flag followed the selection |

### Step 6 — Repeat: send another message, refresh again, history still loads

| Observation | Value |
|---|---|
| MSG2 send-disabled after fill | `False` |
| Second reply | **31.8 s**; items 4 → 6, copy buttons 2 → 3 |
| Second reload `GET conversations/` | **`[200, 200]`** |
| History items after 2nd refresh | **20** (unchanged) |
| Restored conversation | **14** items — `items[0]` again, i.e. the MSG1 conversation |
| MSG1 present after 2nd refresh | **1** |
| MSG2 present after 2nd refresh | **0** — expected, see § Known Deviations |

### Side channels

- **Console errors: `[]`** for the entire run (2 loads + 2 reloads + 2 live replies). Note the digest's
  known dev-server noise (`Module "stream" has been externalized`, `@vite/client` /
  `socket.io` `ERR_CONNECTION_REFUSED`) did not fire in this headless run, but the spec should still
  filter to `type == "error"` and exclude those two URL patterns (digest quirks 6/23).
- **No non-200 support_assistant call of any kind** — `NON-200 SA CALLS: []`.
- Sending is a **WebSocket** frame, not a POST (digest quirk 8) — do not look for a POST.

---

## Handles Reference

Locator policy is **testid-only** (`.agents/testing.md` § Locator policy). Provenance verified with a
fresh `git fetch origin` in **both** repos on 2026-08-22 (two-stage grep, `-i` + `[:=]`).

| # | Element | Testid | Provenance |
|---|---|---|---|
| 1 | Sidebar launcher | `sidebar-support-assistant-button` | `on automation/testids only` (EliteaUI — awaiting human promotion to `main`) |
| 2 | Widget window | `support-assistant-widget` | `on automation/testids only` (elitea_assistant) |
| 3 | Message input | `support-assistant-message-input` | `on automation/testids only` (elitea_assistant) |
| 4 | Send button | `support-assistant-send-button` | `on automation/testids only` (elitea_assistant) |
| 5 | Message item | `support-assistant-message-item` (+ `data-role="user"|"assistant"`) | `on automation/testids only` (elitea_assistant) |
| 6 | Copy button (reply-complete signal) | `support-assistant-message-copy-button` | `on automation/testids only` (elitea_assistant) |
| 7 | **History button** | **`testid needed: support-assistant-history-button`** | `needs-adding` |
| 8 | **History dropdown** | **`testid needed: support-assistant-history-dropdown`** | `needs-adding` |
| 9 | **History item (repeated)** | **`testid needed: support-assistant-history-item`** | `needs-adding` |

Verification output (pasted, not summarised):

```
support-assistant-history-button           main:no   testids:no
support-assistant-history-dropdown         main:no   testids:no
support-assistant-history-item             main:no   testids:no
support-assistant-message-input            main:no   testids:YES
support-assistant-message-copy-button      main:no   testids:YES
sidebar-support-assistant-button           main:no   testids:YES     (EliteaUI)
```

### Testid work needed (rows 7-9) — connected first-party repo

All three live in **`../elitea_assistant/src/components/chat/ChatHeader.tsx`** — a repo **we own**
(`@eliteaai/elitea-assistant`), so canon #705 applies: add the testids in **its** `src/`, on **its**
`automation/testids` branch. This is **not** a #579 third-party waiver.

| Line | Element | Add |
|---|---|---|
| 94-101 | history `<button>` | `data-testid="support-assistant-history-button"` |
| 105 | dropdown `<div className="elitea-assistant-dropdown elitea-assistant-history-dropdown">` | `data-testid="support-assistant-history-dropdown"` |
| 108-112 | item `<button className="elitea-assistant-history-item">` | `data-testid="support-assistant-history-item"` |

**Attributes only — no new DOM node, no new hook, no state change** (zero-functional-impact rule). The
elements already exist and already carry the state the test needs.

**Do NOT add a state-flavoured testid or a new state attribute for "current conversation".** The item
already carries the native `disabled` attribute, derived from `conversation.uuid === currentConversationId`
(`ChatHeader.tsx:113`). Filter on it from a class constant:

```python
HISTORY_ITEM          = '[data-testid="support-assistant-history-item"]'
HISTORY_ITEM_CURRENT  = '[data-testid="support-assistant-history-item"][disabled]'
HISTORY_ITEM_OPENABLE = '[data-testid="support-assistant-history-item"]:not([disabled])'
```

That is testid-keyed locating with a native-attribute filter — the sanctioned shape, and it costs the
product nothing.

### Page-object work needed — `automation/pages/support_assistant_page.py`

Existing `open_history()` (L446), `get_history_session_count()` (L457) and `select_history_session()`
(L475) are **pre-policy tech debt**: `history_button` is a `fallback=` lambda (L60-62) and the two
helpers build `page.locator('button.elitea-assistant-history-item')` **inside method bodies**. Do not
call them and do not extend them; add testid-bound siblings alongside, the same additive pattern
ELITEA-2418/2419/2422 used:

```python
# class level
history_button = LocatorDescriptor(testid="support-assistant-history-button", description="…")
history_dropdown = LocatorDescriptor(testid="support-assistant-history-dropdown", description="…")
history_items = LocatorDescriptor(testid="support-assistant-history-item", description="…")
HISTORY_ITEM          = '[data-testid="support-assistant-history-item"]'
HISTORY_ITEM_CURRENT  = '[data-testid="support-assistant-history-item"][disabled]'
HISTORY_ITEM_OPENABLE = '[data-testid="support-assistant-history-item"]:not([disabled])'
```

plus thin helpers: `open_history_via_testid()`, `get_history_item_count_via_testid()`,
`open_first_openable_history_session()` (clicks `HISTORY_ITEM_OPENABLE` first match),
`close_history_dropdown()` (click-outside — the dropdown closes on outside pointerdown,
`ChatHeader.tsx:36-46`).

Already available and reusable as-is: `open_widget_via_sidebar()`, `set_message_text()`,
`send_message_via_testid()`, `get_copy_button_count()`, `get_message_item_count()`,
`user_message_item_with_text()`, `is_send_button_enabled()`.

---

## Implementation Notes

### Capturing the list-request status (the load-bearing mechanic)

The request fires on **reload**, and **twice**. Collect, don't `expect_response`:

```python
list_responses: list[Response] = []
page.on("response", lambda r: list_responses.append(r)
        if re.search(r"/api/v2/support_assistant/conversations/?$", r.url)
        and r.request.method == "GET" else None)
...
list_responses.clear()
page.reload(wait_until="domcontentloaded")
...
assert list_responses, "no GET /support_assistant/conversations/ observed after reload"
assert all(r.status == 200 for r in list_responses), [r.status for r in list_responses]
```

`assert all(...)` over `assert first == 200` is deliberate: the endpoint is hit twice and the case's
whole point is "200, **not 500**" — tolerating a 500 on the second call would be exactly the regression
this case exists to catch.

### Waiting — no sleeps anywhere

| Wait for | Condition |
|---|---|
| History list loaded after a (re)load | `expect(history_button).to_be_enabled()` — it is `disabled` until `history.length > 0` (`ChatHeader.tsx:100`). This IS the case's observable, and it is the cheapest honest wait on this surface. |
| Widget open | `expect(widget).to_be_visible()` |
| Assistant reply complete | `expect(message_copy_buttons).to_have_count(baseline + 1, timeout=180_000)` — the copy button renders only when `!isStreaming && !isAnimating` (digest quirks 9/17). Measured **32.3 s / 31.8 s** this run; the 33-135 s band still holds, keep **180 s**. |
| History dropdown open | `expect(history_dropdown).to_be_visible()` |
| Session switched (Step 5) | `expect(message_items).not_to_have_count(count_before)` — the list swaps (14 → 4 live). Pair it with the `GET /conversation/{uuid}` 200 capture. |

No `wait_for_timeout`, no `networkidle` (the reload is a real navigation, but the assistant's own fetches
resolve independently — gate on the history button, not on the network being quiet).

### Baselines, not absolutes

Every count on this surface is a **delta** (digest quirks 2/10/24). The widget restores a previous
conversation, and this suite leaves its data behind:

- items / copy buttons → capture a baseline right after the widget opens, assert `baseline + N`.
- history item count → assert `>= 1` and **stability across the refresh** (`after == before`), never
  `== 20`. The 20 observed is almost certainly an API page cap, and it is shared-account data that other
  runs change.
- MSG1 text → `to_have_count(1)` is safe **only** because the message carries a `uuid4` suffix.

### The assertions that actually carry this case

1. Every `GET /support_assistant/conversations/` observed across **each** reload is **200** (Steps 2, 4, 6).
2. After the reload the history panel **opens and lists ≥ 1 session** (button enabled → dropdown visible
   → item count ≥ 1) — Step 4.
3. A **previous, openable** session can actually be opened: click a `:not([disabled])` item →
   `GET /conversation/{uuid}` **200** and the message list changes — Step 5.
4. The pre-refresh conversation **survived** the reload: MSG1 (+ its reply) is present after reopening —
   Step 3.
5. The whole thing **repeats**: second send + second reload → still 200, history item count unchanged —
   Step 6.

### Cleanup

None. Conversations and messages are deliberately left behind — the same convention as every other
support-assistant spec (the widget's restore behaviour is what makes the suite's baseline discipline
necessary). Do not delete conversations; there is no UI for it and other specs depend on the account
having history.

### Suggested location & shape

`automation/tests/ui/support_assistant/test_support_assistant_history_after_refresh.py`
→ `class TestSupportAssistantHistoryAfterRefresh` → `test_history_loads_correctly_after_page_refresh`.

One test, six `allure.step("Step N — …")` blocks mapping 1:1 onto the case steps. Estimated runtime
**~110-150 s** headless (two live replies at ~32 s each dominate; the probe's full pass was ~3 min
including exploration overhead).

### Markers

`@pytest.mark.p2`, `@pytest.mark.support_assistant`, `@pytest.mark.regression`, `@pytest.mark.ui`,
`@pytest.mark.slow` (two live LLM replies). **Not** `smoke`.

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | localhost dev-token auth (`auth_state` on deployed) | fixture | covered |
| Step 1 — open widget, send any message, wait for response | loads successfully | launcher click → widget visible → `fill` + send → copy-button delta | Step 1 block | covered |
| Step 2 — refresh (F5) | completes without error | `page.reload()` with the response collector armed | Step 2 block | covered |
| Step 3 — after reload, open the widget | expected UI state | explicit launcher click (widget does **not** auto-open) + restored conversation contains MSG1 | Step 3 block | covered |
| Step 4 — open History; `GET …/conversations/` returns 200 (not 500) | loads successfully | all collected list responses `== 200`; history button enabled; dropdown visible; ≥1 item | Step 4 block | covered — **with a mechanic correction**: the GET fires on the reload, not on the click (see § How this surface actually works) |
| Step 5 — previous session listed **and can be opened** | condition holds | item count ≥ 1; click first `:not([disabled])` item → `GET /conversation/{uuid}` 200 + message list changes | Step 5 block | covered — "openable" means an **enabled** item; index 0 is the restored current conversation and is `disabled` by design |
| Step 6 — repeat: send another message, refresh, history still loads | no errors | second reply, second reload, list responses all 200, history item count unchanged, panel reopens | Step 6 block | covered |
| Expected final state | history still loads without errors | Steps 4-6 assertions + zero console errors | Steps 4-6 | covered |
| Pass criterion "no errors in any step" | — | `NON-200 SA CALLS == []` + console-error assertion (filtered per digest quirks 6/23) | side-channel block | covered |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why it is grounded |
|---|---|
| **Every** list response is 200, not just the first | The endpoint is hit twice per load (StrictMode). Asserting only the first would let a real second-call 500 through — the exact failure this case names. |
| The restored conversation still contains MSG1 **and its reply** after the reload | Step 3's "expected UI state" is otherwise unfalsifiable; without it "open the widget" passes on an empty widget. |
| The `GET /conversation/{uuid}` on session-select returns 200 | Step 5's "can be opened" needs a system-produced proof, not just a click that does nothing. |
| Zero console errors across both reloads | Skill § Execute step 3 (side channels) — a silent client-side error during history hydration is exactly the class of bug this case guards. |
| History item count is **unchanged** across the second refresh | Step 6's "still loads" is otherwise satisfied by a panel that lost every entry. |

---

## Fidelity Declaration

**No substitutions of any kind.** Every asserted value is produced by the system:

| Potential substitution | Used? |
|---|---|
| `page.route` / `route.fulfill` | No |
| `page.evaluate` to type or click | No — real `fill` + real `click` throughout (this is precisely what disproved #1581) |
| Injected state / monkeypatch / stubbed client | No |
| API-seeded precondition for a UI-created artefact | No — the conversation is created through the widget |

The one `wait_for_function` in the analyst probe (history-button-enabled) is a **read-only** condition
poll and should be written as `expect(history_button).to_be_enabled()` in the spec — no `evaluate` in the
delivered diff.

---

## Known Deviations (case text vs live product)

1. **Step 4's mechanic is misstated in the case, not broken in the product.** The case reads as if
   opening the History panel issues `GET …/conversations/`. It does not — the request is issued on page
   load (`initAssistant.hook.ts:44`) and the panel renders from cached state (live: zero requests during
   the click). The *contract* the case cares about (that list request returns 200, not 500, after a
   refresh) is fully verifiable; only the trigger is different. Automated per the corrected mechanic;
   **not a defect** — reverse-masking guard applies (`.agents/testing.md`). Filed as case-text
   clarification **#1649** (label `question`), not a bug.
2. **Step 5's "can be opened" cannot mean index 0.** (also covered by clarification **#1649**) After a refresh, index 0 is the auto-restored
   current conversation and is rendered `disabled` by design (`ChatHeader.tsx:113`). The spec opens the
   first `:not([disabled])` item. Product behaviour is correct; the case text is simply silent on it.
3. **After a refresh the widget restores `items[0]` of the list — which is NOT necessarily the most
   recently active conversation.** Live: MSG2 was sent into the conversation opened at Step 5 (list
   index 1); after the Step 6 reload the widget restored index 0 again, so MSG2 was **not** visible
   (`MSG2 present: 0`) while MSG1 was. The list appears to be ordered by creation, not by last activity,
   and sending a message does not reorder it. The case asserts nothing about ordering, so this is
   **not** a defect and not a blocker — but the spec must **not** assert MSG2's visibility after the
   second refresh. Recorded as an observation for the lead.

---

## Known Defects

**None found.** In particular, **#1581 is a false bug and must not block this case again** — re-verified
non-reproducing here for the fourth time (digest quirk 21). Any support-assistant AFS still citing
#1581 as blocking is stale.

---

## Blocked Steps

None. All six steps executed end-to-end against the live product.

---

## Gotchas (carried into the surface digest)

1. `GET …/conversations/` fires on page load (mount effect), **not** on the History click — and twice
   per load under StrictMode.
2. The history button is `disabled` while the list is empty/loading — it is the cheapest "history
   loaded" wait, and it is the case's own observable.
3. A history item is `disabled` iff it is the current conversation; the flag follows the selection.
4. The widget does **not** auto-open after a reload — an explicit launcher click is required.
5. Restore after refresh always loads `items[0]`, which is creation-ordered, not activity-ordered.
6. Reply latency this run: 32.3 s and 31.8 s. Zero console errors, zero non-200 support_assistant calls.
