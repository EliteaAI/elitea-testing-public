---
name: ChatPage expanded PARTICIPANTS panel wiring + AgentsListPage search gotcha
description: New ChatPage methods for the ELITEA-2098 expanded PARTICIPANTS panel (as opposed to the collapsed badge popper), plus a live confirmation that AgentsListPage.search_and_wait_for_results() does not actually narrow the rendered card list
type: reference
---

ELITEA-2089 (PR #1023), first case to touch the participant row's pencil
"Edit" icon (`chat-participant-edit-button`, added this case — sibling
`chat-participant-remove-button` already existed on `DeleteParticipantButton.jsx`,
`EditParticipantButton.jsx` had zero testid at any level).

**New `ChatPage` surface** — the (ELITEA-2098) expanded PARTICIPANTS panel
testids (`chat-participants-panel`, `chat-participants-panel-toggle-button`)
existed on `automation/testids` since that case but no page object had wired
them; every prior caller used the legacy text-based
`expand_participants_panel()`/`is_participants_panel_expanded()`. Added:
`is_participants_panel_open()` (checks `data-expanded` attribute — the
testid=identity/state=data-* pattern), `open_participants_panel()` (toggles
if needed), `get_agent_participant_row(agent_id)` (scopes the EXISTING
`PARTICIPANT_ROW` template — same row testid, `application_{id}_{project_id}`
— inside `participants_panel` instead of `participants_popper`; confirmed
live both surfaces render the identical testid), and
`edit_agent_participant(agent_id)` (hover + click the new edit button,
mirrors `remove_agent_participant()`'s existing shape 1:1).

**`AgentCanvasPage.discard_button` gap** (declared improvisation): the AFS
never flagged it, but `AgentEditor.jsx` never passed `BaseEditor`/
`EditorHeader`'s existing optional `discardButtonTestId` prop — 0 matches
live for `AgentFormPage.discard_button`'s `discard-button` testid on the
canvas (that testid belongs to OTHER pages; per
`test_agent_save_as_version.py`'s own prior note it isn't even wired on the
standalone Agent detail page either). Fix mirrors `ToolkitEditor.jsx`'s
existing `discardButtonTestId="toolkit-canvas-discard-button"` pattern —
added `agent-canvas-discard-button` the same way.

**`AgentsListPage.search_and_wait_for_results()` does not visibly narrow the
rendered card list** — confirmed live this run (searched "echo", got back
all 20 rendered cards unfiltered, not just the one match). Likely the same
class of `.fill()`-doesn't-trigger-React-onChange gap
`.claude/rules/mui-patterns.md` documents for OTHER MUI fields (`search()`
uses `.fill()`, not `press_sequentially()`) — NOT investigated further/fixed
here (out of this case's scope; touching a ≥3-caller shared method needs the
full regression protocol). The EXISTING `test_agent_search`/ELITEA-0140
coverage already only asserts `agent_exists_in_list()` (presence), never an
exact single-result match — follow that precedent, don't assume the search
narrows anything. `select_agent(name)`'s own exact-text locator disambiguates
correctly regardless (assuming no real name collision, per the standing
collision-risk note on any `echo`-named test fixture in this suite).

**Card-view pagination**: the Agents-section card view only renders a FIRST
PAGE of cards (confirmed live: exactly 20, against a real project total
> 20, in this shared ever-growing environment) — `agents_list.get_agent_card_names()`
never returns the full inventory once the project passes that threshold.
An exact "count == baseline+1" assertion is not viable here; assert presence
instead (the newest-created agent is reliably on the first page since both
the API's `list_agents()` and the card view sort newest-first).
