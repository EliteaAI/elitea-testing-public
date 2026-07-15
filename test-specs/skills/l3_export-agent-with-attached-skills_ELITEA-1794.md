# Test Case: Export Agent with attached Skills — exported .md contains Skill content

## Metadata
- **TMS ID**: ELITEA-1794
- **Linked Story**: none
- **Priority**: l3 (medium — case authored as "high" priority, but sibling cases in
  this batch are filed at l3; kept consistent with the batch's existing naming
  convention, see `test-specs/skills/l3_*`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), model:
  Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation — case executed end-to-end, all 7 steps pass, no
  defects. The exported `.md` file was downloaded, opened, and its raw content
  (YAML frontmatter + body) inspected directly — Skill name, `base` version, and
  the full instructions text (including a unique marker string planted for this
  run) are all embedded verbatim in the export, not merely referenced by ID.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Skills and Agents sections are available in the project.
- An Agent exists with at least one Skill attached — created fresh in this run (see
  Test Data). No pre-existing Agent in the project had a disposable single-Skill
  shape suitable for export inspection, so seed-and-cleanup was used (this case's
  observable — exported file content — inherently requires knowing the exact
  Skill instructions text planted, so a fresh disposable Skill+Agent is required
  rather than reusing an unknown pre-existing one).
- The Agent export feature is available (confirmed live: `Export` menuitem under
  the agent-actions overflow menu's `VERSION` group).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill name: kebab-case, e.g. `elitea-1794-export-skill` — **must be lowercase
  letters/digits/hyphens only** (client-side Skill-name validation documented in
  `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`, confirmed
  again live in this run). The case's Test Data table ("Formatter" as a literal
  example name) is descriptive shorthand, not a literal value to type — same
  reverse-masking pattern already confirmed for ELITEA-1789/1792/1739/1737/1735.
- Skill description: any non-empty string, e.g. `"Test skill for ELITEA-1794 export
  verification."`
- Skill instructions: any non-empty string under the 2500-char limit, but **must
  contain a unique marker substring** planted by the test so the exported file's
  instructions text can be asserted as verbatim rather than merely "non-empty" —
  used in this run: `"You are elitea-1794-export-skill. This exact instruction
  sentence ELITEA_1794_MARKER_TEXT must appear verbatim in the exported Agent .md
  file, not merely referenced."` (the literal string `ELITEA_1794_MARKER_TEXT` is
  the load-bearing assertion anchor — grep the downloaded file for it).
- Agent name: e.g. `elitea-1794-export-agent`; description and a short generic
  instructions string (agent's own instructions content is asserted separately —
  it appears in the export body, below the YAML frontmatter — but is not this
  case's focus, which is the attached-Skill's content).

