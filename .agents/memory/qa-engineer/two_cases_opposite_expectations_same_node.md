---
name: Two TMS cases asserting opposite expectations at the same DOM node
description: How to review a spec that hard-asserts behaviour another merged spec soft-asserts as a known defect
type: feedback
aliases: [contradictory cases, opposite expected result, "#649", "#1629", currentPrefix, reverse-masking]
tags: [area/artifacts, type/review-trap]
created: 2026-08-21
updated: 2026-08-21
---

## The trap

ELITEA-1834's spec (`test_artifacts_upload_to_selected_subfolder.py`) HARD-asserts
`{bucket}/a1/` in the bucket-menu upload dialog as CORRECT, while the merged
ELITEA-1824 spec (`test_artifacts_upload_three_options_verify_selection.py:445-467`)
SOFT-asserts the opposite value at the same DOM node as KNOWN DEFECT #649.
Reflex reaction — "one of these is masking / one must be wrong, block it" — is wrong.

## How to review it

1. The masking hunt is about *weakening*: a hard assert on the live contract is
   the STRONGEST form, never masking. Nothing to block on that axis.
2. Reverse-masking guard: the live product matches THIS case's text exactly, so
   `ready-for-automation` + assert-the-live-contract is the doctrinally correct
   route. The contradiction is a **case-text** dispute, not a product/test defect.
3. What the reviewer must actually verify is the *declaration chain*, statically:
   a `question`/clarification card exists and is OPEN (here #1629), the module
   docstring names both issues at the point of reading, and the AFS + surface
   digest say "do not align one spec to the other before the ruling".
   All four present ⇒ APPROVED; any missing ⇒ that's the blocker, not the assert.
4. Verify the AFS's overlap-rejection argument against the neighbour's ACTUAL
   assertion (open the file, read the line) — never against the neighbour merely
   existing. Here 1824 abandons the dialog and re-uploads from root, so it proves
   nothing about where the file lands; `already-covered`/`extend-existing` were
   correctly rejected.
5. Flag for the lead: whoever resolves the clarification must touch BOTH specs,
   and one of them will flip. Cross-link the cards.

Related: [[artifacts_surface_digest]]
