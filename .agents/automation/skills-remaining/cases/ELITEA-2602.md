---
id: ELITEA-2602
title: "Fork Skill End-to-End"
priority: high
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:fork]
requirements: []
---

# ELITEA-2602: Fork Skill End-to-End

**Module:** skills · **Priority:** high · **Type:** functional

**Objective:** Verify the complete skill fork workflow: forking creates a complete copy in the target project with all fields preserved, lineage metadata is stored, the "Main entity" card displays correctly, the project dropdown excludes the current project, and the forked skill is fully independent (edits don't cross-propagate).

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- At least two projects exist and are accessible to the user.
- The Skills section is available in both projects.
- User has fork permissions.
- A custom icon file is available for upload.

---

## Test Data

| Field | Value |
|-------|-------|
| Source Project | Project A |
| Target Project | Project B |
| Skill Name | `forkable-skill` |
| Skill Description | Detailed description for fork testing (100+ characters) |
| Skill Instructions | Comprehensive instructions for the skill behavior |
| Skill Tags | `test-tag`, `fork-demo` |
| Custom Icon | Valid PNG/JPG file under 500KB |
| Modified Instructions (post-fork) | Updated instructions after forking to test independence |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | In Project A, create a skill with name, description, instructions, multiple tags, and a custom icon | Skill is created with all fields populated |
| 2 | Save the skill | Skill is saved successfully |
| 3 | Open the skill's overflow menu (three dots) | Menu appears with available actions |
| 4 | Verify "Fork" option is present and enabled | Fork option is visible and clickable |
| 5 | Click "Fork" | Fork modal/dialog opens |
| 6 | Verify "Main entity" card displays the skill details | Card shows skill name, description, and can be expanded for more details |
| 7 | Expand the "Main entity" card | Full skill details are visible (instructions, tags, etc.) |
| 8 | Verify the project dropdown for target selection | Dropdown is present with available projects |
| 9 | Verify the current project (Project A) is NOT in the dropdown | Project A is excluded from selection options |
| 10 | Select the target project (Project B) | Project B is selected |
| 11 | Click "Fork" or "Confirm" to execute the fork | Fork operation completes, success message shown |
| 12 | Navigate to Project B's Skills section | Project B Skills list loads |
| 13 | Locate the forked skill | Forked skill appears in Project B's skill list |
| 14 | Open the forked skill and verify all fields | Name, description, instructions match the original |
| 15 | Verify tags are preserved | Both `test-tag` and `fork-demo` tags are present |
| 16 | Verify custom icon is preserved | Same custom icon is displayed |
| 17 | Check the skill's metadata/properties for lineage information | Lineage metadata shows: parent_entity_id, parent_project_id, parent_version_id |
| 18 | Edit the forked skill's instructions in Project B and save | Changes are saved successfully |
| 19 | Navigate back to Project A and open the original skill | Original skill loads |
| 20 | Verify the original skill's instructions are UNCHANGED | Original instructions remain as they were (no cross-propagation) |

---

## Expected Final State

1. Forked skill exists in Project B with all fields preserved (name, description, instructions, tags, custom icon).
2. Lineage metadata is stored linking the fork to its parent.
3. The forked skill is fully independent — changes to the fork do not affect the original, and vice versa.

---

## Pass/Fail Criteria

**Pass:**
- Fork modal shows correct skill details in "Main entity" card.
- Current project is excluded from target dropdown.
- Fork creates complete copy with all fields preserved.
- Lineage metadata is stored correctly.
- Edits to forked skill do not affect original (independence verified).

**Fail:**
- Fork option not available or disabled for valid skill.
- Current project appears in target dropdown.
- Any field (name, description, instructions, tags, icon) is missing or corrupted.
- Lineage metadata is missing.
- Changes to fork affect the original skill (cross-propagation bug).
