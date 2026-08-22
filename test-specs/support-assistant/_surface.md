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
