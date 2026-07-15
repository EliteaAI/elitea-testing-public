# Test Case: Export Agent with no nested dependencies — .md file has correct
frontmatter, no leaked credentials

## Metadata
- **TMS ID**: ELITEA-1894
- **Linked Story**: none
- **Priority**: l3 (medium — case authored as "high" priority in the source TMS
  file, but sibling export/skill cases in this batch are filed at l3; kept
  consistent with the batch's existing naming convention, see
  `test-specs/skills/l3_export-agent-with-attached-skills_ELITEA-1794.md` and
  other `l3_*` siblings)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399), model: Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login
  via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: ready-for-automation — case executed end-to-end, all 6 case steps
  pass, no defects. Distinct from ELITEA-1794 (see § Relationship to
  ELITEA-1794 below) — genuinely a fresh scenario, not already covered and not
  a partial-overlap extension.

## Relationship to ELITEA-1794 (dedup check)

`test-specs/skills/l3_export-agent-with-attached-skills_ELITEA-1794.md` /
`automation/tests/ui/skills/test_export_agent_with_attached_skills.py` covers
export of an Agent **with** an attached Skill, and asserts the Skill's content
(name/version/instructions) is embedded verbatim in the `skills:` YAML list.

ELITEA-1894 is the deliberate **inverse/baseline** scenario: an Agent with **no**
nested dependencies (no attached Skills, no nested Agents), and its distinct
focus is:
1. The frontmatter for a *simple* agent still contains the required fields
   (`name`, `description`, `model` settings, `instructions` body) with **no**
   `skills:` list present at all (since none are attached).
2. **Credential/API-key scrubbing** — this is the load-bearing new assertion
   ELITEA-1794 does not exercise at all (its agent had no toolkit attached, so
   there was no credential-leakage surface to test). ELITEA-1894 requires an
   agent with an external toolkit (GitHub, in this run) backed by a real
   credential, and asserts the exported file contains the toolkit's
   *reference* (`elitea_title`) but never the underlying secret value
   (access token).

Verdict: **not already-covered, not extend-existing** — this is a fresh,
independently valuable scenario (`ready-for-automation`), sharing only the
export-menu mechanics with ELITEA-1794. The implementer should treat this as
a new test file/class, reusing the existing `export_agent_via_menu()` page-object
method (`automation/pages/agent_detail_page.py:1728`) and the
`github_credential` / `github_toolkit` API fixtures
(`automation/fixtures/data_fixtures.py:204`, `:241`) rather than duplicating
skill-attach setup.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Agents section is available in the project.
- An Agent exists with no nested Agent/Skill dependencies but **with an
  external toolkit attached whose credential carries a real secret value** —
  created fresh in this run (see Test Data). This shape does not pre-exist
  disposably in the project, so seed-and-cleanup was used (needing a known,
  greppable secret value to prove non-leakage requires a freshly created
  credential, not an unknown pre-existing one).
- `GIT_HUB_TOKEN` is set in `.env.test` (required — the `github_credential`
  fixture skips the test otherwise). Confirmed set in this run.
- The Agent export feature is available (confirmed live: `Export` menuitem
  under the agent-actions overflow menu's `VERSION` group — same element
  ELITEA-1794 uses).

## Test Data

### generate-per-test (via API fixtures, cleaned up in their own teardown)
- GitHub credential: created via `credential_api.create_github_credential()`
  (`CredentialAPI`, `automation/api/client.py:1037`), using `GIT_HUB_TOKEN` from
  `.env.test`. In this run: id `1524`, `elitea_title
  github_el1894cred972676c2_1784113834709`.
- GitHub toolkit: created via `toolkit_api.create_github_toolkit()`
  (`ToolkitAPI`, `automation/api/client.py:1437`), linked to the credential
  above via `credential_elitea_title`. In this run: id `1289`, name
  `el1894tk972676c2`, repository `EliteaAI/elitea-testing`, branch `main`.
  **Recommended for automation**: reuse the existing `github_credential` /
  `github_toolkit` pytest fixtures (`automation/fixtures/data_fixtures.py:204`,
  `:241`) instead of calling the API client directly — they already handle
  skip-if-`GIT_HUB_TOKEN`-unset and teardown.
