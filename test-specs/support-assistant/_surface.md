# Exploration digest — Support Assistant widget

Confirmed handles, waits and quirks from live runs on `http://localhost:5173`.
A **cache**, not a source of truth: verify each handle as you use it, and prune what drifted.

- Created 2026-08-22 (qa-engineer/Sage, batch `support-assistant-w01`, ELITEA-2418 run)

## Where the code lives (two repos)

| Piece | Repo / path |
|---|---|
| Sidebar launcher (the element with `onClick`) | **EliteaUI** `src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx:289-303` |
| Widget shell, messages, input, send | **`../elitea_assistant`** (`@eliteaai/elitea-assistant`) `src/components/chat/*.tsx` |

The assistant is a **connected first-party repo** (canon #705): testids belong in ITS `src/` on its own
`automation/testids` branch, aliased live into the dev server by `VITE_ASSISTANT_LOCAL=1`. It is **not**
a #579 third-party waiver. As of 2026-08-22 `../elitea_assistant/src` has **zero** `data-testid`
attributes — every handle below is a grandfathered raw fallback, tech debt to migrate, never precedent.

## Handles (verified live 2026-08-22)

| Element | Current raw handle | Testid to add |
|---|---|---|
| Sidebar launcher (click THIS) | `[data-tour="sidebar-support-assistant"]` | `sidebar-support-assistant-button` (EliteaUI) |
| Floating assistant button (do NOT click) | `button.elitea-assistant-button` | — |
| Widget window | `.elitea-assistant-window` (`--expanded` modifier when full view) | `support-assistant-widget` |
| Header title | `.elitea-assistant-header-title` → text **"ELITEA Support"** | `support-assistant-widget-title` |
| Message list | `.elitea-assistant-messages` | — |
| Message item (repeated) | `.elitea-assistant-message-wrapper` (`--user` / `--assistant` modifier) | `support-assistant-message-item` |
| Message input | `textarea.elitea-assistant-input`, `id="elitea-assistant-message-input"`, placeholder `Type a message...` | `support-assistant-message-input` |
| Send button | `button.elitea-assistant-send-button` / `[aria-label="Send message"]` | `support-assistant-send-button` |
| Stop button (generation only) | `button[aria-label="Stop generation"]` (replaces Send while streaming) | — |
| Attach button | `button[aria-label="Attach file"]` | — |
| Close | `button[aria-label="Close chat"]` | — |
| Typing indicator | `.elitea-assistant-typing-indicator` (3 × `.elitea-assistant-typing-dot`) | — |
| Message bubble (inside an item) | `.elitea-assistant-message--assistant` / `--user` | `support-assistant-message-bubble` |
| Copy-to-clipboard button (assistant responses only) | `button[aria-label="Copy to clipboard"]` (parent `.elitea-assistant-tooltip-trigger`) | `support-assistant-message-copy-button` (+ `data-copied`) |
| Tooltip popup (on hover) | `.elitea-assistant-tooltip` → text "Copy to clipboard" | — |

## Quirks that cost time

1. **Launcher click is intercepted.** A native click on `button.elitea-assistant-button` times out — a
   MUI `Tooltip` clone (`[data-mui-internal-clone-element="true"]`) eats the pointer events. Click the
   **wrapper** `[data-tour="sidebar-support-assistant"]` instead: a real user-equivalent gesture, first
   try, no `page.evaluate` needed (the legacy `SupportAssistantPage.open_widget()` still JS-clicks).
2. **The widget restores the previous conversation on open** — 16 messages in the ELITEA-2418 run. Never
   assert an absolute message count on a freshly opened widget; capture a baseline and assert the delta,
   or start a **New chat** first.
3. **Send-button contract** (`MessageInput.tsx:105-131`): `disabled = !text.trim() || disabled ||
   isUploading || !attachmentsValid`. Enter (without Shift) routes through the same `handleSend`, which
   early-returns on empty-trim with no attachments. So whitespace-only Enter is a no-op AND fires **zero
   POSTs**. A rejected input is **not** cleared. `"  hi  "` (padded) DOES enable the button.
4. **React controlled textarea** — synthetic `input.value = …` + hand-dispatched `InputEvent` does NOT
   update component state, so the Send button appears permanently disabled. This produced a false bug
   (#1581) that does not reproduce with real typing (`fill` / `type` / `pressSequentially`). Always type
   for real on this surface.
5. **Reply latency 33-135 s and NO token streaming** — the assistant message appears atomically
   (0 → ~1450 chars in one 500 ms sample). `AI_RESPONSE_TIMEOUT = 120_000` is tight, not generous. Wait
   on the message-count change, never a sleep. A case asking to observe "progressive arrival" cannot be
   satisfied here — route it.
6. **Console noise:** the Vite dev server logs a `Module "stream" has been externalized…` **warning** on
   this page every load. Filter console assertions to `type == "error"`.

## Existing automation

- `automation/pages/support_assistant_page.py` — full page object, but every field is a `fallback=`
  lambda and several helpers build locators inside method bodies (pre-policy tech debt #25/#42).
- `automation/tests/ui/support_assistant/test_support_assistant_smoke.py` — launcher open/close, send +
  receive, new chat, history, attachments. It does **not** cover the Send-button enable/disable state
  machine (only "input cleared after send", line 172).

## Related AFS in this folder

`l2_empty_message_cannot_be_sent_ELITEA-2418.md` (send-button state machine),
`lextend_launcher-visible-widget-opens-and-closes_ELITEA-1796.md`,
`lextend_send-message-receive-ai-response_ELITEA-1798.md`,
`lcovered_widget-conversation-state-persists-after-close-reopen_ELITEA-1797.md`.

## Resolved/added during ELITEA-2418 implementation (2026-08-22, test-automation-engineer)

**All six testids in the table above now EXIST** on the integration branches (they are no longer
"testid to add"): `sidebar-support-assistant-button` in EliteaAI/EliteaUI@37176b46
(`automation/testids`), and `support-assistant-widget` / `-widget-title` / `-message-input` /
`-send-button` / `-message-item` in EliteaAI/elitea_assistant@b8a287b (its own `automation/testids`).
Not yet on either repo's `main` — a human cherry-picks. Bind to them via the class-level
`LocatorDescriptor(testid=…)` fields now on `SupportAssistantPage` (`sidebar_launcher`, `widget`,
`widget_header_title`, `message_input_field`, `send_message_button`, `message_items`) plus
`open_widget_via_sidebar()` / `get_message_item_count()` / `set_message_text()` — the legacy
`fallback=` fields are untouched for their existing callers.

7. **The Vite dev server does NOT hot-reload edits made under OneDrive.** After adding the testids
   above, the running server kept serving the pre-edit modules — a plain `curl` of the module URL
   returned the OLD source, and `get_by_test_id` timed out even though the JSX on disk was correct.
   fs-watch does not fire reliably on this OneDrive-backed checkout. **Diagnose** with
   `curl -s http://localhost:5173/src/<path>.jsx | grep -c <testid>` (0 ⇒ stale), and for the
   connected assistant repo `curl -s 'http://localhost:5173/@fs<abs-path>.tsx'`. **Fix:** kill the
   `npm run dev` + `vite` PIDs, `rm -rf EliteaUI/node_modules/.vite`, restart, re-curl. Cost one
   full test rerun before it was identified.

8. **Sending is a WebSocket frame, not a POST.** `src/lib/hooks/chat.hook.ts:152` →
   `socket.emit(SOCKET_EVENTS.PREDICT, params)`. Asserting "no POST" alone is therefore a weak
   proof of "no message sent" — assert on outbound Socket.IO frames (`page.on("websocket")` +
   `ws.on("framesent")`, look for `predict` in the payload). Register the listener BEFORE
   navigation: `page.on("websocket")` only fires for sockets opened after it is attached.


## Copy-to-clipboard on assistant responses (verified live 2026-08-22, ELITEA-2419 run)

Source: `../elitea_assistant/src/components/shared/CopyButton.tsx`, rendered from
`src/components/chat/MessageItem.tsx:73`.

9. **The copy button is the response-COMPLETE signal.** `MessageItem.tsx:70-73` renders it only for
   `role === 'assistant' && content && !isStreaming && !isAnimating`. Waiting on
   `copy-button count > baseline` is the cheapest and most accurate "reply finished" wait on this
   surface — better than a message-count delta, which fires while the message is still streaming.
   `SupportAssistantPage.wait_for_response()` already uses it internally.

10. **A "New chat" is NOT empty — it starts with 1 assistant greeting**, therefore 1 copy button.
    Always capture a baseline count; never assert an absolute one (same shape as quirk 2).

11. **The copy confirmation is an SVG PATH swap that self-reverts after exactly 2000 ms.**
    `CopyIcon` → `CheckIcon`; `aria-label` (`"Copy to clipboard"`) and `className`
    (`elitea-assistant-header-action`) are **unchanged**, and the **tooltip text never becomes
    "Copied"** — it stays "Copy to clipboard" before and after the click. So there is no way to assert
    the copied state today except by diffing SVG path data. That is why ELITEA-2419's AFS requests a
    `data-copied="true|false"` state attribute on the button (`CopyButton.tsx:11-15` already holds the
    `copied` state — the attribute only reflects it, no new hook/DOM). Assert it *immediately* after the
    click; a clipboard read + paste round-trip can burn the 2 s window.

12. **The clipboard receives the RAW MARKDOWN, not the rendered text.**
    `navigator.clipboard.writeText(message.content)`. Observed: clipboard held
    `**Need more help?**` and `---` where the bubble renders `<strong>` and `<hr>`. A
    `clipboard == bubble.inner_text()` assertion **will fail**. Compare on a normalised basis (strip
    `[*_`#]`, drop `---` lines, collapse whitespace) or anchor on the first paragraph.
    The **paste round-trip is exact**, though: `Ctrl/Cmd+V` into the widget input reproduces the
    clipboard byte-for-byte, so `to_have_value(clipboard_text)` is a safe strict assertion.

13. **Clipboard permissions are already granted** — `automation/conftest.py:303` sets
    `permissions=["clipboard-read", "clipboard-write"]` on every context. `BasePage.get_clipboard_text()`
    (line 468) reads it. Clearing the clipboard before a copy click is precondition hygiene, not a
    fidelity substitution — precedent `automation/pages/help_center_page.py:130`.

14. **The user's own bubble has no copy button** — confirmed live, the user bubble is a bare
    `<div class="… --user">text</div>` with no children. Useful absence assertion.

15. Reply latency sample 2026-08-22: **69.6 s** for "Explain in one sentence what an AI agent is"
    (in the digest's recorded 33-135 s band). Use a **180 s** wait on this surface; 120 s is tight.

## Resolved/added during ELITEA-2419 implementation (2026-08-22, test-automation-engineer)

**Rows 6-9 of ELITEA-2419's AFS now EXIST** — `EliteaAI/elitea_assistant@216da01` on its
`automation/testids` branch (attributes only; the shared `CopyButton` takes a caller-supplied
`testId` prop, wired at the `MessageItem` call site):

| Element | Handle now available |
|---|---|
| Copy-to-clipboard button | `support-assistant-message-copy-button` |
| Its copied state | `data-copied="true" \| "false"` on that same button |
| Message bubble (user or assistant) | `support-assistant-message-bubble` |
| Message role | `data-role="assistant" \| "user"` on the item that already carries `support-assistant-message-item` |

Bind via `SupportAssistantPage.message_copy_buttons` / `.message_bubbles` and the class constants
`MESSAGE_COPY_BUTTON`, `MESSAGE_COPY_BUTTON_COPIED`, `MESSAGE_COPY_BUTTON_IDLE`,
`ASSISTANT_MESSAGE_ITEM`, `USER_MESSAGE_ITEM`, `MESSAGE_BUBBLE`, plus the helpers
`get_copy_button_count()`, `last_assistant_item()`, `last_user_item()`, `copy_button_in(item)`,
`bubble_in(item)`, `send_message_via_testid(text)` and `BasePage.clear_clipboard()`.

16. **Quirk 11 is now assertable without diffing SVG paths** — `data-copied` flips to `"true"`
    synchronously in the click handler and back to `"false"` after 2000 ms. Assert the "true" edge
    FIRST (before reading the clipboard), then the revert; both with plain auto-retrying
    `to_have_count` assertions, no sleep.

17. **Waiting for a reply needs no `wait_for_function`.** Since exactly one reply is expected,
    `expect(message_copy_buttons).to_have_count(baseline + 1, timeout=180_000)` is the whole wait —
    simpler than the JS recipe and it keeps `page.evaluate` out of the diff. Measured 85.7 s for the
    full spec (~70 s of it the reply).

18. **Quirk 7 (stale Vite modules under OneDrive) reproduced again** for the connected assistant
    repo: after committing the testids, `curl -s 'http://localhost:5173/@fs<abs>/src/components/shared/CopyButton.tsx'`
    still served the pre-edit module. Same fix worked — kill the `npm run dev` + `vite` + `esbuild`
    PIDs, `rm -rf EliteaUI/node_modules/.vite`, restart, re-curl until the new attribute appears.
    **Budget one restart into every dispatch that adds a testid on this surface.**

## In-app navigation & widget mount point (verified live 2026-08-22, ELITEA-2422 run)

19. **The widget is mounted at APP-SHELL level, outside the routed subtree.**
    `../EliteaUI/src/[fsd]/widgets/support-assistant/ui/SupportAssistant.jsx:33-44` renders
    `<EliteaAssistant>` as a *sibling* of `children({ onToggleAssistant })`. Consequence,
    confirmed live across `/chat` → `/agents/all` → `/chat`: React-Router navigation **neither
    unmounts nor closes** the widget, and the conversation is **not re-fetched** — message
    items, `data-role`s, texts and copy-button count are byte-identical before and after.
    So any case text hedging *"or can be reopened via the launcher"* is weaker than the live
    contract: assert the strong form (still open, **no reopen click**). Never write a
    conditional reopen — a branch that never executes is untested code that masks a regression
    to a routed mount.

20. **Sidebar navigation is testid-addressable and already wired.** `BasePage.sidebar_menu_item(value)`
    (`automation/pages/base_page.py:143-190`) uses the dynamic-testid template
    `SIDEBAR_MENU_ITEM = '[data-testid="sidebar-menu-item-{}"]'`, fed by
    `SidebarBody.jsx:272` `testId={\`sidebar-menu-item-${i.value}\`}`. Enumerated live, the
    `value`s are: `chat` (→ `/chat`), `agents` (→ `/agents/all`), `pipelines`, `skills`,
    `toolkits`, `mcps`, `credentials`, `applications`, `artifacts`. Plus
    `sidebar-toggle`, `sidebar-create-button`, `sidebar-settings-button`,
    `sidebar-agent-hub-button`, `sidebar-support-assistant-button`,
    `sidebar-collapse-toggle-button`. **None of these are on EliteaUI `main`** (fresh
    `git fetch origin` + two-stage grep, 2026-08-22) — `automation/testids` only.
    After a sidebar click, wait on `page.wait_for_url("**/agents/all")`, **not**
    `networkidle`: it is a client-side route change.

21. **`#1581` is a false bug — do NOT let it block a case again.** It blocked the 2026-08-18
    ELITEA-2422 analysis at Step 2 (`defect-found`, commit `a77917f1f`) purely because the
    analyst typed with synthetic `input.value = …` (quirk 4). Re-verified non-reproducing a
    **third** time in the 2026-08-22 run: real `fill` → `send button disabled: false`
    immediately, both messages sent and answered. The issue is still OPEN awaiting a human
    close. **Any support-assistant AFS that cites #1581 as blocking is stale — re-run it.**

22. **Reply-latency sample 2026-08-22: 31.0 s and 31.0 s** for short prompts (fast end of the
    33-135 s band in quirk 5/15). Keep the 180 s wait; the variance, not the mean, is the risk.

23. **Console noise, extended.** Beyond the `Module "stream" has been externalized` warning
    (quirk 6), the dev session accumulates `ws://localhost:5173/ @vite/client` and
    `/socket.io/?EIO=4&transport=polling` **`ERR_CONNECTION_REFUSED`** errors — Vite HMR and
    dev-server infrastructure, unrelated to the app. Filter console assertions to
    `type == "error"` **and** exclude those two URL patterns. Every navigation and action of
    the ELITEA-2422 run itself reported `0 errors`.

24. **Resolved/added during ELITEA-2422 implementation (2026-08-22, test-automation-engineer):
    text-based "is my message still there" assertions need a BASELINE too, not just counts.**
    The widget restores the previous session and the support-assistant specs deliberately
    leave their messages behind (no teardown — quirk 2/10 plus every merged spec's § Cleanup),
    so on the **second** run of the same spec the exact message string it sends is *already*
    in the restored conversation. `expect(item_with_text(MSG)).to_have_count(1)` is therefore
    green on run 1 and red on runs 2..N — exactly the shape that survives an implementer's
    single local run and then fails the lead's 3× merge gate. Shipped form: take
    `baseline_named = user_message_item_with_text(MSG).count()` right after the widget opens,
    assert `baseline_named + 1`. Same strength, deterministic. Generalise it: on this surface
    **every** conversation observable is a delta — items, copy buttons, and message text alike.
    Helper `SupportAssistantPage.user_message_item_with_text()` exists for this (additive,
    composed from the `USER_MESSAGE_ITEM` constant).

25. **Resolved/added during ELITEA-2422 implementation:** an in-app sidebar round trip
    (`/chat` → `/agents/all` → `/chat`) with the widget open costs **nothing** in test time and
    needs **no re-settle wait** — the widget's DOM is never torn down (quirk 19), so assert
    directly after `page.wait_for_url(...)`; no `wait_for_timeout`, no `networkidle`, no
    re-open. Full spec runtime with two live replies: **77.8 s** headless (matches the AFS's
    70-90 s estimate).

## History panel & page-refresh restore (verified live 2026-08-22, ELITEA-2423 run)

Source: `../elitea_assistant/src/components/chat/ChatHeader.tsx` (panel) +
`src/lib/hooks/initAssistant.hook.ts` (data).

| Element | Current raw handle | Testid |
|---|---|---|
| History button | `button[aria-label="Chat history"]` (`ChatHeader.tsx:94-101`) | **needed:** `support-assistant-history-button` |
| History dropdown | `.elitea-assistant-history-dropdown` (`:105`) | **needed:** `support-assistant-history-dropdown` |
| History item (repeated) | `button.elitea-assistant-history-item` (`:108-112`) | **needed:** `support-assistant-history-item` |

26. **`GET /api/v2/support_assistant/conversations/` fires on PAGE LOAD, not on the History click.**
    `initAssistant.hook.ts:44` calls `api.getConversations()` in the mount `useEffect`; the History
    button (`ChatHeader.tsx:97 toggleHistory`) only flips local `showHistory` over the already-fetched
    array. **Live: zero requests during the click.** Any test asserting a status code "when the history
    panel opens" must arm its response collector around the **reload/navigation**, or it passes
    vacuously. Also: the list endpoint is hit **twice per load** (StrictMode double-invokes the effect
    in dev) — assert `all(status == 200)`, never just the first.

27. **The History button is `disabled` until `history.length > 0`** (`ChatHeader.tsx:100`). That makes
    `expect(history_button).to_be_enabled()` the cheapest and most honest "conversation list has
    loaded" wait on this surface — no `networkidle`, no sleep. (It is also disabled for a genuinely
    empty account, so a spec that needs the panel must create a conversation first.)

28. **A history item is `disabled` exactly when it is the currently-open conversation**
    (`ChatHeader.tsx:113` — `disabled={conversation.uuid === currentConversationId}`). After a refresh
    the widget auto-restores `items[0]`, so **index 0 is always disabled**; the flag follows the
    selection (live: `[True, False, False]` → select index 1 → `[False, True, False]`). To "open a
    previous session" click the first `:not([disabled])` item. **Do not request a `data-current`
    attribute** — the native `disabled` already encodes it; filter from a class constant
    `'[data-testid="support-assistant-history-item"]:not([disabled])'`.
    Selecting one fires `GET /api/v2/support_assistant/conversation/{uuid}` → 200 and swaps the message
    list (live 14 → 4 items); the dropdown closes on outside pointerdown (`:36-46`).

29. **The widget does NOT auto-open after a page reload** — `[data-testid="support-assistant-widget"]`
    count is 0 after `page.reload()`; an explicit launcher click is required. (Contrast quirk 19: an
    *in-app* route change never closes it. Refresh ≠ navigation on this surface.)

30. **Restore-after-refresh always loads `items[0]` of the conversation list, which is ordered by
    CREATION, not by last activity.** Live: a message sent into the list's index-1 conversation did not
    reorder it, and after the next reload the widget restored index 0 again — so that message was not
    visible (`MSG2 present: 0`) while the index-0 conversation's message was (`MSG1 present: 1`).
    Consequence for specs: after a refresh you may only assert content of the conversation you were in
    **if it was `items[0]`**. Never assert "the message I just sent is visible after refresh" once the
    test has switched conversations.

31. **History item count is shared-account data and appears capped at 20** — assert `>= 1` and
    *stability across the refresh* (`after == before`), never an absolute.

32. **`#1581` disproved a fourth time** (ELITEA-2423, 2026-08-22): real `fill` → `send-disabled: False`
    immediately, twice, both messages answered (32.3 s / 31.8 s). The 2026-08-18 ELITEA-2423 AFS that
    blocked on it (commit `995f775cb`) was stale and has been replaced. Zero console errors and zero
    non-200 `support_assistant` calls across 2 loads + 2 reloads + 2 live replies.

33. **Case-text clarification #1649** (label `question`) records ELITEA-2423's two case-text
    imprecisions (the GET trigger in Step 4, the disabled index-0 item in Step 5) — product is correct
    in both.

## Resolved/added during ELITEA-2423 implementation (2026-08-22, test-automation-engineer)

**All three history testids in the table above now EXIST** — `EliteaAI/elitea_assistant@7413180` on its
`automation/testids` branch (attributes only, no new DOM node / hook / state):
`support-assistant-history-button`, `support-assistant-history-dropdown`,
`support-assistant-history-item`. Not on either repo's `main` — a human cherry-picks. Bind via
`SupportAssistantPage.history_toggle_button` / `.history_dropdown` / `.history_items`, the class
constant `HISTORY_ITEM_OPENABLE`, and the helpers `open_history_via_testid()`,
`get_history_item_count_via_testid()`, `first_openable_history_item()`. The pre-policy `history_button`
`fallback=` field and the legacy `open_history()` / `get_history_session_count()` /
`select_history_session()` helpers are untouched for their existing callers — note the testid field is
named `history_toggle_button` precisely to avoid colliding with it.

34. **The history button only EXISTS while the widget is open** — it lives in the widget header
    (`ChatHeader.tsx`), which is not mounted when the widget is closed. Combined with quirk 29 (the
    widget does not auto-open after a reload), this means `expect(history_toggle_button).to_be_enabled()`
    — the honest "conversation list has loaded" wait of quirk 27 — **cannot be used as the post-reload
    settle**: it fails `element(s) not found`. Order is: `page.reload()` →
    `expect(sidebar_launcher).to_be_visible()` (app shell back) → reopen the widget →
    *then* `expect(history_toggle_button).to_be_enabled()`. The page-level `page.on("response")`
    collector keeps recording the list requests throughout, so the statuses are still asserted at the
    step the case puts them in. Cost one rerun.

35. **Selecting a history entry CLEARS the message list before the fetched conversation renders** — the
    list is transiently EMPTY between the click and the `GET /conversation/{uuid}` render. Any
    `.count()` baseline read in that window returns 0, and an absence assertion
    (`to_have_count(0)` on a message text) is satisfied vacuously by it. Settle first with
    `expect(message_copy_buttons).not_to_have_count(0)` — every conversation holds at least the
    assistant greeting, whose copy button only renders when complete (quirks 9/10) — and only then
    read baselines or assert absence. Cost one rerun (a 0 baseline made the next step expect 1 copy
    button where 4 was correct).

36. **Runtime for the full six-step spec: 92.6 s headless** (two live replies, two full page reloads,
    one conversation switch) — comfortably inside the AFS's 110-150 s estimate. Reply latencies this
    run were at the fast end of the 31-135 s band again.

## Attachments — upload, predict payload, and the sent-message gap (verified live 2026-08-22, ELITEA-2421 run)

Source: `../elitea_assistant/src/components/chat/MessageInput.tsx`,
`src/components/chat/attachments/AttachmentChip.tsx`, `src/lib/hooks/attachmentUpload.hook.ts`,
`src/lib/hooks/chat.hook.ts:483-540`.

| Element | Current raw handle | Testid |
|---|---|---|
| Attach file button | `button.elitea-assistant-attach-button` / `[aria-label="Attach file"]` (`MessageInput.tsx:266-274`) | **needed:** `support-assistant-attach-button` |
| Attachment chip (composer) | `.elitea-assistant-file-chip` (`AttachmentChip.tsx:39`; inside a `<Tooltip>`, renders children normally) | **needed:** `support-assistant-attachment-chip` |
| Chip filename | `.elitea-assistant-file-chip-name` — chip's own text already contains it | — (assert `to_contain_text` on the chip) |
| Chip remove button | `[aria-label="Remove <filename>"]`, `disabled` while uploading | — (no case touches it yet) |
| `+N` overflow chip | `button.elitea-assistant-file-chip--count`, `aria-label="Show N more files"` | — (visible only above 2 chips, 3 when expanded) |

37. **The upload fires on SEND, not on attach.** `handleSend` → `startUpload(conversationId)`
    → `POST /api/v2/support_assistant/attachments/{conversation_uuid}` (multipart `file` +
    `overwrite=1`, `adapter.api.ts:100`, XHR not fetch) → **201**, body `[{filepath}]`. Attaching
    only puts a `PENDING` chip in local state. **A network capture armed around the attach click
    sees nothing** — this is exactly what produced the false bug #1584 ("no file upload to
    backend"). Arm the collector before Send, and remember it is an **XHR**, so
    `page.on("response")` catches it but a `expect_request` scoped to `fetch` would not.

38. **The filepath reaches the model through the WebSocket, not HTTP.** Live frame:
    `42["support_predict",{"conversation_uuid":"…","content":"…","attachments":["/attachments/{uuid}/<file>.txt"],"support_assistant_context":{…}}]`.
    Combined with quirk 8: "no POST" is never evidence that nothing was sent on this surface.

39. **The assistant genuinely reads attached file content.** Planted a unique token in a `.txt`
    (`The secret project codename is ZEPHYR-4417.`), asked for it back — reply was exactly
    `ZEPHYR-4417` in **73.7 s**. This is the cheap deterministic oracle for any
    "does it process the file" case: plant a per-run token, assert it comes back. A
    *"summarize this"* prompt has no assertable observable — do not write one.

40. **The sent message shows NO attachment indicator — product gap #1653.** `TMessage`
    (`chat.types.ts:1-11`) has no attachment field; `chat.hook.ts:492-495` pushes
    `{id, role:'user', content, timestamp}` only, computing `allFilepaths` separately for
    `emitPredict`; `MessageItem.tsx` renders nothing for attachments. Live, the sent bubble is
    bare text. `clearAttachments()` (`chat.hook.ts:424`) wipes the composer chip on send, so the
    file vanishes from the UI entirely. Assert the correct behaviour with `expect.soft(...)
    to_contain_text(FILENAME)` on the already-testid'd user item — **do not** invent a testid for
    an element that does not exist.

41. **Send-button contract, attachment clause** (extends quirk 3): `isSendDisabled = disabled ||
    isUploading || !attachmentsValid || !text.trim()` (`MessageInput.tsx:105-108`), where
    `attachmentsValid` = every chip is `PENDING` or `COMPLETED`. So an **ERROR** chip wedges Send
    until it is removed, and **text is still required** — an attachment alone does not enable the
    button (though `handleSend`'s own guard at `:118` would allow attachment-only, the button is
    unreachable). Attach button disables at 10 attachments (`MAX_ATTACHMENT_COUNT`) or while
    uploading. Allowed extensions are a large fixed set (`attachment.constants.ts`); files > 5 MB
    (`CHUNK_SIZE`) switch to a chunked upload loop, > 150 MB are rejected client-side.

42. **`#1584` is a false bug** — same class as `#1581`/quirk 21. The 2026-08-18 ELITEA-2421 AFS
    (commit `7941ba405`) claimed attachments were an unimplemented stub; disproved point-by-point
    on 2026-08-22 (refutation comment on #1584, issue left OPEN for a human to close). Its
    *"Echo: …"* reply and its `"Elitea Assistant"` widget title (live title is **"ELITEA Support"**)
    both fail to reproduce. **Treat every finding from that 2026-08-18 support-assistant pass as
    unverified until re-run.**

## Resolved/added during ELITEA-2421 implementation (2026-08-22, test-automation-engineer)

**Both attachment testids in the table above now EXIST** — `EliteaAI/elitea_assistant@1960c8e`
on its `automation/testids` branch (pure attribute adds; no new DOM node, hook, state or
removal): `support-assistant-attach-button` (`MessageInput.tsx`) and
`support-assistant-attachment-chip` (`AttachmentChip.tsx`). Not on that repo's `main` — a human
cherry-picks. Bind via `SupportAssistantPage.attach_file_button` / `.attachment_chips` plus the
helpers `attach_file_via_testid()` and `get_attachment_chip_count()`. The pre-policy
`attach_button` `fallback=` field and the legacy `attach_file()` helper are untouched for their
existing callers — the testid field is named `attach_file_button` precisely to avoid colliding
with it.

43. **The composer chip clearing is the whole flow's synchronisation point — no sleep, no
    polling helper needed.** `handleSend` (`chat.hook.ts:483-540`) runs in a fixed order:
    `await startUpload(...)` → push the user message into `setMessages` → `emitPredict(...)`
    → `clearAttachments()`. `clearAttachments` is **last**, so
    `expect(attachment_chips).to_have_count(0)` is a DOM-observable proof that the upload
    response AND the outbound `support_predict` frame have already occurred. Read
    `page.on("response")` / `ws.on("framesent")` collector lists immediately after that
    assertion and they are deterministically populated. This is what makes an
    "assert the network evidence" step honest without a timer — the alternative (polling a
    Python list) has no auto-retry and would need a sleep.

44. **Quirk 7/18 (stale Vite modules under OneDrive) reproduced a THIRD time** after adding
    the two testids above — `curl` of the `@fs`-served `MessageInput.tsx` returned the
    pre-edit module while the existing `support-assistant-message-input` testid in the SAME
    file was served fine, so the diagnostic must grep for the NEW attribute specifically, not
    just "does this module load". Same fix (kill `npm run dev` + `vite` + `esbuild` PIDs,
    `rm -rf EliteaUI/node_modules/.vite`, restart, re-curl). Now 3 for 3 — **budget the
    restart, do not treat it as a surprise.**

45. **The connected repo runs a lint-staged pre-commit hook** (`prettier --write` +
    `eslint --fix` on `src/**/*.{ts,tsx}`). It reformats staged files and re-stages them, so a
    testid commit there may land differently formatted than written. Harmless, but re-read the
    file after committing rather than assuming the diff you authored is the diff that shipped.

46. **The assistant genuinely reads attached file content — re-confirmed** (quirk 39, second
    independent run): planted token returned verbatim, full spec **57.9 s** headless including
    the live reply. `#1584`'s "attachments are an unimplemented stub" claim is disproved twice
    over now.

47. **#1653's aria snapshot contains an `img` — it is the user AVATAR**
    (`MessageItem.tsx:35-43`, `alt="User avatar"`, rendered for every user message), not a
    partial attachment indicator. Anyone re-triaging #1653 off the failure output should not
    read that node as evidence the feature is half-shipped.

48. **The assistant REFUSES to relay opaque identifiers out of an attachment — do not build
    a "plant a token, ask for it back" oracle on this surface.** Quirk 39's recipe
    (planting `The secret project codename is ZEPHYR-4417.` and asking for it back) worked
    once during ELITEA-2421 analysis and then failed to reproduce twice during its
    implementation, both times with an explicit guardrail refusal:
    *"I can't help extract or repeat secret codename values from attachments."* and, after
    the wording was neutralised to `Build identifier: <TOKEN>`,
    *"I can't help extract or repeat secret identifiers from attachments."* The word
    *"secret"* is **not** the trigger — the guardrail keys on relaying an opaque
    **identifier** out of an attachment.

    **The working shape: plant an ordinary-prose FACT and ask a comprehension question.**
    Shipped in `test_support_assistant_attachment_send.py`: the file reads
    `The project mascot is the {word}.` (per-run word from a 10-item list) and the prompt is
    *"According to the attached file, what is the project mascot? Answer with the single
    word."* — green twice consecutively. The oracle is exactly as strong (the word exists
    only inside the upload) and it does not collide with the guardrail.

    **This supersedes quirk 39's recipe, not its conclusion:** the assistant demonstrably
    DOES read attached files — it answers questions about their content, it just will not
    echo identifiers. `#1584` stays refuted.

    **Gate caution:** any Step-7-style assertion here rides a live LLM guardrail that has
    already proven non-reproducible once. A refusal on a gate run is this mechanism, not an
    attachment-pipeline regression — the upload status, the `support_predict` frame and the
    composer-chip lifecycle are all product-produced and independent of it.

49. **Spec runtime for the full attachment flow: 55-65 s headless** across four runs
    (upload + one live reply), against a 90-120 s estimate. The 200 s reply timeout stays —
    the 31-135 s band's variance is the risk, not its mean.

## Drag-and-drop attachment (verified live 2026-08-22, ELITEA-2420 run)

Source: `../elitea_assistant/src/components/chat/MessageInput.tsx:44-50, 105-108, 146-170, 192-199`
+ `src/theme/styles/input.css:13-28`.

| Element | Current raw handle | Testid |
|---|---|---|
| Drop zone (owns `onDragEnter/Over/Leave/Drop`) | `.elitea-assistant-input-area` (`:192`) | **needed:** `support-assistant-drop-zone` |
| Drag-over overlay ("Drop files here") | `.elitea-assistant-drop-overlay` (`:199`, rendered only while `isDragOver`) | **needed:** `support-assistant-drop-overlay` |

50. **Drag-and-drop is fully implemented — and ONLY on the composer, not the "chat area".**
    The four drag handlers sit on the input-area div; the message list
    (`.elitea-assistant-messages`) is its **sibling**, so events there never reach them. Probed
    live: `dragenter` + `drop` on the message list → overlay 0, chips 0, no reaction at all.
    Any case text saying "drop onto the chat area" means the composer — clarification **#1655**.
    On `dragenter` carrying `Files`: overlay renders `"Drop files here"` and the input area gains
    `elitea-assistant-input-area--drag-over` (which hides its own children via CSS
    `visibility: hidden`). `dragleave` reverts it (a `dragCounterRef` balances enter/leave), and
    the `drop` dismisses the overlay and stages a normal attachment chip — from there the flow is
    byte-identical to the attach-button path (quirks 37/38/41/43).

51. **The working file-drop recipe (verified green, full flow, 70.7 s).** There is no OS-level
    file drag available to Playwright, so build the `DataTransfer` in-page **once** and deliver
    each phase to the drop zone:
    ```js
    // page.evaluate_handle — one handle, reused for every phase
    const dt = new DataTransfer();
    dt.items.add(new File([content], name, {type: 'text/plain'}));
    ```
    then dispatch `new DragEvent(phase, {bubbles: true, cancelable: true, dataTransfer})` on it.
    The event **must bubble** — React listens at the root container. Each phase may build its own
    `DataTransfer`: `handleDragEnter` reads only `types.includes('Files')`, `handleDragLeave` reads
    nothing (it decrements `dragCounterRef`), `handleDrop` reads `.files`. **There is already a
    merged precedent for the whole technique** — `ChatPage.drag_and_drop_file()`
    (`automation/pages/chat_page.py:2855-2910`, base64 → `Uint8Array` → `File` → `DataTransfer`,
    dispatched at a testid'd drop zone) — mirror it rather than re-deriving, but expose the phases
    separately so a test can assert the overlay reverting on `dragleave`. Drove overlay → chip →
    upload → predict → reply green in one pass. This is **transit** substitution (the input gesture only) —
    every observable stays product-produced.

52. **An attachment alone does NOT enable Send (extends quirk 41 with the live measurement).**
    After a drop into an empty composer, `send.is_disabled() == True`; typing flipped it to
    `False` immediately. `isSendDisabled = disabled || isUploading || !attachmentsValid ||
    !text.trim()` (`:105-108`). Case texts that assert "Send becomes enabled" right after
    attaching are stale — assert the pair (disabled attachment-only, enabled after typing).

53. **⚠️ A `page.on("response")` collector keyed on the bare fragment `"/attachments/"` matches
    the Vite dev server's OWN module URLs** — `…/src/components/chat/attachments/AttachmentChip.tsx?t=…`,
    `…/AttachmentProgress.tsx`, `…/AttachmentIcon.tsx`, `…/index.tsx`, all `200`. Observed
    verbatim in the ELITEA-2420 run. So `assert upload_statuses` on that fragment can be
    **non-empty with zero real uploads**, and `all(status < 300)` passes on those `200`s too.
    Always filter on the full **`/api/v2/support_assistant/attachments/`**. The merged
    `test_support_assistant_attachment_send.py:196-202` (ELITEA-2421) uses the short fragment —
    currently still green because the real `201` is present, but the assertion is weaker than it
    reads. Same class as the URL-fragment vacuity lesson from ELITEA-2421's own review.

54. **#1653 reproduces identically on the drop path** — the sent user bubble carries only the
    prompt text, no attachment indicator. It is deliberately NOT re-asserted by ELITEA-2420's spec:
    ELITEA-2421's spec owns that soft red, and duplicating it would add a second permanent red for
    one defect with no new information.

55. **Digest size, flagged not actioned (2026-08-22):** this file is ~475 lines and past the
    comfortable single-read smell. A split into an index + per-subarea files (launcher/widget,
    messaging, history, attachments, navigation) is due — deferred because
    `support-assistant-w02` is in flight and several sibling AFS files reference this path.
    Whoever analyses this surface first *after* the batch closes should do the split.

56. **Resolved/added during ELITEA-2420 implementation (2026-08-22):**
    - **Drop-zone + overlay testids now exist** — `support-assistant-drop-zone` (on the
      always-mounted `div.elitea-assistant-input-area` that owns the drag handlers) and
      `support-assistant-drop-overlay` (on the `{isDragOver && …}` "Drop files here" div),
      EliteaAI/elitea_assistant@e134bfc on `automation/testids`. Both attribute-only; the
      drag-over state stays the `--drag-over` CSS modifier, never a testid value.
    - **The connected repo runs prettier + eslint via lint-staged on commit.** A one-line JSX
      edit came back reflowed to multi-line. Harmless, but `git show` will not match what you
      typed — check the committed file, not your edit, before greping for it.
    - **A dev-server restart WAS required (quirk 44 holds, now 4-for-4).** After committing the
      testids, `curl …/@fs<abs>/src/components/chat/MessageInput.tsx | grep -c
      support-assistant-drop-zone` returned **0** despite the alias being live and the file
      correct on disk. Fixed by killing vite, `rm -rf EliteaUI/node_modules/.vite`, and
      restarting with `VITE_ASSISTANT_LOCAL=1 npm run dev`. Budget ~30 s for the restart.
    - **Shipped page-object phases** (`pages/support_assistant_page.py`, additive):
      `drag_file_over_composer(path)` = `dragenter`+`dragover`; `drag_leave_composer(path)` =
      `dragleave`; `drop_file_on_composer(path)` = `dragenter`+`dragover`+`drop`. The drop phase
      is self-contained — `handleDrop` sets `dragCounterRef` to 0 unconditionally, so the
      enter/leave counter cannot leak between phases.
    - **The full flow ran green first try, 63.2 s headless, 0 reruns**, confirming quirks
      8/35/37/43/53 exactly as the analysis recorded them.

## Assistant context payload — project / page / entity (verified live 2026-08-22, ELITEA-2424 + ELITEA-2425 run)

**What the widget sends with every message.** EliteaUI builds a `support_assistant_context` object
and passes it into `<EliteaAssistant supportAssistantContext={…}>`; the assistant emits it on its
Socket.IO connection. Source chain (read, not guessed):

| Piece | File |
|---|---|
| Context builder (project / page / entity) | **EliteaUI** `src/[fsd]/widgets/support-assistant/lib/hooks/useAssistantContext.hooks.js` |
| Prop hand-off | **EliteaUI** `src/[fsd]/widgets/support-assistant/ui/SupportAssistant.jsx:43` |
| Type | **elitea_assistant** `src/lib/types/assistant.types.ts:4` (`TSupportAssistantContext`) |
| Emit | **elitea_assistant** `src/lib/hooks/chat.hook.ts:527` |

Fields: `project_id`, `project_name`, `current_page` (= `useLocation().pathname`), `meta.browser`
always; entity fields added per `pageType` (`ApplicationDetails`→agent, `PipelineDetails`→pipeline,
`ToolkitDetails`/`MCPDetails`/`AppDetails`/`CredentialDetails`/`Chat`). `filterDefined` **drops
undefined keys entirely** — use `ctx.get(...)`, never assume a key exists on a list page.
`current_entity_name` comes from the **RTK-Query cache** (`findApplicationDetailsInCache`), so the
detail query must have resolved before sending or the field is absent.

**The socket event is `support_predict`, NOT `predict`** (corrects quirk 8 above). Verified frames:

```
42["support_predict",{"conversation_uuid":"…","content":"…","support_assistant_context":{
   "project_id":406,"project_name":"Bugs & Features","current_page":"/agents/all/894",
   "meta":{"tab":"all","versionId":1577,"browser":"…"},"current_entity_type":"agent",
   "current_entity_id":894,"current_entity_name":"Qtest_versionID","selected_model":"gpt-5.6-luna"}}]
42["chat_enter_room",{"project_id":536,"conversation_id":"…"}]
```

`chat_enter_room`'s `project_id` (**536**) is the Support Assistant's own **deployment** project —
it is NOT in the user's project selector. `support_assistant_context.project_id` is the **user's**
project. Asserting the two differ is the mechanical form of ELITEA-2424's "NOT the internal
deployment project" clause.

Capture it passively (no `route`/`fulfill` — this is observation, not substitution), registering
**before** the first navigation:

```python
frames = []
page.on("websocket", lambda ws: ws.on("framesent", lambda f: frames.append(f)))
# parse: re.match(r'^\d+(\[.*\])$', frame) -> json.loads -> [event, payload]
```

### 9. The reply-ready signal is the COPY BUTTON, not the message count

The assistant message item mounts **immediately** with a `Starting up…` placeholder and
`data-role="assistant"`, so `expect(assistant_items).to_have_count(base+1)` returns **before the
answer exists** (cost one wasted probe run). `support-assistant-message-copy-button` renders only on
a *completed* assistant response — wait on its count delta:

```python
copies = page.locator('[data-testid="support-assistant-message-copy-button"]')
base = copies.count()
# … send …
expect(copies).to_have_count(base + 1, timeout=240_000)
```

Latencies measured this run: 40.7 s, 41.2 s, 76.5 s, 77.0 s, 77.0 s (digest range 31-135 s holds).

### 10. Project switching from anywhere (app-wide chrome)

`project-selector-trigger-combobox` (EliteaUI `SidebarProjectSelect.jsx:94` — `ProjectSelect`
appends `-combobox` to the passed `data-testid`) + `[data-testid="select-option-{project_id}"]`.
Already implemented twice: `AnalyticsPage.switch_project()` (`analytics_page.py:689`,
`SELECT_OPTION` constant at :402) and `AdminUsersPage.switch_project()` — reuse that shape.
Live project list for the localhost dev-token identity (2026-08-22): `399 Private` (personal),
`406 Bugs & Features`, `25 Elitea Development`, `471 Elitea Testing Team`, `400 UI Testing`.
`/settings` redirects to `/settings/project-general`; `project-general-section` shows the project
name and teammate count — **no project ID is displayed anywhere in the UI**; the ID is only
available from the `select-option-<id>` testid, the config, or the context payload.

### 11. The personal ("Private") project's NAME is not stable in the assistant's answer

Asked the same project question twice against project 399: one run answered
`Project name: project_user_659 / Project ID: 399` ("the UI context label Private is just the
display label"), another answered `Project name: Private / Project ID: 399`. The **ID was correct
3/3**. Assert project identity on the **ID**; assert the name against the captured context frame,
never against the LLM prose. Team projects (e.g. 406) returned their exact display name.

### 12. #1585 (assistant "echoes the question", 403 on `project_info`) did not reproduce

Filed 2026-08-18 from ELITEA-2424. On 2026-08-22 the assistant answered correctly in 3/3 project
questions, 2/2 page questions and 1/1 entity question. A dedicated `page.on("response")` probe over
page load + widget open + a full round trip recorded **zero** `status >= 400` responses. Two console
403s appeared in a longer multi-page probe (settings + project switching) without blocking any
answer; the console API exposes no URL for them. Issue left OPEN with a non-repro comment.

## Resolved/added during ELITEA-2424 + ELITEA-2425 implementation (2026-08-22, test-automation-engineer)

57. **`support-assistant-new-chat-button` now EXISTS** — EliteaAI/elitea_assistant@583b5dd on its
    `automation/testids` (`src/components/chat/ChatHeader.tsx`, attribute-only on the existing
    "New chat" `<button>`). Closes the `needs-adding` row both AFS files carried. A **dev-server
    restart was required again** before Vite served it (quirk 44, now **5-for-5**): kill vite,
    `rm -rf EliteaUI/node_modules/.vite`, restart with `VITE_ASSISTANT_LOCAL=1 npm run dev`.
    Page-object field: `SupportAssistantPage.new_chat_button_testid` +
    `start_new_chat_via_testid()`, whose wait is the greeting's copy button becoming visible (a
    fresh session is never empty — quirk 10) rather than the legacy fixed 1 s timer.

58. **The open widget BLOCKS the project selector *and* the sidebar launcher.** With the widget
    open, `[data-testid="select-option-<id>"]` cannot be clicked — Playwright reports
    `<h2 …elitea-assistant-header-title> … subtree intercepts pointer events` — and clicking
    `sidebar-support-assistant-button` a second time to toggle the widget shut fails the same way
    (`div.elitea-assistant-input-row` intercepts; the widget's bottom-left overlay container covers
    the launcher). The widget's Close button carries **no testid**, and adding one for an element
    no case asserts would breach the testid-scope rule. **The clean move is a full page load**
    (`page.goto`), which unmounts the widget (consistent with quirks 29/30) — that is what
    ELITEA-2424 does between its two project rounds.

59. **Project-selector trigger text is three lines** — avatar letter, `Project:` label, then the
    name: `"U\nProject:\nUI Testing"`. The NAME is the **last line**. Dropdown options are one or
    two lines (`"E\nElitea Testing Team"`, `"Bugs & Features"`) — same last-line rule.

60. **`project-general-section` + `networkidle` is NOT a sufficient wait after a project switch.**
    Both settle while the sidebar trigger still shows the PREVIOUS project — a switch A→B read back
    `'UI Testing'` (the old value) and failed the round-2 assertion. The deterministic, product-
    produced signal: read the project NAME off the dropdown option *before* clicking it, then
    `expect(trigger).to_contain_text(that_name)`. Shipped as
    `SettingsProjectGeneralPage.switch_project()` (`automation/pages/settings_project_general_page.py`
    — new page object; none existed for Settings ▸ General).

61. **Agent detail URL carries query params**: clicking the first `entity-card-name` lands on
    `/agents/all/9433?viewMode=owner&name=Echo%20Agent`. Parse the id from `urlparse(url).path`;
    `current_page` in the context payload is the **pathname only** (`/agents/all/9433`).
    Shipped as `AgentsListPage.open_first_agent()` (additive — the legacy `select_agent(name)`
    resolves cards by a raw `text=` locator and keeps its callers byte-identical).

62. **The context payload behaved exactly as analysed, on the FIRST run of both specs.** Frames
    captured passively via `page.on("websocket")` (armed before the first `goto`); event name
    `support_predict`; `chat_enter_room.project_id == 536` (the deployment project) vs the user's
    selected project in `support_assistant_context.project_id`. Live durations, headless:
    ELITEA-2424 **170.0 s** (2 LLM round trips), ELITEA-2425 **247.9 s** (3 round trips) —
    the widest per-test runtimes on this surface so far. `#1585` again did **not** reproduce
    (5 questions, 5 correct answers, zero console errors across both specs).
