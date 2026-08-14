---
name: UNDER REVIEW AFS Automation Hints still recommend the forbidden mock
description: An AFS marked "UNDER REVIEW — fidelity audit, do not reuse as pattern" may still carry an unedited Automation Hints paragraph recommending the mock the audit itself condemned — read past the banner, don't stop at it
type: feedback
---

## What happened (PR #1502, ELITEA-1990/1991/1993 fidelity rework review, 2026-08-14)

The three AFS files this PR's tests trace to
(`test-specs/skills/l2_generated-skill-draft-fields-are-editable-before-creation_ELITEA-1990.md`,
`test-specs/skills/lextend_create-skill-from-draft-saves-and-redirects-to-skill-details_ELITEA-1991.md`,
`test-specs/skills/l2_build-with-ai-name-field-validation_ELITEA-1993.md`) each
carry the 2026-08-14 fidelity-audit banner at the top ("UNDER REVIEW ... Do NOT
reuse this AFS as a pattern"). Correct and sufficient as a warning — but each
AFS's own **§ Automation Hints** section, further down the same document, still
reads "Recommend mocking the `generate_skill_draft` response ... for
determinism" (ELITEA-1990/1993) or "Reuse
`GenerateSkillModalPage.mock_generate_success(...)` to mock the draft response
for determinism" (ELITEA-1991) — i.e. the exact technique the banner exists to
retire, unedited, in the implementer-facing instructions section a future
reader is most likely to skim straight to.

The banner was written by the audit pass; the Automation Hints paragraph
predates it and nobody swept the rest of the document when the banner was
added. This PR's implementer worked from the **tech-task brief**
(`.agents/automation/skills-buildwithai-fidelity-rework/briefs/mixed-1990-1991-1993.md`),
not the stale hints, so the actual rework is correct — the finding is about
what these three AFS files will tell the *next* reader who opens them without
the brief in hand.

## The lesson

When reviewing (or writing) an AFS carrying an "UNDER REVIEW / do not reuse as
pattern" banner, don't treat the banner alone as sufficient — grep the rest of
the same file for the retired technique's name (`mock_generate_success`,
`page.route`, etc.). A banner at the top does not retroactively edit a
paragraph three screens down. This is the same failure shape as
`afs_drift_check_the_whole_document_not_just_the_last_fixed_section.md` (a
different incident, same root cause: partial edits leave stale sections that
look authoritative). Non-blocking on a rework PR that didn't touch the AFS
file (the code is what's under review, and the brief — not the stale
Automation Hints — is the operative instruction) — but worth a sweep pass if
the #1298/#1399 audit closes out AFS files individually, since the same
paragraph shape likely recurs in the agents-side AFS files under the same
audit.
