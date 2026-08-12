---
name: chat message-item shared testid — agent vs user bubble disambiguation
description: chat-message-item is the SAME container testid for both agent (ApplicationAnswer.jsx) and user (UserMessage.jsx) bubbles — disambiguate via child testids, not the container's own testid
type: project
---

Discovered during ELITEA-1885 analysis (welcome message rendered as agent bubble).

**The container testid does not distinguish sender.** Both
`src/[fsd]/features/chat/ui/chat-box/ApplicationAnswer.jsx` (agent) and
`.../UserMessage.jsx` (user) render their message `<li>`/container with the
identical `data-testid="chat-message-item"`. A test asserting "message N is
agent-styled" cannot do it off the container testid alone — it must inspect
child testids inside that container:

- **Agent-only markers** (present only on the `ApplicationAnswer` path):
  `chat-read-out-button` (TTS), and one of `chat-answer-content` /
  `skill-test-last-response` for the body text.
- **User-only marker** (present only on the `UserMessage` path):
  `chat-message-delete-button`.

So: `has_child('chat-read-out-button')` → agent bubble;
`has_child('chat-message-delete-button')` → user bubble. Absence of the
user-only marker is itself useful as a negative assertion.

**Separate quirk on the agent-answer body testid — a state-conditional
ternary, grandfathered tech debt:** `ApplicationAnswer.jsx` line ~639 sets
`data-testid={isLastMessage ? 'skill-test-last-response' : 'chat-answer-content'}`
on the SAME DOM node. This predates the 2026-07-16 "testid = stable identity,
state via `data-*`" ruling in `.agents/testing.md` and is not remediated —
don't "fix" it opportunistically on an unrelated case; only touch it if a case
specifically targets that element. Practical implication: a lone/last message
(e.g. a fresh welcome message with no prior history) always carries
`skill-test-last-response`, never `chat-answer-content` — assert on the right
one depending on whether other messages exist.

Also confirmed live: the welcome message renders in the embedded chat preview
on every keystroke of the Welcome Message field, before Save is even clicked —
not a bug, just means "visible in preview" isn't the same signal as "persisted
after Save/reload"; use the latter as the actual pass-condition proof.
