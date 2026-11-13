# Test Case: Chat – New conversation, add Agent / Pipeline / Toolkit / MCP as participants (+ misconfigured warning)

## Metadata
- **TMS ID**: ELITEA-2455
- **Priority**: l1 (case priority: critical)
- **Environment explored**: DEV `https://dev.elitea.ai/app` (private project, `${TEST_USER}`), 2026-10-20; scripted Playwright probes (Playwright MCP's Chrome was missing on this host -> repo Python Playwright with the same storage state; substitution noted)
- **Status**: **ready-for-automation**
- **Analyst**: qa-engineer, batch `chat-new-conv-2455`
- **Neighbours read**: ELITEA-2203 AFS (toolkit/MCP toggle flow), ELITEA-2168/2095 (participants panel), ELITEA-2162 (plus menu). `ChatPage` already has `plus_menu_button`, `agents_menuitem`, `pipelines_menuitem`, `toolkits_menuitem`, `mcps_menuitem`, `open_toolkits_submenu`, `add_toolkit_participant_via_slash_menu`, `add_mcp_participant_via_slash_menu`, `close_plus_menu_popper`, `expand_participants_panel_via_toggle`, `PARTICIPANT_ROW_PREFIX`, `PARTICIPANT_WARNING_ICON`. No merged spec asserts the 4-section panel composition + warning + post-send persistence -> not covered. Legacy `add_agent_participant`/`add_toolkit_participant` are text/role based and WRONG for this flow (toggle rows) — do not reuse.

## Preconditions
- Logged in (`auth_state`). Private project (default): the USERS section / "Invite Users" menu item are NOT rendered (`!isPrivateProject` gate, `ExpandedParticipantsList.jsx:90`).
- Entities created by fixtures, unique names, cleaned afterwards: `agent_id` (agent), `pipeline_id` (pipeline), `artifact_toolkit` (Artifact toolkit; fixture yields `id`, `name`, `project_id`), `mcp_toolkit_with_tools` (DeepWiki remote MCP; yields `id`, `name`, `project_id`). Do NOT hardcode "agent" / "ALL Pipeline Nodes" / "storage" / "Aha!" — case names are illustrative (DEV has none of the latter two verbatim).

## Observed flow (all executed live)
1. Open `/app/chat`, click `sidebar-create-button` ("Chat") -> empty conversation, URL stays `/app/chat`. `chat-new-conversation-greeting` visible ("Hello, <user>! ..."). Message input is `chat-message-input` (textarea); **No "Type your message..." hint is rendered at all on DEV (neither placeholder attribute nor text) — observed at implementation time; assert the input is visible, editable and empty instead.**
2. Participants panel is **collapsed by default**; `chat-participants-panel-toggle-button` expands it. Fresh chat: panel text is only `PARTICIPANTS` (no section, no row) — confirmed.
3. `plus-menu-button` -> popper. Items: `chat-attach-menuitem-button` ("Attach Files / 10 left"), `internal-tools-menuitem` ("Modules"), `agents-menuitem`, `pipelines-menuitem`, **`skills-menuitem`**, `toolkits-menuitem`, `mcps-menuitem`. **No "Invite Users" item in a private project** (case step 5 drift, see Clarifications).
4. **[Adjusted 2026-11-13] Agents / Pipelines / Skills / Toolkits / MCPs submenus open on CLICK of the menuitem** (`PlusChatButton.handleItemClick`, `onClick`); hover no longer opens them (was hover at analysis time). Agents: `agents-search-input` (placeholder "Search agents..."), `agents-create-new-button` (text **"Create Agent"**, not "+ Create New Agent"), rows `agents-menu-item-agent-{project}-{id}`. Pipelines: `pipelines-search-input`, `pipelines-create-new-button` ("Create Pipeline"), `pipelines-menu-item-pipeline-{project}-{id}`. Toolkits: `toolkits-search-input`, `toolkits-create-new-button` ("Create Toolkit"), `toolkits-menu-item-toolkit-{project}-{id}`. MCPs: `mcps-search-input`, `mcps-create-new-button` ("Create MCP"), `mcps-menu-item-mcp-{project}-{id}`.
5. **Agent / Pipeline click = select-and-close** (popper closes; re-open `plus-menu-button` before next submenu). **Toolkit / MCP rows are toggle switches** (`MuiSwitch`, inner `input[type=checkbox][role=switch]`, unchecked initially) and do NOT close the popper; go Toolkits -> MCPs in the same open popper, then close with an outside click (`close_plus_menu_popper`), NOT Escape (ELITEA-2203 quirk). Toolkit list on a fresh page may be empty until loaded — wait for the specific row testid, don't type into search.
6. Panel after adding all four (pre-send), top-to-bottom: `AGENTS` -> `PIPELINES` -> `TOOLKITS` -> `MCPS`; each group lists one `chat-participant-row-{id}` (agent shows name + version `base`; pipeline name + `base`; toolkit/MCP name only). Pre-send the row id is the *entity* id (420/22/173); **after Send the ids change to participant-link ids** (167/168/169) — never hardcode, match by row text.
7. Icons: each row has 3 SVGs; the first (type icon inside the avatar chip) has a **distinct `path d` per type** (agent / pipeline / toolkit / MCP differ — confirmed 4 distinct `d` prefixes). Section headers `AGENTS/PIPELINES/TOOLKITS/MCPS` are plain text, no testid.
8. Send "Hi" (`chat-message-input` fill + `chat-send-button`): URL becomes `/app/chat/{conversation_id}?name=...` ; panel persists with the same four sections/rows (ids re-keyed); no duplicates; no error toast. Pipeline participant starts running ("Pipeline is running...") because the active participant is the pipeline.
9. **Warning**: the MCP participant (DeepWiki remote MCP, no OAuth session) renders a `chat-participant-warning-icon` block directly under its row: text **"Server is disconnected! Reconnect it to use. Log in."**, SVG fill/color amber `rgb(242,153,74)`, text color `rgb(255,235,211)`. Present BEFORE and AFTER send. Agent/pipeline/artifact-toolkit rows had 0 warning blocks. Warning is a sibling card (`ParticipantAttentionCard.jsx:135`), not a child of the `chat-participant-row-*` element — scope it by DOM-order/ancestor of the MCP row, or assert `count()==1` panel-wide when only one misconfigured entity is added.
10. Console: no errors observed during flow.

## Handles Reference (verified on DEV 2026-10-20)
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| testid | `sidebar-create-button` | — | testid on DEV ✓ |
| testid | `chat-participants-panel-toggle-button` | — | testid on DEV ✓ (existing `expand_participants_panel_via_toggle`) |
| testid | `plus-menu-button`, `agents-menuitem`, `pipelines-menuitem`, `toolkits-menuitem`, `mcps-menuitem` | — | testid on DEV ✓ (existing fields) |
| testid | `agents-search-input`, `agents-create-new-button`, `pipelines-search-input`, `pipelines-create-new-button`, `toolkits-create-new-button`, `mcps-create-new-button` | — | testid on DEV ✓ (new fields likely needed for the create-new buttons; others exist for toolkits/mcps search) |
| testid | `agents-menu-item-agent-{p}-{id}` / `pipelines-menu-item-pipeline-{p}-{id}` / `toolkits-menu-item-toolkit-{p}-{id}` / `mcps-menu-item-mcp-{p}-{id}` | — | testid on DEV ✓ (toolkit/mcp templates exist in ChatPage; agent/pipeline templates new) |
| testid | `chat-participant-row-{id}` (prefix enumerate), `chat-participant-warning-icon`, `chat-send-button`, `chat-message-input`, `chat-new-conversation-greeting` | — | testid on DEV ✓ |
| ladder (xpath: title span whose wrapper follows the accordion arrow svg; no MUI class) | section header text `AGENTS`/`PIPELINES`/`TOOLKITS`/`MCPS` (role-less text, exact match inside participants panel) | `chat-participants-section-title-{}` | ladder — no testid on DEV; unique per panel (verified one each) |
| ladder | first `svg` in a participant row (type icon) — compare `path d` | `chat-participant-type-icon` | ladder — no testid on DEV; scope = within a `chat-participant-row-*`; NOTE `svg:first` is positional-ish: implementer should declare as ScopedLocator `css=svg` inside row and take `.first` only if lead rules acceptable, else raise `question` |
| ladder | toggle switch `role=switch` inside menu row | — | role+name on DEV, unique within row |

## Steps (AFS)
1. Fixtures create agent, pipeline, skill (`autotest-2455-skill`), artifact toolkit, MCP. Open Chat, click `sidebar-create-button`, expand participants panel. **Verify** greeting visible, message input visible/editable/empty (no "Type your message..." text exists on DEV), panel has no `chat-participant-row-*` and none of the four section headers.
2. Click `plus-menu-button`. **Verify** menu items: Attach Files (text contains "10 left"), Modules, Agents, Pipelines, Toolkits, MCPs present (Skills present too; **Invite Users asserted ABSENT** — `to_have_count(0)` — private project).
3. **Click** Agents (dropdown list opens). **Verify** `agents-search-input` + `agents-create-new-button` + a list of agents. Select an agent (any listed item; the name is not part of the expected result — the test selects its fixture agent for determinism). **Verify** the entity with the selected name is added as a participant in the AGENTS section (row with that name + version text).
4. Re-open plus -> **click** Pipelines (dropdown opens). **Verify** `pipelines-create-new-button` + fixture pipeline row; click. **Verify** PIPELINES section row with name.
5. Re-open plus -> **click** Skills. **Verify** `skills-search-input`, `skills-create-new-button`, list; select a skill (any). **Verify** SKILLS section holds a row with the selected name, section order unaffected.
5b. Re-open plus -> click Toolkits. **Verify** rows render a switch; toggle fixture toolkit row (switch becomes checked). Without closing, hover MCPs -> toggle fixture MCP row. Close popper by outside click. **Verify** TOOLKITS and MCPS sections each contain their one row.
6. **Verify** section order by vertical position AGENTS < PIPELINES < SKILLS < TOOLKITS < MCPS; exactly **4** `chat-participant-row-*` rows (agent, pipeline, skill, toolkit), each name once; the MCP renders as an **attention card** (no row testid, name unresolved pre-send) with exactly one warning; no error toast/alert.
7. **Verify** type icons pairwise distinct (4 pre-send, 5 post-send incl. MCP) (compare first-SVG `path d`).
8. Fill "Hi", click `chat-send-button`. **Verify** URL matches `/chat/\d+`, user message "Hi" shown, and the four sections + the same four names (match by text) still present, still no duplicates.
9. **Verify** exactly one `chat-participant-warning-icon` containing "Server is disconnected", located under the MCP row (misconfigured entity); agent/pipeline/toolkit rows have none.
10. Cleanup: delete the created conversation (by `/chat/{id}` — API delete needs the conversation **uuid**, numeric id 404'd in this probe), fixtures clean their entities.

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| 1 Chats + "+ Chat" | new chat loads | AFS 1 | covered |
| 2 placeholder | "Type your message..." | AFS 1 (input visible/editable/empty) | **clarification**: hint text does not exist on DEV; not asserted |
| 3 panel visible, empty | no participants | AFS 1 | covered |
| 4-5 plus menu options | listed options | AFS 2 | covered; "Invite Users" **clarification**: asserted ABSENT (private project), "Skills" extra |
| 6 Agents submenu | search, create-new, list | AFS 3 | covered ("Create Agent" label) |
| 7 select agent | in AGENTS w/ name, version, icon | AFS 3,7 | covered |
| 8-9 Pipelines | same | AFS 4 | covered |
| 10-11 Toolkits toggle | row in TOOLKITS | AFS 5 | covered |
| 12-13 MCPs toggle | row in MCPS | AFS 5 | covered |
| 14 order | AGENTS,PIPELINES,TOOLKITS,MCPS | AFS 6 | covered (3 rows + MCP attention card) |
| 15 distinct icons | 4 distinct | AFS 7 (3 pre-send), AFS 8 (4 post-send incl. MCP card) | covered via whole-row SVG path signature (declared improvisation: no unique type-icon handle) |
| 16 no dupes/errors | | AFS 6,8 | covered |
| 17 Hi + Send | | AFS 8 | covered |
| 18 owner icon in panel | owner added | — | **clarification/out-of-scope**: USERS section not rendered in a private project; owner shown only as message-header avatar. Not asserted. |
| 19 all participants under sections | | AFS 8 | covered |
| 20 misconfigured -> yellow warning | warning indicator | AFS 9 | covered; colour is amber/orange (#F2994A), assert warning block presence + text, not "yellow" |
Axis 2 extras: row count==4 and no duplicates (case step 16 intent); persistence of rows after Send (ids re-key).

## Clarifications (case-text drift, NOT defects)
- "+ Create New Agent/Pipeline" -> actual labels "Create Agent" / "Create Pipeline".
- "Invite Users" absent in private project; "Skills" menu item exists but is not in the case.
- No "Type your message..." placeholder/text exists on DEV (neither attribute nor text).
- Owner icon in PARTICIPANTS panel (step 18) not applicable in private project.
- Warning is amber, shown for a disconnected MCP; relies on DeepWiki MCP having no live session — deterministic here (3/3 observations incl. pre-send), but it is environment-dependent; if a future DEV MCP gets connected the assertion needs another misconfigured entity (e.g. toolkit with invalid settings).

## Automation Hints
- Add class-level fields for agent/pipeline menu-item templates, create-new buttons, search inputs (testid rung, exist on DEV).
- Entity ids in fixtures: `agent_id`, `pipeline_id` return ids — need names for row text; fetch name from fixture/API.
- Row id re-keys after Send; match by `has_text`.
- Leaked-conversation caution: ConversationAPI.delete_conversation(numeric id) returned 404 in the probe; use the conversation fixture/uuid path. Two probe conversations (ids 702, 703, name "HI Chat") remain on DEV and need manual cleanup.
- Pipeline participant makes the "Hi" send trigger a pipeline run; harmless, but wait for completion or stop before teardown.
- Known finding: `artifact_bucket` fixture teardown logs 404 on bucket delete (leak, not case-related).

## Adjustment (2026-11-13, card #2956) — triage class A (UI drift)
- **Evidence:** failing handle `agents-search-input` after `agents_menuitem.hover()`. `PlusChatButton.jsx` on EliteaUI `origin/main` wires every submenu via `onClick={() => handleItemClick(key)}` (no hover); `ExpandedParticipantsList.jsx` `ENTITY_SECTIONS` = Agents, Pipelines, **Skills**, Toolkits, MCP. Reproduced red on DEV, green after adjust.
- **Handles:** hover -> click on `agents_menuitem` / `pipelines_menuitem` (testids unchanged); Skills via existing `skills_menuitem` / `open_skills_submenu` / `SKILL_PARTICIPANT_MENU_ITEM` (testid on DEV ✓).
- **Expected-result changes (human-sanctioned, card #2956):** (1) plus menu lists Skills; (2) Agents/Pipelines open a dropdown on click and the selected entity name is not part of the expected result — assert the entity with the selected name appears in its section; (3) Skills participant + SKILLS section added to the flow (5 sections, 4 rows pre-send, 5 distinct icons post-send).
