# Test Case: Fork agent version to a different project

## Metadata
- **TMS ID**: ELITEA-1893
- **Linked Story**: none
- **Priority**: l2 (source case frontmatter: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend), model: Anthropic Claude 4.5
  Sonnet (analyst session)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN` — see § Test Data / Known Defects for an
  important caveat this run surfaced about that token's identity)
- **Analyst**: qa-engineer, analyst slot
- **Status**: `defect-found` (one MINOR product defect filed, does not
  block the flow — see below) — case executed end-to-end twice (first
  attempt hit a target-project permission gap during cleanup only, not
  during the fork itself; re-run against a project with full CRUD
  permissions completed clean, including cleanup). `ready-for-automation`
  once the implementer accounts for the target-project permission
  constraint documented in § Test Data.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login via a
  fixed `VITE_DEV_TOKEN` — see caveat below).
- At least two projects are accessible to the user. Confirmed live: five
  projects were available in the project selector this run — `Private`
  (id `399`, home/default project), `Bugs & Features` (id `406`),
  `Elitea Development` (id `25`), `Elitea Testing Team` (id `471`),
  `UI Testing` (id `400`).
- An existing agent with a version to fork is available in the current
  project. Used: agent `Test Agent` (id `3`, version `base`/id `3`) in
  project `Private` (399) — a pre-existing single-version agent with
  Description = Instructions = `"This is a test agent for UI testing."`,
  Step Limit `25`, no attached toolkits/skills/nested agents.

## Test Data

### reuse-existing
- Source agent: `Test Agent` (id `3`) in project `Private` (399) — used
  as-is, no mutation (Fork does not modify the source).
- Target projects (both pre-existing, not created this run): `Elitea
  Testing Team` (id `471`) and `UI Testing` (id `400`).

### Important environment caveat — localhost dev-token permission scoping
On localhost, **every** API request is authenticated with a single fixed
identity (`VITE_DEV_TOKEN`, injected by the Vite proxy — see
`EliteaUI/vite.config.js`), **regardless of which project is selected in
the UI**. This identity does **not** have uniform permissions across all
projects: it has full CRUD (including `models.applications.application.delete`)
in `Private` (399) and `UI Testing` (400), but **lacks delete permission**
in `Elitea Testing Team` (471) — confirmed via a live `403 Forbidden` on
`DELETE /api/v2/elitea_core/application/prompt_lib/471/{id}`, response
body: `{"error": "access_denied", "required":
["models.applications.application.delete"], ...}` — while the *fork* call
into the same project (`POST /api/v2/elitea_core/fork/prompt_lib/471`)
succeeded (`201 Created`), since `models.applications.fork.post` **is**
in that identity's permission set for project 471.
- **Practical effect on this case**: forking *into* 471 works and is a
  valid exercise of case steps 1–8. Cleaning up (case step 9) via UI
  fails there with an "Insufficient permissions to perform this action on
  Elitea Testing Team project." toast.
- **Recommendation for the implementer**: target `UI Testing` (id `400`)
  as the fork-destination project for this test (confirmed full CRUD,
  including delete, for the dev-token identity) — not `Elitea Testing
  Team` (471). If a deployed-env / real-login run needs a different
  project, verify `GET /api/v2/auth/permissions/prompt_lib/{id}` includes
  `models.applications.application.delete` before selecting it as target.
- **Known leftover from this analysis run**: one forked agent, `Test
  Agent` (id `146`, version id `151`), remains undeleted in project
  `Elitea Testing Team` (471) — cleanup blocked by the permission gap
  above, not a product defect. Flagged for a human/admin-token cleanup
  pass; does not affect the correctness of this AFS or the automated
  test (which should target project 400 as above, cleanly avoiding
  the leftover-orphan condition).

### generate-per-test (created by the fork action itself)
- Forked agent — created fresh by the Fork action in each run; deleted
  in the successful (400) run. No other new entities are created (this
  source agent has no nested Skills/toolkits/sub-agents, so the wizard
  shows only a Main entity card, no Nested entities section — confirmed
  live).

## Test Steps

1. Navigate to the agent detail page for `Test Agent` (id `3`, project
   `Private`/399) with version `base` (id `3`) active (single-version
   agent — no explicit selection action needed; the version dropdown
   defaults to and shows `base`).
   - **Verify**: page loads, `agent-version-selector-trigger` /
     VERSION-label combobox shows `base`.
2. Click the three-dot overflow menu (`agent-actions-menu-button`).
   - **Verify**: menu opens (`agent-actions-menu`), showing a VERSION
     group with `Set as a default` (disabled), `Export`, `Share`,
     **`Fork`**, `Publish`, `Delete` (disabled), then an AGENT group with
     `Share`, `Pin to top`, `Delete agent`.
3. Click the `Fork` menuitem (role `menuitem`, name `Fork` — **no
   dedicated testid**, see § Handles Reference for why).
   - **Verify**: the Fork wizard dialog opens
     (`data-testid="agent-import-preview-dialog"`), titled "Fork
     parameters".
4. In the wizard, click the Project selector (`combobox`, placeholder
   "Select project" before selection) and choose a target project
   DIFFERENT from the current one (`Private`/399). Used in this run:
   `UI Testing` (id `400`) — selected via its dropdown option
   (`data-testid="select-option-400"`).
   - **Verify**: the project combobox now displays the target project's
     name (`UI Testing`); the hidden field textbox shows the numeric
     project id (`400`); the `Fork` action button (previously `disabled`)
     becomes enabled.
5. Verify entity cards show the main agent (and any nested dependencies).
   - **Verify**: a "Main entity" card renders showing `Test Agent` /
     "Type: agent", with expandable Description, Instructions, Welcome
     message, Chat starters, and "Other" (Step Limit `25`) sections — all
     populated from the live source agent. Because this source agent has
     no attached toolkits/skills/sub-agents, **no "Nested entities"
     section renders** — confirmed this is the correct, data-driven
     behavior (`IWModalDetails.jsx` only renders the Nested/Skills blocks
     when `nestedEntities.length > 0` / `skillEntities.length > 0`), not
     a missing-data defect.
6. Click `Fork` (role `button`, name `Fork` — **no dedicated testid**,
   see § Handles Reference).
   - **Verify**: network call `POST
     /api/v2/elitea_core/fork/prompt_lib/{target-project-id}` →
     `201 Created`. Dialog re-renders in-place as "Fork Complete"
     (same `data-testid="agent-import-complete-dialog"` container,
     title changes), showing `Forked: 1 agents: Test Agent` (the count
     line's value list carries `data-testid="agent-import-complete-list-agents"`
     per the shared entity-key pattern
     `agent-import-complete-list-{entityKey}`).
7. Click `Got it` (`data-testid="agent-import-complete-got-it-button"`).
   - **Verify**: navigates to `/agents/all/{new-agent-id}?viewMode=owner&name=Test%20Agent`.
     Confirmed live: new agent id `126` in project `UI Testing` (first
     attempt: id `146` in project `Elitea Testing Team`). Page title bar
     confirms the **target project** is now active (`Agent: Test Agent -
     UI Testing`) and the project selector combobox shows the target
     project name/id — i.e. navigation lands the user inside the target
     project, not merely at a URL referencing the new agent id.
8. Verify the forked agent has matching instructions and configuration to
   the source version.
   - **Verify** (all confirmed byte-identical to source, live): Name =
     `Test Agent`; Description = `This is a test agent for UI testing.`;
     Instructions = `This is a test agent for UI testing.`; Step Limit =
     `25`; Tools/Skills empty (`0/5 skills added.`, matching source).
   - **Verify** (bonus traceability, beyond the case text): the forked
     agent's "Information" section shows a `Forked from:` row with a
     clickable "Go to original agent" link back to the source agent
     (no dedicated testid — see § Handles Reference).
   - **Verify** (console/network side-channel check): 0 console errors
     on the forked-agent page load in the clean (`UI Testing`/400) run.
     (The first attempt, into `Elitea Testing Team`/471, surfaced two
     `403 Forbidden` console errors — `GET
     /api/v2/elitea_core/upload_icon/prompt_lib/471` and `GET
     /api/v2/secrets/secrets/default/471` — both explained by the
     permission-scoping caveat above, not a fork defect; they do not
     recur against project 400.)
   - **Separately** (not part of case step 8, but observed on both fork
     completions): a `console.error` React `validateDOMNesting` warning
     (`<p>` inside `<p>`) fires on the "Fork Complete" dialog itself,
     reproduced 2/2. Filed as a defect — see § Known Defects.
9. **Cleanup**: delete the forked agent from the target project.
   - Open the forked agent's overflow menu
     (`agent-actions-menu-button` → `delete-agent-menuitem`).
   - A "Delete confirmation" dialog requires typing the exact agent name
     into a field (`data-testid="delete-confirm-name-input"`, inner
     `#name` input) before the `Delete` button (disabled until the typed
     name matches) becomes clickable.
   - **Verify**: clicking `Delete` fires `DELETE
     /api/v2/elitea_core/application/prompt_lib/{project-id}/{agent-id}`.
     Confirmed live (project 400, agent 126): `204 No Content`, then a
     redirect to `/agents/all` (list view) confirming the agent no longer
     exists. **Caveat**: the same delete action against project 471
     (agent 146) returned `403 Forbidden` — see § Test Data; this is an
     environment/permission gap, not a case-step defect, and is
     documented as a known leftover.

