---
name: Build with AI review-form Name field 32-char validation blocks Approve
description: Unlike agent-name-input's silent truncation, the Build-with-AI review form's Name field BLOCKS approve (disabled button) past MAX_NAME_LENGTH=32
type: feedback
---

Distinct from `pipeline_agent_name_field_32char_silent_truncation.md` (the
regular `agent-name-input` on `ApplicationEditForm.jsx`, which silently
truncates on overflow, no error).

The "Build with AI" review form's Name field
(`generate-agent-review-name-input`, `GenerateAgentReviewForm.jsx`) goes
through a DIFFERENT code path: `validateAgentDraft()`
(`agentDraftValidation.helpers.js`) checks `name.length > MAX_NAME_LENGTH`
(32, `common/constants.js`) and sets `isDraftValid = false` when it fails —
which disables `generate-agent-approve-button` (`Create Agent`) entirely.
`.fill()` on the input still succeeds (the DOM value is whatever you set),
so a naive `get_review_name() == edited_name` assertion passes — the
failure only shows up later, as a `Locator.click: Timeout … element is not
enabled` on the Approve button click, which reads like an unrelated flake
if you don't already know the cap.

**Confirmed live (ELITEA-1912):** the FIELD_POPULATION_DRAFT_PAYLOAD
generated name `"JIRA Ticket Description Writer"` is already 30 chars — the
established `f"{name} [edited]"` suffix convention (9 more chars = 39) blew
the cap and left Approve permanently disabled. Fix: use a short standalone
literal for the Name field specifically (e.g. `"Edited Agent Name [1912]"`,
25 chars) instead of suffixing; the other 4 review-form fields
(Description/Instructions/Welcome Message/Chat starter, caps 2304/none/768/
768) have ample headroom for the suffix convention.

**Any new Build-with-AI test that edits the review-form Name field must
budget for `MAX_NAME_LENGTH = 32` against the ACTUAL generated/mocked draft
name being used** — count it, don't assume a short-looking suffix is safe.
