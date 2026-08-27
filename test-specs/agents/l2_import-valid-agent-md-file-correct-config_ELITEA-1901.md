# Test Case: Import valid agent .md file — agent appears in list with correct config

## Metadata
- **TMS ID**: ELITEA-1901
- **Linked Story**: none
- **Priority**: l2 (source case frontmatter: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend), project `Private` / `${ELITEA_PROJECT_ID}`=399, model:
  GPT-5.2 (`gpt-5.2` — `automation/config.py: default_model_name`)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation — case executed end-to-end against the live
  system, all 7 steps pass, no product defect. One case-text imprecision found
  and filed as a CLARIFICATION (see below); one pre-existing, already-tracked
  console warning observed and filtered (not asserted against).
- **Repair amendment (2026-08-27, board #1813 — targets `main`, not
  `automation/base`)**: Step 1 carried a **test-invented environment
  assumption** (`assert get_agent_card_names()` — "at least one pre-existing
  agent card") that the TMS case never asks for. It went red on
  **dev.elitea.ai** (GHA run 32931571484, job `dev-stable - agents`, shard
  `user5`) where the shard user genuinely owns zero agents. Not a product
  defect and not a timing race — the product rendered its documented empty
  state correctly. Step 1's observables are replaced with data-independent
  ones; see § Environment Independence. Nothing else in this AFS changes, and
  the case's own coverage is **not** weakened (see that section for why).

## Dedup / Board Search Confirmation

Four candidate-overlap tests were read in full before starting exploration —
none is a full match:

- `test_import_agent_recreates_skills_with_new_ids.py` (ELITEA-1795) — imports
  via the same Agents-list "Import" button, but the file is **exported FROM the
  app** (round-trip of an agent the test itself created and exported seconds
  earlier), and the case's whole point is Skill-ID recreation, not
  Name/Description/Instructions verification against an externally-authored file.
- `test_export_agent_no_nested_dependencies.py` (ELITEA-1894) — export only, no
  import step at all.
- `test_import_agent_zip_nested_agent_dependencies.py` (ELITEA-1902) — import via
  the same button, but the fixture is a `.zip` produced by this app's own Export
  (nested-agent dependency), not a plain hand-authored `.md`.
- `l3_export-agent-with-attached-skills_ELITEA-1794.md` (AFS only, no matching
  automated test file exists for a plain single-agent import) — export-only,
  same round-trip shape as 1894/1902.

**The distinguishing scenario ELITEA-1901 actually tests**: does the import
wizard correctly parse a **minimal, externally-authored** `.md` file — one that
was never produced by this app's own Export feature, and therefore lacks the
extra frontmatter keys (`temperature`, `max_tokens`, `agent_type`, `step_limit`,
`toolkits`, `skills`, `nested_agents`, …) every round-trip test's fixture always
carries? None of the four candidates exercises that — they all import a file the
app itself just generated seconds earlier, guaranteed complete. This case proves
the importer tolerates a bare `name`/`description`/`model` + body-instructions
file from a third party.

**Board Search Confirmation**: `env -u GITHUB_TOKEN gh issue list --state all
--limit 200 --json title | grep -i ELITEA-1901` returned only the tracking card
itself (#181, already `In Progress`) — no other issue references this case or
claims prior delivery. No completed board task exists asserting this
observable; proceeding as fresh work.

## Preconditions
- User is logged in (`${TEST_USER}`; on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN`).
- A project is selected/accessible (`Private`, id `${ELITEA_PROJECT_ID}`=399 in
  this run).
- The Agents dashboard's Import feature is available (confirmed live:
  `agents-import-button` testid in the list-page toolbar opens a native file
  chooser).
- **NO precondition on pre-existing agents.** The case does not require the
  project to already hold agents, and this test must not either — see
  § Environment Independence.

## Environment Independence (repair, 2026-08-27 — board #1813)

**The rule for this case: Step 1 asserts that the dashboard LOADED, never that
it has CONTENT.** The count of pre-existing agents is a property of whichever
project/shard-user the run lands on, not of ELITEA-1901.

### What broke

Step 1 previously asserted `assert agents_list_page.get_agent_card_names()`
("at least one existing agent card"). On `dev.elitea.ai` the per-shard user
(`autotest_user_5`) owns **zero** agents — every agents spec seeds and cleans
up its own agent, so between tests the project is legitimately empty — and the
assertion failed on `assert []`. It passed on localhost only because the
shared local identity happens to have leftovers (20 agents observed in project
`Private`/399 during this repair analysis).

TMS ELITEA-1901 Step 1's expected result is, in full: *"The Agents dashboard
loads."* It never mentions pre-existing agents. The assertion was invented by
the test, so removing it removes **nothing the case asked for**.

### Live confirmation of the empty state (2026-08-27)

- **Source (decisive).** `src/pages/Applications/Applications.jsx:108,113` —
  `agents-page-header` (`titleTestId`) and `agents-import-button` are rendered
  by `StickyTabs`' `title` / `middleTabComponent` props, which are **siblings
  of the tab panel that holds the list**. They are structurally independent of
  the list's contents: no list data can gate them.
- **`src/components/CardList.jsx:40-42`** —
  `showEmptyOrError = !isLoading && (isError || isEmptyList)`;
  `showCustomEmptyState = showEmptyOrError && customEmptyState && !isError`.
  So the Agents empty state (`EmptyStatePage`, title `'No agents yet'`,
  `PrivateAgentsList.jsx:169-177`) renders **only** once loading has finished
  **and** the fetch did not error. That makes it a valid load-completion
  signal, not merely an "empty" signal.
- **Observed live** on `http://localhost:5173/agents/all`, zero cards
  rendering: `agents-page-header` visible (text `"Agents"`),
  `agents-import-button` visible (text `"Import"`), `empty-state-title`
  visible exactly once (text `"No agents yet"`), `entity-card-name` count `0`.
  Clicking `agents-import-button` in that state **opened the native file
  chooser** — the import flow is fully reachable from an empty dashboard.
  Screenshot: `test-results/screenshots/ELITEA-1901-step-01-agents-empty-state.png`.
- **Honesty caveat — read this before trusting the above.** A genuinely
  agent-free project was **not** reachable on localhost with the shared
  identity (project `Private`/399 holds 20 agents; a cross-project probe for a
  zero-agent project failed on CORS and was abandoned rather than worked
  around). The zero-card render above was reached through the product's own
  **zero-match search** path. That is a faithful proxy *for the render* — per
  `CardList.jsx:41` `isEmptyList` does not discriminate a zero-match search
  from a genuinely empty project, so both take the identical
  `showCustomEmptyState` branch — but it is **not** the same precondition. No
  state was injected, deleted, or fabricated to produce it. The genuinely-zero
  precondition is evidenced instead by the DEV failure screenshot from GHA run
  32931571484, which shows exactly this render (heading + Import + "No agents
  yet") on a real zero-agent project.

### Why the replacement is not a weakening

The removed assertion's only real function was incidental: because
`get_agent_card_names()` swallows its `wait_for` timeout and returns `[]`
(`agents_list_page.py:254-257`), a truthiness check on it did fail when the
list failed to render. The replacement preserves that **and strengthens it** —
`empty-state-title` is gated on `!isLoading && !isError`, and `entity-card-name`
only exists on a rendered card, so the disjunction cannot pass while the list
is still loading or has errored. What is lost is only the environment
assumption. Card rendering itself is still verified honestly at Step 6, using
an agent **this test imported**, which is the correct place for it.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A **hand-authored** (NOT exported from the app) `.md` fixture file, e.g.:
  ```
  ---
  name: el-1901-import-<unique_suffix>
  description: Externally-authored agent for ELITEA-1901 import verification. <MARKER_DESC> must appear verbatim.
  model: gpt-5.2
  ---
  You are el-1901-import-<unique_suffix>, a hand-authored test agent for ELITEA-1901.
  This exact instruction sentence <MARKER_INSTR> must appear verbatim in the
  imported Agent.
  ```
  - **Critical fixture-shape finding — filed as CLARIFICATION
    EliteaAI/elitea-testing-public#628**: `instructions` must be the **markdown
    BODY** below the closing `---`, NOT a YAML frontmatter key. Confirmed via two
    live attempts through the real Import button → file chooser → Import
    parameters preview dialog:
    - Attempt 1 (`instructions:` as a frontmatter key, YAML block scalar `|`):
      the preview dialog's Description field rendered correctly; the
      Instructions field rendered **empty**.
    - Attempt 2 (identical file, `instructions` moved to the body, no
      frontmatter key): Instructions rendered verbatim in the preview, and the
      resulting Agent's Name/Description/Instructions all matched exactly.
    - This matches the app's own **export** shape already documented in this
      repo (`test_export_agent_no_nested_dependencies.py` / ELITEA-1894:
      `agent_body = parts[2].strip()` is the Agent's instructions) — the import
      parser is consistent with the export format; only the TMS case's Test
      Data wording is imprecise about where `instructions` belongs.
  - The source case's frontmatter list "(name, description, model,
    instructions)" should be read as: `name`/`description`/`model` are
    frontmatter keys, `instructions` is the file's plain-text body — not four
    frontmatter keys.
- `model: gpt-5.2` resolves to the platform default model
  (`automation/config.py: default_model_name`); confirmed on the imported
  Agent's Model Selector (`model-selector-name` → "GPT-5.2"). Any other
  configured model string would work equally — `gpt-5.2` was chosen because
  it's already the suite's cheap-default convention.
- Agent name: unique per run (`el-1901-import-{uuid4().hex[:8]}` — mirrors the
  ELITEA-1794/1795/1894/1902 convention) to avoid collisions with the ~19
  pre-existing agents already in the shared project.
- Marker convention: plant a unique substring in both `description` and the
  instructions body (mirrors ELITEA-1794/1795/1894/1902's `MARKER` pattern) so
  the post-import verification proves verbatim content, not merely non-empty
  fields.
- Upload mechanics: the fixture file must live at a path reachable by the
  automation process (e.g. a pytest `tmp_path` file) — Playwright's
  `file_chooser.set_files()` needs a real filesystem path, same as every
  sibling import test's `download.save_as()` pattern in reverse.

## Test Steps

1. Navigate to `${BASE_URL}/agents/all` (Agents dashboard).
   - **Verify (a)**: `agents-page-header` is visible **and** its text is
     exactly `Agents` — we are on the Agents dashboard, not a redirect,
     error page, or a still-blank shell.
   - **Verify (b)**: `agents-import-button` is visible — the control Step 2
     acts on. This is the case's real Step 1 → Step 2 handoff.
   - **Verify (c)**: the list region has settled into a terminal, non-error
     state — **at least one of `entity-card-name` OR `empty-state-title` is
     visible**. Implement as a single class-level constant on
     `AgentsListPage` so the pattern stays greppable and testid-only:
     ```python
     # Two valid terminal renders; which one appears is a property of the
     # ENVIRONMENT, not of this case. CardList.jsx gates BOTH behind
     # `!isLoading && !isError`, so the disjunction is a genuine
     # "list finished loading, without error" oracle.
     LIST_SETTLED_SELECTOR = (
         '[data-testid="entity-card-name"], [data-testid="empty-state-title"]'
     )
     ```
     exposed via a small page-object method (e.g.
     `wait_for_list_settled(timeout)`) that does
     `self.page.locator(self.LIST_SETTLED_SELECTOR).first.wait_for(state="visible", timeout=timeout)`.
   - **MUST NOT verify**: that any *pre-existing* agent card exists. That is
     environment state the case never asks for, and asserting it is what
     turned this spec red on DEV (§ Environment Independence).
   - **Prefer retrying `expect(...)` assertions over bare `is_visible()`** for
     (a) and (b) — the current spec uses non-retrying `is_visible()`, which is
     an avoidable race on a deployed env.
2. Click the Import button (`agents-import-button`).
   - **Verify**: a native OS file chooser opens (Playwright
     `page.expect_file_chooser()` / MCP `browser_file_upload` modal state).
3. Select the hand-authored `.md` fixture (Test Data — instructions as BODY,
   not frontmatter key) via the file chooser.
   - **Verify**: `agent-import-preview-dialog` becomes visible.
4. Verify the "Import parameters" dialog shows an entity card for the agent.
   - **Verify**: `agent-import-preview-name` is visible; its `text_content()`
     equals the fixture's `name` value.
5. Click the dialog's Import (confirm) button (`agent-import-confirm-button`).
   - **Verify**: `agent-import-complete-dialog` becomes visible;
     `agent-import-complete-list-agents` text contains the agent's name;
     `POST /api/v2/elitea_core/import_wizard/prompt_lib/${ELITEA_PROJECT_ID}`
     returns `201 Created`.
6. Click "Got it" (`agent-import-complete-got-it-button`).
   - **Verify**: browser navigates to `/agents/all/{new_agent_id}`; re-opening
     the Agents list shows a card whose `entity-card-name` text equals the
     imported agent's name (the case's "correct name in the dashboard" check).
7. On the imported Agent's detail page, verify Name, Description, and
   Instructions all match the source file.
   - **Verify**: `agent-name-input` value == fixture `name`;
     `agent-description-input` value == fixture `description` (incl. marker);
     `agent-instructions-input` value == fixture body text, verbatim (incl.
     marker).

## Expected Results
- The Agents dashboard loads with the Import control available — regardless of
  how many agents the project already holds (zero is valid; § Environment
  Independence).
- Selecting the hand-authored `.md` file opens the "Import parameters" preview
  dialog with an entity card for the agent (name shown verbatim).
- Confirming the import shows an "Import Complete" dialog listing the new
  agent by name, backed by a `201 Created` on
  `POST /api/v2/elitea_core/import_wizard/prompt_lib/{project_id}`.
- The imported agent appears in the Agents dashboard with the correct name.
- Opening the imported agent shows Name, Description, and Instructions all
  matching the source file's content verbatim.
- (Axis 2) The imported agent's Model resolves to the fixture's `model` value.
- No console errors during the flow, other than the pre-existing, already-
  tracked `validateDOMNesting` warning on the Import Complete dialog's Tooltip
  (EliteaAI/elitea-testing-public#570 — filtered from the assertion, not
  asserted against, per the ELITEA-1902 precedent).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: "valid .md file with YAML frontmatter (name, description, model, instructions)" | such a file is available/usable for import | Test Data | Test Data section documents the CORRECT fixture shape (instructions = body, not frontmatter key); CLARIFICATION EliteaAI/elitea-testing-public#628 filed for the case-text imprecision | clarification |
| 1 Navigate to Agents dashboard | dashboard loads | step 1 | step 1: `agents-page-header` visible + text == `Agents`; `agents-import-button` visible; list settled — `entity-card-name` OR `empty-state-title` visible. **No pre-existing-card assertion** (§ Environment Independence) | asserted |
| 2 Click Import button | dialog/file picker opens | step 2 | step 2: native file chooser reachable | asserted |
| 3 Upload valid .md file | file uploaded and processed | step 3 | step 3: `agent-import-preview-dialog` visible after `set_files()` | asserted |
| 4 Verify import wizard shows entity card for the agent | entity card displayed | step 4 | step 4: `agent-import-preview-name` visible, text == fixture name | asserted |
| 5 Click Confirm/Import | import operation completes | step 5 | step 5: `agent-import-complete-dialog` visible, `agent-import-complete-list-agents` contains name, `POST .../import_wizard/...` → 201 | asserted |
| 6 Verify agent appears in dashboard with correct name | imported agent visible with correct name | step 6 | step 6: `entity-card-name` in Agents list == imported name | asserted |
| 7 Open imported agent — verify Name, Description, Instructions match file | all three fields match | step 7 | step 7: `agent-name-input`/`agent-description-input`/`agent-instructions-input` values == fixture values verbatim | asserted |

### Axis 2 — Analyst additions

- Step 7 also asserts the imported agent's **Model** (`model-selector-name`)
  resolves to the fixture's `model: gpt-5.2` value — *added: the case title
  says "correct config", and Model is part of an Agent's config just as much as
  Name/Description/Instructions; the fixture already plants a model value, so
  this check is free and closes a config-field gap the case's literal step
  list doesn't spell out.*
- Steps 3–6 assert zero (unfiltered) console errors across the entire
  upload → preview → confirm → navigate flow — *added: silent console errors
  are the worst bugs (test-case-analysis skill discipline); the one error
  actually observed (`validateDOMNesting` on the Import Complete dialog) is
  pre-existing and already tracked at EliteaAI/elitea-testing-public#570, so
  it's filtered rather than asserted against, mirroring the ELITEA-1902
  precedent.*
- Cleanup deletes the imported agent after the test — *added: not case-
  mandated, but required by this repo's test-data hygiene (no orphan data left
  in the shared project).*

## Cleanup
1. Delete the imported agent: `agent_api.delete_agent(imported_agent_id)` (API,
   mirrors ELITEA-1794/1795/1894/1902's cleanup pattern) — or, if API cleanup
   isn't wired for this fixture, via UI:
   `AgentDetailPage.delete_agent_via_menu()` (three-dot menu →
   "Delete agent" → type-to-confirm dialog → Delete).
2. Remove the temporary `.md` fixture file from disk (`tmp_path` auto-cleans
   under pytest; no manual step needed if using the `tmp_path` fixture).

## Concrete Handles (discovered during exploration)

**Step 1 handles — PROVENANCE verified 2026-08-27 after `cd ../EliteaUI && git fetch origin`.**
This repair targets **`main`** (and must run green on DEV), so on-main presence
is load-bearing here, not informational. **No testid needs adding for this
repair** — all four already exist on `origin/main`:

| Handle | Testid | Provenance | Source |
|---|---|---|---|
| Agents page heading | `agents-page-header` | **on-main ✓** | `src/pages/Applications/Applications.jsx:108` (`titleTestId`) |
| Import button | `agents-import-button` | **on-main ✓** | `src/pages/Applications/Applications.jsx:113` (`testId`) |
| Agent card name (collection) | `entity-card-name` | **on-main ✓** | shared `Card.jsx` |
| Empty-state title ("No agents yet") | `empty-state-title` | **on-main ✓** | `src/[fsd]/entities/empty-state-page/ui/EmptyStatePage.jsx:49` |

Verification command + output:

```
$ cd ../EliteaUI && git fetch origin
$ FILTER='(data-testid|testid[[:space:]]*[:=])'
$ for t in agents-page-header agents-import-button entity-card-name empty-state-title; do ... done
agents-page-header           main:YES  testids:YES
agents-import-button         main:YES  testids:YES
entity-card-name             main:YES  testids:YES
empty-state-title            main:YES  testids:YES
```

`empty-state-title` is a **generic** testid on a shared component
(`src/[fsd]/entities/empty-state-page/`), which is the compliant shape for
shared components per `.agents/testing.md` § Locator policy — it is NOT a
feature-scoped testid hardcoded in a shared component. It is also already
established precedent in this suite: `automation/pages/mcp_list_page.py:192`
and `automation/pages/toolkits_list_page.py:68` both bind it as
`empty_state_title`, consumed by three merged specs. On the Agents page it
renders **exactly once** when the list is empty and is **absent** when cards
render (both states observed live), so the disjunction is unambiguous.

| Element | Recommended Locator | Fallback |
|---|---|---|
| Agents page heading | `getByTestId('agents-page-header')` | none — testid-only policy |
| Agents list — empty-state title | `getByTestId('empty-state-title')` | none |
| Import button (Agents list toolbar) | `getByTestId('agents-import-button')` | none — testid-only policy |
| Import parameters dialog | `getByTestId('agent-import-preview-dialog')` | none |
| Import preview — Main entity name | `getByTestId('agent-import-preview-name')` | none |
| Import preview — Confirm button | `getByTestId('agent-import-confirm-button')` | none |
| Import Complete dialog | `getByTestId('agent-import-complete-dialog')` | none |
| Import Complete — imported Agents list | `getByTestId('agent-import-complete-list-agents')` | none |
| Import Complete — "Got it" button | `getByTestId('agent-import-complete-got-it-button')` | none |
| Agents list — entity card name (shared testid) | `getByTestId('entity-card-name')`, filtered by text | none |
| Agent detail — Name field | `getByTestId('agent-name-input')` | none |
| Agent detail — Description field | `getByTestId('agent-description-input')` | none |
| Agent detail — Instructions field | `getByTestId('agent-instructions-input')` | none |
| Agent detail — Model selector (closed-state name) | `getByTestId('model-selector-name')` | none |
| Delete agent — actions menu button | `getByTestId('agent-actions-menu-button')` | none |
| Delete agent — menu item | `getByTestId('delete-agent-menuitem')` | none |
| Delete confirm — name-to-confirm input | `getByTestId('delete-confirm-name-input')` (inner `#name`) | none |
| Delete confirm — Delete button | `getByTestId('delete-confirm-button')` | none |

**Testid gap noted, NOT filed as a defect or added now (scope is load-bearing —
`.agents/testing.md` § Locator policy):** the "Import parameters" dialog's
Main-entity card renders its **Description** field with no `data-testid` at
all (any entity type — `IWModalEntityCard.jsx`'s `IWModalEntityTextField` for
Description never receives a `testId` prop), and its **Instructions** field
also has no testid *specifically for the Main entity* (`IWModalDetails.jsx`
only passes `instructionsTestId` to the Nested-entity and Skill-entity cards,
not the Main-entity card at line 76–80). This case's literal ask (step 4:
"entity card is displayed") is already satisfied by the existing
`agent-import-preview-name` testid, and the deeper verbatim check happens on
the POST-import detail page (step 7, fully testid-backed) — so this AFS's
automation does not need to touch the Main-entity preview's
Description/Instructions text, and per "testids go ONLY on elements tests
actually touch," no new testid is added here. If a future case wants to assert
the Main entity's Description/Instructions verbatim **inside the preview
dialog itself** (not just post-import), that gap will need `add-data-testid`
at that time.

## Network Behavior
- `POST /api/v2/elitea_core/import_wizard/prompt_lib/${ELITEA_PROJECT_ID}` —
  fires on the preview dialog's Import (confirm) button click, `201 Created`
  on success.
- `GET /api/v2/elitea_core/application/prompt_lib/${ELITEA_PROJECT_ID}/{agent_id}`
  — fires on the imported agent's detail page load; available as an
  alternate, non-UI assertion surface for Name/Description/Instructions if the
  implementer prefers a network-level check over reading form field values
  (mirrors the `skills_response_info` pattern in ELITEA-1795's test).

## Known Defects Found During Exploration
- None new. One pre-existing, already-tracked console warning observed on the
  "Import Complete" dialog: `Warning: validateDOMNesting(...): <p> cannot
  appear as a descendant of <p>` (Tooltip inside `IWModalSucceedContent.jsx`)
  — filed previously as EliteaAI/elitea-testing-public#570 (confirmed via the
  ELITEA-1902 AFS documenting the same root cause). Filter this substring out
  of the zero-console-errors assertion rather than asserting against it,
  mirroring `test_import_agent_zip_nested_agent_dependencies.py`'s
  `_KNOWN_NONBLOCKING_CONSOLE_SUBSTRING` pattern.
- Case-text imprecision (not a product defect — reverse-masking guard): the
  case's Test Data row lists `instructions` alongside frontmatter keys; the
  live product requires it as the markdown body instead. Filed as CLARIFICATION
  EliteaAI/elitea-testing-public#628 (see Test Data section above for the full
  finding and disposition).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`); mirrors the
  existing `test_import_agent_recreates_skills_with_new_ids.py` /
  `test_import_agent_zip_nested_agent_dependencies.py` structure (page objects:
  `AgentsListPage`, `AgentDetailPage`, `AgentFormPage`), but the fixture is
  **authored by the test itself** (a plain string written to `tmp_path`), never
  downloaded from the app's own Export — that's the whole point of this case
  versus its round-trip siblings.
- Use `page.expect_file_chooser()` (or the project's existing
  `AgentsListPage.import_agent(file_path)` method, which already wraps the
  click + file-chooser handling and waits for `agent-import-preview-dialog`)
  rather than re-deriving the upload flow from scratch.
- `AgentsListPage.confirm_agent_import()` / `confirm_import_complete()` already
  exist and return the new agent's numeric ID from the post-navigation URL —
  reuse them (same as ELITEA-1795/1902).
- `AgentDetailPage.get_name()` / `get_description()` / `get_instructions()` are
  inherited from `AgentFormPage` — reuse them for step 7, don't re-implement.
- Wait strategy: wait for `agent-import-preview-dialog` visibility after
  `set_files()`, and for `agent-import-complete-dialog` visibility after
  clicking confirm — never a fixed sleep (mirrors this repo's existing import
  tests).
