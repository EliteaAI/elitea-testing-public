# Test Case: Expand widget during active generation does not restart the response

## Metadata

- **TMS ID**: ELITEA-2426
- **Source case**: `.agents/automation/support-assistant-w02/cases/ELITEA-2426.md` (intake snapshot of
  `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-2426_*.md`)
- **Priority**: l2 (case priority `medium`)
- **Module**: support-assistant · **Type**: functional
- **Environment explored**: `http://localhost:5173/chat` — EliteaUI on `automation/testids`,
  `../elitea_assistant` aliased live (`VITE_ASSISTANT_LOCAL=1`), DEV backend
- **User set**: `${TEST_USER}` (localhost auto-auth via `VITE_DEV_TOKEN`; `auth_state` on deployed envs)
- **Analyst**: qa-engineer (Sage), batch `support-assistant-w02`
- **Analysed**: 2026-08-22 — all 6 steps executed live end-to-end, twice (72.7 s and 91.0 s sessions)
- **Status**: `ready-for-automation` — product behaves correctly; **no defect found**
- **Filed**: #1662 (`question` + `case-text-drift`, Steps 4-5 — the case asserts token streaming this
  surface never produces; product is correct, case text is stale)

---

## Classification Rationale

`ready-for-automation` — fresh spec. The flow ran clean end-to-end and the behaviour under test
(expanding mid-generation neither restarts nor drops the in-flight response) **holds**.

**Why Steps 4-5 are re-expressed rather than asserted literally — the reverse-masking guard.**
The case asks to verify that "the response stream continues from where it was" and that "no
previously streamed tokens are lost". **The Support Assistant never renders partial text**, so
there are no partial tokens to continue from or lose. Measured live, sampling every 150 ms across
two independent runs: the assistant bubble holds **0 characters** for the entire generation window
and then jumps to the complete answer in a single sample (0 → 474 chars, run 1; 0 → 707 chars,
run 2), with the completed-response copy button appearing in that same sample.

Root cause, read in source (not inferred): the Support Assistant is an *agent*, so the backend emits
`agent_llm_chunk` — which `chat.hook.ts:258-266` maps to a **status message only, never content** —
and then one terminal `agent_response` that assigns the whole body at once
(`chat.hook.ts:268-281`: `content: responseContent, isStreaming: false`). The token-append branch
(`chunk` / `AIMessageChunk` → `content: m.content + chunk`, `:238-250`) is unreachable here, and the
client-side typewriter (`AnimatedMessage` + `useTypewriter`, 3 chars / 16 ms) is **dead code on this
surface**: `isAnimating` is only ever assigned `false` (`chat.hook.ts:71`, `:302`) — never `true`.

