---
id: ELITEA-2200
title: "Chat – File Error States – Verify Unsupported File Format Displays Error Message"
priority: medium
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2200: Chat – File Error States – Verify Unsupported File Format Displays Error Message

**Module:** chat-interface · **Priority:** medium · **Type:** functional

**Objective:** Verify that uploading an unsupported file type shows an error banner with the invalid formats and list of supported formats.

---

## Preconditions

- User is logged in to the Elitea platform.
- User has an open conversation and an unsupported file (e.g. .mp4, .exe) is available.

---

## Test Data

| Field | Value |
|-------|-------|
| Unsupported format | .mp4 or .exe |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Click + icon, Attach Files; select an unsupported file type | File selected |
| 2 | Verify an error notification/banner appears at top of conversation | Error banner shown |
| 3 | Verify banner text: 'Invalid file types detected:' followed by filename and supported formats list | Error text contains filename and supported formats |
| 4 | Verify the error banner can be dismissed by clicking X | Banner dismissed |
| 5 | Verify the unsupported file is NOT added to the attachment area | File not attached |

---

## Expected Final State

Unsupported file type rejected with informative error banner.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- Error banner shown; unsupported file not attached.

**Fail:**
- Any step produces an error or unexpected result.
- Unsupported file accepted or error not shown.
