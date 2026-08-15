---
name: Chat stop button wipes message exchange
description: Clicking Stop mid-generation deletes the whole turn (user+AI msg) server-side, not just the stream — issue #1569
type: feedback
---

Chat composer's Stop control (`UserInput.jsx` ~line 552-562, `onClick={onStop}`,
no `data-testid` — needs `chat-stop-generation-button` via `add-data-testid`)
does not just cancel the in-progress AI reply. Clicking it during generation
wipes the ENTIRE message exchange for that turn — the user's own already-sent
prompt AND the partial AI reply — both from the UI list and server-side.

Confirmed via direct REST check on the conversation's own endpoint:
`GET /api/v2/elitea_core/conversation/prompt_lib/{project}/{conv_id}?messages_limit=10&sort_order=desc`
returns `"message_groups_count":0,"message_groups":[]` immediately after Stop,
and still after a full page reload — so this is not a client render glitch,
the backend actually drops the message group when a stream is stopped before
completion.

Reproduced 2/2 on independent fresh conversations (ids 8837, 8838), single
gesture (type → Enter → click Stop), filed as issue #1569.

**What still works correctly**: the input bar restoration (waveform button
reappears, input field re-enabled) is NOT affected — only the transcript
persistence is broken. A brand-new send-and-respond cycle AFTER stopping
works perfectly cleanly (no residual stuck state, no error toast) — confirmed
via ELITEA-2183's own flow (type "hello" after stopping → normal LLM reply,
zero console errors).

**Consequence for any future stop-generation test**: don't assert "message
history persists after Stop" as a hard assert — it will fail deterministically
until #1569 is fixed. Use `expect.soft()` + `# Known defect: #1569`. Assert the
things that DO work (input restored, editable, new messages work fine) as hard
asserts.

**Playwright MCP gotcha reconfirmed while reproducing this**: `page.goto("http://localhost:5173/chat")`
does NOT reliably land on a genuinely fresh/blank composer — it can redirect to
the last-viewed conversation (matches the composer-send-button AFS's own
documented gotcha). To force a truly fresh conversation, click the sidebar's
"+ Chat" button (`sidebar-create-button` testid) instead of navigating to the
bare `/chat` URL.
