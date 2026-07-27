# Test Case: Export Agent with attached Skills — exported .md contains Skill content (extension traceability)

## Metadata
- **TMS ID**: ELITEA-1896
- **Linked Story**: none
- **Priority**: n/a — `extend-existing` (traceability + gap-fill record, not a fresh
  implementation)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: extend-existing — Rule-6 behavioural-equivalence dedup against the
  merged spec for ELITEA-1794, **revised from an initial `already-covered` verdict**
  after an orchestrator gate check found the covering test's own traceability
  (`@allure.issue` decorators) didn't reach ELITEA-1896's case file — a real, if
  small, gap per `.agents/memory/qa-engineer/coverage_classification_needs_board_task_not_just_behavioral_match.md`.
  The gap has since been closed (see § Gap assertions — already applied).

## Extension target

- **Covering test**: `automation/tests/ui/skills/test_export_agent_with_attached_skills.py:79`
  (`TestExportAgentWithAttachedSkills.test_export_agent_with_attached_skills`)
- **Covering AFS**: `test-specs/skills/l3_export-agent-with-attached-skills_ELITEA-1794.md`
- **Covering TMS case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/skills/ELITEA-1794_export-agent-with-attached-skills.md`
  (`status: ready`, `execution_type: automated`,
  `automation_test_id: automation/tests/ui/skills/test_export_agent_with_attached_skills.py::TestExportAgentWithAttachedSkills::test_export_agent_with_attached_skills`,
  `automation_pr: https://github.com/EliteaAI/elitea-testing-public/pull/285`)
- **Board task behind the covering test**: issue #36 (ELITEA-1794) — confirmed at
  status `Ready` with `control:audited` + `testids:merged-to-main` labels (board-first
  check per the memory-note ruling; passes).

## Behavioural overlap

ELITEA-1896 and ELITEA-1794 are the same observable under different TMS IDs. Both
specify: (1) create a Skill with named instructions; (2) create an Agent and attach
that Skill at `base` version; (3) export the Agent as `.md`; (4) open the exported
file and confirm it contains the attached Skill's metadata (name, version) and its
instructions content. ELITEA-1794's merged test does exactly this and asserts
strictly more than ELITEA-1896 requires: it parses the exported YAML frontmatter's
`skills:` list and asserts `skills[0].name == <attached skill name>`,
`skills[0].version == "base"`, and `skills[0].instructions` contains — and in fact
equals verbatim — the full planted instructions text (via a unique marker
substring, ruling out the export merely referencing the Skill by ID). It also
asserts the download has a `.md`-suffixed name, that the agent's own
`name`/`description`/instructions round-trip correctly, and that no console errors
fire during the flow. Every clause of ELITEA-1896's Pass criteria ("exported .md
file contains 'ExportSkill' metadata and 'Export test instructions'") is a strict
subset of what the covering test already proves for an equivalent Skill/Agent pair
with different literal names. Re-run live in this session
(`HEADLESS=true pytest tests/ui/skills/test_export_agent_with_attached_skills.py -v`
→ **1 passed in 53.23s**, then again **1 passed in 53.87s** after the gap-fill edit
below), confirming these assertions are currently true of the live product, not
stale.

## Gap assertions

**The gap** (found by orchestrator gate check, not by the initial analyst pass):
the covering test's `@allure.issue` decorator (`test_export_agent_with_attached_skills.py:73-76`)
linked ONLY to ELITEA-1794's case file. No second `@allure.issue` (or equivalent)
pointed at ELITEA-1896's case file, so the merged test's own traceability didn't
reach the case now being dedup'd against it — behavioural equivalence alone is
necessary but not sufficient for `already-covered` per the memory-note ruling.

**The exact insertion made to close it** (pure traceability tag — no new test body,
no new assertions):

```python
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1794_export-agent-with-attached-skills.md",
    "onetest-ai Test Case link",
)
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1896_export-agent-with-attached-skills-exported-md-contains-skill.md",
    "onetest-ai Test Case link (also covers ELITEA-1896 — behavioural duplicate, "
    "see test-specs/agents/lextend_export-agent-with-attached-skills-exported-md-contains-skill_ELITEA-1896.md)",
)
@pytest.mark.p2
@pytest.mark.regression
def test_export_agent_with_attached_skills(self, page, agent_api, skill_api):
```

