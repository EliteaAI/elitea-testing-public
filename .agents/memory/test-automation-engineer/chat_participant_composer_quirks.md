---
name: Chat participant composer quirks
description: "Agents in this conversation" badge count is a CSS ::after pseudo-element (unreadable); real signal is aria-label="Switch Agent"; "Waking the agent…" uses \xa0 and broke transient-message detection (from ELITEA-1736)
type: feedback
---

Discovered while implementing ELITEA-1736 (Interact with Skills from
Conversation — the chat-**participant** variant of ELITEA-1735's agent-level
embedded chat), localhost:5173:

- **The AFS's "Agents in this conversation" participant-count badge is not
  automatable as documented.** The visible count (e.g. "1") is rendered via a
  CSS `::after` pseudo-element — `content: "${count}"` in
  `EliteaUI/src/[fsd]/features/chat/participants/ui/CollapsedParticipants/CollapsedPerticapantsList.jsx:296-297`
  — confirmed by reading the EliteaUI source directly (not guessed from the
  DOM). Pseudo-element content has no DOM text node and is invisible to
  `text_content()`, any accessible-name query, or the accessibility tree
  outside of the MUI `Tooltip`'s hover-only popup. Don't try to read it.
- **The real, stable, semantic signal**: once an agent is added as a chat
  participant, the composer's ButtonGroup member (the same UI region used for
  model selection when no agent is active) gets `aria-label="Switch Agent"`
  and its text content becomes the agent's name + active version. Locate via
  `page.get_by_role("button", name="Switch Agent")` — matches the AFS's own
  "Switch Agent -> {agent name}" wording literally (it's the accessible name,
  not a paraphrase).
- **`[data-testid="model-selector-button"]` is the wrong locator for this.**
  That testid stays on the model-name element and the element it's attached
  to is **replaced entirely** (0 matches) once an agent participant becomes
  active — confirmed via live DOM inspection (`document.querySelectorAll`
  returned `[]` for that testid, `[]`→found the "Switch Agent" button
  instead). Don't reach for it when asserting participant-as-agent state.
- **Shared-helper bug found and fixed**: `ChatPage._is_transient_message()`
  (used by `wait_for_message_content_stable`) matches transient placeholder
  text like "Waking the agent…" against a plain-space `TRANSIENT_MESSAGES`
  frozenset. The actual rendered placeholder uses `\xa0` (non-breaking space)
  between words — `"Waking\xa0the\xa0agent…"` — which silently fails the
  set-membership check. Result: `wait_for_message_content_stable()` treats the
  cold-start placeholder as real, stable content (a false-stable race) and the
  caller reads "Waking the agent…" as if it were the AI's actual response.
  Fixed by normalizing `\xa0` → regular space before comparing (purely
  additive — matches a strict superset of what it matched before; spot-verified
  against `test_chat_interface.py::test_send_text_message`, still green). This
  affects every caller of `wait_for_message_content_stable` project-wide, not
  just chat-participant flows — likely to surface anywhere a fresh
  agent/conversation triggers a cold start.
- **Issue #38 (skill auto-invocation on plain messages) reproduced 3/3 local
  runs** in this chat-participant context, a notably higher repro rate than
  ELITEA-1735's ~1/3 at the agent-level embedded-chat surface. Same defect,
  same root cause (model scans `<available_skills>` and autonomously decides
  to `load_skill`), just a different code path. Worth flagging if a future
  case needs a repro-rate estimate for this specific surface.
- Full AFS: `test-specs/skills/l3_interact-with-skills-from-conversation_ELITEA-1736.md`.
  Test: `automation/tests/ui/skills/test_skill_conversation_interaction.py`.

## Addendum (ELITEA-2369): the SAME "Waking the agent…" placeholder also races `ChatPage.get_last_message_text()` (`.last`), not just `wait_for_message_content_stable`

A distinct manifestation, same root cause. Right after clicking Send,
`ChatPage.get_last_message_text()` (which always reads `messages_container.last`)
can read the transient "Waking\xa0the\xa0agent…" placeholder instead of the
user's own just-sent message — the placeholder already occupies the LAST
slot before the user message settles into its final position, or before the
DOM finishes its post-send reflow. Confirmed live: reading `.last`
immediately after `wait_for_message_count(initial_count + 1)` returned
`'Waking\xa0the\xa0agent…'` instead of the sent text.

**Fix: don't use `.last` to read back a message you just sent** — read the
SPECIFIC index instead. Added `ChatPage.get_message_text_at(index)`
(`messages_container.nth(index)` + `_extract_message_body`). Use
`get_message_text_at(initial_count)` for "what did I just send", and
reserve `get_last_message_text()` for reading the AI's reply AFTER
`wait_for_ai_response()` has already resolved (well past the placeholder
window).
