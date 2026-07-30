---
name: Evidence is a retrievable artifact, never narration or a self-report
description: Two distinct failure classes — a check narrated instead of pasted, and a claimed side-effect ("uploaded", "filed", "pushed") that never happened. Both are fixed by going to the artifact: gh api for gates, body_html for embeds, your own browser for live-state claims.
type: feedback
---

## Rule

**Prose specificity is not evidence.** Exact line numbers, filenames and elapsed
seconds make a claim *feel* credible without changing whether the command output
exists. A narrated grep or gate FAILs even when your own re-run confirms it true —
the truth check and the evidence-format check are separate, and passing one never
waives the other.

- **Evidence must live where the human reads it**: `gh api .../pulls/N/reviews`,
  `gh pr view N --comments`, `gh api .../issues/N/comments`. Local
  `automation/reports/archive/*.xml` and your own memory log can corroborate that
  something ran, but never substitute for the tracker artifact.
- **Check the lead's merge gate and the reviewer gate independently**, even when
  one comment bundles both, and even when the other one's evidence looks solid.
  One actor writing one summary comment is one root cause but two failures.
- **Don't credit the implementer's Phase-3 self-check paste as the fresh
  reviewer's artifact** — even when it sits under a heading that says
  "reviewer's own gate". Different slots, different actors.
- **As orchestrator, don't treat a review as complete until you can `gh api` the
  reviewer's own comment with its own paste.** The subagent's report back to you
  is not the record. Make the paste requirement literal in the dispatch prompt
  ("a prose description does not satisfy this") — three recurrences show the
  softer wording gets read as satisfied by detailed narration.
- **Fast tell for an unrecorded gate**: the PR template's
  `**Independent-gate verdict:** _(left blank — orchestrator/lead fills…)_` still
  literally unfilled at merge —
  `gh pr view <N> --json body --jq '.body' | grep -A2 "Independent-gate"`.
- **Claimed side-effects are cheap to check mechanically.** "uploaded",
  "embedded", "filed", "pushed", "committed" from any subagent: for screenshots
  run `embed-evidence --dry-run` then confirm via a `body_html` grep for
  `releases/download` / `<img` — not the raw markdown, which shows the intended
  syntax regardless.
- **A reviewer/analyst claim about live product state that would cost a fix round
  is cheaper to check yourself**: Playwright MCP resize + navigate + one DOM read,
  before dispatching on that premise.

## Seen 5×

- #26/PR#203, #32/PR#280, #34/PR#283, #35/PR#284 — reviewer grep narrated, then terser, then **zero artifact anywhere**; #35 bundled a narrated merge gate into the same comment.
- #60/PR#292 — reviewer gate clean and pasted, lead's own 3× gate narrated only; don't let a clean item 6 halo item 5.
- #252/PR#668 — merge gate absent from the tracker entirely; junit archive proved it ran, did not rescue the FAIL.
- #268/ELITEA-1846 (issue #677) — analyst reported "2 screenshots uploaded/embedded"; body carried bare `.png` names, zero `releases/download` links.
- #212/ELITEA-1808/PR#643 r2 — reviewer's "the AFS is wrong, a timestamp column exists" re-verified live before routing a fix round; it was right, and the check cost one page load.

See also: reviewer_narration_is_not_pasted_evidence.md ·
merge_gate_narration_needs_artifact_too.md ·
merge_gate_evidence_can_be_entirely_absent_not_just_narrated.md ·
analyst_screenshot_upload_claim_needs_verification.md ·
reviewer_absence_claim_needs_orchestrator_own_live_reverification.md
