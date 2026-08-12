---
id: ELITEA-2059
title: "Pipeline — Attach Files in Chat"
priority: medium
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2059: Pipeline — Attach Files in Chat

**Module:** pipelines · **Priority:** medium · **Type:** functional

**Objective:** Verify that files can be attached in the chat panel of a pipeline with the Attachments module enabled, and that the attachment is processed by the pipeline.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline with the Attachments module enabled is open.

---

## Test Data

| Field | Value |
|-------|-------|
| File type | .txt or .png |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline that supports attachments (Attachments module enabled in Tools) | Pipeline is open with attachments-enabled chat panel |
| 2 | In chat panel, locate "Attach Files (10 left)" button | Attach files button is visible and enabled |
| 3 | Click the attach files button | File picker opens |
| 4 | Upload a supported file (e.g., a .txt or .png file) | File is uploaded and appears as attachment |
| 5 | Verify file appears as attachment in the message area | Attachment thumbnail or name is shown in the message area |
| 6 | Send a message referencing the file | Message with attachment is sent |
| 7 | Verify pipeline processes the attachment | Pipeline responds with content referencing or processing the attached file |

---

## Expected Final State

A file is successfully attached in the chat, included in the sent message, and the pipeline processes the attachment and produces a relevant response.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- File is attached, shown in message area, sent, and pipeline processes it.

**Fail:**
- Any step produces an error or unexpected result.
- File cannot be attached, is not shown, or pipeline does not process the attachment.
