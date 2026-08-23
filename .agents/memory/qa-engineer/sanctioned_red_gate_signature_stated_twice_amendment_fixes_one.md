---
name: Sanctioned-RED gate signature is stated in TWO artifacts — an amendment that fixes one leaves the other steering the gate
description: PR #1678/ELITEA-1810 — AFS Step 13 amended to "ExceptionGroup of 2 sub-exceptions", but the AFS § Known Defects bullet AND the test docstring both still said "exactly ONE soft failure"; the docstring is what the lead reads at gate time
type: feedback
aliases: [gate signature drift, sanctioned red signature, soft failure count, expect.soft count]
tags: [area/review, type/drift]
created: 2026-08-23
updated: 2026-08-23
---

## What happened

ELITEA-1810 ships one sanctioned-RED step (#1677 — a Months retention policy
reopens as Days). The implementer correctly wrote **two** `expect.soft()`
assertions at Step 13 (measure text AND value), so the spec's real gate
signature is a pytest `ExceptionGroup` carrying **2** sub-exceptions from one
cause — and the implementer amended the AFS's Test Step 13 to say exactly
that, explicitly contradicting the analyst's original wording.

The same claim, however, lives in two more places that were never swept:

- `test-specs/artifacts/l2_..._ELITEA-1810.md:282` (§ Known Defects bullet 1)
  — "This spec's gate signature is: exactly one soft failure at step 13."
- `automation/tests/ui/artifacts/test_artifacts_bucket_retention_edit_persistence.py:53`
  (module docstring) — "This spec's gate signature is exactly ONE soft
  failure, at Test Step 13."

## Why it is worth blocking on

`.agents/testing.md` § Merge gate makes the sanctioned-RED signature
load-bearing: the lead classifies the 3× gate run against the stated
signature, and "any AFS / Run Report sentence claiming otherwise mis-steers
this gate". A 2-sub-exception `ExceptionGroup` measured against a documented
"exactly one soft failure" reads as an *unknown extra failure* — the lead
either blocks a correct spec or, worse, waves through a genuinely new second
cause as "the known defect".

## Reviewer technique

When a spec carries a sanctioned-RED step, grep the fact-string — the number
of soft failures — across **both** artifacts, not just the AFS:

```bash
grep -rn "soft failure\|ExceptionGroup\|expect.soft" <afs> <spec>
```

Then count the actual `expect.soft(` calls in the diff and check the stated
number matches. The **test docstring** is the artifact the gate operator
reads first, and it is the one an AFS-focused drift sweep misses.

Related: [[afs_drift_check_the_whole_document_not_just_the_last_fixed_section]] ·
[[afs_amendment_narrates_some_changes_leaves_others_unswept]]