No `reuse-existing` or shared fixture applies — this is a fresh-state flow (1 skill
+ 1 agent, both created and torn down within the run).

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`. Fill Name (`skill-name-input` — wrapper
   div, target descendant `input` via `getByRole('textbox', { name: 'Name *' })`),
   Description (`skill-description-input`, same wrapper-div caveat), and
   Instructions (`skill-instructions-editor-content`, CodeMirror — `.fill()` worked
   directly on the testid in this run despite the memory note recommending
   `press_sequentially`; either approach is safe). Click Save
   (`skill-save-button`); confirm the "There are unsaved changes..." nav-blocker
   dialog via `alert-dialog-confirm-button`.
   - **Verify**: Skill saves successfully; URL settles on `/skills/all/{id}`
     (Skill id `290` in this run).
2. Navigate to `${BASE_URL}/agents/create`. Fill Name (`agent-name-input`),
   Description (`agent-description-input`), and Instructions
   (`agent-instructions-input`, single-line MUI `Textarea` — `.fill()` works
   directly here, unlike the Skill fields). Click Save (`agent-save-button`).
   - **Verify**: navigates to `/agents/all/{agent-id}?destTab=configuration...`
     with no nav-blocker dialog (consistent with ELITEA-1789/1792). Agent id `4702`
     in this run.
3. On the agent detail page, the Skills accordion section is expanded by default,
   shows "0/5 skills added." with an add-skill button (`getByRole('button', {
   name: 'Skill', exact: true })`, no testid — matches the ELITEA-1735/1789/1792
   handle). Click it, then select the Skill from the "Search skills..." popper's
   menuitem list.
   - **Verify** (case Precondition — "Agent exists with at least one Skill
     attached"): counter updates "0/5" → "1/5 skills added."; one skill card
     renders showing `elitea-1794-export-skill` / `base` version. Attachment is
     auto-saved via `PATCH /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}`
     → `201 Created` (same auto-save pattern documented for
     ELITEA-1735/1789/1792); the agent-level `Save` button stays disabled.
4. (Case step 1) Confirm the Agent detail/edit view is open with the Skill
   attached (already satisfied by Test Step 3's verification).
5. (Case step 2) Open the agent-actions overflow menu
   (`agent-actions-menu-button`, same handle documented for ELITEA-1792) and click
   the `Export` menuitem (`agent-actions-export-menuitem` — added 2026-07-15 via
   `add-data-testid`, see Handles Reference — in the `VERSION` group, alongside
   `Set as a default` (disabled), `Share`, `Fork`, `Publish`, `Delete` (disabled)).
   - **Verify** (case step 2): a file download is initiated. Confirmed live via
     the Playwright MCP download event: `elitea-1794-export-agent.agent.md`
     downloaded automatically, no save-location dialog. Network trace shows `GET
     /api/v2//elitea_core/export_import/prompt_lib/{project}/{agent-id}?format=md&follow_version_ids={agent-id}`
     → `200 OK` (note the literal doubled `//` after `/v2` in the URL — the
     endpoint responds successfully despite it; this is a URL-construction
     oddity worth flagging to the implementer as an observation, not a defect,
     since it doesn't affect the response or the pass/fail outcome).
6. (Case step 3) Verify the exported file has a `.md` extension.
   - **Verify** (case step 3): confirmed — filename `elitea-1794-export-agent.agent.md`
     (note the double extension `.agent.md`; the file is still a valid `.md` file
     by extension, satisfying the case's literal "has a .md extension" criterion).
7. (Case steps 4–7) Open and inspect the exported file's raw content.
   - **Verify** (case step 4 — readable): file opens as plain YAML-frontmatter +
     markdown-body text.
   - **Verify** (case step 5 — Skill name present): frontmatter contains a
     `skills:` list with `- name: elitea-1794-export-skill`.
   - **Verify** (case step 6 — Skill instructions embedded, not just a
     reference): the same list item's `instructions:` field contains the full
     planted instructions string verbatim, confirmed by finding the literal
     marker substring `ELITEA_1794_MARKER_TEXT` in the downloaded file.
   - **Verify** (case step 7 — Skill version indicated): the same list item's
     `version:` field reads `base`.
   - Full captured frontmatter (this run):
     ```yaml
     ---
     name: elitea-1794-export-agent
     description: Agent for ELITEA-1794 export verification.
     model: eu.anthropic.claude-sonnet-4-5-20250929-v1:0
     temperature: 0.6
     max_tokens: -1
     agent_type: agent
     step_limit: 25
     skills:
     - name: elitea-1794-export-skill
       description: Test skill for ELITEA-1794 export verification.
       version: base
       instructions: You are elitea-1794-export-skill. This exact instruction sentence ELITEA_1794_MARKER_TEXT must appear verbatim
         in the exported Agent .md file, not merely referenced.
     ---

     You are a test agent used for verifying Agent export with attached Skills.
     ```
   - No console errors observed during navigation, attach, or export/download
     (checked via `browser_console_messages` immediately after the export click).

## Handles Reference

> **Amended 2026-07-15 (ELITEA-1794 testid-rework, PR review of automation PR #53).**
> Per `.agents/role-overrides.md` § Analyst slot, every primary handle below is now
> a testid, and a **Provenance** column records whether that testid is live on
> `EliteaUI` `main`, only on the shared `automation/testids` integration branch
> pending a draft PR, or still missing entirely. Two rows that still resolve via
> role/text (`Agent add-skill button`, `Skill-attach popper item`, `Delete-confirmation
> confirm button`) are pre-existing, out-of-scope tech debt shared with
> ELITEA-1735/1789/1792 — flagged `needs-adding`, not fixed here.

| Element | testid | Provenance | Notes |
|---|---|---|---|
| Skill Name field | `skill-name-input` (wrapper) → descendant `input` or `getByRole('textbox', { name: 'Name *' })` | on-main ✓ | kebab-case validation |
| Skill Description field | `skill-description-input` (wrapper) → descendant `textarea` or `getByRole('textbox', { name: 'Description *' })` | on-main ✓ | same wrapper-div caveat |
| Skill Instructions editor | `skill-instructions-editor-content` | on-automation/testids only (draft EliteaUI#526) | CodeMirror; `.fill()` worked directly in this run; not yet on `main` — pre-existing dependency this case has always had (same gap tracked for ELITEA-1737) |
| Skill Save button | `skill-save-button` | on-main ✓ | |
| Nav-blocker confirm | `alert-dialog-confirm-button` | on-main ✓ | fires on Skill-create Save |
| Agent Name field | `agent-name-input` | on-main ✓ | same wrapper-div fill caveat as Skill Name |
| Agent Description field | `agent-description-input` | on-main ✓ | |
| Agent Instructions field | `agent-instructions-input` | on-main ✓ | `.fill()` works directly (single-line MUI Textarea, not a wrapper div) |
| Agent Save button | `agent-save-button` (create form) | on-main ✓ | |
| Agent add-skill button | no testid; `getByRole('button', { name: 'Skill', exact: true })` | needs-adding | matches ELITEA-1735/1789/1792's amended handle; out of this case's scope |
| Skill-attach popper item | `role="menuitem"`, accessible name = skill name (search box placeholder `"Search skills..."`) | needs-adding | out of this case's scope |
| **Agent actions (overflow) menu (this case's core element)** | `agent-actions-menu-button` | on-main ✓ | opens VERSION/AGENT grouped menu |
| **"Export" menuitem (this case's core element)** | `agent-actions-export-menuitem` | on-automation/testids only (draft EliteaUI#549) | Located in the `VERSION` group, between `Set as a default` (disabled) and `Share`. Clicking it triggers an immediate browser download — no confirmation dialog, no save-location prompt. **Amended 2026-07-15**: replaces the prior `getByRole('menuitem', { name: 'Export' })` handle (PR #53 review finding, `CHANGES_REQUESTED`) — added via `add-data-testid` as `key: 'agent-actions-export'` on `useExportApplicationMenu()`'s menu item (`ExportApplicationButton.jsx`), rendered by `DotMenu.jsx`'s existing `testId: item.key` → `${testId}-menuitem` convention. |
| Downloaded file naming pattern | `{agent-name}.agent.md` | n/a (not a UI handle) | Double extension (`.agent.md`) — still resolves as a valid `.md` file for the case's "has a `.md` extension" criterion |
| Export network call | `GET /api/v2//elitea_core/export_import/prompt_lib/{project}/{agent-id}?format=md&follow_version_ids={agent-id}` → `200 OK` | n/a (network call, not a UI handle) | Note the doubled `//` after `/v2` — cosmetic URL-construction quirk, does not affect response; not filed as a defect since it doesn't violate any pass/fail criterion |
| Skill controls (overflow) menu | `skill-controls-menu-button` | on-main ✓ | opens VERSION/SKILL grouped menu (cleanup) |
| Delete-skill menu item | `skill-delete-menu-item` | on-main ✓ | in the SKILL group |
| Delete-agent menu item | `delete-agent-menuitem` | on-main ✓ | in the AGENT group |
| Delete-confirmation name field | `delete-confirm-name-input` (scope to inner `#name` field) | on-automation/testids only (draft EliteaUI#525) | shared component, both agent and skill delete flows; not yet on `main` |
| Delete-confirmation confirm button | `getByRole('button', { name: 'Delete' })` scoped to the dialog | needs-adding | enabled only once typed name matches; out of this case's scope |

## Expected Results
- An Agent with 1 attached Skill is created successfully.
- Triggering `Export` from the agent-actions overflow menu (`VERSION` group)
  downloads a file with a `.md`-suffixed name (`{agent-name}.agent.md` in this
  run).
- The downloaded file's content is a YAML frontmatter block (`name`,
  `description`, `model`, `temperature`, `max_tokens`, `agent_type`, `step_limit`,
  `skills`) followed by the Agent's own instructions as the markdown body.
- Within the `skills:` list, each attached Skill is represented as a full object
  with `name`, `description`, `version`, and `instructions` fields — the
  `instructions` field contains the Skill's complete instructions text verbatim
  (confirmed via a planted unique marker string), not an ID or bare reference.
- No console errors or failed network requests occur during the functional flow.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: Agent exists with ≥1 Skill attached | Agent detail view shows attached Skill | Test Steps 1–3 | Skill created; attached to fresh Agent; counter "0/5"→"1/5 skills added.", card renders name+`base` version | asserted |
| Step 1: Navigate to Agents, open Agent with attached Skills | Agent detail/edit view open | Test Step 4 | Already satisfied by Step 3's navigation + verification | asserted |
| Step 2: Trigger Export action | File download initiated | Test Step 5 | `Export` menuitem clicked from agent-actions overflow menu; Playwright MCP download event fired; network call `GET .../export_import/...?format=md` → `200 OK` | asserted |
| Step 3: Verify exported file has `.md` extension | Downloaded file is `.md` | Test Step 6 | Filename `elitea-1794-export-agent.agent.md` — resolves as `.md` | asserted |
| Step 4: Open exported file, inspect contents | File contents readable | Test Step 7 | Raw file read directly; YAML frontmatter + markdown body, human-readable | asserted |
| Step 5: Verify Skill name present | Skill name appears in file | Test Step 7 | `skills[0].name: elitea-1794-export-skill` present verbatim | asserted |
| Step 6: Verify Skill instructions/content present (not just ID/reference) | Skill instruction text embedded | Test Step 7 | `skills[0].instructions` contains the full planted string including the unique marker `ELITEA_1794_MARKER_TEXT` | asserted — this is the case's core claim and the strongest evidence gathered (a marker string that could only appear if the full text were embedded, not a reference) |
| Step 7: Verify Skill version indicated | Skill version present (e.g. `base`) | Test Step 7 | `skills[0].version: base` present | asserted |
| Test Data: literal example names ("Export Test Agent", "Formatter") | literal names as written | N/A — case-text drift, not a defect | Live Name fields are validated (Skill: kebab-case-only); used `elitea-1794-export-agent` / `elitea-1794-export-skill` instead | clarification (reverse-masking, same pattern as ELITEA-1789/1792/1739/1737/1735) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Export network call (`GET .../export_import/prompt_lib/{project}/{agent-id}?format=md&follow_version_ids={agent-id}` → `200 OK`) | Gives the implementer a concrete wait-condition (`page.waitForResponse` on this URL pattern) instead of relying solely on the download event, which is more fragile across browsers/CI |
| Full captured YAML frontmatter shape (`name`, `description`, `model`, `temperature`, `max_tokens`, `agent_type`, `step_limit`, `skills[]`) | Documents the complete schema so the implementer can assert on structured fields (e.g. parse YAML) rather than fragile substring matching alone |
| Doubled `//` in the export endpoint URL | Flagged as an observation for awareness — functionally harmless (server returns `200 OK` regardless) but worth noting in case a future strict URL-validation middleware is introduced |
| Double file extension (`.agent.md`) | The case's pass/fail criterion is "exported file is `.md` format" — confirmed satisfied, but the exact naming convention (`{name}.agent.md` vs a bare `{name}.md`) is useful for an implementer asserting on the download's suggested filename |
| Console messages checked immediately after the export click | Zero errors during the functional flow (attach, export, download) |
| Marker-substring technique (`ELITEA_1794_MARKER_TEXT`) for asserting "verbatim, not a reference" | This is the load-bearing technique that actually proves the case's central claim — a bare "Skill name is present" check would pass even if the export only embedded an ID; the marker proves the full instructions text is embedded |

## Known Defects
None. No product defects found. The doubled `//` in the export URL and the
`.agent.md` double-extension are documented as observations in the Handles
Reference / Axis 2 tables, not filed as defects — neither violates the case's own
pass/fail criteria (file is a valid `.md`, downloads successfully, contains full
Skill content).

## Cleanup

Two entities created per run: one Skill and the Agent that attaches it. Both were
deleted live in this run.

1. **Delete the Agent first, then the Skill** — recommended teardown order
   (delete the thing with attached-state dependencies first), consistent with
   ELITEA-1735/1789/1792's prior finding that the API doesn't strictly enforce
   this ordering.
2. **Agent deletion**: UI overflow menu (`agent-actions-menu-button`) → "AGENT"
   group → "Delete agent" (`delete-agent-menuitem`) → type-to-confirm dialog
   (`delete-confirm-name-input` → inner `#name` field) → click "Delete". Verified
   live: after confirming, the page redirected to `/skills/all/290` (the skill
   detail page — likely a leftover navigation-history artifact of this run, not
   asserted further).
   **For automated cleanup, prefer the existing `agent_api` fixture**
   (`automation/fixtures/api_fixtures.py`, `AgentAPI.delete_agent(agent_id)` in
   `automation/api/client.py:452`), same as ELITEA-1735/1789/1792.
3. **Skill deletion**: UI overflow menu (`skill-controls-menu-button`) → "SKILL"
   group → "Delete skill" (`skill-delete-menu-item`) → same type-to-confirm
   dialog → click "Delete". Verified: `DELETE
   /api/v2/elitea_core/skill/prompt_lib/{project}/{skill_id}` → `204 No Content`.
   The immediate follow-up `GET .../skill/prompt_lib/{project}/{skill_id}` →
   `404` seen in the console afterward is an expected stale-refetch artifact of
   the redirect, not a defect (same pattern as ELITEA-1737/1735/1789/1792).
   **For automated cleanup, use the existing `skill_api` fixture**
   (`SkillAPI.delete_skill(skill_id)` in `automation/api/client.py:1227`).
4. **Downloaded export file**: the `.playwright-mcp/` download artifact
   (`elitea-1794-export-agent-agent.md` in this run) is local test-runner output,
   not a product-side entity — no server-side cleanup needed, but an automated
   test should delete/ignore the download directory in its own teardown to avoid
   polluting the CI artifact directory across runs.
5. **Recommended teardown fixture shape**: function-scoped fixture creating one
   skill + one agent via UI/API in the test body (attaching the skill to the
   agent), yielding both IDs, and in its `finally`/post-yield block calling
   `agent_api.delete_agent(agent_id)` then `skill_api.delete_skill(skill_id)`,
   each in its own `try/except` (mirrors the pattern used in
   ELITEA-1735/1737/1738/1739/1789/1792).

## Blocked Steps
None — case executed end-to-end, all 7 case steps confirmed live, no blockers.
