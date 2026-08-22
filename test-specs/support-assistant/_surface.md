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
