---
name: ELITEA-2336 PR #1204 R4 — round-3 matcher fix left the AFS's Expected Results text stale
description: The R3 fix correctly dropped the "SecretsContent.jsx" requirement from _is_known_defect_1203() (code + new unit test), but the AFS's Expected Results section still says the filter requires both substrings — the exact AFS-drift class this project's reviewer contract targets
type: feedback
---

## What happened

Re-reviewing PR #1204 (ELITEA-2336) round 4, after round 3's fix for the prior
blocking finding (`elitea_2336_pr1204_r3_known_1203_matcher_too_strict.md`).
Verified the code fix is correct: `_is_known_defect_1203()` now matches on
`"Maximum update depth exceeded" in text` alone (dropped the
`"SecretsContent.jsx"` AND-clause), and a new
`tests/unit/test_secret_create_inline_known_defect_1203_matcher.py` pins
both the long-form (with stack) and short-form (without stack) shapes as
matched, plus an unrelated error as unmatched — good regression coverage,
same shape as the #518 precedent in `test_credential_create.py`.

But round 3's commit (`86fb3cc6`) only touched the two test files — it never
touched the AFS
(`test-specs/settings-secrets/l3_create-secret-inline-checkmark-x-cancel_ELITEA-2336.md`).
The AFS's "Expected Results" section (line ~132, amended in round 2) still
reads: *"soft-asserted via the `soft_failures`/`pytest.fail()` idiom,
filtered by exact signature (`"Maximum update depth exceeded"` +
`"SecretsContent.jsx"`)"* — describing the OLD dual-substring matcher that
round 3 explicitly proved too fragile and replaced. A future reader of the
AFS (or an auditor grepping AFS Expected Results for the matcher contract)
gets a false picture of what the code actually filters on.

## Why this blocks

Reviewer-contract § Standing reviewer checks: *"AFS amendments — any
selector / observable drift between AFS and implementation must be
reflected in an AFS docs commit in the same PR."* The matcher's filter
condition IS an observable the AFS documents explicitly (it's spelled out
as a parenthetical in the Expected Results prose) — this isn't a case of
"the AFS never mentioned this detail so no update is owed." It mentioned
the exact wrong detail, in the same PR that changed it.

## Durable lesson

**A fix round that changes matcher/filter LOGIC should grep the AFS for
any prose describing that logic's specifics** (exact strings, substrings,
"filtered by X and Y") — not just update the code + add a regression test.
Fixing the code without fixing the AFS narration of the code is the same
species of drift as `afs_narration_vs_afs_edit` gotchas logged for earlier
rounds of this same case (see
`.agents/memory/test-automation-engineer/` fix-round-1 lesson) — it just
shows up on the REVIEWER side this time instead of the implementer side.
