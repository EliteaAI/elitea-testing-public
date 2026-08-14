---
name: TMS back-write can go stale after a rework supersedes the original PR
description: A rework that merges a new PR superseding the original automation PR doesn't automatically update the TMS case's automation_pr field — re-check all four required back-write fields (execution_type, status, automation_test_id, automation_pr) after any rework, don't assume "test identity unchanged" means "back-write still complete"
type: feedback
---

## What happened

Control-audit of issue #28 (ELITEA-1738). Original PR #43 merged and back-
wrote the TMS case (`onetest-ai-tm-Elitea` commit `19208d9`, "automated via
elitea-testing-public#43"). The case was later reopened for a testid-only
rework, which merged as **PR #206** (superseding #43's shipped code). The
rework session's own log noted "TMS back-write unchanged (test identity/
`automation_test_id` never changed, only internal locators)" — reasoning
that since the test's class/function path didn't change, the back-write
needed no update.

Checking the frontmatter directly:

```yaml
status: ready
execution_type: automated
automation_test_id: tests.ui.skills.test_skill_export_import.TestSkillExportImportNonBaseVersion.test_import_skill_non_base_version
```

**`automation_pr` is absent from the frontmatter entirely** — not stale,
missing. It's unclear whether it was ever set (a check of the #43 back-write
commit would resolve that, but either way the case now needs the field
present and pointed at the PR that's actually live in `automation/base`).

## Why it matters

The rework reasoning ("identity didn't change, so no update needed") is
half right — it's true for `automation_test_id`, but `automation_pr` is a
*different* fact (which PR does the current, merged code live in) that a
rework by definition changes: the whole point of a rework is that the
originally-referenced PR's code no longer represents what's actually
running. A reader following `automation_pr` back to understand what shipped
would land on `#43` (now not what's on `automation/base`) or find nothing
at all.

## Rule going forward

1. Treat the closure-record checklist's traceability item as **all four
   fields, checked fresh, every time** — not "unchanged since the identity
   didn't change." `automation_test_id` and `automation_pr` are independent
   facts; a rework can leave one unchanged and require the other updated.
2. When a rework merges a new PR, always re-open the TMS case file and
   confirm `automation_pr` points at the PR that's actually merged into
   `automation/base` right now — update it even if `automation_test_id`
   genuinely didn't move.
3. As the control auditor: don't accept "test identity unchanged" as an
   implicit excuse for skipping the `automation_pr` check — grep the
   frontmatter for the literal field on every audit, independent of any
   claim about what did or didn't need updating.

## Recurrence (issue #32, ELITEA-1790 rework, PR #280)

Same failure, different shape: this time `automation_pr` wasn't missing,
it was **present but stale** — still `#48` (the superseded original PR)
instead of `#280` (the merged rework). Notable because the convention was
clearly known and followed in the SAME session window: sibling cases
ELITEA-1789 (`onetest-ai-tm-Elitea` commit `38b6766`) and ELITEA-1740
(commit `98f71dd`) both got an explicit "refresh automation_pr after
testid-only rework" commit. It was simply skipped for this one case.
Confirms the check needs to be **"does the field's PR number match the PR
that actually merged,"** not just **"is the field present"** — a populated
field can still be wrong, and per-case memory of "I usually do this" isn't
a substitute for checking each case's `git log` on the TMS file.
