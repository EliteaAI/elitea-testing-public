---
id: ELITEA-1891
title: "Version selector lists all versions in correct order with expected metadata"
priority: high
type: functional
module: agents
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:agents]
requirements: []
---

# ELITEA-1891: Version selector lists all versions in correct order with expected metadata

**Module:** agents · **Priority:** high · **Type:** functional

**Objective:** Verify that the version dropdown lists all agent versions in the correct order (Published → Draft → base) and that each entry shows the version name and creation date/time.

---

## Preconditions

- User is logged in to the Elitea platform.
- An agent with base version, at least one Draft named version, and optionally a Published version exists.

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to an agent with: base version, at least one Draft named version, and (if available) a Published version | The agent detail page loads |
| 2 | Click the version dropdown in the toolbar | The version dropdown opens |
| 3 | Verify all versions are listed | All existing versions are present in the dropdown |
| 4 | Verify each entry shows version name and creation date/time | Every version entry displays both its name and creation timestamp |
| 5 | Verify base version appears last | The "base" version is at the bottom of the list |
| 6 | Verify Draft named versions appear above base | Draft versions are listed above the base version |
| 7 | If a Published version exists — verify it appears before Draft versions | Published versions appear above Draft versions |
| 8 | Verify the default/pinned version (if set) appears at the top with a pin icon | The pinned version is at the top with a visible pin icon |

---

## Expected Final State

The version dropdown shows all versions in the correct order (pinned/Published → Draft → base), each with version name and creation date/time.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All versions are listed with correct metadata and in the expected order.

**Fail:**
- Any step produces an error or unexpected result.
- Versions are missing, out of order, or metadata (name/date) is absent.
