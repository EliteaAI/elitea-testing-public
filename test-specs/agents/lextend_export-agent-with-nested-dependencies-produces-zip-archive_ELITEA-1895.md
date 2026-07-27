# Test Case: Export agent with nested agent dependencies — produces .zip archive (extension traceability)

## Metadata
- **TMS ID**: ELITEA-1895
- **Linked Story**: none
- **Priority**: n/a — `extend-existing` (traceability + gap-fill record, not a fresh
  implementation)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: extend-existing — Rule-6 behavioural-equivalence dedup against the
  merged spec for ELITEA-1902, following the ELITEA-1896 precedent exactly
  (`test-specs/agents/lextend_export-agent-with-attached-skills-exported-md-contains-skill_ELITEA-1896.md`):
  live re-execution proved full behavioural coverage, but the covering test's own
  traceability (`@allure.issue` decorators) reached only ELITEA-1902's case file,
  not this one — per
  `.agents/memory/qa-engineer/coverage_classification_needs_board_task_not_just_behavioral_match.md`,
  that is a real (if small) gap that routes to `extend-existing`, not
  `already-covered`, regardless of how complete the behavioural match is. The gap
  has been closed in this run (see § Gap assertions — already applied).

## Extension target

- **Covering test**: `automation/tests/ui/agents/test_import_agent_zip_nested_agent_dependencies.py:96`
  (`TestImportAgentZipNestedAgentDependencies.test_import_agent_zip_nested_agent_dependencies`)
- **Covering AFS**: `test-specs/agents/l3_import-agent-zip-nested-dependencies_ELITEA-1902.md`
- **Covering TMS case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/agents/ELITEA-1902_import-agent-zip-with-nested-agent-dependencies.md`
- **Board task behind the covering test**: issue #143 (ELITEA-1902) — confirmed via
  `env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI` at board status
  `Ready`, label `control:audited`, issue state `OPEN` (agent-terminal per the
  tracker's status machine — awaiting human `Done`). This satisfies the
  board-task-completion check the memory note requires (a behavioural match alone,
  without a completed board task behind it, would not be enough).
- **This case's own tracking issue**: #183 (`[Automate][ELITEA-1895][agents]
  Export agent with nested agent dependencies — produces .zip archive`), OPEN,
  entry-column (untouched) at the time of this analysis.

## Behavioural overlap (live-verified, not assumed)

ELITEA-1895's case text was **not** taken on faith — the full precondition +
export flow was driven live against `http://localhost:5173` in this session
before comparing to the covering test, per the skill's "a written test case is a
hypothesis" principle:

1. **Created a nested (dependency) Agent** via the UI create form
   (`agent-name-input` / `agent-description-input` / `agent-instructions-input` /
   `agent-save-button`): `el1895-nested-a1b2c3d4`, instructions containing the
   planted marker `ELITEA_1895_NESTED_MARKER`. Agent id `5311` in this run.
2. **Created a main Agent** the same way: `el1895-main-a1b2c3d4`, instructions
   containing `ELITEA_1895_MAIN_MARKER`. Agent id `5312` in this run.
3. **Attached the nested agent** to the main agent via the Tools section's
   "+ Agent" picker (`agent-add-agent-button` → popper → menuitem selection).
   Confirmed live: the Tools section rendered a distinct sub-agent card showing
   `el1895-nested-a1b2c3d4` / `base` — the same shared `agent-toolkit-card`-style
   rendering ELITEA-1902's AFS already documented (not conflated with toolkits at
   the data level; distinguishable by name).
4. **Exported the main agent** via the actions overflow menu
   (`agent-actions-menu-button` → `agent-actions-export-menuitem`, in the VERSION
   group). Confirmed live: a **`.zip`** file was downloaded
   (`el1895-main-a1b2c3d4.agent.zip`), NOT a single `.md` — matching the case
   text exactly, and matching ELITEA-1902's prior finding that this behavior
   is genuine product behavior (not case-text drift). Network trace:
   `GET /api/v2//elitea_core/export_import/prompt_lib/399/5312?format=md&follow_version_ids=5427`
   → `200 OK` (same pre-existing doubled `//` URL-construction cosmetic quirk
   already documented in ELITEA-1794/1894/1902 — not re-filed here).
