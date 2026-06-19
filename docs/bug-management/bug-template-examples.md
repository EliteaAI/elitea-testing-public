# Bug Template — Examples

> This guide provides concrete examples of high-quality bug reports that are easy for QA, developers, and AI agents to reproduce and fix.

---

## Table of Contents

1. [Standard Bug Template (Copy/Paste)](#standard-bug-template-copypaste)  
2. [Example 1 — UI Bug](#example-1--ui-bug)  
3. [Example 2 — Backend/API Bug](#example-2--backendapi-bug)  
4. [Example 3 — Integration/Tooling Bug](#example-3--integrationtooling-bug)  
5. [Checklist (Before Submitting)](#checklist-before-submitting)  

---

## Standard Bug Template (Copy/Paste)

> Use this template for all bug reports.

### **Title**
`[BUG] <brief, informative title>`

### **Description**
- Brief, to the point description of what is wrong and why it matters.

### **Preconditions (optional)**
1. …
2. …

### **Steps to reproduce**
1. …
2. …
3. …

### **Test Data**
- Account: …
- Environment: DEV or STAGE
- Link(s):
  - Agent: …
  - Pipeline: …
  - Toolkit: …
  - MCP: …
  - Chat: …

### **Actual Result**
- …

### **Expected Result**
- …

### **Attachments**
- Screenshot(s): *(attach)*
- Video (optional): *(attach)*
- Logs (optional): *(paste or attach)*

### **Notes (optional)**
- …

---

## Example 1 — UI Bug

### **Title**
`[BUG] Pipeline flow does not display selected toolkit after saving`

### **Description**
When a user selects a toolkit for an MCP node and saves the pipeline, the toolkit selection is not displayed in the visual pipeline flow. This causes confusion and can lead to incorrect pipeline edits because the UI does not reflect the stored configuration.

### **Preconditions (optional)**
1. User has access to the Bugs & Features workspace/project in **DEV**.
2. A pipeline exists (or can be created) with an MCP node.

### **Steps to reproduce**
1. Go to **DEV** environment: `<link-to-dev>`
2. Open pipeline: `<pipeline-link>`
3. Add a **Remote MCP** node.
4. In node configuration, select toolkit: `<toolkit-name>`
5. Click **Save**.
6. Return to pipeline flow view.

### **Test Data**
- Environment: **DEV**
- Account: `qa_user_1` (role: QA)
- Pipeline: `<pipeline-link>`
- Toolkit: `<toolkit-link>`
- MCP: `<mcp-link>`
- Chat (if applicable): `<chat-link>`

### **Actual Result**
- The pipeline flow does not show the selected toolkit (field appears empty / default).

### **Expected Result**
- The selected toolkit is shown in the pipeline flow and matches the saved configuration.

### **Attachments**
- Screenshot 1: pipeline configuration with toolkit selected *(attach)*
- Screenshot 2: pipeline flow after save showing missing toolkit *(attach)*
- (Optional) Console/network logs *(attach/paste)*

### **Notes (optional)**
- Reproduced 3/3 times.
- No workaround found.

---

## Example 2 — Backend/API Bug

### **Title**
`[BUG] Summarization fails silently when conversation exceeds token threshold`

### **Description**
Summarization triggers successfully but the summary is not created when conversation token count is high. The UI indicates “summarizing” but the final summary is missing, causing users to lose expected output.

### **Preconditions (optional)**
1. Use **STAGE** environment.
2. Use a chat with long history (or generate one).

### **Steps to reproduce**
1. Open **STAGE**: `<link-to-stage>`
2. Open chat: `<chat-link-with-long-history>`
3. Trigger summarization: `<where/how>`
4. Wait for processing to complete.

### **Test Data**
- Environment: **STAGE**
- Account: `qa_user_2`
- Chat: `<chat-link>`
- Conversation: `<identifier>`
- Settings:
  - Model: `<model-name>`
  - Target Summary Tokens: `4096` (default)

### **Actual Result**
- Summarization completes but no summary is created (no output shown / empty summary).

### **Expected Result**
- Summary is created consistently regardless of conversation token count (or a clear error is shown if not possible).

### **Attachments**
- Screenshot: summarization triggered *(attach)*
- Screenshot: final state with missing summary *(attach)*
- Logs / error traces *(attach/paste)*

### **Notes (optional)**
- If a known limitation exists, UI must show a clear error message and guidance.

---

## Example 3 — Integration/Tooling Bug

### **Title**
`[BUG] Repo update_file tool returns confusing error when target file is missing`

### **Description**
When the automation tool attempts to update a file that does not exist in the target branch, the error message does not explain the root cause or remediation steps, which slows down troubleshooting and reduces automation reliability.

### **Preconditions (optional)**
1. Access to the repo tooling or automation interface in **DEV**.
2. A branch where the target file is intentionally absent.

### **Steps to reproduce**
1. Open tool interface: `<tool-link>`
2. Select repository: `<repo-name>`
3. Choose branch: `<branch-name>`
4. Run `update_file` for path: `<missing-file-path>`
5. Observe the result.

### **Test Data**
- Environment: **DEV**
- Repo: `<repo-link>`
- Branch: `<branch-name>`
- Missing file path: `<path>`
- Command payload (if applicable): *(paste JSON)*

### **Actual Result**
- The tool fails with an unclear error message that does not indicate the file is missing.

### **Expected Result**
- The tool returns a clear error:
  - file does not exist at path
  - suggested action: create file or correct path
  - include branch name and path in error details

### **Attachments**
- Screenshot: tool configuration *(attach)*
- Screenshot/log: returned error *(attach/paste)*

### **Notes (optional)**
- This affects automation and AI workflows; error clarity is critical.

---

## Checklist (Before Submitting)

- [ ] Title starts with `[BUG]` and is concise  
- [ ] Steps to reproduce are numbered and deterministic  
- [ ] Test Data includes all required links and identifiers  
- [ ] Actual and Expected results are clearly separated  
- [ ] At least one screenshot is attached (annotated where helpful)  
- [ ] Project fields are set in ELITEA Board (Type, Status=“Bugs”, Milestone, Priority, Criticality, Assignee)  
- [ ] Labels follow taxonomy (no new labels created)  