- Agent name: e.g. `el1894-nodep` (kept ≤32 chars — same silent-truncation
  cap as ELITEA-1794's agent/skill names — `MAX_NAME_LENGTH`); description
  and an instructions string containing a unique marker substring so the
  exported body can be asserted verbatim (not merely non-empty). Used in this
  run: `"You are a test agent for verifying export of an agent with no nested
  skill/agent dependencies. ELITEA_1894_INSTR_MARKER must appear verbatim in
  the exported file body."` — the literal `ELITEA_1894_INSTR_MARKER` string
  is the load-bearing assertion anchor for the instructions body.
- No Skill is created or attached — this case's precondition is explicitly
  the *absence* of nested dependencies.

No `reuse-existing` or shared fixture applies for the Agent itself — this is a
fresh-state flow (1 credential + 1 toolkit + 1 agent, all created and torn
down within the run).

## Test Steps

1. Navigate to `${BASE_URL}/agents/create`. Fill Name (`agent-name-input`),
   Description (`agent-description-input`), and Instructions
   (`agent-instructions-input`, single-line MUI `Textarea`, `.fill()` works
   directly). Click Save (`agent-save-button`).
   - **Verify**: navigates to `/agents/all/{agent-id}?destTab=configuration...`
     with no nav-blocker dialog (consistent with ELITEA-1789/1792/1794).
     Agent id `4844` in this run.
2. On the agent detail page, expand the Tools section (click "Show less" ↔
   "Show all" toggle if needed — MODULES are shown by default, the
   Toolkit/MCP/Agent/Pipeline sub-tool buttons are always visible above it).
   Click the "Toolkit" button (`agent-add-toolkit-button`), which opens a
   search popper (`getByTestId('toolkit-search-input')` for the search box).
   Select the pre-created toolkit by name from the popper's menuitem list
   (`getByRole('menuitem', { name: toolkitName })`, no dedicated per-item
   testid observed — matches the existing `Popper.select_menuitem()` helper
   used by `add_toolkit()`, `automation/pages/agent_detail_page.py:470`).
   - **Verify** (case precondition — "Agent with no nested dependencies but
     with an external toolkit attached"): a toolkit card renders showing the
     toolkit's name and description; no explicit Save needed (auto-saved, the
     agent-level `Save` button stays disabled — same auto-save pattern as
     Skill-attach in ELITEA-1794/1789/1792).
3. (Case step 1) Confirm the agent detail page loads with the toolkit
   attached and no Skills (`0/5 skills added.` counter, unchanged from
   creation) and no nested sub-Agent. Already satisfied by Steps 1–2.
4. (Case step 2) The version dropdown (`combobox` labeled `base` next to
   "VERSION:") already shows `base` as the only/selected version for a
   freshly created agent — no additional selection action was needed in this
   run (single-version agent). For an agent with multiple versions, select
   the desired one from this dropdown before proceeding to Step 5.
5. (Case step 3) Open the agent-actions overflow menu
   (`agent-actions-menu-button`) and click the `Export` menuitem
   (`agent-actions-export-menuitem`, same handle ELITEA-1794 uses — in the
   `VERSION` group, alongside `Set as a default` (disabled), `Share`, `Fork`,
   `Publish`, `Delete` (disabled)).
   - **Verify** (case step 3 — file download initiated): confirmed live via
     the Playwright MCP download event: `el1894-nodep.agent.md` downloaded
     automatically, no save-location dialog. Network trace shows `GET
     /api/v2//elitea_core/export_import/prompt_lib/{project}/{agent-id}?format=md&follow_version_ids={agent-id}`
     → `200 OK` (same doubled `//` after `/v2` URL-construction quirk
     documented in ELITEA-1794 — cosmetic, not a defect, does not affect the
     response).
6. (Case step 4) Verify the exported file has a `.md` extension.
   - **Verify**: confirmed — filename `el1894-nodep.agent.md` (double
     extension `.agent.md`, same pattern as ELITEA-1794; still resolves as a
     valid `.md` file).
7. (Case step 5) Open and inspect the exported file's raw YAML frontmatter.
   - **Verify** (`name`): `name: el1894-nodep` present.
   - **Verify** (`description`): `description: Agent for ELITEA-1894 export
     no-nested-dependency check.` present.
   - **Verify** (model settings): `model: eu.anthropic.claude-sonnet-4-5-20250929-v1:0`,
     `temperature: 0.6`, `max_tokens: -1`, `agent_type: agent`, `step_limit: 25`
     all present.
   - **Verify** (instructions body): the markdown body below the frontmatter's
     closing `---` contains the full instructions text verbatim, confirmed by
     finding the literal marker substring `ELITEA_1894_INSTR_MARKER`.
   - **Verify** (no `skills:` key): the frontmatter has **no** `skills:` list
     — confirms the "no nested dependencies" precondition is reflected in the
     export shape itself (distinct from ELITEA-1794's frontmatter, which
     always has a populated `skills:` list).
   - Full captured frontmatter (this run):
     ```yaml
     ---
     name: el1894-nodep
     description: Agent for ELITEA-1894 export no-nested-dependency check.
     model: eu.anthropic.claude-sonnet-4-5-20250929-v1:0
     temperature: 0.6
     max_tokens: -1
     agent_type: agent
     step_limit: 25
     toolkits:
     - toolkit: el1894tk972676c2
       type: github
       settings:
         repository: EliteaAI/elitea-testing
         base_branch: main
         active_branch: main
         github_configuration:
           private: false
           elitea_title: github_el1894cred972676c2_1784113834709
     ---

     You are a test agent for verifying export of an agent with no nested
     skill/agent dependencies. ELITEA_1894_INSTR_MARKER must appear verbatim
     in the exported file body.
     ```
8. (Case step 6 — the case's core security assertion) Verify the file does
   NOT contain any toolkit API keys or authentication credentials.
   - **Verify**: grepped the downloaded file's raw bytes for the literal
     GitHub token value (`GIT_HUB_TOKEN` from `.env.test`, 40 chars) — **zero
     matches**. Also grepped for credential-shaped substrings
     (`access_token`, `api_key`, `secret`, `password`, `ghp_`, `github_pat_`)
     — **zero matches**. The `toolkits:` list's `github_configuration` block
     contains only `private: false` and `elitea_title:
     github_el1894cred972676c2_1784113834709` — a **reference** to the
     credential (its `elitea_title`, a non-secret identifier), never the
     underlying access token. This is the load-bearing evidence for the
     case's central security claim: the export mechanism correctly
     dereferences-by-name rather than embedding the raw secret.
   - No console errors observed during navigation, toolkit-attach, or
     export/download (checked via `browser_console_messages` immediately
     after the export click — 0 errors of 8 total messages).

## Handles Reference

| Element | testid | Provenance | Notes |
|---|---|---|---|
| Agent Name field | `agent-name-input` | on-main ✓ | wrapper-div fill caveat, same as ELITEA-1794 |
| Agent Description field | `agent-description-input` | on-main ✓ | |
| Agent Instructions field | `agent-instructions-input` | on-main ✓ | single-line MUI Textarea, `.fill()` works directly |
| Agent Save button | `agent-save-button` (create form) | on-main ✓ | |
| Tools section "Toolkit" sub-button | `agent-add-toolkit-button` | on-main ✓ | opens toolkit search popper; located via `getByTestId`, no accessible-name attribute (button text "Toolkit") |
| Toolkit search input (popper) | `toolkit-search-input` | on-main ✓ | inside `Popper.wait_for()` |
| Toolkit-select popper item | `role="menuitem"`, accessible name = toolkit name (dropdown strips spaces from the name — same caveat documented for `add_toolkit()`) | needs-adding | no dedicated per-item testid observed live; out of this case's scope to add, matches existing `add_toolkit()` page-object pattern |
| Attached toolkit card | `agent-toolkit-card` | on-main ✓ | renders toolkit name + description once attached |
| **Agent actions (overflow) menu (this case's core element)** | `agent-actions-menu-button` | on-main ✓ | opens VERSION/AGENT grouped menu — same handle as ELITEA-1794 |
| **"Export" menuitem (this case's core element)** | `agent-actions-export-menuitem` | on-main (merged via ELITEA-1794's PR #549 per that spec's provenance note — re-verify on-main status at implementation time since that spec recorded it as automation/testids-only when authored) | Located in the `VERSION` group, between `Set as a default` (disabled) and `Share`. Clicking it triggers an immediate browser download — no confirmation dialog, no save-location prompt. |
| Version selector combobox | no dedicated testid observed; `combobox` with accessible text `base` next to "VERSION:" label | needs-adding | not exercised beyond confirming default selection in this run (single-version agent) — case step 2 ("select version from dropdown") needs a multi-version agent fixture to fully exercise the selection action itself; flagged as a gap, see § Blocked Steps |
| Downloaded file naming pattern | `{agent-name}.agent.md` | n/a (not a UI handle) | Double extension (`.agent.md`) — same pattern as ELITEA-1794 |
| Export network call | `GET /api/v2//elitea_core/export_import/prompt_lib/{project}/{agent-id}?format=md&follow_version_ids={agent-id}` → `200 OK` | n/a (network call) | Same doubled `//` quirk as ELITEA-1794; gives implementer a concrete `page.waitForResponse` wait-condition |
| Agent Delete menu item (cleanup) | `delete-agent-menuitem` | on-main ✓ | in the AGENT group — not exercised live this run (API cleanup used instead, see § Cleanup) |

## Expected Results
- An Agent with no attached Skills and no nested sub-Agent, but with one
  external (GitHub) toolkit attached, is created successfully.
- Triggering `Export` from the agent-actions overflow menu (`VERSION` group)
  downloads a file with a `.md`-suffixed name (`{agent-name}.agent.md`).
- The downloaded file's content is a YAML frontmatter block (`name`,
  `description`, `model`, `temperature`, `max_tokens`, `agent_type`,
  `step_limit`, `toolkits[]`) followed by the Agent's own instructions as the
  markdown body — with **no** `skills:` key present (no nested Skill
  dependencies).
- The `toolkits:` list's `github_configuration` contains only a credential
  **reference** (`elitea_title`) — the raw GitHub access token value is never
  present anywhere in the file.
- No console errors or failed network requests occur during the functional
  flow.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: an agent with no nested agent dependencies is available | Simple agent exists, ready for export | Test Steps 1–2 | Fresh Agent created with no Skills/sub-Agents attached, plus a toolkit (for the credential-scrub assertion in step 6) | asserted |
| Step 1: Navigate to an agent with no nested agent dependencies | Agent detail page loads | Test Steps 1, 3 | Agent detail page opens after Save; verified via `verify_on_detail_page()` equivalent (URL pattern + Agent ID field) | asserted |
| Step 2: Select the version to export from the version dropdown | Desired version selected | Test Step 4 | Default `base` version already selected for a freshly created single-version agent; dropdown confirmed present and showing `base` | asserted (partial — see Blocked Steps: multi-version selection itself not exercised) |
| Step 3: Click the three-dot menu → Export | Export action triggered | Test Step 5 | `agent-actions-menu-button` → `agent-actions-export-menuitem` clicked; download event fired; network call → `200 OK` | asserted |
| Step 4: Verify a .md file is downloaded automatically | File download initiated | Test Steps 5–6 | Playwright MCP download event confirmed; filename `el1894-nodep.agent.md` resolves as `.md` | asserted |
| Step 5: Open the file and verify YAML frontmatter (name, description, model settings, instructions body) | All required fields present | Test Step 7 | Raw file read directly; `name`, `description`, `model`, `temperature`, `max_tokens`, `agent_type`, `step_limit` all present in frontmatter; instructions text (with marker) present in body | asserted |
| Step 6: Verify the file does NOT contain toolkit API keys or auth credentials | No secrets present | Test Step 8 | Grepped raw file bytes for the literal token value (0 matches) and credential-shaped substrings (0 matches); confirmed only a non-secret `elitea_title` reference is present | asserted — this is the case's core security claim and the strongest evidence gathered (byte-level grep against the actual live secret value, not a heuristic) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| No `skills:` key present in frontmatter | Directly evidences the "no nested dependencies" precondition in the artifact itself, and is the structural feature that distinguishes this case's export shape from ELITEA-1794's |
| `toolkits:` YAML shape (`toolkit`, `type`, `settings.repository`, `settings.base_branch`, `settings.active_branch`, `settings.github_configuration.private`, `settings.github_configuration.elitea_title`) | Documents the complete toolkit-reference schema so the implementer can assert on structured fields (parse YAML) rather than fragile substring matching alone |
| Export network call (`GET .../export_import/prompt_lib/{project}/{agent-id}?format=md&follow_version_ids={agent-id}` → `200 OK`) | Concrete wait-condition for the implementer, same rationale as ELITEA-1794 |
| Doubled `//` in the export endpoint URL | Same observation already flagged in ELITEA-1794; reconfirmed here — not filed as a new defect, cross-referenced instead |
| Console messages checked immediately after the export click | Zero errors during the functional flow (create, attach toolkit, export, download) |
| Byte-level grep of the raw token value against the downloaded file | The load-bearing technique that actually proves the case's central claim — a bare "no `access_token` key" check would pass even if the token leaked under an unexpected key name; grepping the literal secret value is a stronger, key-name-agnostic proof |

## Known Defects
None. No product defect found. The exported file correctly omits the
`skills:` key when no Skills are attached, and correctly references the
toolkit's credential by its non-secret `elitea_title` rather than embedding
the raw access token. The doubled `//` in the export URL is a pre-existing,
already-documented (ELITEA-1794) cosmetic observation, not re-filed here.

## Cleanup

Three entities created per run: one Credential, one Toolkit, and the Agent
that attaches it. All three were deleted live in this run, via API (faster
and equally valid for this case's purposes — the UI teardown flow itself is
already covered by ELITEA-1794/1789/1792 and not this case's focus).

1. **Delete order**: Agent first (has the attached-toolkit dependency), then
   Toolkit, then Credential — mirrors the "delete the thing with
   attached-state dependencies first" pattern from ELITEA-1794/1789/1792,
   though (per that same prior finding) the API does not strictly enforce
   this ordering.
2. **Agent deletion**: `agent_api.delete_agent(agent_id)`
   (`AgentAPI.delete_agent`, `automation/api/client.py:452`). Verified live:
   agent id `4844` deleted successfully.
3. **Toolkit deletion**: `toolkit_api.delete_toolkit(toolkit_id)`
   (`ToolkitAPI.delete_toolkit`, `automation/api/client.py:1552`). Verified
   live: toolkit id `1289` deleted successfully.
4. **Credential deletion**: `credential_api.delete_credential(credential_id)`
   (`CredentialAPI.delete_credential`, `automation/api/client.py:1096`).
   Verified live: credential id `1524` deleted successfully.
5. **Downloaded export file**: the `.playwright-mcp/` download artifact
   (`el1894-nodep-agent.md` in this run) is local test-runner output, not a
   product-side entity — deleted after content inspection. An automated test
   should delete/ignore the download directory in its own teardown to avoid
   polluting the CI artifact directory across runs.
6. **Recommended teardown fixture shape**: function-scoped fixture chaining
   the existing `github_credential` → `github_toolkit` pytest fixtures
   (`automation/fixtures/data_fixtures.py:204`, `:241` — both already handle
   `GIT_HUB_TOKEN`-unset skip and their own teardown) with a UI-created Agent
   that attaches the toolkit; in the test body's `finally`/post-yield block,
   call `agent_api.delete_agent(agent_id)` in its own `try/except` (the
   toolkit/credential fixtures self-cleanup via their own `yield`/teardown).

## Implementer Amendments (Phase 2)

- **Instructions text shortened (technique, not scope).** The AFS's "used in
  this run" instructions string (~180 chars) times out the shared
  `AgentFormPage.fill_form()` helper's `press_sequentially(delay=80ms/char)`
  call against its 10s default Playwright action timeout (180 * 80ms ≈
  14.4s > 10s). `fill_form()` is a shared-caller page-object method (16
  callers across the suite), so it was left untouched rather than modified
  per-case. The implementation instead uses a shorter instructions string —
  `"Test agent for export verification, no nested deps.
  ELITEA_1894_INSTR_MARKER must appear verbatim."` (98 chars, ≈7.8s) — that
  still carries the load-bearing `ELITEA_1894_INSTR_MARKER` literal
  verbatim. The case's assertion (marker present verbatim in the exported
  body, body matches the Agent's own instructions exactly) is unaffected;
  only the surrounding prose is shorter. Confirmed live: 2/2 consecutive
  green runs (~41s each).

## Blocked Steps

None blocking — case executed end-to-end, all 6 case steps confirmed live,
core security assertion (no credential leakage) proven at the byte level.

One **partial-coverage gap** flagged for the implementer, not a blocker: case
step 2 ("Select the version to export from the version dropdown") was only
confirmed as "default `base` version already selected" in this run, because a
freshly created agent has exactly one version. The dropdown's *selection
interaction itself* (choosing a non-default version before export, and
confirming the exported `.md` reflects the fields of the version actually
selected — via `follow_version_ids={version-id}` in the network call) was not
exercised, since that requires an agent with ≥2 versions (e.g. via "Save As
Version"). Recommend either: (a) accept the single-version default-selection
proof as satisfying this case's step 2 (the dropdown element and its default
state are confirmed present and functional), or (b) extend the fixture to
create a second version via "Save As Version" before export, for full
coverage of the explicit version-selection action. Left as an implementer
judgment call — does not block `ready-for-automation` status since the file's
correctness (frontmatter + no leaked credentials) is independent of which
version was exported.
