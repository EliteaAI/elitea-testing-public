---
id: ELITEA-2603
title: "Fork Non-Base Skill Version"
priority: medium
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:fork, feat:versioning]
requirements: []
---

# ELITEA-2603: Fork Non-Base Skill Version

**Module:** skills · **Priority:** medium · **Type:** functional

**Objective:** Verify that forking a specific non-base version of a skill correctly copies that version's configuration, and the forked skill's version name becomes "base" in the target project.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- At least two projects exist and are accessible to the user.
- The Skills section is available in both projects.
- User has fork permissions.

---

## Test Data

| Field | Value |
|-------|-------|
| Source Project | Project A |
| Target Project | Project B |
| Skill Name | `versioned-skill` |
| Base Version Instructions | Original instructions for base version |
| Version 2 Name | `v2-enhanced` |
| Version 2 Instructions | Enhanced instructions with additional capabilities (different from base) |
| Version 2 Tags | `v2-tag`, `enhanced` |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | In Project A, create a skill with base version instructions | Skill is created with "base" version |
| 2 | Save the skill | Skill is saved successfully |
| 3 | Create a new version named `v2-enhanced` with different instructions and tags | New version is created |
| 4 | Verify the skill now has multiple versions (base and v2-enhanced) | Version dropdown shows both versions |
| 5 | Select the `v2-enhanced` version as the active version | v2-enhanced is now the selected version |
| 6 | Open the skill's overflow menu and click "Fork" | Fork modal opens |
| 7 | Verify the modal shows the v2-enhanced version details (not base) | Version-specific instructions and tags are displayed |
| 8 | Select Project B as the target project | Project B is selected |
| 9 | Complete the fork operation | Fork completes successfully |
| 10 | Navigate to Project B's Skills section | Skills list loads |
| 11 | Open the forked skill | Forked skill opens |
| 12 | Verify the skill's version name is "base" (not "v2-enhanced") | Version dropdown shows "base" as the version name |
| 13 | Verify the instructions match the v2-enhanced version (not original base) | Instructions contain the enhanced content from v2 |
| 14 | Verify the tags from v2-enhanced are present | Tags `v2-tag` and `enhanced` are present |
| 15 | Verify the forked skill does NOT have the original base version content | Content differs from Project A's base version |

---

## Expected Final State

1. Forking a non-base version copies that version's specific configuration.
2. The forked skill in the target project has version name "base" (normalized).
3. All version-specific content (instructions, tags) from the source version is preserved.

---

## Pass/Fail Criteria

**Pass:**
- Fork captures the selected version's configuration (not base).
- Forked skill's version is named "base" in target project.
- Instructions and tags match the source version (v2-enhanced).

**Fail:**
- Fork copies base version instead of selected version.
- Forked skill retains original version name (should be normalized to "base").
- Content doesn't match the selected source version.
