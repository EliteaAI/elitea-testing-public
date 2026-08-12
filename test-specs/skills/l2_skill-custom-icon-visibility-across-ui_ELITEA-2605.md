# Test Case: Skill Custom Icon Visibility Across UI

## Metadata
- **TMS ID**: ELITEA-2605
- **Linked Story**: none
- **Priority**: medium (case frontmatter) — mapped to `l2` (same mapping as the sibling
  medium-priority skill icon case ELITEA-2604)
- **Environment Explored**: local (`http://localhost:5173`, EliteaAI/EliteaUI `automation/testids`
  → DEV backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (agent), 2026-08-12
- **Status**: **ready-for-automation** — case executed end-to-end live: created a skill with a
  distinctive custom icon and confirmed the SAME uploaded-icon `src` renders correctly in all
  five locations the case names (Skills list card, Skill detail page, SkillMenu attach-dropdown,
  Agent SKILLS-section SkillCard, chat `~mention` autocomplete). No functional/visual defect —
  the icon is byte-identical and correctly displayed everywhere. **Three genuine testid gaps
  found** (SkillCard's icon, SkillMenu dropdown item's icon, mention-item's icon all lack any
  `data-testid` on the `<img>` element itself) — implementer work via `add-data-testid`, detailed
  below. Two of the five locations (list card, detail page) already have a usable testid chain
  from prior cases (ELITEA-2428, ELITEA-2604) with no new work needed.
- **Not `extend-existing` against ELITEA-2428** (`l2_skills-card-view-fields_ELITEA-2428.md`,
  merged to `origin/automation/base`): that spec proves the generic `entity-card-icon` container
  is present on a card (a skill with NO custom icon) — it explicitly does not assert custom-icon
  content. This case's scope (5 distinct surfaces: list, detail, SkillMenu, SkillCard, mention
  autocomplete) is far larger than a "gap assertions" append to a single-surface spec would be —
  a near-rewrite by the `extend-existing` boundary rule (`test-case-analysis` skill § Classify
  findings) — so classified `ready-for-automation`, reusing ELITEA-2428's `entity-card-icon-img`
  handle directly rather than duplicating it.

## Preconditions
- User is logged in to the Elitea platform (satisfied automatically on localhost via
  `auth_state`/`VITE_DEV_TOKEN`).
- Admin/Editor role — `${TEST_USER}` has full CRUD on Skills and Agents in project 399.
- **Per this project's Hard Rule 10 test-data guidance**, use a freshly-created, uniquely-named
  disposable skill AND a freshly-created disposable agent — icon visibility across multiple
  surfaces is a case that specifically needs an agent with the skill attached, so mutating a
  shared fixture skill/agent risks polluting other tests' assertions. Both created via their
  respective UI create forms during the case's own steps (skill in steps 1–2, agent in step 7),
  deleted via UI type-to-confirm delete flows (`SkillDetailPage.delete_skill_via_menu()` /
  `AgentDetailPage.delete_agent_via_menu()`) in a `finally`/fixture-teardown block. API-level
  fallback deletes (`skill_api.delete_skill(skill_id)` / `agent_api.delete_agent(agent_id)`) are
  an acceptable safety net, mirroring ELITEA-2602/2604's pattern.
- Test icon file — reuses the existing repo asset `test-data/images/skill-fork-test-icon.png`
  (already added for ELITEA-2602/2604; distinctive, well under the 500KB limit) — no new test
  data file needed for this case.

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill name: `elitea-2605-icon-visibility-skill` (or
  `f"autotest-{request.node.name}"[:32]` per the project's naming convention — must match the
  client-validated regex `/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/`, same constraint documented for
  every prior Skills case).
- Skill description: free text, e.g. "ELITEA-2605 icon visibility verification skill".
- Skill instructions: any non-empty text (content irrelevant).
- Agent name: `elitea-2605-icon-agent`; description free text.
- No toolkits/tags needed on either entity.

## Test Steps