5. **Extracted the archive** and inspected its contents directly (`unzip` +
   `cat`, not assumed from the covering test's own claims):
   ```
   el1895-main-a1b2c3d4.agent.md
   el1895-nested-a1b2c3d4.agent.md
   ```
   Exactly 2 `.agent.md` members — one per entity, confirming the case's Pass
   criterion ("at least two .md files (main agent + nested agent(s))"). Full
   captured content:

   Main entity (`el1895-main-a1b2c3d4.agent.md`):
   ```yaml
   ---
   name: el1895-main-a1b2c3d4
   description: Main agent for ELITEA-1895 export test (has nested agent dependency).
   model: eu.anthropic.claude-sonnet-4-5-20250929-v1:0
   max_tokens: -1
   agent_type: agent
   step_limit: 25
   nested_agents:
   - name: el1895-nested-a1b2c3d4
   ---

   Main agent, delegates. ELITEA_1895_MAIN_MARKER must appear verbatim.
   ```

   Nested entity (`el1895-nested-a1b2c3d4.agent.md`):
   ```yaml
   ---
   name: el1895-nested-a1b2c3d4
   description: Nested dependency agent for ELITEA-1895 export test.
   model: eu.anthropic.claude-sonnet-4-5-20250929-v1:0
   max_tokens: -1
   agent_type: agent
   step_limit: 25
   ---

   Nested dep agent. ELITEA_1895_NESTED_MARKER must appear verbatim.
   ```

   The main entity's frontmatter carries a `nested_agents:` key referencing the
   nested agent by name — the structural feature that makes the "one .md per
   entity" claim assertable programmatically, not just by member count.
6. **Zero console errors** (`browser_console_messages`, level=error: 0 of 8
   total messages) throughout create/attach/export.
7. **Cleanup**: both agents (main `5312`, nested `5311`) deleted live via the
   UI's type-to-confirm delete dialog (`delete-agent-menuitem` →
   `delete-confirm-name-input` → `delete-confirm-button`); local downloaded
   `.zip` and extracted files removed.

This live run is **exactly** what
`automation/tests/ui/agents/test_import_agent_zip_nested_agent_dependencies.py`
already asserts, step for step, in its own Steps 1-3 (`:152`-`:249`):
- Step 1 (`:152-175`): create nested agent, create main agent, attach nested via
  `attach_agent()`, assert `is_toolkit_attached(...)`.
- Step 2 (`:177-190`): `export_agent_via_menu()`, assert
  `download.suggested_filename.endswith(".zip")`.
- Step 3 (`:192-249`): unzip, assert `len(agent_md_members) == 2`, assert a
  member exists per entity name, parse the main entity's YAML frontmatter and
  assert `nested_agents[0].name == nested_agent_name`, assert both planted
  markers appear verbatim in the correct file.

