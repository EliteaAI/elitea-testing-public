---
name: Analyst screenshot-upload claim needs independent verification
description: An analyst's own report ("screenshots uploaded/embedded") can be false — the filed issue can still carry bare local .png filenames; verify via embed-evidence --dry-run or a body_html grep before trusting it, same discipline as the existing narration-not-pasted-evidence class
type: feedback
---

## What happened (#268/ELITEA-1846, 2026-07-20)

The analyst's final report to the orchestrator stated "Two screenshots
uploaded/embedded" for the defect it filed (#677). Trusting that summary would
have been wrong: the actual issue body only referenced bare local filenames as
plain text (`ELITEA-1846-BUG-stale-selection-verify2-reproduced.png (repo
root, untracked)`) — zero `releases/download` links, zero markdown image
syntax (`![...]`). A direct violation of `.agents/role-overrides.md` §
screenshot evidence ("ANY local path OR bare `.png` filename... must be
uploaded + embedded"), and the exact anti-pattern that section calls out by
name.

## Why this is a distinct failure class

This is NOT the already-documented `reviewer_narration_is_not_pasted_evidence`
pattern (a reviewer describing a check in prose instead of pasting output) —
that's about *evidence for a claim*. This is a subagent's **self-report about
its own completed action** being factually wrong: it said it did X, and X
provably did not happen. The two failure modes need the same fix (verify,
don't trust the narrative) but the target is different — one checks "is there
proof this was checked", the other checks "did the claimed action actually
occur".

## The fix

Don't take "uploaded/embedded" (or similarly, "filed", "pushed", "committed")
at face value from any subagent's final report when the claim is
mechanically checkable. For screenshot evidence specifically: run the
installed `embed-evidence` skill in `--dry-run` mode against the filed
issue(s) before considering the delivery done — it's a deterministic,
no-LLM check that reports exactly which issues still carry unembedded
references. If it finds something, run it live (it batches cleanly — this
run also repaired 3 unrelated pre-existing dirty issues from earlier
sessions in the same pass). Confirm the fix landed via a `body_html` grep
for `releases/download` / `<img`, not just re-reading the raw markdown body
(which will show the intended `![...]()` syntax even if GitHub's rendering
pipeline choked on it for some reason — the rendered HTML is the real proof).

## Generalizes to

Any subagent report claiming a tracker/evidence-store side-effect completed
("uploaded", "pushed", "filed", "linked") is cheap to spot-check
mechanically before it becomes the basis for "this case is ready to
merge/close." Prefer a deterministic check (a skill, a grep, an API
read-back) over re-reading the subagent's own prose.
