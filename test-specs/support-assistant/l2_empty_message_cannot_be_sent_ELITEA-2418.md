# Test Case: Empty message cannot be sent

## Metadata
- **TMS ID**: ELITEA-2418
- **Source case**: `.agents/automation/support-assistant-w01/cases/ELITEA-2418.md` (intake snapshot of
  `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2418_empty-message-cannot-be-sent.md`)
- **Priority**: l2 (case priority `high`)
- **Environment Explored**: local (`http://localhost:5173/chat`, EliteaUI `automation/testids`, dev backend via `VITE_DEV_TOKEN`)
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token)
- **Analyst**: qa-engineer (Sage)
- **Analysed**: 2026-08-22 (live, headless pytest scratch invocation, 16.3 s)
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/support-assistant/_surface.md`

## Classification

**Status: `ready-for-automation`**

All six case steps execute exactly as authored against the live product. Empty input keeps the Send
button disabled, Enter on an empty (and on a whitespace-only) input sends nothing and fires **zero**
POST requests, a single space keeps the button disabled, and typing `Hello` enables it (the `disabled`
attribute is removed entirely). No blockers, no defects, no substitutions.

> **Supersedes the previous `defect-found` analysis of this same case** (commit `d472a6103`, which
> filed bug **#1581** "Send button never enables when typing actual text"). That finding **does not
> reproduce** — re-verified twice on 2026-08-22 (an independent triage pass at 00:02 UTC, commented on
> #1581, and this analysis run). The original observation came from synthetic `input.value` assignment
> + hand-dispatched `InputEvent`, which a React controlled `<textarea>` ignores — the component's state
> (`text`) never changed, so `isSendDisabled` stayed true. Real typing (`fill` / `type` /
> `pressSequentially`) works. **#1581 is stale and should be closed by a human** (agents never close);
> it is NOT a known defect for this test, and the implementer must NOT soft-assert Step 6.

## Preconditions

- User logged in (localhost: auto-authenticated via `VITE_DEV_TOKEN`; deployed envs: `auth_state` fixture)
- On any page where the sidebar Support Assistant launcher is visible — `/chat` used here

## Test Data

None. The case exercises control-state transitions driven by input content only
(empty / single space / three spaces / `Hello` / `  hi  `).

## Execution Evidence

Executed 2026-08-22 via a throwaway pytest spec driving the real browser (`HEADLESS=true`,
`tests/ui/support_assistant/test_scratch_2418.py`, deleted after the run). Values below are verbatim
from that run's JSON dump.

### Step 1 — Open the Support Assistant widget

**Action:** real pointer click on the sidebar launcher wrapper `[data-tour="sidebar-support-assistant"]`
(see § Gotchas — a click on `button.elitea-assistant-button` is intercepted by the MUI tooltip clone).

**Observed:** widget opens; `.elitea-assistant-header-title` = **"ELITEA Support"**;
`.elitea-assistant-window` visible. Note the header title is **"ELITEA Support"**, not the
"Elitea Assistant" string the prior AFS recorded.

**Screenshot:** `automation/test-results/screenshots/ELITEA-2418-step-01-widget-opened.png`

### Step 2 — Ensure the message input field is empty

**Observed:** `textarea.elitea-assistant-input` (`id="elitea-assistant-message-input"`,
placeholder `"Type a message..."`) → `input_value() == ""`. ✓
The widget **restored a prior conversation**: 16 `.elitea-assistant-message-wrapper` elements were
present on open. The input is empty regardless — but see § Implementation Notes for why Step 4 must
assert a **count delta**, never an absolute count.

### Step 3 — Verify the Send button is disabled

**Observed:** `button.elitea-assistant-send-button` (`aria-label="Send message"`) →
`get_attribute("disabled") == ""` (present) and `is_disabled() == True`. ✓

### Step 4 — Press Enter, verify no message is sent and the conversation is unchanged

**Action:** click the input to focus, `press("Enter")`, wait 1.5 s.

**Observed:**
- message-wrapper count **16 → 16** (unchanged) ✓
- **zero POST requests** captured on the page during the Enter window (network-level proof, stronger
  than the DOM read alone) ✓
- input value still `""`, Send button still disabled ✓

**Screenshot:** `automation/test-results/screenshots/ELITEA-2418-step-04-enter-no-send.png`

### Step 5 — Type a single space; Send stays disabled

**Observed:** value `" "`; `disabled` attribute present; `is_disabled() == True`. ✓
**Extra (beyond the case):** Enter pressed with the whitespace-only input → count **16 → 16**, zero
POSTs, and the input **retains** the space (`" "` — the product does not clear it). ✓

**Screenshot:** `automation/test-results/screenshots/ELITEA-2418-step-05-space-disabled.png`

### Step 6 — Type actual text; Send becomes enabled

**Action:** clear the input, then `type("Hello", delay=40)` (real per-character key events).

**Observed:** value `"Hello"`; `get_attribute("disabled") == None` (**attribute removed**);
`is_disabled() == False` / `is_enabled() == True`. ✓ **No defect.**

**Screenshot:** `automation/test-results/screenshots/ELITEA-2418-step-06-text-enabled.png`

### Extra boundary probes (beyond the case text)

| Input | Send button |
|---|---|
| `"   "` (three spaces) | disabled ✓ |
| `"  hi  "` (padded text) | **enabled** ✓ — the guard is `text.trim()`, not "starts with non-space" |
| `""` (cleared again) | disabled ✓ — the transition is reversible |

### Side channels

Console over the whole run: **one** message, a Vite dev warning
(`Module "stream" has been externalized for browser compatibility…`). No errors, no failed requests
attributable to the widget.

## Product source (intended contract — decisive)

`../elitea_assistant/src/components/chat/MessageInput.tsx`:

```tsx
const isSendDisabled = useMemo(
  () => Boolean(disabled || isUploading || !attachmentsValid || !text.trim()), ...);   // L105-108

