---
name: Chat attachments — content is never inlined; the model must call a tool
description: Attachments upload at SEND, carry only a filepath reference; assert the read_multiple_files frame
type: project
---

The Elitea chat attachment contract, traced in EliteaUI source and confirmed live
(ELITEA-0500, 2026-08-28):

- **Selecting a file does not upload.** `useAttachmentState.js` pushes `File`
  objects into React state only.
- **Upload happens at SEND**, to
  `POST /elitea_core/attachments/prompt_lib/{projectId}/{conversationId}`
  (`ChatBox.jsx` → `useUploadWithProgress.js`). So a spec must wrap the *send*
  in `page.expect_response(...)` to observe it — wrapping the attach sees nothing.
- **Only a reference reaches the model.** All three payload builders in
  `messagePayloadUtils.js` emit `attachments_info: [{ filepath }]`. Nothing
  appends file text, base64, or even the filename to the prompt.
- Therefore the agent **must call the built-in `attachments` tool** to read it.
  A reply saying *"I don't see the file content embedded in this message"* is the
  product working as designed, not a defect — do not file it as a bug.

**The tool call is observable on the wire.** It rides `chat_predict_attachment`
Socket.IO frames (this flow emits **no** `agent_tool_end` and no
`agent_llm_chunk`), via `utils/websocket_frames.capture_socketio_frames`:

```
event='chat_predict_attachment' _direction='received'
response_metadata -> {"tool_name": "read_multiple_files", "tool_output": {...}, ...}
```

Several such frames appear per turn (observed 3 in one run — two carrying
`tool_meta`, one carrying `tool_output`), so assert `>= 1` **and** check every
match; never `frames[0]`.

UI details worth not re-deriving: the plus-menu popper does **not** close when you
attach (nothing calls `setIsOpen(false)`), so the `chat-attach-menuitem-button`
capacity counter live-updates from `"10 left"` to `"9 left"` in place — close the
popper by clicking `plus-menu-button` again before typing. And with the popper
CLOSED, `button[aria-label="attach files"] input[type="file"]` resolves to a
hidden 0×0 decoy `AttachmentButton` (`pointerEvents: 'none'`) that exists only to
host the drag/drop handle — it "works" only because `set_input_files` ignores
visibility. Drive `chat-attach-menuitem-button` instead.