**EXECUTED END-TO-END LIVE 2026-08-12** — all 17 case steps completed with no blockers.

1. Create a skill with a distinctive custom icon and save it
   - **Verify**: skill is created with custom icon
   - **OBSERVED**: navigated to `/skills/create`, opened the icon picker via
     `SkillFormPage.open_icon_picker()` (hover-then-click quirk, pre-existing/documented),
     uploaded `skill-fork-test-icon.png` via `upload_skill_icon()`. Filled name/description/
     instructions, saved. URL settled on `/skills/all/1508` (this run's id). `skill-form-icon-img`
     src: `https://dev.elitea.ai/app/skill_icon/399/19418163-8a9d-474a-b2a9-33b916b20a46.png`.
2. Navigate to the Skills list page
   - **Verify**: Skills list (CardList view) loads
   - **OBSERVED**: `/skills/all` loads with Card view active by default (same default-view
     behavior as ELITEA-2428).
3. Locate the skill in the list
   - **Verify**: skill card is visible
   - **OBSERVED**: `SkillsListPage.skill_card.filter(has_text=name)` locates the card
     (pre-existing pattern, ELITEA-2428/2437/2439 etc.).
4. Verify the custom icon is displayed on the skill card
   - **Verify**: custom icon (not default) is shown on the card
   - **OBSERVED — CONFIRMED LIVE**: the card's `entity-card-icon-img` (inner `<img>`, ELITEA-2428
     handle, currently on `automation/testids` only — see PROVENANCE below) is present with `src`
     **byte-identical** to step 1's uploaded icon URL. No new testid needed — `entity-card-icon-img`
     already exists; it just needs page-object plumbing (`CARD_ICON_IMG_SELECTOR` alongside the
     existing `CARD_ICON_SELECTOR`), same as ELITEA-2428's own Automation Hints already flagged.
     **Automation distinction from ELITEA-2428**: that case asserts `entity-card-icon` (outer
     container) is merely present — this case additionally asserts `entity-card-icon-img` (inner
     `<img>`) is present AND its `src` matches the uploaded icon's URL, which is the actual
     "custom, not default" signal (`entity-card-icon-img` is absent entirely when a skill has no
     custom icon — same EntityIcon convention documented across ELITEA-1899/2604).
5. Click on the skill to open the detail/edit page
   - **Verify**: skill detail page loads
   - **OBSERVED**: clicking the card (or navigating directly, both confirmed) lands on
     `/skills/all/{id}`.
6. Verify the custom icon is displayed on the detail page
   - **Verify**: custom icon is visible in the header/icon area
   - **OBSERVED — CONFIRMED LIVE**: `skill-form-icon-img` (`SkillFormPage.skill_icon_img`,
     pre-existing since ELITEA-2602/2604) `src` is identical to step 1/4's URL. No new work.
