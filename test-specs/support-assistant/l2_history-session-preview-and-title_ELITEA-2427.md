# Test Case: History session shows correct preview and title

## Metadata

- **TMS ID**: ELITEA-2427
- **Source case**: `.agents/automation/support-assistant-w02/cases/ELITEA-2427.md` (intake snapshot of
  `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2427_*.md`)
- **Priority**: l2 (case priority `medium`)
- **Module**: support-assistant · **Type**: functional
- **Environment explored**: `http://localhost:5173/chat` — EliteaUI on `automation/testids`,
  `../elitea_assistant` aliased live (`VITE_ASSISTANT_LOCAL=1`), DEV backend
- **User set**: `${TEST_USER}` (localhost auto-auth via `VITE_DEV_TOKEN`; `auth_state` on deployed envs)
- **Analyst**: qa-engineer (Sage), batch `support-assistant-w02`
- **Analysed**: 2026-08-22 — all 8 steps executed live end-to-end in one 83 s session
- **Status**: `ready-for-automation` — **RED BY DESIGN** on Steps 7-8 until the product ships them
- **Filed**: #1658 (`bug`, Step 7 — no timestamp) · #1659 (`bug`, Step 8 — no preview, upstream 5723)
  · #1660 (`question` + `case-text-drift`, Steps 2 & 6 case-text imprecision)

---

## Classification Rationale

`ready-for-automation` — fresh spec, with two of the eight steps asserted as linked soft failures.

