---
id: ELITEA-2197
title: "Chat – File Attachments – Upload Maximum 10 Files and Verify Limit Warning"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2197: Chat – File Attachments – Upload Maximum 10 Files and Verify Limit Warning

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that uploading more than 10 files shows a warning notification and only the first 10 are attached.

---

## Preconditions

- User is logged in to the Elitea platform.
- User has an open conversation and 11+ test files are available.

---

## Test Data

| Field | Value |
|-------|-------|
| File limit | 10 | Warning text | You've reached the 10-file limit. Only the first 10 will be processed. |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Click + icon, select 'Attach Files', upload 10 files | All 10 files shown as chips |
| 2 | Attempt to attach an 11th file via + icon > Attach Files | File picker opens |
| 3 | Select one more file | Warning notification appears at top of conversation |
| 4 | Verify warning: 'You've reached the 10-file limit. Only the first 10 will be processed.' | Warning text correct |
| 5 | Verify yellow/orange background with warning triangle | Warning styled correctly |
| 6 | Verify only 10 files remain attached | 11th file not added |

---

## Expected Final State

10-file limit enforced with correct warning.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Limit enforced; correct warning shown.

**Fail:**
- Any step produces an error or unexpected result.
- 11th file accepted or warning not shown.
