---
name: Build-with-AI post-create canvas reads settle async
description: Right after a Build-with-AI Create-Agent POST, ANY canvas read (Save/Discard disabled, form field values) needs a web-first expect(), never a one-shot read
type: feedback
---

ELITEA-2073/2074 (wave-16, + fix round 1): after Build-with-AI's "Create
Agent" click resolves (`POST .../applications/prompt_lib/{project}` ->
201), the canvas re-hydrates from the just-created agent — and every part
of that hydration is ASYNCHRONOUS relative to the create-POST response
landing. Two independent instances confirmed so far, same root cause:

1. **Save/Discard disabled state.** `agent-save-button` /
   `agent-discard-button` are correctly DISABLED post-create (nothing left
   dirty — the create POST already persisted the full config). A one-shot
   `agent_canvas.discard_button.is_disabled()` read caught a transient
   `False` once (R1 failure) even though manual/MCP exploration always
   read `True` immediately. Fix: `expect(locator).to_be_disabled(timeout=...)`.
2. **Form field values (Welcome Message / Conversation Starters).** The
   canvas's own `agent-welcome-message-input` / `agent-conversation-
   starter-input` fields re-hydrate from the created agent a moment AFTER
   the create response lands — even though the chat-area starter TILES
   (a different data source, populated from the create response itself)
   are already visible at the same instant. A one-shot
   `.input_value()` read caught a transient empty string (fix-round-1
   fix). Fix: `expect(locator).not_to_have_value("", timeout=...)`.

**Rule:** ANY assertion reading canvas state (button disabled/enabled,
field values, counts) immediately after a Build-with-AI Create-Agent flow
(agent OR skill review-form approve) must use a web-first, retrying
`expect(...)` assertion — never a bare `.is_disabled()` / `.input_value()`
/ `.count()` snapshot read. Same discipline the project already applies to
`wait_for_participants_badge_absent` (a one-shot bool-returning check can
catch pre-settle DOM state). If a NEW kind of post-create canvas read
starts flaking, suspect this same hydration race before anything else and
add a third bullet here rather than opening a new entry.

Also confirmed this session: the generated Echo Agent's own instructions
explicitly permit (and demonstrably add) an `"Echo:"` prefix on its echo
replies — any case asserting exact-echo behavior against an AI-generated
"echo agent" must assert containment (`sent_text in reply_text`), not
literal equality. Full writeup: `test-specs/chat-interface/_surface.md`
§ ELITEA-2073/2074.