## Handles Reference

| Element | testid | Provenance | Notes |
|---|---|---|---|
| Agent actions (overflow) menu trigger | `agent-actions-menu-button` | on-main ✓ | pre-existing (ELITEA-1794 lineage) |
| Agent actions menu container | `agent-actions-menu` | on-main ✓ | |
| **Fork menuitem (case's core trigger)** | **none — `testid needed: agent-actions-fork-menuitem`** | needs-adding | Confirmed live via DOM: `getAttribute('data-testid')` → `null`. Root cause (static, `EliteaUI/src/components/Fork/ForkEntityButton.jsx` `useForkEntityMenu()`): the returned `menuItem` object has no `key` field, and the rendering `DotMenu.jsx` only emits `data-testid={testId ? \`${testId}-menuitem\` : undefined}` where `testId = item.key` — so Fork silently gets no testid, unlike sibling `Export` (`agent-actions-export-menuitem`, whose `useExportApplicationMenu()` DOES set `key: 'agent-actions-export'`). Implementer should add via `add-data-testid`: set `key: 'agent-actions-fork'` in `useForkEntityMenu()`'s `menuItem` object (`ForkEntityButton.jsx` line ~49) — this is the minimal fix, reusing the existing `${key}-menuitem` convention, no new component needed. |
| Fork wizard dialog | `agent-import-preview-dialog` (pre-fork) / `agent-import-complete-dialog` (post-fork) | on-main ✓ (`ImportWizardModal/index.jsx`) | same container swaps testid based on `importSucceedData \|\| forkedData` state — do not assert on this element persisting a single testid across the fork action |
| Fork wizard Project selector | **none — `testid needed: agent-fork-project-select`** | needs-adding | `ProjectSelect` component (`@/components/ProjectSelect`) renders no `data-testid` on its trigger; confirmed via full-page `data-testid` enumeration on the forked-agent page (list did not include any select/project-select handle for this control). Locate via `getByRole('combobox', { name: /Project:/ })` is the closest fallback but **is a role/label locator, forbidden as primary per this project's testid-only policy** — this MUST be filed as `testid needed` for the implementer, not spec'd directly. |
| Fork wizard project dropdown option | `select-option-{projectId}` | on-main ✓ | confirmed live: `select-option-471`, `select-option-400`, `select-option-399` all fired for their respective options — **numeric, stable, semantic** (keyed to the project's actual id, not its list position) |
| Fork wizard Main-entity card title | `agent-import-preview-name` | on-main ✓ (`IWModalDetails.jsx` passes `titleTestId="agent-import-preview-name"` to the main entity's `IWModalEntityCard`) | not independently re-verified live this run (static-code-confirmed prop wiring); low risk, same component family as verified `agent-import-preview-card-toggle` |
| Fork wizard Main-entity card toggle | `agent-import-preview-card-toggle` | on-main ✓ | |
| **Fork button (case's core action, this dialog)** | **none — `testid needed: agent-fork-confirm-button`** | needs-adding | Confirmed live via DOM: `getByRole('button', {name:'Fork'}).evaluate(el => el.getAttribute('data-testid'))` → `null`. `IWModalForkButton.jsx` renders a bare `Button.BaseBtn` with no `data-testid` prop at all (contrast `IWModalImportButton.jsx`'s sibling `agent-import-confirm-button`, which DOES have one). Implementer should add via `add-data-testid`: `data-testid="agent-fork-confirm-button"` on the `Button.BaseBtn` in `IWModalForkButton.jsx` (~line 274), mirroring the Import button's existing pattern. |
| Fork wizard Cancel button | none observed | needs-adding (low priority — not exercised by this case; only noted for completeness) | shared `Cancel` button in `IWModalActions.jsx`, no testid on either the import or fork branch |
| **"Got it" button (post-fork, case's core action)** | `agent-import-complete-got-it-button` | on-main ✓ | confirmed live, drives navigation to the forked agent |
| Fork-complete "Forked: N agents: ..." value | `agent-import-complete-list-{entityKey}` | on-main ✓ | e.g. `agent-import-complete-list-agents`; `{entityKey}` iterates `pipelines \| agents \| toolkits \| skills \| skipped_toolkits` — useful generic assertion target if a future case forks a pipeline or skill instead |
| Forked-agent "Forked from" traceability link | none observed | needs-adding (bonus handle, beyond case scope — flagged for completeness, not required for this case's pass/fail) | text "Go to original agent", clickable, navigates back to source agent; confirmed present via live DOM enumeration (`Forked from:` label + clickable sibling `generic`), no `data-testid` in the full-page testid list captured this run |
| Delete-agent menuitem (cleanup) | `delete-agent-menuitem` | on-main ✓ | pre-existing, reused unmodified from prior specs (ELITEA-1794/1894 lineage) |
| Delete-confirmation Name input (cleanup) | `delete-confirm-name-input` | on-main ✓ | wraps an inner `#name` `<input>` — fill via `.locator('#name').fill(...)`, not the outer testid element directly (same pattern needed for other MUI-wrapped inputs in this suite) |
| Delete-confirmation Delete button (cleanup) | none observed (role `button`, name `Delete`) | needs-adding (low priority) | disabled until the typed name matches exactly; not independently testid'd from the dialog's `Cancel` sibling |
| Fork network call | `POST /api/v2/elitea_core/fork/prompt_lib/{target-project-id}` → `201 Created` | n/a (network) | body carries `{ applications: [...] }` (agents) or `{ toolkits: [...] }` / `{ skills: [...] }` depending on `mainEntityName` — concrete `page.waitForResponse` wait-condition for the implementer |
| Cleanup (delete) network call | `DELETE /api/v2/elitea_core/application/prompt_lib/{project-id}/{agent-id}` → `204 No Content` (success) / `403 Forbidden` (permission-denied project) | n/a (network) | implementer's test MUST target a project confirmed to carry `models.applications.application.delete` for the auth identity in use — see § Test Data caveat |

## Expected Results
- Forking `Test Agent` (id 3, `Private`/399) via the three-dot menu →
  Fork wizard, into a different, permitted target project, succeeds:
  the wizard shows the correct entity card(s) (main entity only, since
  this source agent has no nested dependencies), the `Fork` action
  returns `201 Created`, and clicking `Got it` navigates the user into
  the target project, onto the newly forked agent.
- The forked agent's Name, Description, Instructions, and Step Limit
  match the source version exactly; Tools/Skills counts also match
  (both empty here).
- Deleting the forked agent (cleanup) succeeds with `204 No Content`
  when the acting identity has delete permission in the target project;
  fails with a clear `403 Forbidden` + user-facing toast otherwise (an
  environment/test-data concern, not a case-step failure).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | N/A (localhost `auth_state`) | `auth_state` fixture skips login via `VITE_DEV_TOKEN`; confirmed session active throughout (all pages loaded authenticated) | asserted |
| Precondition: ≥2 projects accessible | Multiple projects available | Test Step (pre-flight project-selector inspection) | 5 projects confirmed live in the project selector dropdown | asserted |
| Precondition: an agent with a version to fork exists | Source agent available | Test Step 1 | `Test Agent` (id 3, `Private`/399) confirmed pre-existing, single version `base` | asserted |
| Step 1: Navigate to agent detail, select version to fork | Desired version active | Test Step 1 | Version dropdown default `base` confirmed (single-version agent — selection-interaction itself not separately exercised, same partial-coverage note as ELITEA-1894's Blocked Steps for version dropdowns) | asserted (partial — default-selection only, not an explicit multi-version pick) |
| Step 2: Click three-dot menu → Fork | Fork wizard opens | Test Steps 2–3 | `agent-actions-menu-button` → `Fork` menuitem clicked; dialog testid `agent-import-preview-dialog` confirmed present | asserted |
| Step 3: Verify Fork wizard opens | Dialog displayed | Test Step 3 | Same as above | asserted |
| Step 4: Select a target project DIFFERENT from current | Target project selected | Test Step 4 | `select-option-400` clicked; combobox updates to show target name/id; `Fork` button becomes enabled | asserted |
| Step 5: Verify entity cards show main agent + nested dependencies | Cards visible | Test Step 5 | Main entity card confirmed (name, type, description, instructions, welcome message, chat starters, step limit); no nested-entities section, correctly, since source has none | asserted |
| Step 6: Click Fork | Fork operation initiated | Test Step 6 | `POST .../fork/prompt_lib/{id}` → `201 Created`; dialog swaps to "Fork Complete" | asserted |
| Step 7: Click "Got it" — verify navigation to forked agent in target project | Navigated correctly | Test Step 7 | URL + project-selector + page title all confirm landing on new agent id inside target project | asserted |
| Step 8: Verify forked agent has matching instructions/config to source | Config matches | Test Step 8 | Name/Description/Instructions/Step Limit all confirmed byte-identical live | asserted |
| Step 9: Clean up — delete the forked agent from target project | Deletion succeeds | Test Step 9 | Confirmed `204 No Content` + list-redirect against project `UI Testing`/400; documented `403` gap against project `Elitea Testing Team`/471 as an environment/permission issue, not a step failure | asserted (with a documented environment caveat — see § Test Data) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| No "Nested entities" section for a dependency-free source agent | Directly confirms the wizard's entity-card rendering is data-driven (matches ELITEA-1894's finding that the analogous Export flow correctly reflects "no nested deps" in its own output shape) — rules out a false-positive "missing UI" read of case step 5 |
| "Forked from" traceability link on the destination agent | Bonus product behavior worth flagging to the implementer as a possible future assertion, though not required by this case's text |
| `select-option-{projectId}` testid pattern on the project dropdown | Stable, semantic (keyed by numeric project id, not list position) — safe primary handle for the implementer, discovered live rather than guessed |
| `agent-import-complete-list-{entityKey}` generic pattern | Documents the shared success-dialog's structure so a *different* case (forking a Skill or Pipeline instead of an Agent) can reuse the same assertion shape |
| Two `403 Forbidden` console errors when landing on the forked agent inside project 471 | Investigated and attributed to the dev-token permission-scoping caveat (§ Test Data), not a fork-specific defect — recorded so nobody re-discovers and misfiles this as a new bug later |
| React `validateDOMNesting` `<p>`-in-`<p>` warning on Fork Complete dialog | Reproduced 2/2, real invalid-HTML defect in shared component `IWModalSucceedContent.jsx` — filed (see below) |
| Fork/Delete network call status codes and bodies | Gives the implementer concrete `page.waitForResponse` wait-conditions and a documented `403` response shape for permission-gap handling |

## Known Defects

1. **MINOR — `<p>` nested inside `<p>` (invalid HTML) on the Fork/Import
   Complete dialog.** Filed:
   [EliteaAI/elitea-testing-public#570](https://github.com/EliteaAI/elitea-testing-public/issues/570).
   Root cause (static): `IWModaSucceedlContent`
   (`src/[fsd]/entities/import-wizard/ui/ImportWizardModal/IWModalSucceedContent.jsx`)
   renders its "Forked:"/"Imported:" label `Typography` with no explicit
   `component` prop (defaults to `<p>`), while nested per-category
   `Typography` elements further down explicitly set `component="p"` —
   producing a React `validateDOMNesting` console error. Does not block
   the functional flow (fork completes, forked agent correct); reproduced
   2/2 live attempts.

No other product defects found. Case-text is accurate and matches live
behavior — no CLARIFICATION-class case-text drift observed.

## Blocked Steps

None blocking the case itself. One **environment/test-data gap**
affecting only the *cleanup* half of step 9 in one of the two target
projects tried, fully documented in § Test Data:

- Forking into `Elitea Testing Team` (project id 471) succeeds
  end-to-end for steps 1–8, but the localhost dev-token identity lacks
  `models.applications.application.delete` in that specific project, so
  UI-driven cleanup (case step 9) fails there with a `403 Forbidden` +
  "Insufficient permissions..." toast. The re-run against `UI Testing`
  (id 400) — confirmed to carry full CRUD for this identity — completed
  cleanly end-to-end including cleanup, and is the recommended target
  project for the automated implementation.
- **Known leftover test debt**: forked agent id `146` (`Test Agent`,
  version id `151`) remains in project `Elitea Testing Team` (471),
  undeleted, from the first (471) attempt. Requires a human with
  elevated/admin permissions (or a different, project-471-scoped
  credential) to clean up manually; does not affect this AFS's validity
  or the recommended automated-test target project.
