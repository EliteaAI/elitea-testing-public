# Test Case: Chat – Create New Conversation with Agent, Toolkit, MCP, and Pipeline – Verify All Participants Are Added and Displayed Correctly

## Metadata
- **TMS ID**: ELITEA-2094
- **Tracking card**: EliteaAI/elitea-testing-public#297
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend), project 399 "Private"
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (analyst slot), batch `elitea-2094`
- **Analysed**: 2026-08-27 (re-attempt; the human dragged #297 back to `Approved` with "Proceed")
- **Status**: **defect-found** — blocked by EliteaAI/elitea-testing-public#1279, **independently
  re-confirmed live today over 7 fresh repetitions (0/6 combined-state successes, both orders,
  clean console every run)**. See § Re-attempt evidence.

## Relationship to ELITEA-2455 (read this first)

**ELITEA-2094 and ELITEA-2455 are the same scenario at two levels of detail.** ELITEA-2094's 11
steps are a strict subset of ELITEA-2455's 20; both exist to prove that an Agent, a Pipeline, a
Toolkit and an MCP can coexist as participants of one conversation and render in four distinct
PARTICIPANTS sections.

- ELITEA-2455's AFS lives at
  `test-specs/chat-interface/l1_chat-create-conversation-add-all-participant-types_ELITEA-2455.md`
  (on `automation/base`) and is **also `defect-found`**, re-analysed 2026-08-26 over 16 repetitions.
- **This is NOT `already-covered`**: `already-covered` requires a *merged spec* proving the
  observable. No spec exists for either case — both are blocked by the same product defect, so
  there is nothing to dedup against. Both cases stay open, and both unblock together.
- When #1279 is fixed, **implement ELITEA-2455 first** (it is the superset) and then re-classify
  ELITEA-2094 as `already-covered` against the resulting merged spec. Doing it in the other order
  wastes the broader case's extra coverage.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Available agents, pipelines, toolkits and MCPs exist in the project.
  - **Case-precondition correction, carried forward and RE-VERIFIED today:** the suite's default
    project `${ELITEA_PROJECT_ID}` = **399 ("Private")** satisfies this precondition *via fixtures*
    — `agent_id`, `pipeline_with_llm_id`, `artifact_toolkit` and `mcp_toolkit_with_tools` all
    create their own entities in 399 and all resolved first try this pass. The July note that
    project 399 "has zero pipelines and zero MCPs" and that analysis must move to project 471 is
    **retired** — it described the pre-existing catalogue, not what the fixtures build. No project
    switch is needed.
- The conversation under test is created fresh by the case itself (step 1).

## Test Data

| Field | Value | Source |
|---|---|---|
| Agent | `agent_id` fixture (fresh, healthy) | `automation/fixtures/data_fixtures.py:85` |
| Pipeline | `pipeline_with_llm_id` fixture (fresh, healthy, executable) | `data_fixtures.py:166` — **NOT** the bare `pipeline_id` fixture, which trips the unrelated #684 orphaned-version defect |
| Toolkit | `artifact_toolkit` fixture (fresh, healthy) | `data_fixtures.py:1719` |
| MCP | `mcp_toolkit_with_tools` fixture (public `mcp.deepwiki.com`, 3 tools) | `data_fixtures.py:2085` |
| First message | `Hi` | case's own Test Data table |
| Misconfigured entity (step 11) | `github_toolkit_with_invalid_credential` fixture | `data_fixtures.py:2022` — **test-data addition**, see § Axis 2 |

## Test Steps (as executed live this pass)
1. Navigate to Chats, click "+ Chat" — a new blank conversation opens, PARTICIPANTS panel empty
2. Expand the PARTICIPANTS panel; verify zero participant rows
3. Add the Agent: + → Agents → agent row — verify it appears in the AGENTS section
4. Add the Pipeline: + → Pipelines → pipeline row — verify it appears in the PIPELINES section
5. Add the Toolkit: + → Toolkits → toggle — verify it appears in the TOOLKITS section
6. Add the MCP: + → MCPs → toggle (same open popper) — verify it appears in the MCPS section
7. Verify all four sections visible: AGENTS, PIPELINES, TOOLKITS, MCPS
8. Verify each participant type shows a distinct icon
9. Verify no duplicate entries
10. Type "Hi", click Send — conversation created, owner appears in PARTICIPANTS
11. Verify all participants remain under their type sections; misconfigured entities show a yellow warning

## Expected Results
- All four participant types coexist in one conversation, each under its own section, in the fixed
  order AGENTS → PIPELINES → TOOLKITS → MCPS.
- Each type renders a distinct icon; no duplicates; no console errors.
- After Send, the conversation persists and the owner is shown.
- A genuinely misconfigured entity shows the yellow misconfiguration warning; healthy ones do not.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| **Precondition** — agents/pipelines/toolkits/MCPs exist in the project | entities available | fixtures | `agent_id` / `pipeline_with_llm_id` / `artifact_toolkit` / `mcp_toolkit_with_tools` | **satisfied** — re-verified live in project 399 this pass (the July "switch to project 471" note is retired) |
| 1 Navigate to Chats, click "+ Chat"; PARTICIPANTS empty | new conversation, no participants | live step 1–2 | `sidebar-create-button` click → `expand_participants_panel_via_toggle()` → `PARTICIPANT_ROW_PREFIX` count == 0 | **asserted** — 0 rows in 7/7 live reps |
| 2 + → Agents → select agent; appears in AGENTS | agent participant row | live step 3 | `AGENT_MENU_ITEM.format(project_id, agent_id)` click → `chat-participant-row-application_{agent_id}_{project_id}` visible | **asserted WHEN the agent is the FIRST Agent/Pipeline add** (4/4). **NOT asserted when it is the second** — 0/2 live this pass, silently dropped |
| 3 + → Pipelines → select pipeline; appears in PIPELINES | pipeline participant row | live step 4 | `[data-testid="pipelines-menu-item-pipeline-{proj}-{pid}"]` click → `chat-participant-row-pipeline_{pid}_{proj}` visible | **blocked — #1279.** Lands 1/1 when added ALONE (control run); **0/4 when added after the Agent**, silently, with a clean console |
| 4 + → Toolkits → enable toggle; appears in TOOLKITS | toolkit participant row | live step 5 | `TOOLKIT_PARTICIPANT_MENU_ITEM.format(project_id, toolkit_id)` click → `chat-participant-row-toolkit_{id}_{proj}` visible | **asserted** — 4/4 live, unaffected by the Agent/Pipeline race |
| 5 + → MCPs → enable toggle; appears in MCPS | MCP participant row | live step 6 | `MCP_PARTICIPANT_MENU_ITEM.format(...)` click → MCPS section | **clarification/defect — #687.** The MCP *is* added and *is* visible in the MCPS section, but a **healthy** remote MCP is falsely flagged "Server is disconnected!", which routes it through the warning branch so it renders **no `chat-participant-row-*` testid at all** (0/4 by that locator). Any assertion must therefore accept the warned shape, or #687 must be fixed |
| 6 Four sections visible: AGENTS, PIPELINES, TOOLKITS, MCPS | all four displayed | — | — | **blocked — #1279.** This is the case's structural core. PIPELINES never renders in 4/4 Agent→Pipeline reps (screenshot evidence) |
| 7 Each participant has a distinct icon (robot/flowchart/wrench/plugin) | icons distinct and correct | — | — | **blocked — #1279** (depends on the 4-participant state) **and clarification:** the only testid-backed per-type icon signal is `chat-participants-badge-icon-{section}`, which renders **only while the panel is COLLAPSED**. The EXPANDED panel's per-row `EntityIcon` (`ParticipantItem.jsx`) carries no testid and no per-type attribute — a "distinct icon" assertion must toggle to collapsed specifically for this check |
| 8 No duplicate entries | no duplicates | — | — | **blocked — #1279.** Cannot meaningfully assert "no duplicates" against a state where an expected participant is missing. Also entangled with #689 (picker duplicate-exclusion filter intermittently fails once a Pipeline coexists) |
| 9 Type "Hi", click Send; owner icon added to PARTICIPANTS | conversation created, owner shown | — | — | **blocked — #1279** for reachability; **and clarification independent of it:** the owner/Users section **never renders for a Private project** (`showUsersSection = !isPrivateProject`, both collapsed and expanded). In project 399 this step's expected result is unobservable *by design*, not by defect — the case text assumes a team project |
| 10 All participants visible under their type sections | all listed | — | — | **blocked — #1279**, same dependency chain |
| 11 Misconfigured entities show yellow warning messages | warnings shown | — | — | **blocked for the combined state — #1279**, and the case supplies **no misconfigured entity** (see Axis 2). Independently: `chat-participant-warning-icon` did render 1/1 per rep this pass — but on the **healthy** MCP, i.e. the observable currently fires as a *false positive* (#687), not as a true misconfiguration signal. Coverage gap for Agent/Toolkit warning parity is already tracked as #685 |

### Axis 2 — Analyst additions
- **Deliberately-misconfigured toolkit** (`github_toolkit_with_invalid_credential`) — *added: the
  case's Test Data table provides no misconfigured entity, so step 11 has nothing to verify. Reuses
  an existing fixture; no new fixture needed.*
- **Pipeline-alone control** — *added: distinguishes "pipeline participants are broken" (would be a
  new, worse defect) from "#1279's second-add race". Control passed 1/1, confirming the latter.*
- **Console + pageerror capture across the whole flow** — *added: standard side-channel guard.
  Recorded here with a negative result that matters (below): it does NOT detect this defect.*

## Re-attempt evidence (2026-08-27) — the question this re-attempt existed to settle

The re-attempt directive asked whether the July park still holds. It does, and the answer took ~7
minutes. **7 fresh live repetitions** in the real pytest/page-object harness (fresh `agent_id` +
`pipeline_with_llm_id` per rep, fresh UI-created conversation, `HEADLESS=true`, localhost:5173 /
DEV backend, **no fixed wall-clock delays**, only `wait_for_network()` + product-observable
condition waits):

| Variant | Reps | Result |
|---|---|---|
| **Agent → Pipeline** (this case's own step order) | 4 | **0/4** — Pipeline silently dropped; PIPELINES section never renders |
| **Pipeline → Agent** | 2 | **0/2** — Agent silently dropped |
| **Pipeline alone** (control) | 1 | **1/1 OK** |

Four things this pass establishes:

1. **#1279 is not fixed, and it is not order-dependent.** Whichever of Agent/Pipeline is added
   second is dropped. This independently reproduces the ELITEA-2455 pass's finding on a different
   day, from a different analyst session, with a different step order as the primary variant.
2. **The pipeline-alone control passes.** A pipeline participant adds fine on its own — so this is
   specifically a second-version-carrying-participant race, not broken pipeline participants.
3. **The console is clean in all 7 runs** (`console=[] pageerrors=[]`). No 400, no `icon_meta`
   TypeError, no toast, no error UI. **A "no console errors" assertion cannot detect this failure
   mode** — do not write one as the guard for this behaviour.
4. **Toolkit and MCP adds are unaffected** — both landed in 4/4 reps, consistent with ELITEA-2203's
   merged, green `tests/ui/chat/test_slash_mention_toolkit_and_mcp_participants.py`.

Evidence screenshot (Agent → Pipeline, rep 4 — AGENTS ✓, TOOLKITS ✓, MCPS present-but-falsely-warned,
**PIPELINES absent**): `test-results/screenshots/ELITEA-2094-probe-rep4.png`, attached to
EliteaAI/elitea-testing-public#1279 and #687 as
`ELITEA-2094-step-06-participants-panel-missing-pipelines.png`.

**Why `defect-found` and not `ready-for-automation` + soft-assert.** `.agents/testing.md`
§ Merge gate's analysis-time-entry bullet turns on whether the defect *blocks further exploration*.
It does. Steps **6** (four sections), **7** (distinct icon per type), **8** (no duplicates), **10**
(all participants under their sections) and step **3** itself are all permanently unsatisfiable —
5 of 11 steps, including the case's entire structural core. That is not an isolable tail assertion
a soft-assert keeps visible; it is a state nobody has ever observed. Soft-asserting all five would
produce a cascading multi-assertion red, which is not the single deterministic signature the
sanctioned-RED exception is written for.

## Blocked Steps
- **Steps 3 (pipeline), 6, 7, 8, 10** — blocked by EliteaAI/elitea-testing-public#1279, re-confirmed
  live 2026-08-27 (7 reps, see above).
- **Step 5's row-testid assertion and step 11's warning semantics** — entangled with
  EliteaAI/elitea-testing-public#687 (healthy MCP falsely warned). Even with #1279 fixed, an
  assertion written as "MCP appears as `chat-participant-row-toolkit_{id}_{proj}`" will fail while
  #687 is open, because a warned participant renders through a different branch with no row testid.
- **Step 9's owner half** — not a defect: the owner/Users section never renders for a Private
  project by design. Needs either a team project or a case-text clarification.
- **Unblock signal (mechanical, ~4 min to re-check):** re-run the probe shape in § Automation Hints.
  If the second Agent/Pipeline add lands without a fixed wall-clock delay across 6 reps, #1279 is
  fixed and ELITEA-2455 (the superset case) becomes implementable — do that one first.

### Not blocked, and worth harvesting separately
Steps 1, 2, 4 (toolkit), 5 (MCP, modulo #687) are independently workable today, as is a narrow
"misconfigured participant shows a warning" scenario built on `github_toolkit_with_invalid_credential`
— none of that path touches the Agent/Pipeline race. Raised as a `note` to the lead, not actioned
here (out of this case's scope). Coverage gap #685 already tracks the warning-parity half.

## Concrete Handles (verified live this pass, 2026-08-27)

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| + Chat button | `[data-testid="sidebar-create-button"]` | **on-main ✓** | via `ChatPage.click_create_conversation()` |
| New-conversation greeting | `[data-testid="chat-new-conversation-greeting"]` | **on-main ✓** | also the correct outside-click target before the first Send |
| Plus menu button | `[data-testid="plus-menu-button"]` | **on-main ✓** | `ChatPage.plus_menu_button` |
| Agents / Pipelines / Toolkits / MCPs menu items | `[data-testid="agents-menuitem"]` / `pipelines-menuitem` / `toolkits-menuitem` / `mcps-menuitem` | **on-main ✓** | hover-triggered (`onMouseEnter`), not click |
| Agent item row (dynamic) | `[data-testid="agents-menu-item-agent-{project_id}-{agent_id}"]` | **on-`automation/testids` ✓** | `ChatPage.AGENT_MENU_ITEM`; select-and-close semantics |
| Pipeline item row (dynamic) | `[data-testid="pipelines-menu-item-pipeline-{project_id}-{pipeline_id}"]` | **on-`automation/testids` ✓** — same generic `PlusChatSubmenu.jsx` template | **resolved first try live this pass**; no page-object constant exists yet — see § Automation Hints |
| Toolkit / MCP item rows (dynamic) | `[data-testid="toolkits-menu-item-toolkit-{p}-{id}"]` / `[data-testid="mcps-menu-item-mcp-{p}-{id}"]` | **on-`automation/testids` ✓** (commit `73595e8d`, this case's own prior pass) | `ChatPage.TOOLKIT_PARTICIPANT_MENU_ITEM` / `MCP_PARTICIPANT_MENU_ITEM`; toggle-switch semantics, does NOT close the popper |
| Participant row (dynamic, per type) | `[data-testid="chat-participant-row-{uniqueId}"]`; `uniqueId` = `application_{id}_{proj}` (agent) / `pipeline_{id}_{proj}` / `toolkit_{id}_{proj}` (toolkit AND MCP share this shape) | **on-main ✓** | `ChatPage.PARTICIPANT_ROW`. **Only rendered for a NON-misconfigured participant** — see #687 note above |
| All participant rows (enumeration) | `[data-testid^="chat-participant-row-"]` | **on-main ✓** | `ChatPage.PARTICIPANT_ROW_PREFIX` |
| Misconfiguration warning | `[data-testid="chat-participant-warning-icon"]` | **on-main ✓** | shared/static across all misconfigured participant types |
| Collapsed badge / badge icon, per section | `[data-testid="chat-participants-badge-{section}"]` / `[data-testid="chat-participants-badge-icon-{section}"]` (`section` ∈ agents/pipelines/toolkits/mcp/users) | **on-main ✓** / **on-`automation/testids` ✓** (commit `8971529f`) | render **only while the panel is COLLAPSED**; the badge icon is the only per-type-distinct-icon signal with a testid at all |
| Participants panel toggle | `[data-testid="chat-participants-panel-toggle-button"]`, state via `data-expanded` | **on-main ✓** | `expand_participants_panel_via_toggle()` |

**No testids need adding to EliteaUI for this case** — every handle above already exists and every
one of them resolved first try during this pass.

## Network Behavior
- Each participant add fires the participant-update mutation; `wait_for_network()` (networkidle)
  after each add is sufficient **in isolation** and is NOT sufficient to make the second
  Agent/Pipeline add land (#1279 — client-side participant state settles after every DOM and
  network signal has gone quiet).
- A brand-new, unsent conversation is **not persisted** (URL stays `/chat`, no id) — any
  reload-based persistence check must come after step 10's Send.

## Known Defects Found During Exploration
- **[BLOCKING]** EliteaAI/elitea-testing-public#1279 — second Agent/Pipeline participant add
  silently dropped, both orders, clean console. **Re-confirmed 2026-08-27, 7 live reps**; evidence
  commented on the issue. Not filed anew (already tracked) per `.agents/profile.md` § Bug filing.
- **[MAJOR, blocks a clean step-5/11 assertion]** EliteaAI/elitea-testing-public#687 — healthy
  remote MCP falsely flagged "Server is disconnected!". **Re-confirmed 2026-08-27, 4/4 reps**;
  evidence commented on the issue, with the newly-recorded automation consequence (a warned
  participant renders **no** `chat-participant-row-*` testid).
- Cited, not re-diagnosed this pass: #684 (pipeline orphaned-version silent crash, no warning UI),
  #689 (picker duplicate-exclusion filter fails once a Pipeline coexists), #685 (`question` —
  Agent/Toolkit misconfiguration-warning parity coverage gap). All still OPEN.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Markers: `ui`, `chat`, `regression`, `p2`.
- Fixtures — all pre-existing, **no new fixture needed**: `agent_id`, `pipeline_with_llm_id` (NOT
  bare `pipeline_id`), `artifact_toolkit`, `mcp_toolkit_with_tools`,
  `github_toolkit_with_invalid_credential` (step 11's test-data gap).
- Page-object surface that **already exists on base** (the `chat-remaining` campaign landed it —
  the July AFS's "these methods must be added" list is largely obsolete):
  `ChatPage.add_agent_participant_by_id(project_id, agent_id)`, `open_agents_submenu()`,
  `open_pipelines_submenu()`, `open_toolkits_submenu()`, `open_mcps_submenu()`,
  `add_toolkit_participant_via_slash_menu(project_id, toolkit_id)`,
  `add_mcp_participant_via_slash_menu(project_id, toolkit_id, open_plus_menu=…)`,
  `expand_participants_panel_via_toggle()`, `is_participants_badge_visible(section=…)`,
  `PARTICIPANT_ROW` / `PARTICIPANT_ROW_PREFIX` / `PARTICIPANT_WARNING_ICON` /
  `PARTICIPANTS_BADGE_ICON` constants.
- **The one genuine page-object gap**: there is no pipeline analogue of
  `add_agent_participant_by_id`. An implementer needs a class-level constant
  `PIPELINE_MENU_ITEM = '[data-testid="pipelines-menu-item-pipeline-{}-{}"]'` plus an
  `add_pipeline_participant_by_id(project_id, pipeline_id)` method mirroring the agent one
  (click `plus_menu_button` → hover `pipelines_menuitem` → click the item → `wait_for_network()`).
  Verified working live this pass.
- **Row-lookup gotcha:** `agent_id` and `pipeline_with_llm_id` both derive their display name from
  the identical `f"autotest_{request.node.name}"[:32]` pattern, so their names collide. Resolve
  participant rows by UNIQUE-ID testid, never by `get_participant_row_by_name()`'s text filter,
  when both are present.
- **`close_plus_menu_popper()` does not work on an unsent conversation** — it clicks
  `chat-message-list`, which `NewConversationView` does not render. Use the
  `chat-new-conversation-greeting` container as the outside-click target instead.
- **Do not use a console-error assertion as the guard for #1279** — silent-drop runs have a
  completely clean console (7/7 this pass).
- **Unblock probe (run FIRST on any future re-attempt, ~4 min).** Parameterized throwaway pytest,
  6 reps, fresh `agent_id` + `pipeline_with_llm_id` + fresh UI-created conversation per rep:
  `navigate_to_chat()` → `click_create_conversation()` → `expand_participants_panel_via_toggle()`
  → add Agent by testid → `wait_for_network()` → wait for
  `chat-participant-row-application_{aid}_{proj}` → add Pipeline by testid → `wait_for_network()`
  → assert `chat-participant-row-pipeline_{pid}_{proj}` visible within 10 s. Six greens with **no
  fixed delay** means #1279 is fixed.

## Cleanup
- Conversation deleted via `ConversationAPI.delete_conversation()` once created (a brand-new unsent
  conversation is not persisted and needs no cleanup).
- Agent / pipeline / toolkits deleted by their respective fixtures' teardown.
