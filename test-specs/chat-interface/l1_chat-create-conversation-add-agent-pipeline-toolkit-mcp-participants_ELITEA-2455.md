# Test Case: Chat – Create new conversation and add Agent, Pipeline, Toolkit, and MCP as participants

## Metadata
- **TMS ID**: ELITEA-2455
- **Priority**: l1 (case priority: critical)
- **Environment Explored**: DEV (`https://dev.elitea.ai/app`), Private project, `${TEST_USER}`
- **Analyst**: combined analyst+implementer slot, batch `chat-conversation-basics-2460`
- **Status**: **ready-for-automation** — all 20 steps executed live on DEV (via the real `+ Chat` -> plus-menu -> Agents/Pipelines/Toolkits/MCPs flow, then "Hi" sent). Sections, ordering, warning indicator and no-duplicate observed.

## Preconditions
- `${TEST_USER}` logged in (auth_state). Private project (id 575 on DEV).
- Fresh API-created Agent, Pipeline (empty is fine), Artifact toolkit and Remote-MCP toolkit (existing fixtures `agent_id`, `pipeline_id`, `artifact_toolkit`, `mcp_toolkit_with_tools`). The case's literal names ("agent", "ALL Pipeline Nodes", "storage", "Aha!") are cosmetic examples; fixture-generated entities are used so the test is name-independent and zero-leak.

## Test Steps (as observed live)
1. Open Chats, click `+ Chat` (`sidebar-create-button`). New blank conversation; composer placeholder is "Type your message...".
2. PARTICIPANTS panel (expanded via `chat-participants-panel-toggle-button`) shows title PARTICIPANTS and no entity sections / no `chat-participant-row-*`.
3. Click `plus-menu-button`: menu items (all `*-menuitem`): Modules, Agents, Pipelines, Skills, Toolkits, MCPs (Invite Users only in Team projects; "Attach Files" is `chat-attach-menuitem-button`).
4. Agents (hover/click `agents-menuitem`): submenu has `agents-search-input` (placeholder "Search agents..."), `agents-create-new-button` ("Create Agent"), and rows `agents-menu-item-agent-{project}-{id}`. Select ours: it appears under AGENTS (`chat-participant-row-{id}`, name + version "base" + icon).
5. Pipelines: `pipelines-search-input`, `pipelines-create-new-button`, rows `pipelines-menu-item-pipeline-{project}-{id}`. Select ours -> PIPELINES section.
6. Toolkits: `toolkits-search-input`, `toolkits-create-new-button`, toggle rows `toolkits-menu-item-toolkit-{project}-{id}`; toggle ours -> TOOLKITS section (row `chat-participant-row-{id}`).
7. MCPs: `mcps-search-input`, `mcps-create-new-button`, toggle rows `mcps-menu-item-mcp-{project}-{id}`; toggle ours -> MCPS section.
8. Section headings in order top-to-bottom: AGENTS, PIPELINES, TOOLKITS, MCPS (DOM text "Agents"/"Pipelines"/"Toolkits"/"MCPs", CSS-uppercased).
9. Agent, pipeline and toolkit rows each carry a different icon SVG (distinct path data); the MCP card has its own wrench/plug icon.
10. No duplicates: exactly one row per added entity; no error banner.
11. Type "Hi", Send: URL becomes `/chat/{id}?name=...`, conversation created, "Hi" shown; participant sections unchanged.
12. The misconfigured MCP (Remote MCP "Server is disconnected! Reconnect it to use. Log in.") shows `chat-participant-warning-icon` (orange triangle); healthy rows do not.

## Expected Results
- Each entity appears under its own typed section; sections ordered AGENTS, PIPELINES, TOOLKITS, MCPS; distinct icons; no duplicates; conversation created on send; misconfigured MCP shows the warning indicator.

## Coverage Map

### Axis 1 — Case coverage
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Chats + `+ Chat` | page loads | step 1 | composer visible | asserted |
| 2 placeholder | "Type your message..." | step 1 | composer placeholder attr == text | asserted |
| 3 PARTICIPANTS empty | visible, no participants | step 2 | title visible, 0 participant rows, 0 section titles | asserted |
| 4-5 plus menu options | Modules, Agents, Pipelines, Toolkits, MCPs (+ Attach Files) | step 3 | six menuitems visible (Team-only Invite Users + "10 left" counter not asserted, see Axis 2) | asserted (partial: see note) |
| 6 Agents submenu | search + Create + list | step 4 | search input, create button, our row visible | asserted |
| 7 agent added | in AGENTS w/ name, version, icon | step 4 | row visible, text has name, icon svg present | asserted |
| 8-9 pipeline | same | step 5 | same | asserted |
| 10-11 toolkit toggle | same | step 6 | same | asserted |
| 12-13 MCP toggle | same | step 7 | MCP name visible in panel | asserted |
| 14 section order | AGENTS, PIPELINES, TOOLKITS, MCPS | step 8 | section title y-coords strictly ascending | asserted |
| 15 distinct icons | 4 distinct | step 9 | agent/pipeline/toolkit svg path data pairwise different; MCP has its own icon block | asserted (MCP via section presence, see Axis 2) |
| 16 no duplicates/errors | | step 10 | 3 testid rows unique, each name appears once | asserted |
| 17 send "Hi" | | step 11 | URL has `/chat/<id>` | asserted |
| 18 owner icon in PARTICIPANTS | | step 11 | **NOT OBSERVED** in a Private project (no USERS section / avatar rendered; owner avatar appears only on the message header) | dropped — clarification filed as finding (Private project has no USERS section) |
| 19 participants under sections | | step 11 | all four still present post-send | asserted |
| 20 misconfigured -> yellow warning | | step 12 | warning icon visible under MCP card, absent on healthy rows | asserted |

### Axis 2 — Additions
- "10 left" attach counter and Invite Users are tenant/project dependent (Invite Users absent in Private); not asserted.
- Colour (yellow/orange) of the warning is not asserted; the indicator's presence and text are the contract.

## Concrete Handles
| Element | Rung | Handle | Provenance |
|---|---|---|---|
| +Chat | testid | `sidebar-create-button` | DEV ✓ |
| Panel toggle | testid | `chat-participants-panel-toggle-button` | DEV ✓ |
| plus menu / items | testid | `plus-menu-button`, `{agents,pipelines,toolkits,mcps}-menuitem` | DEV ✓ |
| Submenu search/create | testid | `{k}-search-input`, `{k}-create-new-button` | DEV ✓ |
| Menu rows | testid | `{k}-menu-item-{type}-{project}-{id}` | DEV ✓ |
| Participant row | testid | `chat-participant-row-{id}` (not rendered for misconfigured MCP card) | DEV ✓ |
| Warning | testid | `chat-participant-warning-icon` | DEV ✓ |
| Section title | xpath | `//span[normalize-space(.)='{}'][../preceding-sibling::*[name()='svg']]` | ladder — no testid on DEV; `suggested_testid=chat-participants-section-title-{}` |
| Row icon | css | `svg path` inside a row | ladder; `suggested_testid=chat-participant-icon` |
| Composer placeholder | attribute of `chat-message-input` textarea | | DEV ✓ |

## Cleanup
Fixtures delete agent, pipeline, toolkits; the conversation created by the UI is deleted via API in test `finally` (name `HI Chat`).