Per `test-automation-workflow` § Reverse-masking guard, the live contract is what gets asserted and
the stale wording is filed as a **clarification** (#1662), not a defect. Steps 4-5 are therefore
mapped onto the honest observables that carry the same intent — see § Coverage Map:

| Case wording | Honest observable asserted instead |
|---|---|
| 4 — "does NOT restart from the beginning" | Exactly **one** `support_predict` WebSocket frame for the whole flow; generation still in flight immediately after the expand click; assistant message-item count unchanged across the expand (no second/duplicate message) |
| 5 — "no previously streamed tokens are lost" | The rendered assistant text **never decreases** across the flow, and the message that completes is the same single item that was in flight |

**Why not `blocked`.** Nothing stopped exploration and nothing needs simulating — every step ran
against the live system and produced a real, assertable observable. The unproducible thing is
*partial text*, and the case's actual subject (no restart, no loss) is fully observable without it.

**Why not `already-covered`.** `test_support_assistant_smoke.py::TestSupportAssistantViewModes::test_expand_collapse_fullview`
(merged, `automation/tests/ui/support_assistant/test_support_assistant_smoke.py:376-406`) expands and
collapses an **idle** widget and asserts only the `--expanded` modifier class. It sends no message,
never enters a generation window, and would pass identically if expanding mid-generation killed the
request outright. Verified:

```
grep -rn "expand\|fullview\|Stop generation\|streaming" automation/tests/ui/support_assistant/*.py
  → only test_expand_collapse_fullview (idle expand/collapse); zero hits for streaming / Stop generation
```

**Why not `extend-existing`.** The nearest candidate is that same idle expand/collapse test, whose
whole body is two toggle clicks with 500 ms animation waits. This case needs a fresh conversation, a
live ~90 s LLM round trip, a WebSocket frame collector armed before navigation, and in-flight-state
sampling — a near-rewrite, which § Classify findings routes to a fresh spec.

---

## Preconditions

- User is logged in (localhost: automatic via `VITE_DEV_TOKEN`).
- EliteaUI dev server on `automation/testids` with `VITE_ASSISTANT_LOCAL=1`
  (see digest quirk 44 — a testid edit needs a vite restart + `rm -rf node_modules/.vite`).
- The WebSocket frame collector must be armed **before** the first `page.goto` —
  `page.on("websocket")` only fires for sockets opened after it is attached (digest quirk 8).
- **New chat first.** The widget restores the previous conversation on mount (digest quirks 2/30/65),
  so a fresh session is required before any baseline count is taken.

---

## Test Data

| Field | Value |
|---|---|
| Prompt | `List all ELITEA toolkits and describe each one in detail` (the case's prompt, `in detail` appended — a long-answer prompt; the exact wording does not matter, only that generation lasts long enough to click Expand inside it) |
| Observed generation window | **72.5 s** (run 1) and **86.6 s** (run 2) from send to content — a very wide window; expanding at t≈8 s left ~80 s of in-flight generation |
| Project context | `399` (personal "Private") — irrelevant to this case; the answer's *content* is never asserted |

---

## How this surface actually works (read this before writing the test)

1. **Generation has exactly two visible states, and neither is growing text.**
   - *In flight*: the **Stop generation** button replaces Send (`MessageInput.tsx:298-306`,
     rendered when `isStreaming`), and a cycling **status message** shows above the bubble
     (`MessageItem.tsx:48`). Observed sequence, run 2: `Starting up...` (t=3.9 s) →
     `Looking things up...` (37.6 s) → `Consulting knowledge base...` (39.8 s) →
     `Looking things up...` (75.5 s) → `Consulting knowledge base...` (78.4 s) →
     `Looking things up...` (79.5 s) → `Writing response...` (84.1 s).
     **The status text cycles and revisits earlier values — never assert a monotonic status
     progression, and never assert a specific status string.**
   - *Complete*: content + copy button appear together in one frame; Stop is replaced by Send.
2. **The assistant message item mounts immediately** with `data-role="assistant"` and an empty
   bubble, so an item-count delta is **not** a reply-ready signal (digest quirk 9). The
   completed-reply signal is the **copy button** count delta — `CopyButton` renders only when
   `content && !isStreaming && !isAnimating` (`MessageItem.tsx:74-80`).
3. **Expand is a pure className toggle on the same DOM node** — `ChatWindow.tsx:71`
   (`elitea-assistant-window${expanded ? ' elitea-assistant-window--expanded' : ''}`), driven by
   `toggleFullscreen` in `EliteaAssistant.tsx:78/145`. The chat state (`useChat`) lives **above**
   `ChatWindow`, and `MessageItem` is `memo`'d, so expanding cannot unmount the message list. This
   is *why* the case passes — worth knowing, but the test must still assert it observationally.
4. **The expand button is a toggle and its `aria-label` never changes** — it reads
   `"Expand chat"` in both states; only the tooltip text flips (`ChatHeader.tsx:129-134`).
5. **Expand geometry is animated.** Right after the click the widget measures `684×644`, settling
   through `716×674` to `720×678` (viewport 1920×1080). **Assert the state signal, not pixels** —
   a geometry assertion taken immediately after the click will read a mid-transition value.
6. **One send = one `support_predict` frame** (digest § context payload). This is the protocol-level
   proof of "did not restart", and it is captured passively — pure observation, no interception.

---

## Execution Evidence (live, 2026-08-22, `http://localhost:5173`, headless)

Timeline JSON: `test-results/json/ELITEA-2426-timeline-run2.json` (run 2, the canonical run — expand
clicked *during* generation) and `test-results/json/ELITEA-2426-timeline.json` (run 1 — expand
clicked at the first non-empty text sample; that sample turned out to be *after* generation
finished, which is how the atomic-delivery finding surfaced).
Screenshot: `test-results/screenshots/ELITEA-2426-step-06-fullview-complete-run2.png`.

**Run 2 — the case as written, executed:**

| t (s) | Observation |
|---|---|
| 0.0 | Fresh session after New chat: 1 assistant item (greeting, 44 chars), 1 copy button, widget `460×480`, no `--expanded` |
| 0.0 | Prompt sent → **1** `support_predict` frame emitted (`conversation_uuid`, `content`, `support_assistant_context.project_id: 399`) |
| 3.9 | Generation in flight: assistant items 1 → **2**, new bubble `len=0`, **Stop generation visible**, status `Starting up...` |
| **8.07** | **Step 3 — Expand clicked while in flight** (Stop visible, status `Starting up...`, `len=0`) |
| 8.09 | Immediately after: widget has `--expanded` (`684×644`, mid-animation); **Stop still visible**; status still `Starting up...`; assistant items still **2** (no duplicate, none lost) |
| 37.6-84.1 | Generation continues in full view for a further **82 s**, status cycling through 6 more transitions; widget stays `--expanded` for every one of the 463 samples |
| 90.54 | **Completes in full view**: `len` 0 → **707** chars in one sample, copy buttons 1 → **2**, Stop gone |
| 91.0 | Final: expanded `720×678`, 2 assistant items, 3 items total, **1** `support_predict` frame for the whole flow, **0** console errors, **0** `pageerror` |

**Invariants measured across all 463 samples:** rendered text length never decreased (`LEN DROPS: []`);
`expanded` never flipped back to `False` after the click; assistant item count never exceeded 2.

**Run 1 (independent, same conclusions):** 1 `support_predict` frame, 0 console errors, text atomic
0 → 474 chars in one 150 ms sample, expand at t=72.6 s → `--expanded` applied, no text loss.

---

## Handles Reference

**Locator policy is testid-only** (`.agents/testing.md` § Locator policy). Provenance verified with a
fresh `git fetch origin` in **both** repos on 2026-08-22.

| # | Element | Handle (primary) | Provenance | Used in |
|---|---|---|---|---|
| 1 | Sidebar launcher | `sidebar-support-assistant-button` | EliteaUI — `on automation/testids only (awaiting human promotion to main)` | Step 1 |
| 2 | Widget window | `support-assistant-widget` | elitea_assistant — `on automation/testids only` | Steps 1, 3, 6 |
| 3 | **Expanded state** | **`testid needed`: add `data-expanded={expanded}`** to the element that already carries `support-assistant-widget` (`ChatWindow.tsx:71-72`); filter as `[data-testid="support-assistant-widget"][data-expanded="true"]` | `needs-adding` | Steps 3, 6 |
| 4 | New chat | `support-assistant-new-chat-button` | elitea_assistant — `on automation/testids only` | Step 1 |
| 5 | Message input | `support-assistant-message-input` | elitea_assistant — `on automation/testids only` | Step 2 |
| 6 | Send button | `support-assistant-send-button` | elitea_assistant — `on automation/testids only` | Step 2 |
| 7 | **Expand toggle** | **`testid needed`: `support-assistant-expand-button`** — `ChatHeader.tsx:129-134`, the `<button class="elitea-assistant-header-action" aria-label="Expand chat">` inside the `Tooltip` | `needs-adding` | Step 3 |
| 8 | **Stop generation** | **`testid needed`: `support-assistant-stop-button`** — `MessageInput.tsx:298-306`, rendered only while `isStreaming` | `needs-adding` | Steps 2, 3, 4, 6 |
| 9 | **Status message** | **`testid needed`: `support-assistant-status-message`** — `StatusMessage` rendered at `MessageItem.tsx:48`; live class today is `.elitea-assistant-status-message` | `needs-adding` | Steps 2, 4 |
| 10 | Message item (assistant) | `support-assistant-message-item` + `[data-role="assistant"]` (attribute already present, `MessageItem.tsx:25`) | elitea_assistant — `on automation/testids only` | Steps 2, 4, 5 |
| 11 | Message bubble | `support-assistant-message-bubble` | elitea_assistant — `on automation/testids only` | Steps 5, 6 |
| 12 | Copy button (reply-complete signal) | `support-assistant-message-copy-button` | elitea_assistant — `on automation/testids only` | Steps 1, 6 |

**Four `needs-adding` rows (#3, #7, #8, #9)** — all in the **connected first-party repo**
`../elitea_assistant` (canon #705: *not* a #579 third-party waiver), on its own `automation/testids`
branch, attribute-only additions with zero functional impact. Row #3 is a `data-*` **state attribute**
on an element that already has a stable testid — the shape `.agents/testing.md` § Locator policy
requires (PR #581 ruling), never a state-switched testid. The existing page object reads the
`--expanded` **CSS modifier class** instead (`support_assistant_page.py:289-303`, `is_fullview_mode()`,
a legacy raw-class read); once `data-expanded` exists, prefer the attribute filter for this spec.

**Non-DOM handle — WebSocket frames.** Event name `support_predict`
(`chat.constants.ts:3`). Capture passively, armed before the first navigation:

```python
frames = []
page.on("websocket", lambda ws: ws.on("framesent", lambda f: frames.append(f)))
# parse: re.match(r'^\d+(\[.*\])$', frame) -> json.loads -> [event, payload]
predicts = [f for f in frames if '"support_predict"' in f]
```

---

## Implementation Notes

1. **Reuse what is merged.** `SupportAssistantPage` already has `expand_to_fullview()` /
   `is_fullview_mode()` (`automation/pages/support_assistant_page.py:289-303, 596-620`) — but they
   bind the legacy `fallback=` `expand_button` field (`:70`) and read the raw modifier class. Add
   class-level `LocatorDescriptor(testid=…)` fields for the four new testids and new helpers
   alongside them; **do not** edit the legacy fields — they have other callers (digest, ELITEA-2418
   implementation note).
2. **The in-flight window is the whole test.** Click Expand once the Stop button is visible
   (observed at t≈3.9 s; the button is the product's own "generation in flight" signal). Do **not**
   use a fixed delay. `expect(stop_button).to_be_visible(timeout=60_000)` is the wait.
3. **Timeouts must be wide.** Measured generation: 72.5 s and 86.6 s; total spec runtime ~95-110 s.
   Use `240_000` for the completion wait (the copy-button count delta), consistent with ELITEA-2424/2425.
4. **Assert the state attribute, not geometry** (see § How this surface works, point 5).
5. **Baseline, never absolutes.** Take the copy-button and assistant-item counts *after* New chat
   (a fresh session has exactly one greeting + one copy button — digest quirk 10) and assert deltas.
   `expect(copy_buttons).to_have_count(1)` right after New chat is the strongest fresh-session settle
   (digest note 69).
6. **`allure.step("Step N — …")` per AFS step** (mandatory, `.agents/testing.md` § Step reporting).
7. **Console assertion**: filter to `type == "error"` — the Vite dev server logs a
   `Module "stream" has been externalized…` warning on every load (digest quirk 6).
8. **Markers**: `p2`, `ui`, `support_assistant`, `regression`, `slow` (≈2 min runtime).
9. **Suggested location**: new file
   `automation/tests/ui/support_assistant/test_support_assistant_expand_during_streaming.py`.

**Step-by-step spec:**

1. **Setup** — arm the WebSocket collector, `page.goto('/chat')`, click
   `sidebar-support-assistant-button`, wait for `support-assistant-widget`, click
   `support-assistant-new-chat-button`, `expect(copy_buttons).to_have_count(1)`.
   *Assert*: widget visible; `data-expanded` is `"false"` (compact mode).
2. **Send the long prompt** — fill `support-assistant-message-input`, click
   `support-assistant-send-button`.
   *Assert*: `support-assistant-stop-button` becomes visible (timeout 60 s) — generation is in
   flight; the status message is visible; assistant item count = baseline + 1; the in-flight
   bubble's text is captured as `pre_expand_text` (empty today — captured, not assumed).
3. **Expand while in flight** — click `support-assistant-expand-button`.
   *Assert*: widget `data-expanded="true"`.
4. **Not restarted** — immediately after the click, still inside the generation window:
   *Assert*: `support-assistant-stop-button` **still visible**; assistant item count **unchanged**;
   exactly **1** `support_predict` frame captured so far.
5. **Nothing lost** — *Assert*: the in-flight bubble's current text `.startswith(pre_expand_text)`
   (a real prefix guard the moment token streaming ever ships; trivially true today), and the
   assistant item count is still baseline + 1 (the in-flight message was neither replaced nor duplicated).
6. **Completes normally in full view** — wait for `support-assistant-message-copy-button` count =
   baseline + 1 (timeout 240 s).
   *Assert*: final bubble text is non-empty (`len > 100`) and still `.startswith(pre_expand_text)`;
   widget **still** `data-expanded="true"`; Stop button gone; total `support_predict` frames == **1**;
   assistant item count = baseline + 1; no console errors.

---

## Coverage Map

### Axis 1 — every case element accounted for

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | localhost `VITE_DEV_TOKEN` auto-auth | Setup | covered |
| 1 Open the Support Assistant widget in compact/widget mode | page/section loads | AFS step 1 | widget visible + `data-expanded="false"` | covered |
| 2 Send a long-response prompt | completes without error, expected UI state | AFS step 2 | Stop button visible, status message visible, assistant item = base+1 | covered |
| 3 While actively streaming, click Expand (↗) | completes without error, expected UI state | AFS step 3 | `data-expanded="true"` after the click, clicked while Stop was visible | covered |
| 4 Stream continues from where it was — does NOT restart | condition holds | AFS steps 4-5 | **re-expressed** (#1662): 1 `support_predict` frame total; Stop still visible right after expand; item count unchanged | covered *(clarification — see § Known Deviations)* |
| 5 No previously streamed tokens lost after expanding | condition holds | AFS steps 5-6 | **re-expressed** (#1662): text never decreases (`startswith(pre_expand_text)` at expand and at completion); same single in-flight item completes | covered *(clarification)* |
| 6 Response completes normally in full-view mode | condition holds | AFS step 6 | copy-button delta, non-empty body, `data-expanded` still `"true"`, Stop gone | covered |
| Expected Final State: response completes normally in full-view | — | AFS step 6 | same as above | covered |
| Pass criterion: all steps complete without errors | — | AFS step 6 | zero console `error` messages, zero `pageerror` | covered |

### Axis 2 — asserted beyond the case

| Extra observable | Why |
|---|---|
| Exactly **one** `support_predict` frame for the whole flow | The only protocol-level proof of "did not restart"; without it a silent re-send would still look correct in the DOM (digest quirk 8 / § context payload) |
| Assistant message-item count unchanged across the expand | Catches the other restart shape — a *new* message replacing the in-flight one, which a text-only check cannot see while text is empty |
| Widget still `data-expanded="true"` at completion | Guards the inverse regression: an arriving response silently collapsing the widget back to compact |
| Zero console errors / `pageerror` | Standard side-channel check (`test-case-analysis` § Execute step 3) |
| Fresh session via New chat before the baseline | The widget restores the previous conversation on mount (digest quirks 2/30/65) — without it the baseline counts are non-deterministic |

---

## Fidelity Declaration

**No substitutions.** Every asserted value is produced by the system:

| Mechanism | Classification |
|---|---|
| `page.on("websocket")` + `framesent` | **Passive observation**, not substitution — no `route`/`fulfill`, nothing intercepted or altered. Established precedent on this surface (ELITEA-2424/2425, merged). |
| Live LLM round trip (~90 s) | The real producer. No mocked response, no injected state; the case's observables (in-flight state, completion, message identity) all come from the product. |
| `data-expanded` attribute (to be added) | A product-rendered attribute reflecting product state — the policy-required shape for a state assertion. |

No `page.route`, no `route.fulfill`, no `page.evaluate` for interaction, no `monkeypatch` anywhere in
the specced flow. The analysis probe used `page.evaluate` **read-only**, to sample DOM state every
150 ms; the implemented spec needs none of it — Playwright's own expect-polling covers every assertion.

---

## Known Deviations (case text vs live product) — filed as #1662

- **Steps 4-5 presuppose token-by-token streaming; this surface has none.** The bubble is empty for
  the entire generation window, then renders the complete answer in one frame (measured twice at
  150 ms sampling). Cause: agent-mode delivery (`agent_llm_chunk` → status only; `agent_response` →
  whole body, `chat.hook.ts:258-281`) plus a typewriter path that never activates
  (`isAnimating` is only ever set `false`). **The product is correct; the case text is stale** —
  filed as a clarification (`question` + `case-text-drift`), not a defect, per the reverse-masking
  guard. The AFS asserts the live contract and preserves the case's intent (see § Classification
  Rationale table).
- **Step 3's "(↗)" Expand button carries no `data-testid`** — same gap ELITEA-1801 recorded; now
  specced as `needs-adding` (row #7) rather than accepted as a raw handle.

---

## Known Defects

None. Both live runs completed cleanly: zero console errors, zero `pageerror`, one `support_predict`
frame each, no lost or duplicated messages, the widget staying expanded throughout.

---

## Blocked Steps

None — all 6 steps executed live.

---

## Gotchas (carried into the surface digest)

- The Support Assistant renders **no partial text, ever** — status messages are the only in-flight
  feedback, and the typewriter (`AnimatedMessage`/`useTypewriter`) is dead code (`isAnimating` never
  `true`). Any case asking to observe progressive text arrival on this surface is case-text drift.
- The status message **cycles and revisits earlier values** (`Looking things up...` appeared three
  times in one run) — never assert progression or a specific string.
- Expand geometry is **animated** (`684×644` → `716×674` → `720×678`): assert the state signal, not pixels.
- `Stop generation` visible is the cleanest "generation in flight" gate — it exists only while
  `isStreaming`, and it is the product's own signal.