const handleSend = () => {
  const trimmed = text.trim();
  const completedAttachments = attachments.filter(a => a.status === COMPLETED && a.filepath);
  if (!trimmed && completedAttachments.length === 0) return;                            // L114-124
  ...
};

const handleKeyDown = e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } };  // L126-131
```

So: trim-based disable, Enter routed through the same `handleSend` early-return. Live behaviour and
source agree — the case text is accurate as authored.

## Handles Reference

Locator policy is **testid-only** (`.agents/testing.md` § Locator policy). `../elitea_assistant/src`
currently contains **zero** `data-testid` attributes, so every handle below is `needs-adding` in the
**connected repo** (`EliteaAI/elitea_assistant`, branch `automation/testids`) per
`.agents/workflow.md` § Connected repos — this is work to do, **not** a #579 third-party waiver
(canon #705). The raw handles in the "observed as" column are what the analyst drove; they are the
grandfathered fallbacks already in `support_assistant_page.py`, not a licence to add new ones.

> **Amended during ELITEA-2418 implementation (2026-08-22):** all six testids have been ADDED and
> pushed. PROVENANCE below is the shipped truth, replacing the analyst's `needs-adding` rows.
> EliteaUI `automation/testids` commit `37176b46`; `elitea_assistant` `automation/testids` commit
> `b8a287b`. Both are `on-automation/testids only (awaiting human promotion to main)`.

| # | Element | Testid (added) | Where (file) | Observed as (analyst transit) | PROVENANCE |
|---|---|---|---|---|---|
| 1 | Sidebar launcher (the clickable target) | `sidebar-support-assistant-button` | **EliteaUI** `src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx:294-298` (the `<Box data-tour=… onClick={onToggleAssistant}>`) | `[data-tour="sidebar-support-assistant"]` | added — EliteaAI/EliteaUI@37176b46, on `automation/testids` only |
| 2 | Widget window | `support-assistant-widget` | `elitea_assistant` `src/components/chat/…` window container | `.elitea-assistant-window` | added — EliteaAI/elitea_assistant@b8a287b, on `automation/testids` only |
| 3 | Widget header title | `support-assistant-widget-title` | `elitea_assistant` header component | `.elitea-assistant-header-title` (text "ELITEA Support") | added — EliteaAI/elitea_assistant@b8a287b, on `automation/testids` only |
| 4 | Message input | `support-assistant-message-input` | `elitea_assistant` `src/components/chat/MessageInput.tsx:275-287` (`<textarea>`) | `textarea.elitea-assistant-input` | added — EliteaAI/elitea_assistant@b8a287b, on `automation/testids` only |
| 5 | Send button | `support-assistant-send-button` | `elitea_assistant` `src/components/chat/MessageInput.tsx:296-307` | `button.elitea-assistant-send-button` / `[aria-label="Send message"]` | added — EliteaAI/elitea_assistant@b8a287b, on `automation/testids` only |
| 6 | Message item (repeated — for the unchanged-conversation count) | `support-assistant-message-item` | `elitea_assistant` `src/components/chat/MessageItem.tsx:22` (wrapper div) | `.elitea-assistant-message-wrapper` | added — EliteaAI/elitea_assistant@b8a287b, on `automation/testids` only |

**Disabled state is read off the element itself** (`disabled` attribute / `is_disabled()`), not a
state-suffixed testid — consistent with `.agents/testing.md` § Locator policy ("testid = stable
identity; state via attributes"). `disabled` is a native HTML attribute, so no `data-*` addition is
needed.

## Coverage Map

### Axis 1 — TMS Case Coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition — user logged in | holds | `auth_state` fixture / dev token | setup | ✓ covered |
| Step 1 — open the widget | page/section loads | Step 1: click launcher wrapper, wait for title | widget window visible + title == "ELITEA Support" | ✓ covered |
| Step 2 — input is empty | condition holds | Step 2: read input value | `input_value() == ""` | ✓ covered |
| Step 3 — Send button disabled | condition holds | Step 3: read button state | `expect(send).to_be_disabled()` | ✓ covered |
| Step 4 — Enter sends nothing, conversation unchanged | control responds, state unchanged | Step 4: focus + Enter, compare message count **delta**, capture POSTs | count(after) == count(before) **and** zero POSTs during the window **and** button still disabled | ✓ covered |
| Step 5 — single space keeps Send disabled | field accepts input, button stays disabled | Step 5: fill `" "`, read value + button | `input_value() == " "` **and** `to_be_disabled()` | ✓ covered |
| Step 6 — actual text enables Send | field accepts input, button enables | Step 6: type `Hello`, read value + button | `input_value() == "Hello"` **and** `expect(send).to_be_enabled()` | ✓ covered |
| Expected final state | Send enabled after real text | Step 6 assertion | same as above | ✓ covered |
| Pass criterion — "no errors" | no errors on any step | console capture across the test | no console `error` entries (Vite `stream` warning is dev-server noise, filter by type=="error") | ✓ covered |

### Axis 2 — Additional Coverage (beyond the case)

| Observable | Why asserted | Grounding |
|---|---|---|
| **Zero POST requests** during the Enter window | "no message is sent" asserted at the network layer, not only by a DOM count that could lag | live run captured 0 POSTs for both empty and whitespace-only Enter |
| Enter on a **whitespace-only** input also sends nothing | Step 4 tests Enter-on-empty and Step 5 tests the button on whitespace; the union (Enter + whitespace) is the actual regression risk in `handleSend`'s early return | `MessageInput.tsx:114-124`; verified live (16→16, 0 POSTs) |
| Three spaces → still disabled | proves the guard is `trim()`, not a single-space special case | verified live |
| `"  hi  "` (padded text) → **enabled** | the complementary half: leading whitespace must not suppress a valid message | verified live |
| Input cleared again → disabled again | the state transition is reversible, not a one-way latch | verified live |
| Input retains the typed space after Enter | documents that the product does not clear a rejected input | verified live |

## Blocked Steps

None.

## Known Defects

**None for this case.** Bug **#1581** (filed by the superseded analysis of this same case) is **stale
and non-reproducing** — see § Classification. It is still OPEN awaiting a human close; the implementer
must **not** add a `# Known defect: #1581` comment or a `expect.soft()` on Step 6. This spec is a
hard-green spec.

