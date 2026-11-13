# Test Case: Chat - "~" mention of a skill participant in a chat with no agent participant

## Metadata
- **TMS ID**: ELITEA-4629
- **Priority**: l1 (case priority: critical)
- **Environment explored**: DEV `https://dev.elitea.ai/app` (private project 575, `${TEST_USER}`), 2026-11-11; scripted python-playwright probes (storage state from `dev_storage_state.py`)
- **Status**: **ready-for-automation** (with case-text drift declared below)
- **Analyst**: qa-engineer, batch `elitea-4629`
- **surface_key**: chat-tilde-skill-mention
- **Neighbours read**: ELITEA-4628 AFS + `test_chat_add_skill_participant_plus_menu.py` (plus-menu skills flow; reused for setup, `ChatPage.add_skill_participant`), `ChatPage.open_mention_skill_popper` / `send_message_with_skill_mention` / `is_skill_in_mention_popper` (existing `~` popper handles, used today only with an AGENT participant: `test_ghost_skill_after_agent_removed.py`), EliteaUI `useChatSkillMention.hooks.js` + `MentionSkillList.jsx` (origin/main), story EliteaAI/elitea_issues#6924. Not already-covered: no merged spec drives `~` with skill participants and no agent (grep `open_mention_skill_popper` callers -> agent-participant only).

