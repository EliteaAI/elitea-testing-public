---
id: ELITEA-1978
title: "Credential — Duplicate/Mismatch Validation"
priority: high
type: functional
module: toolkits-credentials
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:toolkits]
requirements: []
---

# ELITEA-1978: Credential — Duplicate/Mismatch Validation

**Module:** toolkits-credentials · **Priority:** high · **Type:** functional

**Objective:** Verify that the system prevents creation of duplicate credentials with the same Display Name and shows appropriate validation errors, and that saving with empty required fields is blocked.

---

## Preconditions

- User is logged in to the Elitea platform.
- A project exists and the Credentials section is accessible.

---

## Test Data

| Field | Value |
|-------|-------|
| Duplicate credential name | autotest_duplicate_cred |
| Credential type | Github |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a credential "autotest_duplicate_cred" of type Github | Credential is created successfully |
| 2 | Attempt to create another credential with the same Display Name "autotest_duplicate_cred" | Credential creation form is submitted |
| 3 | Click Save | System shows error: "Credential with ID 'autotest_duplicate_cred' already exists" |
| 4 | Verify an error or warning about the duplicate name is shown (or save is prevented) | Error message is visible to the user |
| 5 | Attempt to save a credential with empty required fields (e.g., empty Client Id or Token) | Save button remains disabled or form validation triggers |
| 6 | Verify required field validation indicators appear and Save remains disabled | Validation indicators are shown; Save is not allowed |

---

## Expected Final State

The system prevents duplicate credentials with the same ID and blocks saving when required fields are empty, displaying clear validation messages.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Duplicate credential creation shows the expected error message; empty required fields block saving with validation indicators.

**Fail:**
- Any step produces an error or unexpected result.
- Duplicate credential is saved without error, or empty required fields allow saving.
