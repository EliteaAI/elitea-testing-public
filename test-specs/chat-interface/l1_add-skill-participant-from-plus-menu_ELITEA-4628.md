# Test Case: Chat - Add own + Catalog skill as participants from the "+" menu

## Metadata
- **TMS ID**: ELITEA-4628
- **Priority**: l1 (case priority: critical)
- **Environment explored**: DEV `https://dev.elitea.ai/app` (private project 575, `${TEST_USER}`), 2026-11-11; scripted python-playwright probes (storage state from `dev_storage_state.py`)
- **Status**: **ready-for-automation**
- **Analyst**: qa-engineer, batch `elitea-4628`
- **surface_key**: chat-plus-menu-skills-participants
- **Neighbours read**: ELITEA-2455 AFS (same flow for agents/pipelines/toolkits/MCPs, `test_new_conversation_add_participants.py`), chat `_surface.md`, EliteaUI `PlusChatButton.jsx` / `PlusChatSubmenu.jsx` (origin/main). Not already-covered: no merged spec adds a *skill* via the plus menu (grep "skills-menuitem" in automation/tests -> none; `ChatPage` has no skills menu fields yet).

## Preconditions
- Logged in (`auth_state`). New blank chat via `sidebar-create-button` (no conversation is persisted until a message is sent -> no conversation cleanup needed).
- **Own skill**: create via `skill_api` fixture (`api/client.py:1849 create_skill(name, description, instructions)`), unique name, delete in teardown. Do NOT rely on a pre-existing "jira-skill"/"code-task-breakdown" (neither exists on DEV).
- **Catalog skill**: DEV catalog (project 1) holds `code-reviewer` (menu item `skills-menu-item-skill-1-31`, "Catalog" tag, participant shows `v1.0`) and `bug-report-generator` (`...-1-33`). Resolve by NAME at runtime (filter by `has_text`), never hardcode ids. Shared/mutable env data: if the catalog skill is absent, fail loudly (precondition), do not skip.
- Platform banner (`platform-banner-close`) can block clicks on first load of a fresh session - dismiss if present.

## Observed flow (all executed live)
1. `/app/chat` -> dismiss banner -> `sidebar-create-button` -> blank chat. Expand panel with `chat-participants-panel-toggle-button` (collapsed by default).
2. `plus-menu-button` -> items: `chat-attach-menuitem-button` ("Attach Files / 10 left"), `internal-tools-menuitem` (Modules), `agents-menuitem`, `pipelines-menuitem`, `skills-menuitem`, `toolkits-menuitem`, `mcps-menuitem`. **No "Invite Users"** (private project) - case text drift, see Clarifications.
3. **`skills-menuitem` opened its submenu on CLICK in my probe; HOVER (3 s) did NOT open it** (Agents/Pipelines hover per ELITEA-2455). Implementer: click it (or hover then click if hover is flaky); verify live, `PlusChatButton.handleItemClick` toggles `openItem`.
4. Submenu: `input[placeholder="Search skills..."]` (inputProps `data-testid="skills-search-input"` is declared in source `PlusChatSubmenu.jsx:91` but my DOM dump did NOT list it - verify at implement time; fall back to placeholder), "Create Skill" row (`skills-create-new-button` per source), rows `skills-menu-item-skill-{projectId}-{skillId}` (`<li>`). Own skills: project 575 (e.g. `-575-496` "employee-onboarding-checklist"); catalog: project **1**, row text = `name | Catalog` (inner text "code-reviewer\nCatalog"). Own rows have no Catalog text. List is long (20+ own, 20+ catalog) and scrolls inside the popper -> filter via search before clicking.
5. Search filter works live (typing `employee-onboarding-checklist` -> exactly one row after ~2 s; no Enter needed).
6. **Skill click = select-and-close** (popper closed; search input count 0). Re-open `plus-menu-button` -> `skills-menuitem` before next skill.
7. Panel after own skill: section text `SKILLS`, row `chat-participant-row-{skillId}` (id = skill id, e.g. `-496`) text "name | base" - **own skill shows version "base", not "v1.0"** (case table says "v1.0": drift). Row has `chat-participant-edit-view-button`, `chat-participant-remove-button`; no catalog tag.
8. After catalog skill: same SKILLS section, second row `chat-participant-row-31` with `chat-participant-catalog-tag` (text "Catalog") inside the row and a separate version text **"v1.0"**. Both rows under ONE "SKILLS" header (section inner text: `SKILLS | own | base | code-reviewer | Catalog | v1.0`). Catalog row icon is `<img alt="elitea">` default entity icon; own row uses an svg.
9. Console: only 404 "Failed to load resource" errors (unrelated resource loads, present on blank chat too); no functional errors.