**Why not `blocked`, even though two steps cannot pass today.** The case's Step 8 / Expected Final
State (a conversation preview) is not implemented — the case text says so itself
(*"Issue 5723 is assigned for current release"*) — and Step 7 (timestamp) is not implemented either.
Neither prevented exploration: every step ran, and Steps 1-6 pass against the live product. That is
exactly the situation `.agents/testing.md` § Merge gate ▸ *Sanctioned-RED, analysis-time entry
(2026-07-23, #557/ELITEA-1965)* governs: a deterministic, single-cause, filed-and-linked defect
found during **analysis** is classified `ready-for-automation`, the **correct** expected behaviour is
written with `expect.soft()` + `# Known defect: #N`, and the spec flips green when the product ships.
`defect-found`/`blocked` is reserved for a defect that blocks reaching later steps — this one does not.
Both known defects satisfy the gate's criteria:

| Criterion | #1658 (timestamp) | #1659 (preview) |
|---|---|---|
| (a) deterministic | structural — the item's whole body is `{conversation.name}`; 100 % of entries, every load | same render site, same certainty |
| (b) single-cause | one render site, `ChatHeader.tsx:112-121` | one render site + a missing API field |
| (c) open, filed, linked, soft-asserted | #1658 | #1659 |

They form a **closed, enumerable set** of two — the gate's closed-set variant — so a gate run showing
either or both is one sanctioned signature. Anything else red blocks.

**Why not `already-covered`.** No merged spec asserts anything about a history entry's *content*.
`test_support_assistant_history_after_refresh.py` (ELITEA-2423, merged) counts entries and clicks the
first openable one; `test_support_assistant_smoke.py::TestSupportAssistantHistory` (ELITEA-1800)
selects a session and continues messaging. Verified:

```
grep -rn "history_item\|open_history" automation/tests/                    → 2 files, count/select only
grep -rn "to_have_text\|to_contain_text" .../support_assistant/*.py | grep -i hist → 0 hits
```

Neither would fail if the title regressed to an empty string or to another conversation's name.

**Why not `extend-existing`.** The nearest candidate is ELITEA-2423's spec, but its subject is
*survival of a page refresh* and its whole body is built around reload-scoped response collectors.
Appending a title/timestamp/preview flow means a different conversation lifecycle (New chat →
distinctive message → New chat), a live LLM round trip it does not have, and two soft-linked defect
assertions — a near-rewrite, which § Classify findings routes back to `ready-for-automation`.
Reuse is at the *code* level: the same page object, the same copy-button reply signal, the same
console side channel.

**Why not `un-automatable`.** Fully scriptable; ran green (for the implemented steps) first try.

---

## Preconditions

1. EliteaUI dev server on `http://localhost:5173` serving `automation/testids`, with
   `VITE_ASSISTANT_LOCAL=1` so `../elitea_assistant` is aliased live (`start-ui-localhost` skill).
2. Authenticated session — localhost needs none (`auth_state` returns empty state, dev token).
3. The account may hold any number of prior conversations; the spec is written to tolerate 0 or 20+
   (see § How this surface actually works, point 3).

## Test Data

| Field | Value |
|---|---|
| Distinctive message | `HISTORY-TITLE-TEST: Tell me about ELITEA` (case-mandated verbatim) |
| Distinctive token | `HISTORY-TITLE-TEST` — the fragment the generated title provably preserves |
| Run isolation | none needed; the token is unique to this spec and titles are regenerated per session |

No cleanup: the suite convention on this surface leaves conversations behind (they are shared account
data, and the widget's own restore behaviour depends on them existing).

---

## How this surface actually works (read this before writing the test)

1. **A history entry's entire DOM body is the conversation's generated title.** Verbatim, live:

   ```html
   <button class="elitea-assistant-history-item" type="button"
           data-testid="support-assistant-history-item">HISTORY-TITLE-TEST: Tell about ELITEA</button>
   ```

   No child nodes, no `title` attribute, no `aria-label` (`title_attr: null`, `aria: null`).
   Source: `elitea_assistant/src/components/chat/ChatHeader.tsx:112-121` → `{conversation.name}`.
   **This single fact is what makes Steps 7 and 8 red** (#1658, #1659).

2. **The title is an LLM-generated paraphrase delivered over the socket, not the message text.**
   The backend emits `conversation_name_updated`; the client strips a `User ID <n> - ` prefix
   (`chat.hook.ts:326-329`). Live, `HISTORY-TITLE-TEST: Tell me about ELITEA` became
   **`HISTORY-TITLE-TEST: Tell about ELITEA`** — *"me"* dropped. **Never assert equality with the
   sent message**; assert containment of the distinctive token. (Case-text point, #1660.)

3. **Sending straight after opening the widget does NOT create a new session.** The widget restores
   `items[0]` of the conversation list on mount (`initAssistant.hook.ts:44-58`), so on a populated
   account a message joins a *pre-existing* conversation and the top history entry keeps its old
   title — the case's Step 6 observable would never exist. **Click New chat before sending.**
   `handleSend` then calls `createConversation()` and prepends it locally:
   `setHistory(prev => [created, ...prev])` (`chat.hook.ts:460-466`). Live: 20 → 21 entries, new one
   at index 0. (Case-text point, #1660.)

4. **The history button is `disabled` until `history.length > 0`** (`ChatHeader.tsx:101`) — the honest
   "list loaded" wait, no `networkidle`, no sleep. It exists only while the widget is open (digest
   quirk 34).

5. **An entry is `disabled` exactly when it is the currently-open conversation** (`ChatHeader.tsx:119`).
   After the case's Step 4 (New chat) `currentConversationId` is cleared, so **index 0 is enabled** at
   Step 5 — confirmed live (`disabled: false`). Before that New chat, the just-created conversation is
   index 0 *and* disabled; its text is still readable (disabled buttons render text normally).

6. **The reply-ready signal is the copy-button count**, not the message count (digest quirks 9/10) —
   the copy button renders only on a completed assistant message.

7. **`GET /api/v2/support_assistant/conversations/` fires on page load, not on the History click**
   (digest quirk 26) — do not arm a response wait around the click; it captures nothing.

8. **The server list is capped at ~20 while the client prepends locally**, so counts can read 21
   after a send. Assert `>= 1` and a delta, never an absolute (digest quirk 31).

9. **The list payload has no message-body field.** Item keys, live:
   `attachment_participant_id, author_id, created_at, duration, id, instructions, is_private,
   message_groups_count, meta, name, participants_count, source, updated_at, users_count, uuid`.
   `created_at`/`updated_at` exist and are simply not rendered (#1658); a preview needs a new field
   or a per-conversation fetch (#1659).

---

## Execution Evidence (live, 2026-08-22, `http://localhost:5173`, headless, 83 s total)

Probe: direct Playwright drive of the real UI (real click/`fill`/click-send — no synthetic value
writes, no route interception). Screenshot: `test-results/screenshots/ELITEA-2427-step-05-history-panel.png`.

### Step 1 — Open the Support Assistant widget
Sidebar launcher `[data-tour="sidebar-support-assistant"]` → `[data-testid="support-assistant-widget"]`
visible at 2.9 s. History button enabled at 6.8 s; panel opened; **20 entries** baseline. ✅ as case says.

### Step 2 — Send the distinctive message
*Deviation (declared, #1660):* **New chat first**, then send (point 3 above). Real `fill` →
send button enabled immediately (**#1581 disproved a fifth time**) → click. ✅

### Step 3 — Wait for the assistant response
Copy-button count 1 → 2 at **74 s** after send (within the surface's observed 31-135 s band). ✅

### Step 4 — Click New Chat to push the session into history
`[data-testid="support-assistant-new-chat-button"]` → composer reset, `currentConversationId` cleared. ✅

### Step 5 — Open the History panel
`[data-testid="support-assistant-history-button"]` → dropdown present, **21 entries** (20 + the new
one, prepended). ✅

### Step 6 — Most recent entry shows a recognizable label ✅ **PASSES**
Index 0 text: **`HISTORY-TITLE-TEST: Tell about ELITEA`** — contains the distinctive token
`HISTORY-TITLE-TEST`; `disabled: false`. Present already at the first poll after the reply landed
(82.0 s), i.e. the socket name update arrives no later than the completed reply.
*Not* equal to the sent message (dropped *"me"*) — containment only.

### Step 7 — Entry shows a timestamp or date indicator ❌ **FAILS — #1658**
No timestamp, date, `title` attribute or `aria-label` anywhere in the item. The API returns
`created_at: 2026-08-22T04:36:29+00:00Z` / `updated_at: …` for every entry; the UI drops them.

### Step 8 — Entry shows a short preview of the conversation content ❌ **FAILS — #1659**
No preview node and no second line — the item's only text is the title. Matches the case's own
annotation that this is upstream issue 5723, still unshipped.

### Side channels
- Console errors captured over the whole run: **0** (`console_errors: []`).
- All `GET /api/v2/support_assistant/conversations/` responses: **200**.
- No `pageerror`.

---

## Handles Reference

All handles are **testids that already exist** in the connected assistant repo — no testid work is
needed for this case (they landed with ELITEA-2423, `EliteaAI/elitea_assistant@7413180`, on its
`automation/testids` branch).

| # | Element | Handle (primary, testid-only) | PROVENANCE | Page-object binding |
|---|---|---|---|---|
| 1 | Sidebar launcher | `[data-tour="sidebar-support-assistant"]` | EliteaUI, pre-existing (grandfathered raw — reused via `sidebar_launcher`, not added by this case) | `SupportAssistantPage.sidebar_launcher` |
| 2 | Widget window | `support-assistant-widget` | on `elitea_assistant automation/testids` only (awaiting human promotion to main) | `.widget` |
| 3 | Header title | `support-assistant-widget-title` | on `elitea_assistant automation/testids` only | `.widget_header_title` |
| 4 | Message input | `support-assistant-message-input` | on `elitea_assistant automation/testids` only | `.message_input_field` |
| 5 | Send button | `support-assistant-send-button` | on `elitea_assistant automation/testids` only | `.send_message_button` |
| 6 | Assistant copy button (reply-complete signal) | `support-assistant-message-copy-button` | on `elitea_assistant automation/testids` only | `.message_copy_buttons` |
| 7 | New chat button | `support-assistant-new-chat-button` | on `elitea_assistant automation/testids` only | `.new_chat_button_testid` |
| 8 | History toggle | `support-assistant-history-button` | on `elitea_assistant automation/testids` only | `.history_toggle_button` |
| 9 | History dropdown | `support-assistant-history-dropdown` | on `elitea_assistant automation/testids` only | `.history_dropdown` |
| 10 | History entry (repeated) | `support-assistant-history-item` | on `elitea_assistant automation/testids` only | `.history_items` |

Verified 2026-08-22 by reading `../elitea_assistant/src` on `automation/testids` (branch confirmed
checked out) — every row above is a literal `data-testid=` attribute in `ChatHeader.tsx`,
`ChatWindow.tsx`, `MessageInput.tsx`, `MessageItem.tsx`, `CopyButton.tsx`.

**Deployed-env note:** none of rows 2-10 are on `elitea_assistant` `main`, and reaching a deployed
env needs the extra hop of EliteaUI bumping the `@eliteaai/elitea-assistant` git-dependency
(`.agents/workflow.md` § Connected repos). Local runs are unaffected.

### Page-object work needed — `automation/pages/support_assistant_page.py`

Nothing structural. Existing members cover the flow:
`open_widget_via_sidebar`, `set_message_text`, `send_message_button`, `get_copy_button_count`,
`new_chat_button_testid`, `open_history_via_testid`, `get_history_item_count_via_testid`,
`history_items`.

**Shipped (implementer, 2026-08-22):** one additive method, no new class constant — the proposed
`HISTORY_ITEM` constant turned out unnecessary, because the existing `history_items`
`LocatorDescriptor` already addresses the entry and `.first` composes off it:

```python
def newest_history_item(self):
    """Locator for the most recent conversation in the history dropdown. …"""
    return self.history_items.first
```

No new raw handles, no `fallback=`, no `locator=`, nothing built inside a method body. Verified on
the branch diff: locator grep 0 hits, fidelity grep 0 hits, `grep -E '^-[^-]'` on the page object
empty (additive-only).

---

## Implementation Notes

### The assertions that carry this case

```python
MESSAGE = "HISTORY-TITLE-TEST: Tell me about ELITEA"
TOKEN   = "HISTORY-TITLE-TEST"

# Step 6 — HARD. The label is a generated paraphrase; the token survives, the wording may not.
expect(top_item).to_contain_text(TOKEN, timeout=TITLE_TIMEOUT)   # 60 s: socket-delivered

# Step 7 — SOFT, red by design.
# Known defect: #1658 — the entry renders no timestamp/date indicator.
expect.soft(top_item).to_contain_text(
    re.compile(r"\d{1,2}[:/.\-]\d{2}|\d{4}-\d{2}-\d{2}"),
)

# Step 8 — SOFT, red by design.
# Known defect: #1659 — the entry renders no conversation preview (upstream 5723).
# The verbatim message is the discriminator: the TITLE provably does not contain it
# (the generator drops words — "Tell about" vs "Tell me about"), so this can only pass
# once real conversation content is rendered.
expect.soft(top_item).to_contain_text(MESSAGE)
```

Both soft assertions encode **the case's expected observable**, not today's behaviour — that is the
point of the sanctioned-RED pattern, and it is why they must never be inverted into
"assert no timestamp is shown" (that would be reverse-masking: it would go green today and stay green
after the fix, permanently hiding the feature). If the shipped shape differs from the encoding above
(e.g. the preview renders the assistant's reply rather than the user's message, or the timestamp
lands in a `title` attribute), that is an `adjust-automated-test` follow-up on a passing product —
not a licence to weaken the assertion here.

### Waits — no sleeps anywhere

| Moment | Wait |
|---|---|
| Widget open | `expect(widget).to_be_visible()` |
| History list loaded | `expect(history_toggle_button).to_be_enabled()` (disabled until `history.length > 0`) |
| Send enabled | `expect(send_message_button).to_be_enabled()` after a real `fill` |
| Reply complete | `expect(message_copy_buttons).to_have_count(baseline + 1, timeout=180_000)` |
| Title delivered | the `to_contain_text(TOKEN, timeout=60_000)` assertion itself polls |
| Dropdown open | `expect(history_dropdown).to_be_visible()` |

Observed reply latency this run: **74 s** (band 31-135 s). Whole flow: **83 s** headless.

### Baselines, not absolutes

Read the history count before the send and assert `after == before + 1` **and** `>= 1` — never a
literal (shared account, server cap ~20, client prepends locally: live 20 → 21).

### Side channels (both required)

Register before Step 1: a `console` listener (excluding the two dev-server noise patterns already
used by `test_support_assistant_history_after_refresh.py`) and a `pageerror` listener. Assert both
empty at the end. The analysis run recorded zero of each, so anything captured is real.

### Suggested location & shape

`automation/tests/ui/support_assistant/test_support_assistant_history_title_preview.py` →
`TestSupportAssistantHistoryTitleAndPreview::test_history_entry_shows_title_timestamp_and_preview`.
One test — the three observables share one live conversation and one 74 s reply; splitting them would
triple the runtime for no isolation gain (all three read the same DOM node).

Docstring must state: RED BY DESIGN on Steps 7-8, linked to #1658 / #1659; the New-chat-first
deviation and why (#1660); no substitutions.

### Markers

`p2`, `ui`, `support_assistant`, `regression`, `slow` (one live LLM round trip, ~85-150 s).

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | session active | `auth_state` (no-op on localhost) | fixture | covered |
| Step 1 — open the widget | widget loads | `open_widget_via_sidebar` | `expect(widget).to_be_visible()` + header title text | covered |
| Step 2 — send the distinctive message | completes without error, message appears | `set_message_text` + send click, **preceded by New chat** | user bubble `to_have_text(MESSAGE)` | covered (deviation #1660) |
| Step 3 — wait for the response | reply arrives, state ready | copy-button count delta | `to_have_count(baseline+1, 180 s)` | covered |
| Step 4 — New chat pushes the session into history | control responds, session listed | `new_chat_button_testid` click | history count `before + 1` | covered |
| Step 5 — open the History panel | panel loads | `open_history_via_testid` | `expect(history_dropdown).to_be_visible()`, `history_items >= 1` | covered |
| Step 6 — newest entry shows a recognizable label | first-message text **or** generated title | index-0 entry text | `to_contain_text("HISTORY-TITLE-TEST")` **hard** | covered — passes live |
| Step 7 — entry shows a timestamp/date | timestamp visible | index-0 entry text | `expect.soft(...)` date/time regex | **red by design — #1658** |
| Step 8 — entry shows a short content preview | preview visible | index-0 entry text | `expect.soft(...)` verbatim message | **red by design — #1659** |
| Expected Final State — preview shown | preview visible | same as Step 8 | same | **red by design — #1659** |
| Pass criterion "all steps complete without errors" | no errors | console + pageerror listeners | both empty | covered |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why it belongs |
|---|---|
| Widget header title is `ELITEA Support` | cheap proof the widget under assertion is the right one (surface convention, every SA spec) |
| History count delta `+1` | the case says "push the session into history" but asserts nothing about it; without this, Step 4 is unverified |
| Index-0 entry is `:not([disabled])` after New chat | encodes quirk 5 (current-conversation flag cleared) — a regression here would silently break every "open a previous session" spec |
| Zero console errors / zero page errors | the case's own pass criterion, which has no step of its own |
| After Step 4's New chat, the distinctive user message is gone from the composer (`to_have_count(0)`) | *added by the implementer* — proves the session was genuinely left behind rather than merely re-rendered, so the entry read at Steps 6-8 really is a *history* entry |

---

## Fidelity Declaration

**No substitutions of any kind.** No `page.route`, no `route.fulfill`, no `page.evaluate` state
injection, no monkeypatching, no API-seeded preconditions. Every asserted value — the entry text, the
entry count, the reply completion, the console/pageerror channels — is produced by the live product
reached through the real UI: real click on the launcher, real `fill` into the React textarea, real
send click, real LLM round trip, real socket-delivered title.

The New-chat-first ordering is a **navigation choice, not a substitution**: it uses the product's own
control to reach the state the case describes (a session created by the distinctive message), and the
case's own observable — the generated title of that session — is still read off the live DOM.

---

## Known Deviations (case text vs live product) — filed as #1660

1. **Step 2 ordering.** The case sends before creating a new session; on a populated account the
   widget restores the newest conversation on open, so the message would join it. New chat is clicked
   first. Product is correct; the case assumes an empty account.
2. **Step 6 label semantics.** "the first user message text" never holds literally — the label is
   always a backend-generated paraphrase (`HISTORY-TITLE-TEST: Tell about ELITEA` for
   `HISTORY-TITLE-TEST: Tell me about ELITEA`). Asserted by distinctive-token containment.

Neither is a defect (reverse-masking guard) — asserting the stale case text would be reverse-masking.

---

## Known Defects

| # | Step | Behaviour | Handling |
|---|---|---|---|
| #1658 | 7 | History entry renders no timestamp/date indicator (API has `created_at`/`updated_at`; UI drops them) | `expect.soft()` + `# Known defect: #1658` |
| #1659 | 8 / Final State | History entry renders no conversation preview (upstream issue 5723 unshipped) | `expect.soft()` + `# Known defect: #1659` |

Closed, enumerable set of two, same flow, each independently deterministic + single-cause + open +
linked → one sanctioned-RED signature per `.agents/testing.md` § Merge gate (closed-set variant).
The gate must record **which** members fired across the three runs. Any other failure blocks.

**#1581 ("send button never enables") is not applicable** — disproved again here with real typing.

---

## Blocked Steps

None. All eight steps executed; two fail for filed, linked product gaps rather than for anything that
stopped exploration.

---

## Gotchas (carried into the surface digest)

- History entry DOM = title only; no timestamp, no preview, no `title`/`aria-label` (#1658/#1659).
- Title is an LLM paraphrase over `conversation_name_updated`; assert token containment, never equality.
- New chat **before** the distinctive message, or the message joins the restored conversation.
- Client prepends the created conversation locally, so the count can exceed the server's ~20 cap.

---

## Implementer amendments (2026-08-22, `tests/2427-history-session-preview-and-title`)

Shipped as
`automation/tests/ui/support_assistant/test_support_assistant_history_title_preview.py::TestSupportAssistantHistoryTitleAndPreview::test_history_entry_shows_title_timestamp_and_preview`
— the file/class/method shape § Suggested location proposed, unchanged.

1. **The baseline history count is read by opening the panel in Step 1 and closing it again.**
   The AFS asked for "the history count before the send" without saying how; the count only exists
   while the dropdown is rendered. Clicking `support-assistant-history-button` a second time closes
   it (`ChatHeader.tsx:49` toggles `showHistory`; the outside-click handler does *not* fire, because
   the button lives inside the `historyDropdownRef` wrapper). The panel is closed before touching the
   composer so it cannot overlay the message area or turn the New-chat click into a dismiss.
2. **Both soft assertions run with `timeout=1000`, not the default 5 s.** The entry's text is already
   resolved by the hard token assertion immediately above them, so a correctly built entry would
   match instantly; the short timeout removes ~8 s of dead wait from every RED-by-design run without
   weakening either assertion (same reasoning, and the same neighbour precedent, as
   `test_attach_unsupported_file_format_error.py`'s `#1121` soft assert).
3. **The greeting is the copy-button baseline.** A New chat opens with exactly one completed
   assistant greeting (digest quirk 10), so the spec asserts `to_have_count(1)` after each New chat
   and `to_have_count(2)` for the reply — a deterministic settle that also guarantees the previous
   conversation's messages have been cleared before any baseline is read.

**Implementation run (headless, 89.7 s, 2026-08-22):** every hard assertion passed on the first
attempt, zero reruns. The live title reproduced the analyst's observation byte-for-byte —
`HISTORY-TITLE-TEST: Tell about ELITEA` for `HISTORY-TITLE-TEST: Tell me about ELITEA` — on an
independent run, which is what makes the Step-8 verbatim-message assertion a genuine discriminator
rather than an accident of one generation. Both soft assertions failed with the entry's full text as
the actual value (`HISTORY-TITLE-TEST: Tell about ELITEA` — no timestamp, no preview), i.e. the
closed set {#1658, #1659} fired together and nothing else was red. Console and pageerror channels
were empty.