Convention check performed before applying: no neighbouring test in this repo
stacks two `@allure.issue(<TMS-case-URL>, "onetest-ai Test Case link")` decorators
for two distinct TMS case IDs on one test (existing multi-decorator tests pair one
TMS-case link with one known-defect issue link, e.g.
`test_skill_agent_version_selector.py:89-96`). The chosen shape — a second
`@allure.issue` with the same `"onetest-ai Test Case link"` label text, differing
only in URL and an inline note — is the natural extension of the project's single
established convention (one decorator per linked case) rather than an invented
one.

**Applied and verified in this run**: the decorator + a docstring cross-reference
were added to `test_export_agent_with_attached_skills.py`; the test was re-run
green (`1 passed in 53.87s`) to confirm the traceability-only change didn't affect
behavior.

Nothing else is missing — the gap was purely the traceability tag; the assertions
themselves already fully cover ELITEA-1896 per § Behavioural overlap above.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Create a Skill "ExportSkill" with instructions "Export test instructions" | Skill created successfully | ELITEA-1794 test, `_create_skill()` helper (`test_export_agent_with_attached_skills.py:43-67`) + Step 1 | Skill created via UI with a planted marker in its instructions; `SkillDetailPage.verify_on_detail_page()` + numeric id extraction | already-covered |
| Step 2: Create an Agent "ExportAgent", attach "ExportSkill" (version: base) | Agent created with Skill attached | ELITEA-1794 test, Steps 2–4 (`:133-184`) | Agent created via UI; `detail_page.attach_skill(...)`; asserts `"1/" in get_skills_counter_text()`, `is_skill_attached(...)`, `get_skill_version_text(...) == "base"` | already-covered |
| Step 3: Export "ExportAgent" as .md | A .md file is downloaded | ELITEA-1794 test, Steps 5–6 (`:186-214`) | `detail_page.export_agent_via_menu(...)`; asserts `download.suggested_filename` truthy and `.endswith(".md")`; file saved and asserted non-empty | already-covered |
| Step 4: Open the exported file and verify it contains the attached Skill's metadata and instructions | File includes "ExportSkill" metadata and "Export test instructions" content | ELITEA-1794 test, Step 7 (`:216-269`) | Raw file parsed as YAML frontmatter + body; asserts `skills[0].name`, `skills[0].version == "base"`, and `skills[0].instructions` contains the marker AND equals the full planted instructions string verbatim | already-covered — strictly stronger assertion (verbatim match + marker proof) than the case's literal "contains" requirement |
| Pass criteria: exported file missing nothing, no step errors | All steps complete without error | Same test, end-to-end | Test passed green in this run (1 passed in 53.23s / 53.87s) | already-covered |
| Traceability: the covering test's own linkage reaches ELITEA-1896 | The merged test names both TMS IDs it satisfies | This AFS's § Gap assertions | Second `@allure.issue` decorator + docstring cross-reference added and re-verified green | gap closed this run |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Zero console errors during attach/export/download flow | Covering test guards against silent JS errors the case didn't ask for but that would indicate a regression |
| Agent's own `name`/`description`/instructions round-trip in the export | Extra confidence the export mechanism as a whole is sound, not just the Skill sub-object |
| Verbatim-equality assertion (not just substring) on the Skill instructions | Stronger than ELITEA-1896's literal "contains" wording — rules out partial/truncated embedding |
| Traceability now names both TMS IDs the merged test satisfies | Lets future audits/dedup passes find both cases from the one test, closing exactly the gap this AFS was raised to fix |

## Known Defects
None. The covering test has no linked defect (docstring: "No product defect
found"), and re-running it live in this session (twice — before and after the
traceability edit) reproduced a clean pass both times.

## Cleanup
None required beyond what the covering test's own `finally` block already
performs (`agent_api.delete_agent(...)` then `skill_api.delete_skill(...)`, plus
local downloaded-file cleanup) — no new entities were created by this AFS's
gap-fill work, since the change was a decorator/docstring edit, not new test
setup.

## Blocked Steps
None.
