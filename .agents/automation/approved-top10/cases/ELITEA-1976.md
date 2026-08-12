---
id: ELITEA-1976
title: "Credential — Create Private Credential from Toolkit Flow"
priority: high
type: functional
module: toolkits-credentials
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:toolkits]
requirements: []
---

# ELITEA-1976: Credential — Create Private Credential from Toolkit Flow

**Module:** toolkits-credentials · **Priority:** high · **Type:** functional

**Objective:** Verify that a user can create a private credential directly from a toolkit's credential dropdown, and that the new private credential is only visible to its creator when linked to the toolkit.

---

## Preconditions

- User is logged in to the Elitea platform.
- A project exists with an existing toolkit that uses Github credentials.
- The Credentials and Toolkits sections are accessible.

---

## Test Data

| Field | Value |
|-------|-------|
| Toolkit type | Github-based toolkit |
| Private credential name | autotest_private_cred |
| Token value | (any valid or placeholder token) |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to the Toolkits section from the sidebar | Toolkits list page loads |
| 2 | Open an existing Github toolkit | Toolkit detail/configuration page loads |
| 3 | In the toolkit Configuration section, click the credential dropdown (e.g., "Github Configuration *") | Dropdown opens showing CREATE and "Saved github Credentials" sections |
| 4 | Verify the dropdown shows two sections: "CREATE" and "Saved github Credentials" | Both sections are visible |
| 5 | Verify the CREATE section has two options: "New private github credentials" (person icon) and "New project github credentials" (briefcase icon) | Both options are present |
| 6 | Click "New private github credentials" | Credential creation form opens with Github type pre-selected |
| 7 | Fill in Display Name: "autotest_private_cred" and Token value | Fields accept the input |
| 8 | Save the credential | Credential is saved successfully |
| 9 | Navigate back to the toolkit | Toolkit configuration page loads |
| 10 | Click the credential dropdown again | Dropdown reopens |
| 11 | Click the "Refresh the configurations" button next to "Saved github Credentials" header | List refreshes |
| 12 | Verify "autotest_private_cred" appears in the saved credentials list | Newly created credential is visible |
| 13 | Select "autotest_private_cred" | Credential is linked to the toolkit |
| 14 | Verify this credential is only visible to the creator (private scope) | Credential is not visible to other project members |

---

## Expected Final State

"autotest_private_cred" is created as a private credential, linked to the toolkit, and visible only to its creator.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Private credential is created, appears in the toolkit dropdown after refresh, is linked successfully, and has private scope.

**Fail:**
- Any step produces an error or unexpected result.
- Private credential is not created, does not appear in the dropdown, or is visible to other project members.