7. Navigate to Agents section and create or open an agent
   - **Verify**: Agent editor loads
   - **OBSERVED**: created a fresh agent (`elitea-2605-icon-agent`) via `/agents/create` →
     `AgentFormPage.fill_form()` + `save_and_wait_for_navigation()`. Landed on
     `/agents/all/{id}?viewMode=owner` (this run's id 9108). **Note**: a bare
     `/agents/all/{id}` without `?viewMode=owner` hits the wrong (public) endpoint and 404s —
     already-documented `public_application` vs `application` split
     (`.agents/role-overrides.md` § 4xx/5xx cross-check); confirmed live again this run (not a
     new defect, just a reminder for whichever page-object method reopens an agent by id).
8. Go to the SKILLS section of the agent
   - **Verify**: Skills attachment area is visible
   - **OBSERVED**: the "Skills" accordion is expanded by default on a freshly-created agent,
     showing "0/5 skills added." with the "+ Skill" button (`agent-add-skill-button`,
     pre-existing) — matches every prior Skills-attach case (ELITEA-1789/1790/1791/1793 etc.).
9. Click to add/attach a skill
   - **Verify**: Skill picker/menu opens
   - **OBSERVED**: `AgentDetailPage.attach_skill()`'s existing flow — click
     `agent-add-skill-button`, `Popper.wait_for()` opens the `UnifiedDropdown` (`SkillMenu.jsx`).
10. Locate the skill in the SkillMenu dropdown
    - **Verify**: Skill appears in the list
    - **OBSERVED**: confirmed live via `Popper.select_menuitem_by_testid`'s existing pattern —
      `[data-testid="toolkit-menu-item"]` filtered by `has_text=skill_name` locates the row.
11. Verify the custom icon is displayed in the SkillMenu
    - **Verify**: Custom icon is shown next to skill name in dropdown
    - **OBSERVED — CONFIRMED LIVE, NEW TESTID GAP**: the dropdown row for
      `elitea-2605-icon-visibility-skill` visually renders the SAME custom icon (`<img alt="elitea"
      src=".../19418163-....png">`, byte-identical to steps 1/4/6) — confirmed both via
      accessibility snapshot (the row shows `img "elitea"` as a child, unlike every other
      no-custom-icon row in the same list, which show no `img` at all) and via
      `page.evaluate()` DOM inspection during exploration (exploration-only, never a shipped
      locator — testid-only policy has no fallback rung). **The `<img>` element itself has NO
      `data-testid`** — confirmed via source read (`SkillMenu.jsx`'s `items` builder passes
      `icon={skill.icon_meta?.url ? <EliteAImage image={skill.icon_meta} .../> : <SkillIcon/>}`
      with no testid prop on either branch), and the shared row testid (`toolkit-menu-item`) is
      NOT unique per row (repeats once per dropdown item, same as every other `UnifiedDropdown`
      consumer) — see Concrete Handles / testid-gap fix below.
12. Attach the skill to the agent
    - **Verify**: Skill is attached successfully
    - **OBSERVED**: clicking the row attaches via `PATCH .../skill/prompt_lib/399/{id}` → 201
      (existing `AgentDetailPage.attach_skill()` mechanism); the "0/5" counter updated to "1/5
      skills added." — confirmed live, no separate agent-level Save needed (auto-save, same
      pattern as every prior Skills-attach case).
13. Verify the custom icon is displayed in the Agent's SKILLS section (SkillCard)
    - **Verify**: Custom icon is shown on the attached skill card
    - **OBSERVED — CONFIRMED LIVE, NEW TESTID GAP**: the attached-skill `SkillCard`
      (`skill-card-{skill_id}`, pre-existing container testid, ELITEA-1735/1792 etc.) visually
      renders the SAME custom icon — confirmed both via accessibility snapshot (`img "elitea"`
      as a child of the skill-name row) and DOM inspection (`img.src` byte-identical to steps
      1/4/6/11). **The `<img>` itself has NO `data-testid`** — confirmed via source read
      (`SkillCard.jsx`: `{skill.icon_meta?.url ? <EliteAImage image={skill.icon_meta}
      .../> : <SkillIcon .../>}`, no testid prop on either branch, unlike the card's OTHER
      interactive elements which already carry testids — `skill-card-remove-button` etc.) — see
      Concrete Handles / testid-gap fix below.
14. Save the agent
    - **Verify**: Agent is saved with skill attached
    - **OBSERVED — CLARIFICATION, same reverse-masking pattern as ELITEA-1899/2604's icon-persist
      steps**: skill attachment is an immediate auto-save (step 12's PATCH already persisted it
      server-side) — there is no separate "click Save to persist the attachment" action needed.
      Confirmed live: the agent-level `Save` button stays disabled after attaching a skill (only
      `Save As Version` is ever enabled, and only when other version-level fields change).
      Automation should assert the attachment survives a full agent reload rather than clicking a
      Save button that has nothing new to save.
