---
name: Build-with-AI post-create Save/Discard disabled state settles async
description: Right after a Build-with-AI Create-Agent POST, Save/Discard disabled state needs a web-first expect(), not a one-shot is_disabled() read
type: feedback
---

ELITEA-2073/2074 (wave-16): after Build-with-AI's "Create Agent" click
resolves (`POST .../applications/prompt_lib/{project}` -> 201), the canvas's
`agent-save-button` / `agent-discard-button` are correctly DISABLED — the
create POST already persisted the full generated config (name,
instructions, welcome message, starters), so there is nothing dirty to
save. Confirmed via two independent live MCP explorations (both read
`disabled === true` immediately).

**But the disabled state settles ASYNCHRONOUSLY** right after the create
response lands — a real pytest run using a one-shot
`agent_canvas.discard_button.is_disabled()` read caught a transient
`False` once (R1 failure), even though the same flow read `True`
immediately in manual/MCP exploration. Switching to the web-first,
retrying `expect(locator).to_be_disabled(timeout=...)` fixed it on the
next run (R2 green).

**Rule:** any assertion on Save/Discard's disabled state immediately after
a Build-with-AI Create-Agent flow (agent OR skill review-form approve) must
use `expect(...).to_be_disabled()`, never a bare `.is_disabled()` snapshot
read — same discipline the project already applies to
`wait_for_participants_badge_absent` (a one-shot bool-returning check can
catch pre-settle DOM state).

Also confirmed this session: the generated Echo Agent's own instructions
explicitly permit (and demonstrably add) an `"Echo:"` prefix on its echo
replies — any case asserting exact-echo behavior against an AI-generated
"echo agent" must assert containment (`sent_text in reply_text`), not
literal equality. Full writeup: `test-specs/chat-interface/_surface.md`
§ ELITEA-2073/2074.