## KEY FINDING - precondition drift (live product + source are the contract)
Case says "no skill explicitly added as participant" yet expects `animal-joke` in the `~` list. On DEV the `~` popper in a chat WITHOUT an agent lists **only the conversation's skill participants** (`toConversationSkillItems`, issue #6924 S4 decision), and **excludes the currently active participant**. Observed:
- blank chat, no participants: `~` -> popper `MENTION SKILL / No skills in this chat` (`skill-mention-list-empty`). Typing `animal` -> same empty state.
- ONE skill participant added: it becomes the active participant (chip `chat-switch-participant-button` shows its name) and is excluded -> still `No skills in this chat`.
- TWO skill participants added (A then B): B active, popper lists exactly `A`.
So the only way to satisfy "skill appears in `~` autocomplete, no agent" is: add TWO skills as participants through the plus menu; the NON-active one (added first) is the one mentioned. Sending `~A ...` applies A to the turn (response shows "Skill: B" and "Skill: A" tool chips; reply contained both skills' output tokens). Not a defect: clarification (file per Bug-filing style only if lead wants; none filed).

## Preconditions
- `auth_state`; new blank chat via `sidebar-create-button` (dismiss `platform-banner-close` if present), no agent/pipeline participant.
- Two fixture skills via `skill_api.create_skill(name, description, instructions)` (unique names, ≤32 chars lowercase/hyphen), deleted in `finally`. Do NOT rely on a pre-existing `animal-joke` (shared DEV data). Use a name starting `animal-joke-<ts>`-style for the mention (query prefix `animal` still meaningful) and a second distinct name (e.g. `zebra-fact-<ts>`). Instructions force a deterministic marker: mention skill -> "Reply with a one-line animal joke. Begin with the exact token ANIMALJOKE:"; active skill -> "Begin with ZEBRAFACT:".
- Add order: mention-target FIRST, helper SECOND (second becomes active and is excluded from the popper). Use `ChatPage.add_skill_participant(name)` twice (existing).

## Observed flow (executed live, 2 full passes)
1. Blank chat -> `chat-participants-panel-toggle-button` expands panel (no rows, no agent). Step 1 "empty participants panel": assert no `chat-participant-row-*` and no `chat-switch-participant-button` BEFORE adding skills.
2. (Case steps 2-3 on a chat with zero skills = empty state; AFS asserts that as a negative control, then adds skills.)
3. After adding A then B: `chat-switch-participant-button` text = B. Type `~` (press_sequentially, delay 50-80; `fill()` will NOT open it) -> `skill-mention-list` visible, text `MENTION SKILL\n<A>`; only `skill-mention-item-<A>` present; **no group label** (`skill-mention-group-*` absent when only chat group).
4. Continue typing `animal` -> list filters, still exactly `skill-mention-item-<A>`. Typing further non-matching (`-x`) -> `skill-mention-list-empty` "No skills in this chat" (list stays open).
5. Select: click `skill-mention-item-<A>` -> popper unmounts (count 0), composer value becomes `~<A> ` (trailing space). `input_value()` works on `chat-message-input` (a textarea here).
6. Append `tell me a joke` via `press_sequentially` -> value `~<A> tell me a joke`. Click `chat-send-button` (force) -> sent. Message list item shows the user text `~<A> tell me a joke` (`chat-message-item`). URL becomes `/app/chat/<id>?name=...` (conversation persisted -> **conversation cleanup needed**: delete via ConversationAPI / fixture used by sibling chat specs).
7. Response (wait for `button[aria-label="enter speaking mode"]` to return, ~5-20 s): reply contains `ANIMALJOKE: ...` (and `ZEBRAFACT: ...` from the active skill B) plus tool chips `Skill: <A>` and `Skill: <B>`. Assert the response text contains `ANIMALJOKE:` (the marker only the mentioned skill can produce) - this ties the response to the mentioned skill (case step 8 "response comes from skill").
8. Console: only unrelated 404 "Failed to load resource"; no functional errors.

## Handles Reference (verified on DEV 2026-11-11)
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| testid | `chat-message-input` (`ChatPage.message_input`) | - | testid on DEV ✓ existing field |
| testid | `skill-mention-list` (`ChatPage.mention_skill_list`), header text "MENTION SKILL" (CSS-uppercased) | - | testid on DEV ✓ existing |
| testid | `skill-mention-item-{name}` (`ChatPage.MENTION_SKILL_ITEM`, `MENTION_SKILL_ITEM_PREFIX`) | - | testid on DEV ✓ existing |
| testid | `skill-mention-list-empty` (`MENTION_LIST_EMPTY`) text "No skills in this chat" | - | testid on DEV ✓ existing constant |
| testid | `chat-switch-participant-button` (`switch_participant_button`) - active participant chip; text = active skill name | - | testid on DEV ✓ existing |
| testid | `chat-send-button`, `plus-menu-button`, `skills-menuitem`, `skills-search-input`, `skills-menu-item-skill-{pid}-{id}`, `chat-participant-row-{skillId}`, `chat-participants-panel-toggle-button`, `sidebar-create-button` | - | testid on DEV ✓ existing (ELITEA-4628 additions) |
| testid | `chat-message-item` (message rows; user message text assert via `to_contain_text`) | - | testid on DEV ✓; check whether ChatPage already has a field/helper for message items and the last AI response text (grep `chat-message-item`); reuse before adding |
| ladder (existing helper) | "ready" signal: `button[aria-label="enter speaking mode"]` returns after generation | `chat-speaking-mode-button` | ladder - already used by ELITEA-2466 notes in chat `_surface.md`; reuse existing `wait_for_response`-style helper |
| ladder (scoped text) | skill tool chip text `Skill: <name>` in response | `chat-message-skill-tool-chip-{}` | ladder - no testid seen; optional extra assertion via message-item `to_contain_text("Skill: <A>")`, avoid if no clean scope |

## Steps (AFS)
1. Fixtures create skills A (`animal-joke-<ts>`) and B (`zebra-fact-<ts>`). Open `/app/chat`, dismiss banner, `sidebar-create-button`, expand participants panel. **Verify** no participant rows and no `chat-switch-participant-button` (no agent/skill participant).
2. Negative control: type `~` -> **Verify** `skill-mention-list` visible and `skill-mention-list-empty` present ("No skills in this chat"), i.e. a skill not added as participant is NOT offered. Clear input (Control+a, Backspace), Escape.
3. `add_skill_participant(A)`, then `add_skill_participant(B)`. **Verify** rows `chat-participant-row-{idA}`, `-{idB}` under SKILLS and still no agent participant.
4. Click input, type `~` (`open_mention_skill_popper`). **Verify** `skill-mention-list` visible and contains `skill-mention-item-A`; does NOT contain item B (active, excluded) - assert exactly 1 item.
5. Type `animal` (press_sequentially). **Verify** item A still present (single match).
6. Click `skill-mention-item-A`. **Verify** popper hidden and composer value `~A ` (assert startswith `~A`).
7. Press-type `tell me a joke`. **Verify** composer value == `~A tell me a joke`.
8. Send (`chat-send-button`). **Verify** user message item contains `~A tell me a joke`.
9. Wait for generation complete. **Verify** the mentioned skill A is present in the thinking steps (the `chat-answer-tool-chip` chips inside the AI reply's Thought accordion) at least once. Other skills may be called too - do NOT assert exact reply text or an exact chip count.
10. Teardown: delete conversation (id from URL) and skills A, B.

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| 1 Open chat w/o agent, empty participants | loads, empty panel | AFS 1 | covered |
| 2 Type "~" | dropdown appears | AFS 2/4 | covered; **clarification**: with zero skill participants the dropdown shows the empty state, not skills |
| 3 "~animal" -> animal-joke listed | matching skills | AFS 5 | covered; requires skill participants (**clarification**: precondition "no skill added" is wrong) |
| 4 select -> reference in input | `~animal-joke` | AFS 6 | covered (`~name ` with trailing space) |
| 5 full message in input | | AFS 7 | covered |
| 6 send | sends | AFS 8 | covered |
| 7-8 skill executes, response from skill | joke appears | AFS 9 | covered via mentioned-skill chip in thinking steps (2026-11-13) |
| Fail: works only with agent | | AFS 1-9 (no agent anywhere) | covered |
Axis 2 extras: negative control (AFS 2) and "active participant excluded" (AFS 4) - both grounded in observed behaviour/source and issue #6924 S5.

## Clarifications (case-text drift, NOT defects)
- Precondition "No skill explicitly added as participant" is not achievable for the `~` list: it lists only the chat's skill participants (not all project skills), excluding the active one. Need >=2 skill participants.
- `animal-joke` does not exist on DEV; fixture-created skills used.
- Response is asserted via a marker token, not joke semantics.

## Known defects
None.

## Automation Hints
- Mostly reuse: `ChatPage.add_skill_participant`, `open_mention_skill_popper`, `is_skill_in_mention_popper`, `MENTION_SKILL_ITEM`. `send_message_with_skill_mention` assumes the item is in the list and always sends - OK but this test needs the intermediate asserts, so drive the steps inline via page-object methods (add small methods: `get_mention_item(name)`, `select_mention_skill(name)`).
- Typing MUST use `press_sequentially`; `fill()` skips the mention trigger.
- Order matters: first-added skill = mention target; last-added = active/excluded.
- Conversation is persisted on send -> delete in `finally` (find existing conversation cleanup fixture used by chat specs).
- Wait for response by condition (speaking-mode button returns / mentioned skill chip present in thinking steps), never sleep. LLM output must start with the marker: instructions say so; DEV model followed it 2/2.
- Markers: `@pytest.mark.tms("ELITEA-4629")` + `@allure.issue` pair; ui, chat, skills, p0, regression.


## Adjustment (2026-11-13, #2955)

- Triage class: **A** (assertion drifted: the reply no longer reliably contains the `ANIMALJOKE:` marker - CI failed 0 matches after 90 s; other skills may be invoked).
- Step 9 now checks only that the `~`-mentioned skill name appears at least once in the thinking-step tool chips (`testid on DEV ✓` `chat-answer-tool-chip`, scoped to the last AI reply).
- Expected-result change: yes, requested by the card - response-text marker check replaced by thinking-step presence check (TMS case step 8 updated alongside).