## Fidelity Declaration

**No substitutions.** Every observable — input value, `disabled` attribute, message count, request log,
console — was produced by the live product and read directly. Typing used real key events
(`Locator.type`, `Locator.fill`) and the launcher was opened with a genuine pointer click on the
element that carries the `onClick` handler (no `page.evaluate` click, unlike the legacy
`SupportAssistantPage.open_widget()`). No `route.fulfill`, no injected state, no API-seeded precondition.

## Implementation Notes

1. **Conversation baseline is NOT zero.** The widget restores the user's previous session (16 messages
   in this run). Step 4 must capture the count **before** Enter and compare, and must first wait for the
   restored list to settle (wait for the widget title, then for the message-item count to be stable /
   non-changing) — an absolute `to_have_count(0)` or `(1)` will false-fail. Alternatively the
   implementer may open a fresh session via the header **New chat** control as a precondition; the case
   does not require it, and the delta assertion is sufficient and less coupled.
2. **Launcher click:** click the sidebar wrapper element that owns `onClick` (handle #1), not
   `button.elitea-assistant-button` — the MUI `Tooltip` clone intercepts pointer events on the latter
   (`support_assistant_launcher_click_quirk` in role memory; verified again this run).
3. **Page object:** `automation/pages/support_assistant_page.py` already has `is_send_button_enabled()`
   and `is_input_empty()`, but both build locators **inside method bodies** and every field is a
   `fallback=` lambda — pre-policy tech debt (#25/#42). New/changed locators for this case must be
   class-level `LocatorDescriptor(testid=…)` fields once the six testids land. Prefer adding the
   testid-based fields alongside, and drive assertions through Playwright `expect()` on the descriptor's
   locator rather than the boolean helpers (a boolean read has no auto-retry).
4. **Testid work spans two repos** — handle #1 in `EliteaUI` (`automation/testids`), handles #2-#6 in
   `../elitea_assistant` (its own `automation/testids`, aliased live via `VITE_ASSISTANT_LOCAL=1`).
   Both are commit + push, terminal; a human promotes. Note the extra promotion hop for the connected
   repo (`.agents/workflow.md` § Connected repos) in the closure record.
5. **Console assertion:** filter to `type == "error"`. The Vite dev server emits a `stream`
   externalization **warning** on this page on every load — asserting "no console messages" would false-fail.
6. **No AI wait needed.** This case never sends a message, so none of the 33-135 s reply latency
   applies — the whole spec runs in ~15 s. Do not import `AI_RESPONSE_TIMEOUT` machinery.
7. **Markers:** `p2` (case priority high → l2), `support_assistant`, `ui`, `regression`.

## Recommendations

1. Implement as a fresh spec in `automation/tests/ui/support_assistant/` (no existing spec asserts the
   Send-button state machine — the only neighbour, `test_support_assistant_smoke.py:172`, asserts the
   input is *cleared after* a successful send, a different observable).
2. Add the six testids first (§ Handles Reference), then bind class-level `LocatorDescriptor(testid=…)`.
3. Ask a human to close **#1581** as not-reproducing (agents never close; the non-repro evidence is
   already commented on the issue).

## Implementation Record (appended by the implementer, 2026-08-22)

- **Spec:** `automation/tests/ui/support_assistant/test_support_assistant_empty_message.py`
  (`TestSupportAssistantEmptyMessage::test_empty_message_cannot_be_sent`) — GREEN 1/1, 13.9 s.
- **Page object:** six class-level `LocatorDescriptor(testid=…)` fields plus
  `open_widget_via_sidebar()`, `get_message_item_count()`, `set_message_text()` appended to
  `automation/pages/support_assistant_page.py`. Purely additive — the legacy `fallback=` fields and
  their callers are byte-identical.
- **Stronger network observable than the AFS specified.** The AFS's Axis-2 row asserts "zero POST
  requests" during the Enter window. Sending is **not** a POST: `chat.hook.ts:152` does
  `socket.emit(SOCKET_EVENTS.PREDICT, params)` over Socket.IO. The spec therefore asserts **no
  outbound WebSocket frame containing `predict`** during the window *in addition to* zero POSTs —
  a genuine "no message was sent" proof rather than a vacuous one. Same observable, stronger
  evidence; no scope change.
- **Settle window:** asserting an absence has no positive condition to wait on, so the two
  no-send windows use a single commented `page.wait_for_timeout(1500)` (`NO_SEND_SETTLE_MS`) —
  the documented exception to the no-sleep rule. `handleSend` emits synchronously, so 1.5 s is
  far more than a real send needs to become observable.
- **#1581 confirmed non-reproducing** — Step 6 is a hard `to_be_enabled()`, no soft assert, no
  `# Known defect` comment, exactly as the AFS directs.
