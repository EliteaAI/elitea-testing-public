# Test Case: Export Agent with attached Skills — exported .md contains Skill content (dedup traceability)

## Metadata
- **TMS ID**: ELITEA-1896
- **Linked Story**: none
- **Priority**: n/a — `already-covered` (traceability record, not a fresh implementation)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: already-covered — Rule-6 behavioural-equivalence dedup against the
  merged spec for ELITEA-1794. No fresh `.spec.ts`/pytest test is written for this
  case; the existing test already proves everything ELITEA-1896 asks for.

## Dedup proof

**Covering spec**: `test-specs/skills/l3_export-agent-with-attached-skills_ELITEA-1794.md`
**Covering test**: `automation/tests/ui/skills/test_export_agent_with_attached_skills.py:79`
(`TestExportAgentWithAttachedSkills.test_export_agent_with_attached_skills`)
**Covering TMS case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/skills/ELITEA-1794_export-agent-with-attached-skills.md`
(`status: ready`, `execution_type: automated`,
`automation_test_id: automation/tests/ui/skills/test_export_agent_with_attached_skills.py::TestExportAgentWithAttachedSkills::test_export_agent_with_attached_skills`,
`automation_pr: https://github.com/EliteaAI/elitea-testing-public/pull/285`)

**Re-verified live in this run**: `cd automation && HEADLESS=true ../.venv/bin/pytest
tests/ui/skills/test_export_agent_with_attached_skills.py -v` → **1 passed in 53.23s**
against `http://localhost:5173` (dev server responding `200`), confirming the
covering test's assertions are currently true of the live product, not stale.

**Behavioural-equivalence argument**: ELITEA-1896 and ELITEA-1794 are the same
observable under different TMS IDs. Both specify: (1) create a Skill with named
instructions; (2) create an Agent and attach that Skill at `base` version; (3)
export the Agent as `.md`; (4) open the exported file and confirm it contains the
attached Skill's metadata (name, version) and its instructions content. ELITEA-1794's
merged test does exactly this and asserts strictly more than ELITEA-1896 requires:
it parses the exported YAML frontmatter's `skills:` list and asserts
`skills[0].name == <attached skill name>`, `skills[0].version == "base"`, and
`skills[0].instructions` contains — and in fact equals verbatim — the full planted
instructions text (via a unique marker substring, ruling out the export merely
referencing the Skill by ID). It also asserts the download has a `.md`-suffixed
name and that the agent's own `name`/`description`/instructions round-trip
correctly, and that no console errors fire during the flow. Every clause of
ELITEA-1896's Pass criteria ("exported .md file contains 'ExportSkill' metadata
and 'Export test instructions'") is a strict subset of what the covering test
already proves for an equivalent Skill/Agent pair with different literal names.
There is no case-specific behavior in ELITEA-1896 (e.g. a different skill version,
a different export trigger, a different file format) that the covering test
doesn't already exercise — the only difference between the two cases is the
literal test-data strings ("ExportSkill"/"ExportAgent" vs
`el-1794-skill-<suffix>`/`el-1794-agent-<suffix>`), which is exactly the kind of
variation Rule-6 dedup exists to absorb.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Create a Skill "ExportSkill" with instructions "Export test instructions" | Skill created successfully | ELITEA-1794 test, `_create_skill()` helper (`test_export_agent_with_attached_skills.py:43-67`) + Step 1 | Skill created via UI with a planted marker in its instructions; `SkillDetailPage.verify_on_detail_page()` + numeric id extraction | already-covered |
| Step 2: Create an Agent "ExportAgent", attach "ExportSkill" (version: base) | Agent created with Skill attached | ELITEA-1794 test, Steps 2–4 (`:133-184`) | Agent created via UI; `detail_page.attach_skill(...)`; asserts `"1/" in get_skills_counter_text()`, `is_skill_attached(...)`, `get_skill_version_text(...) == "base"` | already-covered |
| Step 3: Export "ExportAgent" as .md | A .md file is downloaded | ELITEA-1794 test, Steps 5–6 (`:186-214`) | `detail_page.export_agent_via_menu(...)`; asserts `download.suggested_filename` truthy and `.endswith(".md")`; file saved and asserted non-empty | already-covered |
| Step 4: Open the exported file and verify it contains the attached Skill's metadata and instructions | File includes "ExportSkill" metadata and "Export test instructions" content | ELITEA-1794 test, Step 7 (`:216-269`) | Raw file parsed as YAML frontmatter + body; asserts `skills[0].name`, `skills[0].version == "base"`, and `skills[0].instructions` contains the marker AND equals the full planted instructions string verbatim | already-covered — strictly stronger assertion (verbatim match + marker proof) than the case's literal "contains" requirement |
| Pass criteria: exported file missing nothing, no step errors | All steps complete without error | Same test, end-to-end | Test passed green in this run (1 passed in 53.23s) | already-covered |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Zero console errors during attach/export/download flow | Covering test guards against silent JS errors the case didn't ask for but that would indicate a regression |
| Agent's own `name`/`description`/instructions round-trip in the export | Extra confidence the export mechanism as a whole is sound, not just the Skill sub-object |
| Verbatim-equality assertion (not just substring) on the Skill instructions | Stronger than ELITEA-1896's literal "contains" wording — rules out partial/truncated embedding |

## Known Defects
None. The covering test has no linked defect (`automation/tests/ui/skills/test_export_agent_with_attached_skills.py` docstring: "No product defect found"), and re-running it live in this session reproduced a clean pass.

## Cleanup
None required for this traceability AFS — no new entities were created. The
re-verification run's own Skill/Agent fixtures were created and torn down by the
covering test's existing `finally` block (`agent_api.delete_agent(...)` then
`skill_api.delete_skill(...)`, plus local downloaded-file cleanup).

## Blocked Steps
None.