## Handles Reference (verified on DEV 2026-11-11)
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| testid | `sidebar-create-button`, `plus-menu-button`, `chat-participants-panel-toggle-button`, `platform-banner-close` | - | testid on DEV ✓ (existing ChatPage fields) |
| testid | `skills-menuitem` (`<li role=menuitem>`, text "Skills") | - | testid on DEV ✓ - **no ChatPage field yet; add** |
| testid | `skills-menu-item-skill-{projectId}-{skillId}` template | - | testid on DEV ✓ (new template constant, like `AGENT_PARTICIPANT_MENU_ITEM`). Catalog rows: project id `1`; own rows: `${ELITEA_PROJECT_ID}` (575) |
| ladder (placeholder) | search input `input[placeholder="Search skills..."]` -> `css=` rung 4 (or testid `skills-search-input` if present when implementing) | `chat-plus-menu-skills-search-input` | ladder - probe found 1 placeholder match; testid per source but not seen in dump; re-check, use testid if served |
| testid | `chat-participant-row-{skillId}` (prefix enumerate / template) | - | testid on DEV ✓ |
| testid | `chat-participant-catalog-tag` (inside catalog row) | - | testid on DEV ✓ |
| testid | `chat-participant-remove-button` (inside row) | - | testid on DEV ✓ |
| ladder (existing) | section header "Skills" via `ChatPage.PARTICIPANT_SECTION_TITLE.within('Skills')` | `chat-participants-section-title-{}` | ladder - existing ScopedLocator is for Agents/Pipelines/Toolkits/MCPs; **'Skills' arg NOT verified with that xpath** (probe used container innerText "SKILLS") - verify at implement time |
| ladder (scoped text) | version text inside a row: row text "v1.0"/"base" | `chat-participant-version-text` | ladder - no testid on DEV (`<div aria-label="">v1.0</div>`); assert via row `to_contain_text` |
| ladder (scoped text) | "Catalog" label in submenu row | - | assert row `to_contain_text("Catalog")`; own rows `not_to_contain_text("Catalog")` |

## Steps (AFS)
1. Fixture creates own skill (unique name). Open chat (`/app/chat`), dismiss banner, click `sidebar-create-button`, expand participants panel. **Verify** blank chat; no `chat-participant-row-*`.
2. Click `plus-menu-button`. **Verify** `skills-menuitem` visible (text "Skills") alongside Attach Files, Modules, Agents, Pipelines, Toolkits, MCPs. (Do NOT assert "Invite Users" present - absent on private project; may assert absent as in ELITEA-2455.)
3. Open Skills submenu (click `skills-menuitem`). **Verify** search input (placeholder "Search skills...") visible and "Create Skill" button visible.
4. **Verify** list contains the fixture own-skill row (`skills-menu-item-skill-{ELITEA_PROJECT_ID}-{id}`) AND at least the catalog skill row `code-reviewer` (project-1 prefix). Search for each by name first if the list virtualises/scrolls.
5. **Verify** catalog row text contains "Catalog"; own-skill row does not.
6. Search own skill name (type in search input, wait for single match), click row. **Verify** popper closes; panel shows SKILLS section with `chat-participant-row-{id}` containing own name and a version text (observed `base`; assert non-empty version text, prefer exact `base` - declared in Clarifications), no `chat-participant-catalog-tag` in that row.
7. Re-open `plus-menu-button` -> Skills; search `code-reviewer`; click the catalog row. **Verify** popper closes.
8. **Verify** SKILLS section has TWO rows: own row (name, no tag) and catalog row (`code-reviewer`, `chat-participant-catalog-tag` text "Catalog", version text `v1.0`). Both under a single SKILLS header (assert header count == 1). Assert exactly 2 `chat-participant-row-*`.
9. Teardown: skill fixture deletes own skill. No conversation exists (never sent) -> nothing else to clean.

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| 1 Open chat | loads | AFS 1 | covered |
| 2 "+" menu options | Attach Files, Modules, Agents, Pipelines, Skills, Toolkits, MCPs, Invite Users | AFS 2 | covered; "Invite Users" **clarification** (private project: absent) |
| 3 Skills submenu | search "Search skills..." + list | AFS 3 | covered (opens on click, not hover) |
| 4 both own + catalog in list | both present | AFS 4 | covered; example names are **clarification** (code-task-breakdown/jira-skill absent -> fixture own skill; `code-reviewer`/`bug-report-generator` exist) |
| 5 Catalog badge in list | "Catalog" | AFS 5 | covered |
| 6 select own skill | selected | AFS 6 | covered |
| 7 appears in PARTICIPANTS->SKILLS with name + version badge | name, version | AFS 6 | covered; version text for own skill is `base` not "v1.0" (**clarification**) |
| 8-9 re-open, select catalog | selected | AFS 7 | covered |
| 10 catalog in panel with Catalog + version | "code-r... Catalog v1.0" | AFS 8 | covered (full name shown, not truncated at 1500px) |
| 11 both listed in SKILLS | both | AFS 8 | covered |
| Pass: multiple skills in same chat | | AFS 8 | covered |
Axis 2 extras: popper closes after selection (observed select-and-close, step 3-ish); exactly one SKILLS header and exactly 2 rows (case "both listed" intent); own row has no Catalog tag.

## Clarifications (case-text drift, NOT defects)
- Example skills `jira-skill` / `code-task-breakdown` do not exist; use a fixture-created skill.
- Own skill's participant version badge reads `base` (draft/base version), not "v1.0"; catalog skill reads `v1.0`.
- "Invite Users" is absent in a private project (same as ELITEA-2455).
- Menu opens on click for Skills.

## Known defects
None.

## Automation Hints
- Add to `ChatPage`: `skills_menuitem` (testid), `SKILL_MENU_ITEM` template `[data-testid="skills-menu-item-skill-{}-{}"]`, skills search input, a helper `add_skill_participant(name, project_id)`. Reuse `plus_menu_button`, `expand_participants_panel_via_toggle`, `get_participant_row_by_name`.
- Catalog project id is 1 (public); own = `settings.ELITEA_PROJECT_ID`. Prefer locating rows by `has_text` over id for the catalog skill (id could change if re-published).
- Row id = skill id (not re-keyed pre-send).
- Do NOT send a message (would persist a conversation).
- Markers: `@pytest.mark.tms("ELITEA-4628")` + `@allure.issue` pair; chat + skills + p0/regression markers.
