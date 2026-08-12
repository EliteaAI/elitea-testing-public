---
id: ELITEA-1979
title: "Credential — Usage in Toolkit Flows"
priority: high
type: functional
module: toolkits-credentials
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:toolkits]
requirements: []
---

# ELITEA-1979: Credential — Usage in Toolkit Flows

**Module:** toolkits-credentials · **Priority:** high · **Type:** functional

**Objective:** Verify that a credential can be successfully linked to a toolkit, enables toolkit operations that require authentication, and that the toolkit reflects an empty/error state when the linked credential is deleted.

---

## Preconditions

- User is logged in to the Elitea platform.
- A project exists with access to Toolkits and Credentials sections.
- A Github toolkit is available or can be created.

---

## Test Data

| Field | Value |
|-------|-------|
| Credential name | autotest_toolkit_cred |
| Credential type | Github |
| Token | (valid Github personal access token) |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create a valid Github credential "autotest_toolkit_cred" with a valid token | Credential is created successfully |
| 2 | Navigate to the Toolkits section | Toolkits list loads |
| 3 | Create or open a toolkit that requires Github credentials | Toolkit configuration page loads |
| 4 | In the credential selection dropdown, choose "autotest_toolkit_cred" | Credential is selected and linked to the toolkit |
| 5 | Verify the credential is successfully linked to the toolkit | Toolkit shows "autotest_toolkit_cred" as the selected credential |
| 6 | Test a toolkit operation that uses the credential (e.g., list branches) | Toolkit operation succeeds using the linked credential |
| 7 | Navigate back to Credentials and delete "autotest_toolkit_cred" | Credential is deleted |
| 8 | Return to the toolkit and check the credential field | Credential field shows an empty or error/missing state |

---

## Expected Final State

The toolkit successfully uses the linked credential for its operations; deleting the credential results in an empty/error state in the toolkit's credential field.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Toolkit operation succeeds with the linked credential; credential field shows empty/error after the credential is deleted.

**Fail:**
- Any step produces an error or unexpected result.
- Toolkit operation fails with a valid credential, or credential field does not reflect the deleted state.
