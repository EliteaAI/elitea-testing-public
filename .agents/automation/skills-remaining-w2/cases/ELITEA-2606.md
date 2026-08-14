---
id: ELITEA-2606
title: "Skill Custom Icon Persistence on Save As Version"
priority: low
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:icon, feat:versioning]
requirements: []
---

# ELITEA-2606: Skill Custom Icon Persistence on Save As Version

**Module:** skills · **Priority:** low · **Type:** functional

**Objective:** Verify that when creating a new version of a skill using "Save As Version", the custom icon is preserved on the new version.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills section is available in the project.
- A custom icon file is available.

---

## Test Data

| Field | Value |
|-------|-------|
| Skill Name | `version-icon-skill` |
| Custom Icon | Distinctive custom icon file |
| Base Version Instructions | Original instructions |
| New Version Name | `v2` |
| New Version Instructions | Updated instructions for version 2 |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a skill with a distinctive custom icon | Skill is created with custom icon |
| 2 | Fill in all required fields and save | Skill is saved successfully |
| 3 | Verify the custom icon is displayed | Custom icon is visible on skill |
| 4 | Click "Save As Version" or equivalent versioning action | Version creation dialog/form appears |
| 5 | Enter a new version name (`v2`) | Version name is entered |
| 6 | Optionally modify the instructions | Instructions are updated |
| 7 | Save the new version | New version is created successfully |
| 8 | Verify the new version is now active/selected | Version dropdown shows `v2` as current |
| 9 | Verify the custom icon is displayed on the new version | Custom icon is preserved (not reverted to default) |
| 10 | Switch back to the base version | Base version is selected |
| 11 | Verify the custom icon is still present on base version | Custom icon is displayed |
| 12 | Switch to v2 again | v2 is selected |
| 13 | Verify both versions share the same custom icon | Custom icon is consistent across versions |

---

## Expected Final State

The custom icon is preserved when creating new versions of a skill. Both the original version and new versions display the same custom icon.

---

## Pass/Fail Criteria

**Pass:**
- "Save As Version" creates a new version successfully.
- Custom icon is preserved on the new version.
- Custom icon remains on the original version.
- Icon is consistent when switching between versions.

**Fail:**
- New version loses the custom icon (reverts to default).
- Original version loses icon after creating new version.
- Icons differ between versions unexpectedly.