15. Open a chat conversation with the agent
    - **Verify**: Chat interface loads
    - **OBSERVED**: used the agent detail page's embedded chat (same composer
      `AgentDetailPage`/`ChatPage` share via `MentionSkillList.jsx`) — the case's wording ("open a
      chat conversation with the agent") is satisfied equally by the embedded chat or a full
      `/chat` conversation with the agent as participant; both consume the identical
      `MentionSkillList` component (confirmed via source read, same file backs both surfaces —
      same finding already documented in ELITEA-1791's AFS for the Instructions-field variant of
      this same component). This case exercises the embedded-chat / conversation composer
      specifically (not the Instructions-field variant), matching the case's own step 15 wording.
16. Type `~` to trigger skill autocomplete
    - **Verify**: Autocomplete dropdown appears
    - **OBSERVED**: `press_sequentially("~")` into the message input opens the "Mention skill"
      popper (`skill-mention-list` testid, pre-existing since ELITEA-1735/1791/1793), listing the
      one attached skill as `skill-mention-item-elitea-2605-icon-visibility-skill` (pre-existing
      dynamic testid template `MENTION_SKILL_ITEM`/`SKILL_MENTION_ITEM`).
17. Verify the custom icon is displayed in the `~mention` autocomplete
    - **Verify**: Custom icon is shown next to skill name in autocomplete
    - **OBSERVED — CONFIRMED LIVE, NEW TESTID GAP**: the mention-item row visually renders the
      SAME custom icon (`<img>` inside the `skill-mention-item-{name}`-testid row) — confirmed via
      DOM inspection: `src` byte-identical to steps 1/4/6/11/13. **The `<img>` itself has NO
      `data-testid`** — confirmed via source read (`MentionSkillList.jsx`'s `filteredItems.map`
      passes `icon={item.icon_meta?.url ? <EliteAImage image={item.icon_meta} .../> :
      <SkillIcon/>}` into the shared `MentionToolItem.jsx`, which renders `{icon && <Box
      sx={styles.iconBox}>{icon}</Box>}` — no testid prop anywhere in the icon path, even though
      the row's own OUTER testid (`skill-mention-item-{name}`) already exists) — see Concrete
      Handles / testid-gap fix below.

## Expected Results

Per case: the custom skill icon is consistently displayed across all five UI locations — Skills
list card, Skill detail/edit page, SkillMenu dropdown (skill picker), Agent SKILLS-section
SkillCard, and `~mention` autocomplete in Chat.

**Actual (observed 2026-08-12)**: matches expected on all five points — the SAME uploaded icon
`src` (`https://dev.elitea.ai/app/skill_icon/399/19418163-8a9d-474a-b2a9-33b916b20a46.png`)
renders correctly and identically in every location. **Case PASSES, no product/visual defect.**
Zero console errors across the entire flow (verified via `browser_console_messages(level="error")`
after each major step) except one already-documented, unrelated navigation artifact: a bare
`/agents/all/{id}` URL (no `?viewMode=owner`) hit the wrong `public_application` endpoint → 400 —
this is the pre-existing, already-canon `public_application` vs `application` split documented in
`.agents/role-overrides.md` § 4xx/5xx cross-check, reproduced by this run's OWN navigation choice
(reopening the agent without the query param), not a new defect and not part of the case's own
17 steps (the case never asks to reopen the agent by bare URL).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in, Admin/Editor role | session valid | n/a (auto via `auth_state`) | — | asserted (environment-level) |
| Precondition: skill with distinctive custom icon exists | icon set | AFS step 1 | step 1 | covered — created fresh, disposable |
| Precondition: agent exists that can have skills attached | agent available | AFS step 7 | step 7 | covered — created fresh, disposable |
| 1 Create a skill with a distinctive custom icon and save | skill created with custom icon | step 1 | step 1: `skill-form-icon-img` src set | covered |
| 2 Navigate to the Skills list page | Skills list (CardList) loads | step 2 | step 2: `/skills/all` loads, Card view default | covered |
| 3 Locate the skill in the list | skill card visible | step 3 | step 3: card located by name filter | covered |
| 4 Verify custom icon displayed on the skill card | custom (not default) icon shown | step 4 | step 4: `entity-card-icon-img` src match | covered — testid pre-existing (ELITEA-2428), page-object plumbing needed |
| 5 Click skill to open detail/edit page | detail page loads | step 5 | step 5: `/skills/all/{id}` loads | covered |
| 6 Verify custom icon displayed on detail page | custom icon visible in header | step 6 | step 6: `skill-form-icon-img` src match | covered — testid + page-object already exist (ELITEA-2602/2604) |
| 7 Navigate to Agents, create/open an agent | Agent editor loads | step 7 | step 7: `/agents/all/{id}?viewMode=owner` loads | covered |
| 8 Go to SKILLS section of the agent | Skills attachment area visible | step 8 | step 8: "0/5 skills added." + `agent-add-skill-button` visible | covered |
| 9 Click to add/attach a skill | Skill picker/menu opens | step 9 | step 9: `UnifiedDropdown` popper opens | covered |
| 10 Locate the skill in the SkillMenu dropdown | Skill appears in list | step 10 | step 10: `toolkit-menu-item` filtered by name | covered |
| 11 Verify custom icon displayed in SkillMenu | Custom icon shown next to name | step 11 | step 11: visual/DOM confirm; **NEW TESTID GAP** | covered — testid needed: `skill-menu-item-icon-img` |
| 12 Attach the skill to the agent | Skill attached successfully | step 12 | step 12: PATCH 201, counter "0/5"→"1/5" | covered |
| 13 Verify custom icon in Agent's SKILLS section (SkillCard) | Custom icon shown on attached card | step 13 | step 13: visual/DOM confirm; **NEW TESTID GAP** | covered — testid needed: `skill-card-icon-img` |
| 14 Save the agent | Agent saved with skill attached | step 14 | step 14 | covered — CLARIFICATION: auto-saved at attach time, no separate Save action (same pattern as ELITEA-1899/2604) |
| 15 Open a chat conversation with the agent | Chat interface loads | step 15 | step 15: embedded chat composer active | covered |
| 16 Type `~` to trigger skill autocomplete | Autocomplete dropdown appears | step 16 | step 16: `skill-mention-list` visible | covered |
| 17 Verify custom icon in `~mention` autocomplete | Custom icon shown next to name | step 17 | step 17: visual/DOM confirm; **NEW TESTID GAP** | covered — testid needed: `skill-mention-item-icon-img` |
| Expected Final State: custom icon consistent across all 5 locations | as above | AFS steps 1–17 | all steps | covered — all 5 confirmed, same byte-identical `src` |

### Axis 2 — Analyst additions

- Asserted `src` **byte-equality** across all five locations (not just "an icon is present") —
  a stronger check than the case's own wording ("is displayed"), catching a future regression
  where one surface silently falls back to a stale/default/wrong icon URL while the others stay
  correct.
- Confirmed, via source read, that the SkillMenu dropdown and the `~mention` autocomplete BOTH
  render custom icons through the exact same `icon_meta?.url ? <EliteAImage/> : <SkillIcon/>`
  ternary pattern used by `SkillCard.jsx` and (via `EntityIcon.jsx`) `Card.jsx`'s list-card icon —
  confirming this is one consistent app-wide convention, not five independently-implemented icon
  paths that happened to agree in this run.
- Distinguished, for automation purposes, which of the 5 locations already have a fully-wired
  testid chain (list card: testid exists, page-object plumbing missing; detail page: fully wired)
  from which 3 need a genuinely new testid on the `<img>` element itself (SkillMenu item, SkillCard
  in Agent SKILLS section, mention-autocomplete item) — the case text treats all 5 as equally
  "verify the icon is shown," but the automation cost differs sharply per location.
- Verified zero console errors across the full 17-step flow (the one 400 noted in Expected Results
  is a pre-existing, already-documented artifact of this run's OWN navigation shortcut, not part
  of the case's own steps — see role-overrides § 4xx/5xx cross-check).
- Clarified (case-text drift, not a defect) that "chat conversation with the agent" in step 15 is
  satisfied by either the embedded agent-detail chat or a full `/chat` conversation — both share
  the identical `MentionSkillList` component, same finding already on file for ELITEA-1791's
  Instructions-field variant.

## Cleanup
- **Skill created during this pass (id 1508, name `elitea-2605-icon-visibility-skill`)** was
  deleted via the UI's type-to-confirm delete flow (detail page → overflow "⋮" menu → "Delete
  skill" → typed exact name → Delete). Verified via network:
  `DELETE /api/v2/elitea_core/skill/prompt_lib/399/1508` → **204 No Content**. (A subsequent
  `GET` for the same id returned 404 — expected stale-refetch artifact, same pattern documented in
  ELITEA-2604's Expected Results, not something this run's own flow caused.)
- **Agent created during this pass (id 9108, name `elitea-2605-icon-agent`)** was deleted via the
  same UI type-to-confirm flow (overflow menu → "Delete agent" → typed exact name → Delete).
  Verified via network: `DELETE /api/v2/elitea_core/application/prompt_lib/399/9108` →
  **204 No Content**.
- Nothing left behind from this analysis run.

## Concrete Handles (discovered/confirmed during exploration)

All testids below are **pre-existing** except the three explicitly marked NEW GAP.

| Element | Testid / Handle | Notes | PROVENANCE |
|---|---|---|---|
| Skill form icon `<img>` (create + detail/edit page) | `skill-form-icon-img` (`SkillFormPage.skill_icon_img`) | pre-existing (ELITEA-2602/2604) | on `automation/testids` only (awaiting human promotion to `main`) |
| Skills list card icon container | `entity-card-icon` (`SkillsListPage.CARD_ICON_SELECTOR`, wired via `card_icon_locator()`) | pre-existing (ELITEA-2428) | on `automation/testids` only |
| **Skills list card icon `<img>` (custom-icon signal)** | `entity-card-icon-img` — testid EXISTS but **no page-object field yet on `SkillsListPage`** (only the outer `entity-card-icon` is wired) | pre-existing testid (ELITEA-2428 already flagged the gap), implementer adds `CARD_ICON_IMG_SELECTOR = '[data-testid="entity-card-icon-img"]'` + a `card_icon_img_locator(name)` helper mirroring `card_icon_locator()` | on `automation/testids` only |
| Agent "+ Skill" button | `agent-add-skill-button` (`AgentDetailPage.agent_add_skill_button`) | pre-existing (ELITEA-1735) | on `main` ✓ |
| SkillMenu dropdown item (row, shared/generic) | `toolkit-menu-item` (filtered by `has_text=skill_name`, `Popper.select_menuitem_by_testid`) | pre-existing, NOT unique per row — must scope by text filter | on `main` ✓ |
| **SkillMenu dropdown item's icon `<img>` — NEW GAP** | **NONE** | `SkillMenu.jsx`'s `items` builder passes `icon={skill.icon_meta?.url ? <EliteAImage image={skill.icon_meta} .../> : <SkillIcon/>}` with no testid on either branch. Fix: pass `data-testid="skill-menu-item-icon-img"` to the `EliteAImage` (custom-icon) branch only — per this project's same-element-conditional-pair convention (`.agents/testing.md` § Locator policy, "only the used branch is named" shape), leave the default `SkillIcon` branch untagged. Scope by chaining off the ALREADY-filtered `toolkit-menu-item` row: `row.locator('[data-testid="skill-menu-item-icon-img"]')` — this is collision-safe (the testid repeats once per row, exactly like `entity-card-icon`/`skill-card-*`, but each usage is scoped to its own already-name-filtered row) | needs-adding |
| Agent SKILLS-section SkillCard container | `skill-card-{skill_id}` (`AgentDetailPage.SKILL_CARD_SELECTOR`, via `_skill_card()`) | pre-existing (ELITEA-1735) | on `main` ✓ |
| **Agent SKILLS-section SkillCard's icon `<img>` — NEW GAP** | **NONE** | `SkillCard.jsx` (`src/[fsd]/features/skill/ui/SkillCard.jsx`) renders `{skill.icon_meta?.url ? <EliteAImage image={skill.icon_meta} .../> : <SkillIcon/>}` with no testid on either branch — unlike the card's OTHER elements (`skill-card-remove-button` etc.), which already carry testids. Fix: pass `data-testid="skill-card-icon-img"` to the `EliteAImage` (custom-icon) branch only, same conditional-pair convention as above. Scope: `self._skill_card(skill_name).locator('[data-testid="skill-card-icon-img"]')` | needs-adding |
| Chat `~mention` popper container | `skill-mention-list` (`ChatPage.mention_skill_list` / `AgentDetailPage` equivalent) | pre-existing (ELITEA-1735/1791/1793) | on `main` ✓ |
| Chat `~mention` popper item (row, per-skill) | `skill-mention-item-{name}` (`MENTION_SKILL_ITEM`/`SKILL_MENTION_ITEM` template) | pre-existing dynamic testid | on `main` ✓ |
| **Chat `~mention` item's icon `<img>` — NEW GAP** | **NONE** | `MentionSkillList.jsx` passes `icon={item.icon_meta?.url ? <EliteAImage image={item.icon_meta} .../> : <SkillIcon/>}` into the shared `MentionToolItem.jsx`, which renders `{icon && <Box sx={styles.iconBox}>{icon}</Box>}` with no testid anywhere in the icon path, even though the row's own outer testid already exists. Fix: pass `data-testid="skill-mention-item-icon-img"` to the `EliteAImage` (custom-icon) branch only, same conditional-pair convention. Scope: `self.MENTION_SKILL_ITEM.format(name)`-located row `.locator('[data-testid="skill-mention-item-icon-img"]')`. **Note**: `SkillMenu.jsx`'s dropdown item (the row above) uses the SAME `<EliteAImage>`/`<SkillIcon>` ternary but is a DIFFERENT JSX call site — do not conflate the two fixes; both need their own testid string even though the underlying pattern is identical | needs-adding |
| Skill controls overflow menu / Delete skill flow | `skill-controls-menu-button`, `skill-delete-menu-item`, `delete-confirm-name-input`, `delete-confirm-button` (`SkillDetailPage.delete_skill_via_menu()`) | pre-existing | on `main` ✓ |
| Agent actions overflow menu / Delete agent flow | `agent-actions-menu-button`, `delete-agent-menuitem`, `delete-confirm-name-input`, `delete-confirm-button` (`AgentDetailPage.delete_agent_via_menu()`) | pre-existing | on `main` ✓ |

**Fallbacks**: none — testid-only locator policy, no fallback rung (`.agents/testing.md` §
Locator policy). Where a testid is genuinely missing (the 3 NEW GAP rows above), the fix is
`add-data-testid`, never a role/CSS/text handle.

## Network Behavior

| Action | Request | Response |
|---|---|---|
| Upload icon during skill creation | `POST /api/v2/elitea_core/upload_skill_icon/prompt_lib/399` | 200 OK |
| Save skill (create) | `POST /api/v2/elitea_core/skill/prompt_lib/399` | 200/201 |
| Load Skills list | `GET /api/v2/elitea_core/skill/prompt_lib/399?...` | 200 OK — `icon_meta.url` present per row |
| Save agent (create) | `POST /api/v2/elitea_core/application/prompt_lib/399` | 200/201 |
| Open SkillMenu dropdown (skill search) | `GET /api/v2/elitea_core/skill/prompt_lib/399?query=...` | 200 OK — `icon_meta.url` present per row |
| Attach skill to agent | `PATCH /api/v2/elitea_core/skill/prompt_lib/399/{id}` | 201 Created |
| Delete skill (cleanup) | `DELETE /api/v2/elitea_core/skill/prompt_lib/399/{id}` | 204 No Content |
| Delete agent (cleanup) | `DELETE /api/v2/elitea_core/application/prompt_lib/399/{id}` | 204 No Content |

The `~mention` autocomplete fires NO new network request when `~` is typed — it reads from data
the page already holds from an earlier agent/skills fetch (same finding already documented in
ELITEA-1791's AFS).

## Known Defects Found During Exploration

None. All five UI locations correctly and consistently display the custom icon. The three testid
gaps (SkillMenu item icon, Agent SKILLS-section SkillCard icon, mention-autocomplete item icon)
are automation-locator gaps, not functional/visual product defects — the icon renders correctly
in the browser in all three cases, it's only invisible to a testid-only automated locator today.

## Blocked Steps

None. All 17 case steps executed to completion with no blockers.

## Automation Hints

- **Reuse existing page-object surfaces** — `SkillFormPage.open_icon_picker()`/
  `upload_skill_icon()`/`get_form_icon_src()` (ELITEA-2602/2604) for step 1;
  `SkillsListPage.card_icon_locator()` (ELITEA-2428) for step 3, extended with a new
  `card_icon_img_locator()` for step 4; `AgentDetailPage.attach_skill()` (ELITEA-1735) for
  steps 8–12; `ChatPage.open_mention_skill_popper()`/`is_skill_in_mention_popper()`
  (ELITEA-1791/1793) for steps 16–17. Do not re-implement any of these.
- **The three testid-gap fixes are the SAME conditional-pair shape, applied at three different
  call sites** — `SkillMenu.jsx`, `SkillCard.jsx`, and `MentionSkillList.jsx` all independently
  implement `icon_meta?.url ? <EliteAImage .../> : <SkillIcon/>`. Each needs its OWN
  `data-testid` string on its own `EliteAImage` (custom-icon branch only, leave `SkillIcon`
  untagged — the "only the used branch is named" shape from `.agents/testing.md` § Locator
  policy). Recommended names (verified unique against the existing testid inventory this run):
  `skill-menu-item-icon-img`, `skill-card-icon-img`, `skill-mention-item-icon-img`. All three
  fixes land via ONE `add-data-testid` pass on `../EliteaUI` since they're all small, additive
  JSX prop additions in files the implementer will already have open.
- **Assertion shape**: for each of the 5 locations, assert (a) the icon `<img>` element for a
  CUSTOM-icon skill is present, and (b) its `src` equals the uploaded icon's URL captured at step
  1 — do not just assert "an icon element exists" (that passes even for the generic/default
  glyph, which is a DIFFERENT element entirely — `EntityTypeIcon`/`SkillIcon` SVG vs `EliteAImage`
  `<img>` — see the `entity-card-icon-img` PROVENANCE row: its very presence IS the "has custom
  icon" signal, its absence IS the "default icon" signal, matching the established convention from
  ELITEA-1899/2604).
- **Negative-control opportunity (Axis-2, optional)**: this run observed live that OTHER skills in
  the same SkillMenu dropdown (skills with no custom icon set) render NO `<img>` in their row at
  all — a parametrized test could additionally assert `to_have_count(0)` for the icon-img testid
  on a known no-custom-icon skill's row, strengthening the "custom vs default" distinction beyond
  a single-skill positive check. Not required to satisfy the case's own pass criteria.
- **Timeouts**: this run observed all navigation/attach/mention-popper-open actions complete well
  under 2s on localhost — the project's standard `UI_ELEMENT_TIMEOUT = 10_000` is comfortably
  sufficient.
- **Agent reopen gotcha**: if the implementer's test reopens the created agent by direct URL
  navigation (rather than staying on the page after create), it MUST include `?viewMode=owner`
  (`/agents/all/{id}?viewMode=owner`) — a bare `/agents/all/{id}` hits the `public_application`
  endpoint and 404s (pre-existing, documented — `.agents/role-overrides.md` § 4xx/5xx
  cross-check). Not relevant if the test stays on the page after the create-save redirect (the
  URL already carries the param at that point).
