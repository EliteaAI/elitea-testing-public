---
id: ELITEA-2604
title: "Skill Custom Icon Upload and Validation"
priority: high
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:icon]
requirements: []
---

# ELITEA-2604: Skill Custom Icon Upload and Validation

**Module:** skills · **Priority:** high · **Type:** functional

**Objective:** Verify that custom icons can be uploaded during skill creation and editing, accepted formats work correctly (png, jpg, gif, webp), oversized files are rejected (>500KB limit), and deleting an icon reverts to the default `skill-icon.svg`.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills section is available in the project.
- Test icon files prepared:
  - Valid PNG file (under 500KB)
  - Valid JPG file (under 500KB)
  - Valid GIF file (under 500KB)
  - Valid WEBP file (under 500KB)
  - Oversized file (over 500KB)

---

## Test Data

| Field | Value |
|-------|-------|
| Skill Name | `icon-test-skill` |
| Valid PNG Icon | `test-icon.png` (< 500KB) |
| Valid JPG Icon | `test-icon.jpg` (< 500KB) |
| Valid GIF Icon | `test-icon.gif` (< 500KB) |
| Valid WEBP Icon | `test-icon.webp` (< 500KB) |
| Oversized Icon | `large-icon.png` (> 500KB) |
| Default Icon | `skill-icon.svg` (system default) |

---

## Steps

### Part A: Upload During Creation

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to Create Skill page | Create skill form loads |
| 2 | Click on the icon upload area/button | File picker dialog opens |
| 3 | Select a valid PNG file (under 500KB) | File is selected |
| 4 | Confirm upload | Icon preview shows the uploaded PNG |
| 5 | Fill in required fields (name, description, instructions) | Fields are populated |
| 6 | Save the skill | Skill is created with custom icon |
| 7 | Reopen the skill | Custom PNG icon is displayed |

### Part B: Replace Icon with Different Format

| # | Action | Expected Result |
|---|--------|-----------------|
| 8 | Click on the icon to change it | File picker or icon edit option appears |
| 9 | Upload a valid GIF file | GIF is uploaded successfully |
| 10 | Save the skill | Changes are saved |
| 11 | Verify the icon is now the GIF | GIF icon is displayed |
| 12 | Repeat with WEBP format | WEBP icon uploads and displays correctly |
| 13 | Repeat with JPG format | JPG icon uploads and displays correctly |

### Part C: Validation — Oversized File

| # | Action | Expected Result |
|---|--------|-----------------|
| 14 | Attempt to upload an oversized file (>500KB) | Upload is rejected |
| 15 | Verify error message is displayed | Error indicates file size exceeds 500KB limit |
| 16 | Verify the previous icon is retained (not cleared) | Current icon remains unchanged |

### Part D: Delete Icon — Revert to Default

| # | Action | Expected Result |
|---|--------|-----------------|
| 17 | Click on the icon delete/remove option | Delete confirmation or immediate removal |
| 18 | Confirm deletion if prompted | Icon is removed |
| 19 | Verify the icon reverts to default `skill-icon.svg` | Default system icon is displayed |
| 20 | Save the skill | Changes are saved |
| 21 | Reopen the skill | Default icon is still displayed |

---

## Expected Final State

1. Custom icons can be uploaded during creation and editing.
2. All valid formats (PNG, JPG, GIF, WEBP) work correctly.
3. Files exceeding 500KB are rejected with a clear error message.
4. Deleting a custom icon reverts the skill to the default `skill-icon.svg`.

---

## Pass/Fail Criteria

**Pass:**
- Icon upload works during skill creation.
- Icon replacement works during editing.
- All specified formats (PNG, JPG, GIF, WEBP) are accepted.
- Oversized files are rejected with appropriate error.
- Icon deletion reverts to default system icon.

**Fail:**
- Icon upload fails for valid files.
- Any supported format is rejected.
- Oversized files are accepted.
- Deleting icon does not revert to default.
- Error messages are missing or unclear.
