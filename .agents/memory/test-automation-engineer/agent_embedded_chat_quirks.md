---
name: Agent embedded chat quirks
description: Skills-in-agent-chat handles and a pre-existing bug in AgentDetailPage.get_last_chat_message() found during ELITEA-1735
type: feedback
---

## Context

Found while implementing ELITEA-1735 (interact with skills via `~mention` in
an agent's embedded chat panel). Source: `automation/pages/agent_detail_page.py`
+ live exploration of `EliteaAI/EliteaUI` (`automation/testids` branch).

## Findings

1. **`get_last_chat_message()` returns polluted text for the LAST message.**
   `ApplicationAnswer.jsx` sets `data-testid={isLastMessage ? 'skill-test-last-response'
   : 'chat-answer-content'}` — i.e. the *last* AI message uses
   `skill-test-last-response`, NOT `chat-answer-content`. The existing method
   only checks for `chat-answer-content`, so on the last message it always
   falls through to raw `text_content()` on the whole `<li>`, which includes
   header metadata ("Thought for N secs", agent name, timestamp) glued onto
   the body. This is load-bearing for any exact-formatting assertion
   (upper-case, delimiter checks, etc.) — silently wrong before now.
   **Did not modify the existing method** (3+ callers: `agent_page.py` facade,
   `test_guardrails_live_reload.py`, `test_artifacts_multi_file.py` —
   additive-only rule). Added a new method `get_last_chat_response_text()`
   instead, which reads `skill-test-last-response` directly (mirrors
   `SkillDetailPage.get_last_test_response()`). **Prefer the new method for
   any assertion on the LAST embedded-chat message** — the old one is only
   reliable for non-last messages.

2. **Two distinct "Mention skill"-labeled poppers exist — do not conflate them.**
   - Add-skill-to-agent popper (Skills section "+ Skill" button): real
     `UnifiedDropdown` — MUI `MenuItem`, `role="menuitem"`, accessible name =
     skill name, `data-testid="toolkit-menu-item"` (shared/generic testid,
     reused from the Toolkits flow). `components/mui.py::Popper.select_menuitem`
     works as-is.
   - Chat `~mention` popper (typing `~` into `chat-message-input`):
     `MentionSkillList.jsx` / `MentionToolItem.jsx` — plain `<Box>` divs, **NO
     role, NO data-testid**. Select by text: locate the "Mention skill" header
     text, walk up 2 ancestor `div`s to the list container, then
     `get_by_text(skill_name, exact=True)` within it.
   An earlier AFS draft had conflated these two into one Handles Reference row
   claiming both are `role="menuitem"` — only the first one is. Corrected in
   the AFS via a Phase-2 amendment.

3. **Agent add-skill button DOES have a stable accessible name** — `getByRole(
   'button', { name: 'Skill', exact: true })` (BaseBtn renders a plus icon +
   visible "Skill" text). No `data-testid`, but no `add-data-testid` request
   needed either — don't assume "no testid" means "no stable handle" without
   checking the accessible name first.

4. **`aria-label="clear the chat"` is not unique on the agent detail page** —
   `RunHistoryContainer.jsx` uses the same label. Scope with `.first` (or a
   narrower container) when targeting the embedded chat's own clear button.

5. **`attach_skill()` needs to poll the Skills counter, not just wait for
   networkidle.** The PATCH attach call resolving is not sufficient — the
   Skills section reads from an RTK Query cache that needs to invalidate +
   refetch before the counter/card reflect the new attachment. Poll
   `get_skills_counter_text()` for a change rather than trusting
   `wait_for_network()` alone (silent race otherwise: attach "succeeds" with
   no error, counter briefly still reads the old value).