Every clause of ELITEA-1895's 4 case steps and its Pass/Fail criteria ("A .zip
file is downloaded and contains multiple .md files (one per entity)" / fail if
"A .md file is downloaded instead of a .zip, or the archive does not contain
files for all entities") is a direct match — not merely a superset via extra
unrelated assertions, but the *same* observable at the *same* granularity
(exact member count, per-entity presence by name, structural cross-reference).
The covering test additionally continues on to import the `.zip` back in
(Steps 4-8, ELITEA-1902's own scope) — none of that extra scope is needed to
satisfy ELITEA-1895, which stops at "archive downloaded and correctly
populated."

Re-run live in this session after the gap-fill edit below:
`HEADLESS=true pytest tests/ui/agents/test_import_agent_zip_nested_agent_dependencies.py -v -p no:cacheprovider`
→ **1 passed in 139.56s**.

## Gap assertions

**The gap** (found by applying the `coverage_classification_needs_board_task_not_just_behavioral_match`
memory-note ruling before finalizing a status, not assumed from the behavioural
match alone): the covering test's `@allure.issue` decorator
(`test_import_agent_zip_nested_agent_dependencies.py:98-101`, pre-edit) linked
ONLY to ELITEA-1902's case file. No second `@allure.issue` (or equivalent)
pointed at ELITEA-1895's case file, so the merged test's own traceability didn't
reach the case now being dedup'd against it.

**The exact insertion made to close it** (pure traceability tag — no new test
body, no new assertions, following the exact ELITEA-1896 precedent shape):

```python
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1902_import-agent-zip-with-nested-agent-dependencies.md",
    "onetest-ai Test Case link",
)
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1895_export-agent-with-nested-dependencies-produces-zip-archive.md",
    "onetest-ai Test Case link (also covers ELITEA-1895 — behavioural duplicate, "
    "see test-specs/agents/lextend_export-agent-with-nested-dependencies-produces-zip-archive_ELITEA-1895.md)",
)
@pytest.mark.p2
@pytest.mark.regression
def test_import_agent_zip_nested_agent_dependencies(self, page, agent_api):
```

Also added a module-docstring cross-reference paragraph ("Also covers
ELITEA-1895 ...") mirroring ELITEA-1896's docstring cross-reference pattern.

**Convention check performed before applying**: `test_export_agent_with_attached_skills.py`
(ELITEA-1794/1896) already established the precedent of stacking two
`@allure.issue(<TMS-case-URL>, "onetest-ai Test Case link")` decorators for two
distinct TMS case IDs proven by one test — this edit follows that exact,
already-established convention rather than inventing a new one.

**Applied and verified in this run**: the decorator + docstring cross-reference
were added to `test_import_agent_zip_nested_agent_dependencies.py`; syntax
checked (`ast.parse`); the test was re-run green
(`1 passed in 139.56s`, `HEADLESS=true pytest tests/ui/agents/test_import_agent_zip_nested_agent_dependencies.py -v -p no:cacheprovider`)
to confirm the traceability-only change didn't affect behavior.

Nothing else is missing — the gap was purely the traceability tag; the
assertions themselves already fully cover ELITEA-1895 per § Behavioural overlap
above (re-confirmed by live, independent re-execution in this session, not
merely by reading the covering test's code).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: an agent with at least one nested agent attached exists | Nested-agent-dependency structure exists | This AFS's live setup (nested agent `5311`, main agent `5312`, attached via `attach_agent()`/Tools "+Agent" picker) + covering test's Step 1 (`:152-175`) | `is_toolkit_attached(nested_agent_name)` assertion; live-confirmed Tools-section card rendering | already-covered |
| Step 1: Navigate to an agent that has at least one nested agent attached | Agent detail page loads | Covering test Step 1 (`:152-175`); this AFS's live create+attach flow | `verify_on_detail_page()` after agent creation/attach | already-covered |
| Step 2: Click three-dot menu → "Export" | Export action triggered | Covering test Step 2 (`:177-190`); this AFS's live click on `agent-actions-menu-button` → `agent-actions-export-menuitem` | `export_agent_via_menu()` triggers the download event | already-covered |
| Step 3: Verify a .zip file is downloaded | .zip download initiated | Covering test Step 2 (`:182-185`); this AFS's live download event (`el1895-main-a1b2c3d4.agent.zip`) | `assert download.suggested_filename.endswith(".zip")` | already-covered |
| Step 4: Extract the archive and verify it contains multiple .md files (one per entity) | ≥2 `.agent.md` files, one per entity | Covering test Step 3 (`:192-249`); this AFS's live `unzip` + `cat` inspection (2 members, matched by entity name, `nested_agents` frontmatter cross-reference) | `assert len(agent_md_members) == 2`; per-entity member-name match; `main_frontmatter["nested_agents"][0]["name"] == nested_agent_name` | already-covered |
| Pass criteria: all steps complete without errors; .zip contains multiple .md (one per entity) | End-to-end success | Same test, Steps 1-3 | Test passed green in this run (1 passed in 139.56s) | already-covered |
| Fail criteria: a single .md downloaded instead of a .zip, or archive missing entity files | Would fail the covering test's own assertions | Covering test's `assert download.suggested_filename.endswith(".zip")` and `assert len(agent_md_members) == 2` | Both are hard `assert`s — a regression to single-.md or missing-entity would fail this test, not silently pass | already-covered |
| Traceability: the covering test's own linkage reaches ELITEA-1895 | The merged test names both TMS IDs it satisfies | This AFS's § Gap assertions | Second `@allure.issue` decorator + docstring cross-reference added and re-verified green | gap closed this run |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Main entity's frontmatter carries a `nested_agents:` key referencing the nested agent by name | Structural proof beyond a bare member-count check — rules out two unrelated `.agent.md` files coincidentally both being present |
| Both planted markers (`ELITEA_1895_MAIN_MARKER` / `ELITEA_1895_NESTED_MARKER`, this run's equivalents of the covering test's `MAIN_MARKER`/`NESTED_MARKER`) appear verbatim in the correct member | Confirms per-entity content correctness, not just filename presence |
| Zero console errors during create/attach/export flow | Guards against silent regressions the case didn't ask for |
| Export network call (`GET .../export_import/prompt_lib/{project}/{agent-id}?format=md&follow_version_ids={version-id}` → `200 OK`) | Concrete wait-condition, consistent with ELITEA-1794/1894/1902's documentation of the same doubled-`//` cosmetic quirk (not re-filed) |
| Traceability now names both TMS IDs the merged test satisfies | Lets future audits/dedup passes find both cases from the one test, closing exactly the gap this AFS was raised to fix |

## Handles Reference (testid-only, provenance verified this run)

| Element | testid | Provenance | Notes |
|---|---|---|---|
| Agent Name field | `agent-name-input` | on-main ✓ | used live to create both agents this run |
| Agent Description field | `agent-description-input` | on-main ✓ | |
| Agent Instructions field | `agent-instructions-input` | on-main ✓ | |
| Agent Save button (create form) | `agent-save-button` | on-main ✓ | |
| Tools section "+ Agent" button | `agent-add-agent-button` | on-main ✓ | opens agent picker popper (ELITEA-1887) |
| Attached sub-agent card | `agent-toolkit-card` (shared with Toolkit attachments, by design) | on-main ✓ | confirmed live: renders `el1895-nested-a1b2c3d4` / `base` after attach |
| Agent actions (overflow) menu | `agent-actions-menu-button` | on-main ✓ | opens VERSION/AGENT grouped menu |
| Export menuitem | `agent-actions-export-menuitem` | on-main ✓ | in the VERSION group; click triggers immediate `.zip` download, no confirmation dialog |
| Delete agent menuitem (cleanup) | `delete-agent-menuitem` | on-main ✓ | in the AGENT group |
| Delete-confirm name input (cleanup) | `delete-confirm-name-input` | on-main ✓ | type-to-confirm dialog |
| Delete-confirm button (cleanup) | `delete-confirm-button` | on-main ✓ | |
| Downloaded archive naming pattern | `{agent-name}.agent.zip` | n/a (not a UI handle) | contains `{entity-name}.agent.md` per member |
| Export network call | `GET /api/v2//elitea_core/export_import/prompt_lib/{project}/{agent-id}?format=md&follow_version_ids={version-id}` → `200 OK` | n/a (network call) | pre-existing doubled `//` cosmetic quirk, already documented (ELITEA-1794/1894/1902), not re-filed |

No new/missing testids found this run — every element this case touches already
has a stable `data-testid` on `main`, confirmed by fresh live interaction (not
assumed from ELITEA-1902's prior AFS).

## Known Defects
None. No product defect found. Live re-execution in this session independently
reproduces ELITEA-1902's prior finding: exporting an Agent with a nested Agent
dependency correctly produces a `.zip` archive containing one `.agent.md` per
entity (main + nested), with the main entity's frontmatter correctly
cross-referencing the nested entity by name. The pre-existing doubled `//` in
the export endpoint URL is the same already-documented (ELITEA-1794/1894/1902)
cosmetic observation, not re-filed here.

## Cleanup
Two agents created live in this run (main `5312`, nested `5311`), both deleted
live via the UI's type-to-confirm delete dialog in this same session — no
lingering entities. Local downloaded `.zip` and extracted files removed after
inspection. No new entities were created by the gap-fill work itself (a
decorator/docstring edit only), so no additional cleanup is owed there.

## Blocked Steps
None.
